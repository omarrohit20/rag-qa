import os
from dotenv import load_dotenv

load_dotenv()

# Use free models: groq or cohere
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "groq")

# Groq - FREE API (llama-3.3-70b-versatile, llama-3.1-8b-instant)
# Get free key at: https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Cohere - Free tier (command-r-plus)
# Get free key at: https://dashboard.cohere.com
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r-plus")

# OpenAI (optional - has quota issues)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Anthropic (optional)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet")

# Jira
JIRA_BASE_URL = ""
JIRA_EMAIL = ""
JIRA_API_TOKEN = ""

# Figma
FIGMA_TOKEN = ""

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
