# RAG Test Generator

Generate Test Plan, Test Scenarios, and Detailed Test Cases from product requirements using a Retrieval-Augmented Generation (RAG) pipeline over Jira issues and Figma designs.

## Features
- Pull requirements from Jira (JQL or project key)
- Extract text and comments from Figma files
- Index with FAISS + HuggingFace embeddings
- Retrieve context and generate structured outputs via LangChain
- Model provider selection: Groq (free), Anthropic, OpenAI
- CLI with dry-run/demo mode for local testing
- Improved JSON parsing with automatic unwrapping and error recovery

## Quick Start

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

### 2) Configure environment
Create `.env` file:
```env
# Use free Groq API
MODEL_PROVIDER=groq
GROQ_API_KEY=your_groq_key_here

# Or use Anthropic/OpenAI
# MODEL_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your_key_here
```

Get a free Groq API key at: https://console.groq.com

### 3) Run (demo mode - generates test artifacts)
```bash
python -m src.rag_test_generator --demo
```

### 4) Run dry-run (show retrieved context without LLM calls)
```bash
python -m src.rag_test_generator --demo --dry-run
```

### 5) Run with Jira + Figma
```bash
python -m src.rag_test_generator \
  --jira-jql "project = ABC AND status = 'Done'" \
  --figma-file <FILE_KEY> \
  --output ./out
```

## Outputs
- JSON files:
  - `test_plan.json`
  - `test_scenarios.json`
  - `test_cases.json`
- Markdown mirrors in `out/` for human readability.

## Notes
- **Dry-run mode**: `--dry-run` shows retrieved context and system prompts without calling LLMs (no cost)
- **Demo mode**: Uses built-in sample requirements from Jira/Figma
- **Free LLM**: Groq provides free API access to LLaMA and other open models
- **Structured Output**: Test Plan, Test Scenarios, and Test Cases are properly separated as independent structures (not nested)
- **Robust JSON Parsing**: Automatic JSON extraction, unwrapping, and error recovery for malformed responses from free LLMs
- **Field Mapping**: Automatically maps model-specific field names (e.g., `testCaseId` → `id`, `expectedResults` → `expected_result`)
- **Type Coercion**: Handles type mismatches (e.g., `preconditions` as string or list)

## Architecture

### RAG Pipeline
1. **Document Retrieval**: FAISS vector store with HuggingFace embeddings retrieves relevant context from requirements
2. **LLM Integration**: Supports Groq (free), Anthropic, OpenAI, or Cohere
3. **Structured Output**: 
   - OpenAI/Anthropic: Use built-in structured output
   - Groq/Cohere: Custom JSON parsing with bracket matching and error recovery
4. **Three-Chain Architecture**: Independent chains for Test Plan, Test Scenarios, and Test Cases ensure separation

### Schema Design
- **TestCase**: Flexible schema that maps alternate field names and handles type conversions
  - Supports: `id`/`testCaseId`, `title`/`name`, `expected_result`/`expectedResult`
  - Auto-generates missing `title` from `id` and `objective` from `expected_result`
  - Converts `preconditions` from string to list when needed
- **TestScenario**: Separate from test cases (empty `cases` array)
- **TestPlan**: Comprehensive plan with scope, objectives, strategy, risks, metrics

### JSON Parsing Strategy
Free LLM models often return malformed JSON. The parser handles:
1. Markdown code block extraction
2. Complete JSON boundary detection via bracket stack matching
3. Trailing comma removal
4. Error position-based truncation with bracket balancing
5. Schema-aware field extraction (TestPlan vs List[TestScenario] vs List[TestCase])
6. Unwrapping of nested/wrapped structures
