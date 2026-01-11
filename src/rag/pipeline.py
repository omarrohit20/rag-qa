from typing import List, Optional, Tuple
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEndpoint
from pydantic import BaseModel

from src.models.schemas import TestPlan, TestScenario, TestCase, GenerationBundle
from src.prompts.templates import SYSTEM_DIRECTIVE, PLAN_INSTRUCTIONS, SCENARIO_INSTRUCTIONS, CASE_INSTRUCTIONS
from src.config import (
    MODEL_PROVIDER,
    OPENAI_API_KEY, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    HUGGINGFACEHUB_API_TOKEN, HF_INFERENCE_MODEL,
    DEFAULT_EMBED_MODEL,
)

class RAGTestGenerator:
    def __init__(self, docs: List[Document]):
        self.docs = docs
        self.embeddings = HuggingFaceEmbeddings(model_name=DEFAULT_EMBED_MODEL)
        self.vs = FAISS.from_documents(docs, self.embeddings)
        self.retriever = self.vs.as_retriever(search_kwargs={"k": 6})
        self.llm = None

    def _make_llm(self):
        if MODEL_PROVIDER == "openai" and OPENAI_API_KEY:
            return ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0.2)
        elif MODEL_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
            return ChatAnthropic(api_key=ANTHROPIC_API_KEY, model=ANTHROPIC_MODEL, temperature=0.2)
        elif MODEL_PROVIDER == "huggingface" and HUGGINGFACEHUB_API_TOKEN:
            return HuggingFaceEndpoint(
                repo_id=HF_INFERENCE_MODEL,
                huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
                task="text-generation",
                temperature=0.2,
                max_new_tokens=1024,
            )
        else:
            raise RuntimeError("No LLM provider configured. Set env vars for OpenAI/Anthropic/HuggingFace.")

    def _context_from_query(self, query: str) -> str:
        """Retrieve and join contexts for prompt."""
        docs = self.retriever.invoke(query)
        joined = "\n\n".join([d.page_content for d in docs])
        return joined

    def _chain_structured(self, schema: BaseModel, system: str, task: str):
        if self.llm is None:
            self.llm = self._make_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("human", "Context:\n{context}\n\nTask:\n" + task + "\n\nConstraints: Be precise; return only the structured output."),
        ])
        return prompt | self.llm.with_structured_output(schema)

    def generate_all(self, query: Optional[str] = None) -> GenerationBundle:
        q = query or "Generate QA assets from given requirements"
        context = self._context_from_query(q)

        plan_chain = self._chain_structured(TestPlan, SYSTEM_DIRECTIVE, PLAN_INSTRUCTIONS)
        scen_chain = self._chain_structured(List[TestScenario], SYSTEM_DIRECTIVE, SCENARIO_INSTRUCTIONS)  # type: ignore
        case_chain = self._chain_structured(List[TestCase], SYSTEM_DIRECTIVE, CASE_INSTRUCTIONS)  # type: ignore

        test_plan: TestPlan = plan_chain.invoke({"context": context})
        scenarios: List[TestScenario] = scen_chain.invoke({"context": context})
        cases: List[TestCase] = case_chain.invoke({"context": context})

        return GenerationBundle(test_plan=test_plan, scenarios=scenarios, cases=cases)
