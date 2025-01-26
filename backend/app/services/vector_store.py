
import os
import uuid
from dotenv import load_dotenv

# LangChain imports
# from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings  
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document

load_dotenv()


class ChromaVectorStore:
    """
    Stores user text in a local Chroma DB, uses AzureOpenAIEmbeddings from langchain-openai.
    Make sure your environment variables are set:
      AZURE_OPENAI_ENDPOINT=https://<my-resource>.openai.azure.com
      AZURE_OPENAI_API_KEY=...
      AZURE_OPENAI_VERSION=...
      AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
    """

    def __init__(self, persist_directory: str = ""):
        # 1) Instantiate the Azure OpenAI embeddings
        #    'model' is the Azure embedding deployment (ex: "text-embedding-ada-002")
        #    If you also set them in env, you can omit the parameters below,
        #    but we'll show them for clarity.

        self.embeddings = AzureOpenAIEmbeddings(
            model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
            # If not given, it’ll read from AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, etc.
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            openai_api_version=os.getenv("AZURE_OPENAI_VERSION", "2024-06-01"),
        )

        # 2) Create a local Chroma VectorStore using LangChain
        #    "collection_name" is optional, default is "langchain"
        #    If persist_directory is "", it's in-memory only. If you want actual disk storage, set a path.
        self.persist_directory = persist_directory or None
        self.db = Chroma(
            collection_name="collab_writing",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def store_text(self, text: str):
        """
        Insert a single text into the Chroma store.
        """
        # lets generate a random ID or you can store metadata ... you can do this as optional method if u want
        doc_id = str(uuid.uuid4())

        # By default, add_texts returns a list of doc-ids from Chroma
        self.db.add_texts(texts=[text], metadatas=[{"id": doc_id}])

        # If persist_directory was set, you can do self.db.persist() to save on disk, also something u can choooose
        if self.persist_directory:
            self.db.persist()

    def search_similar(self, query_text: str, n_results: int = 3):
        """
        Retrieve docs from Chroma using similarity_search.
        Returns a dict with "documents" so manager.py usage remains unchanged.
        """
        # similarity_search returns a list of Document objects
        docs = self.db.similarity_search(query_text, k=n_results)

        # manager.py expects results["documents"] to be list of list-of-strings
        # This will  put all doc.page_content in one list
        # then wrap that in another list as in your existing code.
        doc_texts = [doc.page_content for doc in docs]

        return {"documents": [doc_texts]}
