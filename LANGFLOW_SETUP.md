# Langflow + Free Models Setup Guide

## Quick Start with Free Models

Your project has been updated to use **free LLM APIs** via Langflow instead of costly providers.

### Option 1: Groq (Recommended - FREE)

**Setup:**
1. Get free API key: https://console.groq.com
2. Create `.env` file:
   ```
   MODEL_PROVIDER=groq
   GROQ_API_KEY=your_key_here
   GROQ_MODEL=mixtral-8x7b-32768
   ```
3. Run:
   ```bash
   python -m src.rag_test_generator --demo
   ```

**Free models available:**
- `mixtral-8x7b-32768` (Recommended - faster, high quality)
- `llama2-70b-4096`
- `gemma-7b-it`

### Option 2: Cohere (FREE TIER)

**Setup:**
1. Get free API key: https://dashboard.cohere.com
2. Create `.env` file:
   ```
   MODEL_PROVIDER=cohere
   COHERE_API_KEY=your_key_here
   COHERE_MODEL=command-r-plus
   ```
3. Run:
   ```bash
   python -m src.rag_test_generator --demo
   ```

### Quick Test (No API needed)

Run in dry-run mode to test the pipeline without LLM calls:
```bash
python -m src.rag_test_generator --demo --dry-run
```

## Files Updated

1. **src/config.py** - Now reads from Groq/Cohere/OpenAI API keys
2. **src/rag/pipeline.py** - Added support for Groq and Cohere LLMs
3. **requirements.txt** - Added `langchain-groq` dependency
4. **.env.local** - Template for environment variables

## API Key Setup

### Get Groq API Key (FREE)
1. Visit: https://console.groq.com
2. Sign up (free)
3. Go to API Keys section
4. Create new key
5. Copy and paste into `.env`

### Get Cohere API Key (FREE TIER)
1. Visit: https://dashboard.cohere.com
2. Sign up
3. Go to API Keys
4. Create new key
5. Free tier includes API access (limited rate)

## Environment Variables

Create a `.env` file in the project root:

```env
MODEL_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
GROQ_MODEL=mixtral-8x7b-32768
```

Or use environment variables in terminal:
```powershell
$env:MODEL_PROVIDER="groq"
$env:GROQ_API_KEY="your_key_here"
python -m src.rag_test_generator --demo
```

## Troubleshooting

**Error: "No LLM provider configured"**
- Ensure MODEL_PROVIDER is set in `.env` or as env var
- Verify API key is set for the chosen provider

**Error: "Invalid API key"**
- Double-check your API key is correct
- Regenerate key if needed

**Error: "Rate limit exceeded"**
- Groq/Cohere have rate limits on free tier
- Wait a few seconds and retry

## Next Steps

1. Set up `.env` with your free API key
2. Run demo: `python -m src.rag_test_generator --demo`
3. Connect to Jira/Figma for real data
4. Generate test artifacts

Happy testing!
