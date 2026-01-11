# RAG Test Generator — Workflow

This document explains the end-to-end workflow for generating QA artifacts (Test Plan, Test Scenarios, and Detailed Test Cases) from product requirements using a LangChain-based RAG pipeline.

## Overview
- Ingest requirements from Jira and Figma.
- Normalize and index into FAISS using HuggingFace embeddings.
- Retrieve relevant context per task and prompt an LLM.
- Produce structured outputs via Pydantic models: Test Plan, Scenarios, Cases.
- Expose a CLI with demo/dry-run modes for fast verification.

## Components
- Config: [src/config.py](src/config.py)
- Clients:
  - Jira: [src/clients/jira_client.py](src/clients/jira_client.py)
  - Figma: [src/clients/figma_client.py](src/clients/figma_client.py)
- Models/Schemas: [src/models/schemas.py](src/models/schemas.py)
- Prompts: [src/prompts/templates.py](src/prompts/templates.py)
- RAG Pipeline: [src/rag/pipeline.py](src/rag/pipeline.py)
- CLI Entrypoint: [src/rag_test_generator.py](src/rag_test_generator.py)

## Data Sources
- Jira: Issues fetched via JQL or project key; description and acceptance criteria extracted and converted into LangChain `Document`s.
- Figma: Text nodes and file comments pulled via Figma REST API and represented as `Document`s.

## Indexing & Retrieval
- Embeddings: HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (configurable).
- Vector Store: FAISS created from combined Jira + Figma documents.
- Retrieval: Top-k (default 6) relevant chunks are joined to form the prompt context.

## Generation
- Model Provider (env-driven): OpenAI (default), Anthropic, or HuggingFace Endpoint.
- Structured Output: LangChain `with_structured_output()` returns `pydantic` models:
  - `TestPlan`, `List[TestScenario]`, `List[TestCase]` (see [src/models/schemas.py](src/models/schemas.py)).
- Prompts: System directive and task-specific instructions (plan/scenario/case) defined in [src/prompts/templates.py](src/prompts/templates.py).

## Sequence Flow
1. CLI parses input flags (Jira JQL/project, Figma file key, output paths). See [src/rag_test_generator.py](src/rag_test_generator.py).
2. Jira/Figma clients fetch and convert inputs to `Document`s.
3. RAG pipeline builds FAISS index and retriever over documents.
4. For each generation task (plan/scenarios/cases):
   - Retrieve relevant context via the retriever.
   - Compose a prompt with system directive + task instructions + context.
   - Call the selected LLM with structured outputs.
5. Persist results as JSON and Markdown mirrors in the output directory.

## CLI Usage
- Demo dry-run (verifies retrieval without calling LLM):
```bash
python -m src.rag_test_generator --demo --dry-run
```
- Full generation with Jira + Figma:
```bash
python -m src.rag_test_generator \
  --jira-jql "project = ABC AND status = 'Done'" \
  --figma-file <FILE_KEY> \
  --output ./out
```
- Flags:
  - `--jira-jql` or `--jira-project`
  - `--figma-file`
  - `--dry-run` to print retrieved context only
  - `--demo` to use built-in sample docs
  - `--output` path for JSON/Markdown

## Configuration
- Environment variables loaded via `.env`:
  - `MODEL_PROVIDER` = `openai` | `anthropic` | `huggingface`
  - Provider-specific keys and default models: see [.env.example](.env.example) and [src/config.py](src/config.py)
  - Jira: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
  - Figma: `FIGMA_TOKEN`

## Model Selection
- Frontier models (OpenAI/Anthropic) typically provide the most reliable structured outputs and reasoning for QA assets.
- HuggingFace Endpoint supports OSS models; quality depends on selection. Tune temperature, max tokens, and instruction specificity for consistency.

## Outputs
- JSON: `test_plan.json`, `test_scenarios.json`, `test_cases.json`
- Markdown: `test_plan.md`, `test_scenarios.md`, `test_cases.md`

## Error Handling & Observability
- HTTP errors from Jira/Figma surfaced with clear messages.
- Dry-run allows inspecting retrieval context before invoking LLMs.
- Add logging around retrieval and prompt construction if deeper observability is needed.

## Security & Access
- Use API tokens; avoid storing secrets in code. `.env` is required.
- Ensure Jira/Figma scopes are minimal and auditable.

## Extensibility
- Add new sources: Implement a client that returns `Document`s and include in indexing.
- Change embeddings/vector DB: swap `HuggingFaceEmbeddings` or replace FAISS with another store.
- Add post-processing: enforce style guides, deduplicate cases, or integrate traceability checks.

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and set your keys.
3. Run demo dry-run to verify retrieval.
4. Run full generation with Jira + Figma inputs.
