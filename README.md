# RAG Test Generator

Generate Test Plan, Test Scenarios, and Detailed Test Cases from product requirements using a Retrieval-Augmented Generation (RAG) pipeline over Jira issues and Figma designs.

## Features
- Pull requirements from Jira (JQL or project key)
- Extract text and comments from Figma files
- Index with FAISS + HuggingFace embeddings
- Retrieve context and generate structured outputs via LangChain
- Model provider selection: OpenAI (default), Anthropic, HuggingFace Inference
- CLI with dry-run/demo mode for local testing

## Quick Start

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

### 2) Configure environment
Copy `.env.example` to `.env` and fill values:
- `MODEL_PROVIDER` = `openai` | `anthropic` | `huggingface`
- For OpenAI: `OPENAI_API_KEY`
- For Anthropic: `ANTHROPIC_API_KEY`
- For HuggingFace: `HUGGINGFACEHUB_API_TOKEN` and `HF_INFERENCE_MODEL`
- Jira: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
- Figma: `FIGMA_TOKEN`

### 3) Run (demo mode without external APIs)
```bash
python -m src.rag_test_generator --demo
```

### 4) Run with Jira + Figma
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
- Dry-run shows retrieved context and prompts without calling LLMs.
- Demo mode uses built-in sample requirements.
- Best-performing model tends to be frontier models (OpenAI/Anthropic). Choose based on your org’s access, cost, latency, and compliance.
