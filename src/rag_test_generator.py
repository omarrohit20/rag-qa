import os
import json
import argparse
import warnings
from pathlib import Path
from typing import List

# Suppress deprecation warnings
warnings.filterwarnings('ignore', category=UserWarning)

from langchain_core.documents import Document

from src.config import (
    JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN,
    FIGMA_TOKEN,
)
from src.clients.jira_client import JiraClient
from src.clients.figma_client import FigmaClient
from src.rag.pipeline import RAGTestGenerator
from src.models.schemas import GenerationBundle

DEMO_DOCS = [
    Document(page_content=(
        "Jira ABC-123: User can sign in with email and password.\n\n"
        "Description:\nImplement login screen with validation. Error states shown for invalid credentials.\n\n"
        "Acceptance Criteria:\n1) Email format validated\n2) Incorrect password shows error\n3) Successful login navigates to dashboard"
    ), metadata={"source": "demo"}),
    Document(page_content=(
        "Figma: Auth Flow\n\nExtracted Text:\n"
        "Login\nEmail\nPassword\nSign In\nForgot password?\n\nComments:\n"
        "Consider password strength hints."
    ), metadata={"source": "demo"}),
]


def build_docs(jira_jql: str = None, jira_project: str = None, figma_file: str = None) -> List[Document]:
    docs: List[Document] = []
    if jira_jql or jira_project:
        if not (JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN):
            raise RuntimeError("Jira env vars missing. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN.")
        jc = JiraClient(JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN)
        docs.extend(jc.search(jql=jira_jql, project_key=jira_project))
    if figma_file:
        if not FIGMA_TOKEN:
            raise RuntimeError("Figma env var FIGMA_TOKEN missing.")
        fc = FigmaClient(FIGMA_TOKEN)
        docs.extend(fc.fetch_file_documents(figma_file))
    return docs


def write_outputs(bundle: GenerationBundle, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "test_plan.json").write_text(json.dumps(bundle.test_plan.model_dump(), indent=2), encoding="utf-8")
    (out_dir / "test_scenarios.json").write_text(json.dumps([s.model_dump() for s in bundle.scenarios], indent=2), encoding="utf-8")
    (out_dir / "test_cases.json").write_text(json.dumps([c.model_dump() for c in bundle.cases], indent=2), encoding="utf-8")

    # Markdown mirrors for readability
    (out_dir / "test_plan.md").write_text(render_plan_md(bundle), encoding="utf-8")
    (out_dir / "test_scenarios.md").write_text(render_scenarios_md(bundle), encoding="utf-8")
    (out_dir / "test_cases.md").write_text(render_cases_md(bundle), encoding="utf-8")


def render_plan_md(bundle: GenerationBundle) -> str:
    p = bundle.test_plan
    md = [f"# {p.title}", "", "## Scope", p.scope, "", "## Objectives"]
    md += ["- " + o for o in p.objectives]
    md += ["", "## Strategy", p.strategy, "", "## In Scope"]
    md += ["- " + s for s in p.in_scope]
    md += ["", "## Out of Scope"]
    md += ["- " + s for s in p.out_of_scope]
    md += ["", "## Assumptions"]
    md += ["- " + s for s in p.assumptions]
    md += ["", "## Risks"]
    md += ["- " + s for s in p.risks]
    md += ["", "## Metrics"]
    md += ["- " + s for s in p.metrics]
    return "\n".join(md)


def render_scenarios_md(bundle: GenerationBundle) -> str:
    md = ["# Test Scenarios", ""]
    for s in bundle.scenarios:
        md += [f"## {s.id} - {s.title}", s.description, ""]
    return "\n".join(md)


def render_cases_md(bundle: GenerationBundle) -> str:
    md = ["# Test Cases", ""]
    for c in bundle.cases:
        title = c.title or "Untitled"
        case_id = c.id or "NO-ID"
        md += [f"## {case_id} - {title}"]
        
        if c.objective:
            md += ["### Objective", c.objective]
        
        if c.preconditions:
            md += ["### Preconditions"]
            md += ["- " + p for p in c.preconditions]
        
        if c.steps:
            md += ["### Steps"]
            md += ["1. " + s for s in c.steps]
        
        if c.expected_result:
            md += ["### Expected Result", c.expected_result]
        
        md += [f"### Priority: {c.priority or 'Medium'}"]
        
        if c.traceability:
            md += ["### Traceability"]
            md += ["- " + t for t in c.traceability]
        
        md += [""]
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(description="RAG Test Generator")
    ap.add_argument("--jira-jql", type=str, default=None)
    ap.add_argument("--jira-project", type=str, default=None)
    ap.add_argument("--figma-file", type=str, default=None)
    ap.add_argument("--output", type=str, default="out")
    ap.add_argument("--dry-run", action="store_true", help="Retrieve context and show prompts, skip LLM")
    ap.add_argument("--demo", action="store_true", help="Run with built-in sample docs")
    args = ap.parse_args()

    if args.demo:
        docs = DEMO_DOCS
    else:
        docs = build_docs(args.jira_jql, args.jira_project, args.figma_file)

    rag = RAGTestGenerator(docs)

    if args.dry_run:
        ctx = rag._context_from_query("Generate QA assets from given requirements")
        print("=== Retrieved Context (dry-run) ===\n")
        print(ctx[:4000])
        print("\nSet --dry-run off to generate outputs.")
        return

    bundle = rag.generate_all()
    write_outputs(bundle, Path(args.output))
    print(f"Wrote outputs to {args.output}")

if __name__ == "__main__":
    main()
