"""Custom Groq LLM wrapper for LangChain compatibility."""
import json
from typing import Any, Dict, List, Optional
from groq import Groq
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import BaseModel, Field


class ChatGroq(BaseChatModel):
    """Groq chat model wrapper for LangChain."""
    
    client: Any = Field(default=None, exclude=True)
    api_key: str
    model: str = "mixtral-8x7b-32768"
    temperature: float = 0.2
    max_tokens: int = 1024
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = Groq(api_key=self.api_key)
    
    @property
    def _llm_type(self) -> str:
        return "groq"
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to Groq format."""
        groq_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                groq_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                groq_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                groq_messages.append({"role": "assistant", "content": msg.content})
            else:
                groq_messages.append({"role": "user", "content": str(msg.content)})
        return groq_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate response from Groq API."""
        groq_messages = self._convert_messages(messages)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=groq_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs
        )
        
        message = AIMessage(content=response.choices[0].message.content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    
    def with_structured_output(self, schema: BaseModel):
        """Enable structured output by wrapping the model."""
        return GroqStructuredOutput(chat_model=self, schema=schema)


class GroqStructuredOutput:
    """Wrapper for structured JSON output from Groq."""
    
    def __init__(self, chat_model: ChatGroq, schema: BaseModel):
        self.chat_model = chat_model
        self.schema = schema
    
    def invoke(self, input_data: Dict[str, Any]) -> BaseModel:
        """Invoke the model and parse JSON response."""
        # Get messages from input
        if "messages" in input_data:
            messages = input_data["messages"]
        else:
            # Build from prompt template
            messages = input_data.get("__chain_input__", [])
        
        # Add JSON format instruction
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                last_msg.content += "\n\nReturn ONLY valid JSON matching the schema. No additional text."
        
        result = self.chat_model._generate(messages)
        content = result.generations[0].message.content
        
        # Try to extract JSON from response
        try:
            # Try direct parsing
            data = json.loads(content)
            return self.schema.model_validate(data)
        except json.JSONDecodeError:
            # Try to find JSON in the content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)
                return self.schema.model_validate(data)
            raise ValueError(f"Could not parse JSON from response: {content[:200]}")
