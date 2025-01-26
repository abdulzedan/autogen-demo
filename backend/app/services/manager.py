import logging
from typing import Dict, List
from pydantic import BaseModel
from .agents import IdeaAgent, FactCheckAgent, EditorAgent

logging.basicConfig(level=logging.DEBUG)

class PipelineStep(BaseModel):
    role: str
    color: str
    content: str

class MultiAgentManager:
    def __init__(self):
        self.idea_agent = IdeaAgent()
        self.fact_agent = FactCheckAgent()
        self.editor_agent = EditorAgent()

    def process_user_message(self, user_message: str) -> Dict:
        """
        Returns { "steps": [ {role, color, content}... ] }
        for the pipeline of Idea -> FactCheck -> Editor.
        """

        logging.debug(f"[MultiAgentManager] User message: '{user_message}'")

        steps = []

        # --- (1) IdeaAgent ---
        idea_chat = self.idea_agent.initiate_chat(
            recipient=self.fact_agent,
            clear_history=True,
            message=user_message,
            max_turns=1
        )
        idea_out = idea_chat.summary or ""
        logging.debug(f"[MultiAgentManager] IdeaAgent output:\n{idea_out}")

        steps.append(PipelineStep(
            role="Idea Agent",
            color="#FFC107",  # amber
            content=idea_out
        ))

        # --- (2) FactCheckAgent ---
        fact_chat = self.fact_agent.initiate_chat(
            recipient=self.editor_agent,
            clear_history=True,
            message=idea_out,
            max_turns=1
        )
        fact_out = fact_chat.summary or ""
        logging.debug(f"[MultiAgentManager] FactCheckAgent output:\n{fact_out}")

        steps.append(PipelineStep(
            role="FactCheck Agent",
            color="#03A9F4",  # light blue
            content=fact_out
        ))

        # --- (3) EditorAgent ---
        edit_chat = self.editor_agent.initiate_chat(
            recipient=self.editor_agent,
            clear_history=True,
            message=fact_out,
            max_turns=1
        )
        final_text = edit_chat.summary or ""
        logging.debug(f"[MultiAgentManager] EditorAgent output:\n{final_text}")

        steps.append(PipelineStep(
            role="Editor Agent",
            color="#8BC34A",  # green
            content=final_text
        ))

        return {
            "steps": [step.dict() for step in steps]
        }
