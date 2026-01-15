from typing import List, Optional
import base64
import requests
from langchain_core.documents import Document

class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str):
        if not base_url or not email or not api_token:
            raise ValueError("JiraClient requires base_url, email, and api_token")
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        token = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def search(self, jql: Optional[str] = None, project_key: Optional[str] = None, limit: int = 50) -> List[Document]:
        if not jql and not project_key:
            raise ValueError("Provide either JQL or project_key")
        if project_key and not jql:
            jql = f"project = {project_key} ORDER BY updated DESC"
        
        # Use Jira API v3 search/jql endpoint
        url = f"{self.base_url}/rest/api/3/search/jql"
        params = {
            "jql": jql, 
            "maxResults": limit,
            "fields": "summary,description,customfield_10073"
        }
        
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        
        # Better error messages
        if resp.status_code == 410:
            raise ValueError(f"Jira API returned 410 Gone. The API token may be expired or invalid. Response: {resp.text[:200]}")
        if resp.status_code == 401:
            raise ValueError("Jira authentication failed. Check JIRA_API_TOKEN.")
        if resp.status_code == 403:
            raise ValueError("Jira access forbidden. Check permissions.")
        if resp.status_code == 404:
            raise ValueError("Jira API endpoint not found. Check JIRA_BASE_URL.")
        
        resp.raise_for_status()
        data = resp.json()
        docs: List[Document] = []
        for issue in data.get("issues", []):
            key = issue.get("key")
            fields = issue.get("fields", {})
            summary = fields.get("summary", "")
            description = self._extract_description(fields)
            acceptance = self._extract_acceptance_criteria(fields)
            body = f"Jira {key}: {summary}\n\nDescription:\n{description}\n\nAcceptance Criteria:\n{acceptance}"
            docs.append(Document(page_content=body, metadata={
                "source": "jira",
                "jira_key": key,
                "summary": summary,
            }))
        return docs

    def _extract_description(self, fields: dict) -> str:
        desc = fields.get("description")
        if isinstance(desc, dict) and desc.get("content"):
            # Atlassian doc format
            return self._concat_atlassian_doc(desc)
        return desc or ""

    def _extract_acceptance_criteria(self, fields: dict) -> str:
        # Common custom field names
        for key in ["Acceptance Criteria", "acceptanceCriteria", "customfield_12345"]:
            val = fields.get(key)
            if val:
                if isinstance(val, dict):
                    return self._concat_atlassian_doc(val)
                return str(val)
        return ""

    def _concat_atlassian_doc(self, doc: dict) -> str:
        try:
            blocks = []
            for content in doc.get("content", []):
                for p in content.get("content", []):
                    text = p.get("text")
                    if text:
                        blocks.append(text)
            return "\n".join(blocks)
        except Exception:
            return ""
