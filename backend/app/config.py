import os
from dotenv import load_dotenv

# If you have a .env file, uncomment:
load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_BASE = os.getenv("AZURE_OPENAI_API_BASE", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_DEPLOYMENT_ID = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

# If you don't have the environment variables set, 
# and these remain empty, you'll get a credentials error from AzureOpenAI... make sure u adjust accordingly 
# Make sure they're set properly before running uvicorn.
