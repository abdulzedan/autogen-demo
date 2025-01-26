# backend/app/services/agents.py

import os
import json
import logging
from dotenv import load_dotenv

from typing import Dict, Any, List
from autogen import ConversableAgent

# Azure Bing search imports
from azure.cognitiveservices.search.websearch import WebSearchClient
from msrest.authentication import CognitiveServicesCredentials

import openai
from pydantic import BaseModel

load_dotenv()

# -------------- LOGGING CONFIGURATION --------------
# Adjust the logging level as needed (DEBUG, INFO, WARNING, etc.). FOr production, use INFO or WARNIN G
logging.basicConfig(level=logging.DEBUG)

class ExtractedReferences(BaseModel):
    references: List[str]



def bing_search(query: str) -> str:
    """
    Perform a Bing web search via direct requests to the /v7.0/search endpoint.
    """
    subscription_key = os.getenv("BING_SEARCH_SUBSCRIPTION_KEY", "")
    # Notice we explicitly append /v7.0/search to match your working test file
    endpoint = os.getenv("BING_SEARCH_ENDPOINT", "") + "/v7.0/search"

    if not subscription_key or not endpoint:
        logging.warning("No Bing search configured. Returning placeholder info.")
        return f"No Bing search configured. (Would have searched '{query}')"

    try:
        headers = {
            "Ocp-Apim-Subscription-Key": subscription_key
        }
        params = {
            "q": query,
            "mkt": "en-US",
        }
        logging.debug(f"[bing_search] GET {endpoint} (q={query})")
        import requests
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        # The Bing JSON has "webPages" if it finds something
        web_pages = data.get("webPages", {}).get("value", [])
        if web_pages:
            first_page = web_pages[0]
            snippet = f"First webpage result: {first_page['name']}\nURL: {first_page['url']}"
            return snippet
        else:
            return f"No Bing results found for '{query}'."

    except Exception as e:
        logging.error(f"Bing search exception: {e}")
        return f"Bing search exception: {e}"



# ------------------ System Messages ------------------
factcheck_system_message = """
You are the FactCheck Agent. You do the following steps internally:

1) Identify references (people, places, historical facts) in the text.
2) For each reference, call bing_search(...) to see if it's accurate.
3) Rewrite the text with corrections or disclaimers based on the results.
4) Return the final corrected text plus a short note describing changes.

We will do the extracting references with structured output,
then do another call to incorporate the results.
"""

idea_system_message = """
You are the Idea Agent.
ROLE:
- Provide fresh, imaginative, or comedic ideas.
- Emphasize creativity over factual accuracy.

GUIDELINES:
1) If the user wants comedic style, be playful.
2) Summaries or outlines can be short or extended.
3) Factual correctness is not your primary job.
"""

editor_system_message = """
You are the Editor Agent.
ROLE:
- Polish style, grammar, clarity, and flow.
- Keep comedic or creative tone if user wants it.

GUIDELINES:
1) Keep disclaimers if provided by FactCheck.
2) Add subtle humor or playful wording if suits user’s request.
3) Return final text that is cohesive and user-friendly.
"""

# ------------------ LLM Configuration ------------------
base_llm_config = {
    "config_list": [
        {
            "model": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
            "api_type": "azure",
            "base_url": os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/"),
            "api_version": os.getenv("AZURE_OPENAI_VERSION", "2024-10-21"),
            
        }
    ],
}

def is_termination_msg(message: Dict) -> bool:
    """
    A simple check to see if the content is "exit" or "quit".
    """
    content = message.get("content", "").strip().lower()
    return content in ["exit", "quit"]


# ------------------ FactCheckAgent ------------------
class FactCheckAgent(ConversableAgent):
    def __init__(self):
        super().__init__(
            name="fact_checker",
            system_message=factcheck_system_message,
            is_termination_msg=is_termination_msg,
            human_input_mode="NEVER",
            llm_config=base_llm_config,
            code_execution_config=False,
        )

    def generate_reply(self, messages=None, sender=None, **kwargs: Any) -> str:
        """
        Overridden to do a 2-step approach:
          1) GPT structured output parse references
          2) For each reference, do bing_search
          3) Another GPT call to finalize text
        We'll return the final text as the agent's "assistant" message.
        """
        if not messages:
            logging.debug("[FactCheckAgent] No messages to process.")
            return "No text to check."

        # The last content is typically the text from the IdeaAgent
        story_text = messages[-1].get("content", "")
        logging.debug(f"[FactCheckAgent] Story text to check:\n{story_text}")

        # Step A: Extract references
        references = self._extract_references_gpt(story_text)
        logging.debug(f"[FactCheckAgent] Extracted references: {references}")

        # Step B: Bing searches
        bing_results = {}
        for ref in references:
            snippet = bing_search(ref)
            bing_results[ref] = snippet
        logging.debug(f"[FactCheckAgent] Bing results:\n{json.dumps(bing_results, indent=2)}")

        # Step C: Rewrite text
        corrected_text = self._rewrite_text_gpt(story_text, references, bing_results)
        logging.debug(f"[FactCheckAgent] Corrected text:\n{corrected_text}")

        return corrected_text

    def _extract_references_gpt(self, text: str) -> List[str]:
        """
        Use GPT in structured-output mode to parse references from the text....
        """
        # Keep your AzureOpenAI usage as-is:
        from openai import AzureOpenAI

        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            api_version="2024-10-21", 
        )

        system_prompt = """
You are a sub-process for fact-checking.
Return a JSON with a 'references' array of strings for each real-world name, place, or date.
If none found, return an empty array.
"""
        user_prompt = f"Text to parse:\n\n{text}\n\nExtract references in a 'references' array."

        # Using the parse() method from autogen or your custom AzureOpenAI:
        completion = client.beta.chat.completions.parse(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=ExtractedReferences,
        )

        parsed_obj = completion.choices[0].message.parsed
        return parsed_obj.references

    def _rewrite_text_gpt(
        self, original_text: str, references: List[str], bing_data: Dict[str, str]
    ) -> str:
        """
        Given the original text, references, and Bing snippets,
        produce final corrected text plus a short note on changes.
        """
        from openai import AzureOpenAI

        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            api_version="2024-10-21", 
        )

        system_prompt = """
You are a fact-check rewriting module.
You have:
 - An original text
 - A list of references
 - A dictionary of Bing results for each reference

Correct or disclaim the text as needed. 
Then return the final text plus a short note about changes at the end.
"""

        user_prompt = f"""
Original text:
{original_text}

References found: {references}

Bing results:
{json.dumps(bing_data, indent=2)}

Rewrite the text with corrections or disclaimers. 
End with a short "Note:" describing what changed.
"""

        completion = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        final_text = completion.choices[0].message.content
        return final_text


# ------------------ IdeaAgent ------------------
class IdeaAgent(ConversableAgent):
    def __init__(self):
        super().__init__(
            name="idea_agent",
            system_message=idea_system_message,
            is_termination_msg=is_termination_msg,
            human_input_mode="NEVER",
            llm_config=base_llm_config,
            code_execution_config=False,
        )

    def generate_reply(self, messages=None, sender=None, **kwargs):
        """
        Optionally, you could add logging to see your idea-generation step.
        """
        if messages:
            logging.debug("[IdeaAgent] Received messages for creative idea generation.")
        return super().generate_reply(messages=messages, sender=sender, **kwargs)


# ------------------ EditorAgent ------------------
class EditorAgent(ConversableAgent):
    def __init__(self):
        super().__init__(
            name="editor",
            system_message=editor_system_message,
            is_termination_msg=is_termination_msg,
            human_input_mode="NEVER",
            llm_config=base_llm_config,
            code_execution_config=False,
        )

    def generate_reply(self, messages=None, sender=None, **kwargs):
        """
        You could add logging if you want to see the polished text.
        """
        if messages:
            logging.debug("[EditorAgent] Received messages for editing/polish.")
        return super().generate_reply(messages=messages, sender=sender, **kwargs)
