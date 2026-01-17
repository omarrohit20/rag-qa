import os
from dotenv import load_dotenv

load_dotenv()

# Use free models: groq or cohere
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "groq")

# Groq - FREE API (llama-3.3-70b-versatile, llama-3.1-8b-instant)
# Get free key at: https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Cohere - Free tier (command-r-plus-08-2024)
# Get free key at: https://dashboard.cohere.com
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "YOUR_COHERE_API_KEY_HERE")
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r-plus-08-2024")

# OpenAI (optional - has quota issues)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Anthropic (optional)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY_HERE")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet")

# Jira
JIRA_BASE_URL = "JIRA_BASE_URL_HERE"
JIRA_EMAIL = "JIRA_EMAIL_HERE"
JIRA_API_TOKEN = "YOUR_JIRA_API_TOKEN_HERE"

# Figma
FIGMA_TOKEN = "YOUR_FIGMA_TOKEN_HERE"

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
