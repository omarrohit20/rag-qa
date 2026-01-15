from typing import List, Optional, Tuple
import json
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatCohere
from pydantic import BaseModel

from src.rag.groq_wrapper import ChatGroq

from src.models.schemas import TestPlan, TestScenario, TestCase, GenerationBundle
from src.prompts.templates import SYSTEM_DIRECTIVE, PLAN_INSTRUCTIONS, SCENARIO_INSTRUCTIONS, CASE_INSTRUCTIONS
from src.config import (
    MODEL_PROVIDER,
    OPENAI_API_KEY, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    GROQ_API_KEY, GROQ_MODEL,
    COHERE_API_KEY, COHERE_MODEL,
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
        print(f"Using model provider: {MODEL_PROVIDER}")
        if MODEL_PROVIDER == "groq" and GROQ_API_KEY:
            return ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.2)
        elif MODEL_PROVIDER == "cohere" and COHERE_API_KEY:
            return ChatCohere(cohere_api_key=COHERE_API_KEY, model=COHERE_MODEL, temperature=0.2)
        elif MODEL_PROVIDER == "openai" and OPENAI_API_KEY:
            return ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0.2)
        elif MODEL_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
            return ChatAnthropic(api_key=ANTHROPIC_API_KEY, model=ANTHROPIC_MODEL, temperature=0.2)
        else:
            raise RuntimeError(f"No LLM provider configured for '{MODEL_PROVIDER}'. Set env vars: GROQ_API_KEY, COHERE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY.")

    def _context_from_query(self, query: str) -> str:
        """Retrieve and join contexts for prompt."""
        docs = self.retriever.invoke(query)
        joined = "\n\n".join([d.page_content for d in docs])
        return joined

    def _chain_structured(self, schema: BaseModel, system: str, task: str):
        if self.llm is None:
            self.llm = self._make_llm()
        
        # Add schema example to prompt for better formatting
        try:
            schema_json = schema.model_json_schema()
            schema_name = schema.__name__
        except AttributeError:
            # Handle List[Model] types
            schema_json = {"type": "array", "items": "objects"}
            schema_name = str(schema)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("human", f"Context:\n{{context}}\n\nTask:\n{task}\n\nReturn ONLY valid JSON matching the schema. Do not wrap in markdown. Output pure JSON only."),
        ])
        
        # OpenAI and Anthropic support structured output; Groq/Cohere need JSON parsing
        if MODEL_PROVIDER in ["openai", "anthropic"]:
            return prompt | self.llm.with_structured_output(schema)
        else:
            # Groq/Cohere: parse JSON response and handle markdown code blocks
            def parse_json_response(text: str):
                import re
                
                # Step 1: Remove markdown code blocks if present
                if "```json" in text:
                    start = text.find("```json") + 7
                    end = text.rfind("```")
                    if end > start:
                        text = text[start:end].strip()
                elif "```" in text:
                    start = text.find("```") + 3
                    end = text.rfind("```")
                    if end > start:
                        text = text[start:end].strip()
                
                # Step 2: Extract raw JSON from text (find first { or [ and match closing bracket)
                text = text.strip()
                if not text.startswith("{") and not text.startswith("["):
                    # Find first { or [
                    brace_idx = text.find("{")
                    bracket_idx = text.find("[")
                    indices = [i for i in [brace_idx, bracket_idx] if i != -1]
                    if indices:
                        json_start = min(indices)
                        text = text[json_start:]
                
                # Step 3: Extract complete JSON by matching brackets
                def extract_json_object(s):
                    """Extract a complete JSON object/array from text"""
                    if not s or s[0] not in ['{', '[']:
                        return None
                    
                    stack = []
                    in_string = False
                    escape_next = False
                    start_char = s[0]
                    end_char = '}' if start_char == '{' else ']'
                    
                    for i, char in enumerate(s):
                        if escape_next:
                            escape_next = False
                            continue
                        
                        if char == '\\' and in_string:
                            escape_next = True
                            continue
                        
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            continue
                        
                        if not in_string:
                            if char in ['{', '[']:
                                stack.append(char)
                            elif char in ['}', ']']:
                                stack.pop()
                                if not stack:
                                    return s[:i+1]
                    
                    return None
                
                json_str = extract_json_object(text)
                if not json_str:
                    json_str = text
                
                # Step 4: Fix common JSON issues
                # Remove trailing commas
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                
                # Step 5: Try to parse JSON with error recovery
                data = None
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    # Handle unterminated strings and other JSON errors
                    if e.pos is not None:
                        # For unterminated string errors, try to find the last complete object
                        if "Unterminated string" in str(e) or "unterminated" in str(e).lower():
                            # Find the last complete item in array or object
                            truncated = json_str[:e.pos]
                            
                            # If we're in an array, find the last complete object before the error
                            if json_str.strip().startswith('['):
                                # Find the last complete object by looking for '},\n' or '},'
                                last_complete = truncated.rfind('},')
                                if last_complete == -1:
                                    last_complete = truncated.rfind('}')
                                if last_complete != -1:
                                    truncated = truncated[:last_complete + 1]
                            
                            # Close the string if we're inside quotes
                            if truncated.count('"') % 2 != 0:
                                truncated = truncated.rstrip() + '"'
                        else:
                            # For other errors, just truncate at error position
                            truncated = json_str[:e.pos]
                        
                        # Remove trailing commas
                        truncated = truncated.rstrip(',').rstrip()
                        
                        # Close any open brackets/braces
                        open_braces = truncated.count('{') - truncated.count('}')
                        open_brackets = truncated.count('[') - truncated.count(']')
                        truncated = truncated + ']' * open_brackets + '}' * open_braces
                        
                        try:
                            data = json.loads(truncated)
                        except Exception as truncate_err:
                            # Last resort: try to extract just the valid items from the array
                            if json_str.strip().startswith('['):
                                # Find all complete objects in the array
                                valid_items = []
                                depth = 0
                                current_obj = ""
                                in_string = False
                                escape_next = False
                                
                                for char in json_str[1:]:  # Skip opening [
                                    if escape_next:
                                        current_obj += char
                                        escape_next = False
                                        continue
                                    if char == '\\' and in_string:
                                        escape_next = True
                                        current_obj += char
                                        continue
                                    if char == '"' and not escape_next:
                                        in_string = not in_string
                                    
                                    current_obj += char
                                    
                                    if not in_string:
                                        if char == '{':
                                            depth += 1
                                        elif char == '}':
                                            depth -= 1
                                            if depth == 0:
                                                # Complete object found
                                                try:
                                                    obj = json.loads(current_obj.strip())
                                                    valid_items.append(obj)
                                                    current_obj = ""
                                                except:
                                                    pass
                                
                                if valid_items:
                                    data = valid_items
                                else:
                                    raise ValueError(f"Failed to parse JSON. Error: {e}")
                            else:
                                raise ValueError(f"Failed to parse JSON. Error: {e}")
                    else:
                        raise ValueError(f"Failed to parse JSON. Error: {e}")
                
                # Step 6: Extract data for specific schema
                schema_name = str(schema)
                if hasattr(schema, '__name__'):
                    schema_name = schema.__name__
                
                # Check for List[Type] pattern
                if 'List' in schema_name and hasattr(schema, '__args__'):
                    try:
                        inner_type = schema.__args__[0]
                        inner_name = inner_type.__name__ if hasattr(inner_type, '__name__') else str(inner_type)
                        schema_name = f"List[{inner_name}]"
                    except:
                        pass
                
                # For TestPlan schema
                if 'TestPlan' in schema_name:
                    if isinstance(data, dict):
                        # Look for testPlan key
                        if 'testPlan' in data:
                            data = data['testPlan']
                        elif 'test_plan' in data:
                            data = data['test_plan']
                        # Remove other keys if present
                        for unwanted_key in ['testScenarios', 'test_scenarios', 'testCases', 'test_cases']:
                            data.pop(unwanted_key, None)
                    return schema.model_validate(data)
                
                # For TestScenario list
                elif 'TestScenario' in schema_name:
                    if isinstance(data, dict):
                        # Look for testScenarios/scenarios key
                        for key in ['testScenarios', 'test_scenarios', 'scenarios', 'testScenarios']:
                            if key in data:
                                data = data[key]
                                break
                        # If still dict but has list inside, find it
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, list) and len(value) > 0:
                                    if isinstance(value[0], dict) and ('id' in value[0] or 'description' in value[0]):
                                        data = value
                                        break
                    
                    if hasattr(schema, '__args__'):
                        inner_type = schema.__args__[0]
                        if isinstance(data, list):
                            # Remove testCases from each scenario
                            for item in data:
                                if isinstance(item, dict):
                                    item.pop('testCases', None)
                                    item.pop('test_cases', None)
                                    item.pop('cases', None)
                            return [inner_type.model_validate(item) for item in data]
                    return data
                
                # For TestCase list (MOST IMPORTANT - separate from scenarios)
                elif 'TestCase' in schema_name:
                    if isinstance(data, dict):
                        # First, remove scenario-related keys
                        data.pop('testPlan', None)
                        data.pop('test_plan', None)
                        data.pop('testScenarios', None)
                        data.pop('test_scenarios', None)
                        data.pop('scenarios', None)
                        
                        # Look for testCases/cases key
                        cases_data = None
                        for key in ['testCases', 'test_cases', 'cases', 'testcases']:
                            if key in data:
                                cases_data = data[key]
                                break
                        
                        if cases_data is not None:
                            data = cases_data
                        elif isinstance(data, dict) and len(data) > 0:
                            # If still dict but has list inside, find it
                            for key, value in data.items():
                                if isinstance(value, list):
                                    if len(value) > 0:
                                        # Check if items look like test cases
                                        if isinstance(value[0], dict) and any(k in value[0] for k in ['id', 'title', 'objective', 'steps', 'testCaseId']):
                                            data = value
                                            break
                    
                    if hasattr(schema, '__args__'):
                        inner_type = schema.__args__[0]
                        if isinstance(data, list):
                            return [inner_type.model_validate(item) for item in data]
                        elif isinstance(data, dict) and len(data) == 0:
                            return []
                    return data if isinstance(data, list) else ([] if isinstance(data, dict) and len(data) == 0 else data)
                
                # Default handling
                return schema.model_validate(data) if hasattr(schema, 'model_validate') else data
            
            return prompt | self.llm | StrOutputParser() | parse_json_response

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
