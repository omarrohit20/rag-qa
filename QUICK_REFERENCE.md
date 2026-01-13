# Quick Reference Guide

## Installation
```bash
pip install -r requirements.txt
```

## Environment Setup
Create `.env` file:
```env
MODEL_PROVIDER=groq
GROQ_API_KEY=your_key_from_https://console.groq.com
```

## Usage

### Demo Mode (Built-in Sample Data)
```bash
# Generate test artifacts
python -m src.rag_test_generator --demo

# Show context without generating (no API calls)
python -m src.rag_test_generator --demo --dry-run
```

### Production Mode (Jira + Figma)
```bash
python -m src.rag_test_generator \
  --jira-jql "project = ABC AND status = 'Done'" \
  --figma-file YOUR_FIGMA_FILE_KEY \
  --output ./out
```

## Generated Files

Located in `out/` directory:
- `test_plan.json` / `test_plan.md` - Comprehensive test plan
- `test_scenarios.json` / `test_scenarios.md` - Test scenarios
- `test_cases.json` / `test_cases.md` - Detailed test cases

## Test Case Structure

```json
{
  "id": "TC-001",
  "title": "Test TC-001",
  "objective": "Verify user login succeeds",
  "preconditions": ["User is on login screen"],
  "steps": [
    "Enter valid email",
    "Enter valid password",
    "Click Sign In"
  ],
  "expected_result": "User navigates to dashboard",
  "priority": "High"
}
```

## Switching LLM Providers

### Groq (Free, Default)
```env
MODEL_PROVIDER=groq
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
```

### OpenAI
```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
```

### Anthropic
```env
MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Cohere
```env
MODEL_PROVIDER=cohere
COHERE_API_KEY=your_cohere_key
COHERE_MODEL=command-r-plus
```

## Troubleshooting

### JSON Parsing Errors
The system automatically handles:
- Markdown code blocks
- Truncated JSON
- Missing/extra fields
- Type mismatches (string vs list)

If you still see errors:
1. Check that MODEL_PROVIDER is set correctly
2. Verify API key is valid
3. Try with --dry-run first to see retrieved context

### Empty Test Cases
If test_cases.json is empty:
- The model may be returning scenarios without separate test cases
- Check IMPLEMENTATION_SUMMARY.md for schema details
- The parser automatically generates title/objective from available fields

### API Rate Limits
- Groq free tier: No rate limits (as of Dec 2024)
- OpenAI: Depends on your plan
- Anthropic: Depends on your plan

## Key Features

✅ **Free LLM**: Uses Groq's free API (LLaMA 3.3 70B)
✅ **Robust Parsing**: Handles malformed JSON from free models
✅ **Field Mapping**: Auto-maps model field names to schema
✅ **Type Coercion**: Converts strings to lists when needed
✅ **Separation**: Test Plan, Scenarios, Cases are independent
✅ **Dry-Run Mode**: Test without API costs

## File Structure

```
rag-qa/
├── src/
│   ├── config.py              # Environment configuration
│   ├── rag_test_generator.py  # CLI entry point
│   ├── rag/
│   │   ├── pipeline.py        # RAG pipeline & JSON parsing
│   │   └── groq_wrapper.py    # Custom Groq LLM wrapper
│   ├── models/
│   │   └── schemas.py         # Pydantic schemas with validators
│   ├── prompts/
│   │   └── templates.py       # LLM prompts
│   ├── clients/
│   │   ├── jira_client.py     # Jira API client
│   │   └── figma_client.py    # Figma API client
│   └── utils/
│       └── text_clean.py      # Text preprocessing
├── out/                        # Generated test artifacts
├── docs/                       # Documentation
├── requirements.txt           # Python dependencies
├── README.md                  # Main documentation
└── IMPLEMENTATION_SUMMARY.md  # Technical details
```

## Support

For technical details, see:
- `IMPLEMENTATION_SUMMARY.md` - Implementation details
- `README.md` - Full documentation
- `docs/code_explanation.md` - Code architecture
- `docs/workflow.md` - Workflow diagram
