from typing import List
import requests
from langchain_core.documents import Document

class FigmaClient:
    def __init__(self, token: str):
        if not token:
            raise ValueError("FigmaClient requires FIGMA_TOKEN")
        self.headers = {
            "X-Figma-Token": token,
        }

    def fetch_file_documents(self, file_key: str) -> List[Document]:
        """Pulls Figma file JSON and extracts text nodes and comments."""
        file_url = f"https://api.figma.com/v1/files/{file_key}"
        resp = requests.get(file_url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        file_json = resp.json()

        texts: List[str] = []
        name = file_json.get("name", "Unknown File")
        document = file_json.get("document", {})
        self._collect_text(document, texts)

        comments_url = f"https://api.figma.com/v1/files/{file_key}/comments"
        crep = requests.get(comments_url, headers=self.headers, timeout=30)
        comments = []
        try:
            crep.raise_for_status()
            comments = [c.get("message", "") for c in crep.json().get("comments", [])]
        except Exception:
            comments = []

        body = f"Figma: {name}\n\nExtracted Text:\n" + "\n".join(texts)
        if comments:
            body += "\n\nComments:\n" + "\n".join(comments)

        return [Document(page_content=body, metadata={"source": "figma", "figma_file": name})]

    def _collect_text(self, node: dict, texts: List[str]):
        if not isinstance(node, dict):
            return
        if node.get("type") == "TEXT":
            chars = node.get("characters")
            if chars:
                texts.append(chars)
        for child in node.get("children", []) or []:
            self._collect_text(child, texts)
