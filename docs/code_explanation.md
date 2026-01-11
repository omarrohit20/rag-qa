# Code Explanation: `_chain_structured` Method

## Overview
The `_chain_structured` method in [src/rag/pipeline.py](src/rag/pipeline.py#L53-L60) builds a LangChain **chain** that:
1. Lazily initializes the LLM (only once, when first needed).
2. Constructs a prompt template with system directives and task instructions.
3. Chains the prompt to the LLM's structured output parser.
4. Returns a runnable chain ready to execute with context.

## Method Signature
```python
def _chain_structured(self, schema: BaseModel, system: str, task: str):
```

**Parameters:**
- `schema: BaseModel` — A Pydantic model class (e.g., `TestPlan`, `List[TestScenario]`) that defines the expected JSON output shape.
- `system: str` — System directive (e.g., "You are an expert QA architect...").
- `task: str` — Task-specific instructions (e.g., "Create a concise test plan...").

## Step-by-Step Breakdown

### 1. Lazy LLM Initialization
```python
if self.llm is None:
    self.llm = self._make_llm()
```
- The LLM is **only instantiated once**, when this method is first called.
- Subsequent calls reuse the same LLM instance (avoiding repeated authentication/setup).
- This enables **dry-run mode** to work without LLM API keys (dry-run calls `_context_from_query()` but never calls `_chain_structured()`).

### 2. Prompt Template Construction
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "Context:\n{context}\n\nTask:\n" + task + "\n\nConstraints: Be precise; return only the structured output."),
])
```
- Builds a **multi-turn prompt** with two roles:
  - **"system"**: Sets the model's behavior (e.g., "You are an expert QA architect").
  - **"human"**: The actual user query with three sections:
    - Context (retrieved via FAISS, injected at runtime).
    - Task (task-specific instructions).
    - Constraints (enforcement to ensure JSON compliance).

**Example Flow:**
```
System: "You are an expert QA Test Architect..."
Human: "Context:
Jira ABC-123: User can sign in...

Task:
Create a concise, actionable Test Plan...

Constraints: Be precise; return only the structured output."
```

### 3. Structured Output Chain
```python
return prompt | self.llm.with_structured_output(schema)
```
- **`|` operator**: LangChain's pipe operator chains runnable components.
- **`prompt`**: Formats the input context into the multi-turn message.
- **`self.llm.with_structured_output(schema)`**: 
  - Instructs the LLM to return JSON that conforms to the Pydantic schema.
  - Uses the model's function-calling or native JSON mode (model-dependent).
  - Automatically parses and validates the output against the schema.

## Usage in `generate_all()`
```python
def generate_all(self, query: Optional[str] = None) -> GenerationBundle:
    q = query or "Generate QA assets from given requirements"
    context = self._context_from_query(q)

    plan_chain = self._chain_structured(TestPlan, SYSTEM_DIRECTIVE, PLAN_INSTRUCTIONS)
    scen_chain = self._chain_structured(List[TestScenario], SYSTEM_DIRECTIVE, SCENARIO_INSTRUCTIONS)
    case_chain = self._chain_structured(List[TestCase], SYSTEM_DIRECTIVE, CASE_INSTRUCTIONS)

    test_plan: TestPlan = plan_chain.invoke({"context": context})
    scenarios: List[TestScenario] = scen_chain.invoke({"context": context})
    cases: List[TestCase] = case_chain.invoke({"context": context})

    return GenerationBundle(test_plan=test_plan, scenarios=scenarios, cases=cases)
```

**Execution Flow:**
1. **Retrieve Context**: Fetch top-6 relevant doc chunks from FAISS.
2. **Build Chains**: Create three separate chains, one per artifact type.
3. **Invoke**: Pass `{"context": context}` to each chain.
   - Prompt interpolates the context.
   - LLM receives the full prompt and returns structured JSON.
   - Parser validates and returns a Pydantic model instance.
4. **Combine**: Bundle all three outputs into `GenerationBundle`.

## Key Design Benefits

| Aspect | Benefit |
|--------|---------|
| **Lazy Init** | Dry-run mode works without API keys; only LLM loads when needed. |
| **Prompt Chaining** | Clean separation: system role + task-specific instructions. |
| **Structured Output** | Type-safe; no manual JSON parsing; automatic validation. |
| **Reusable Chains** | Same chain template used for different schemas (plan/scenarios/cases). |
| **Runnable Interface** | `.invoke()` is composable and testable; chains are first-class objects. |

## Example: Generating a Test Plan
**Input:**
```python
schema = TestPlan
system = "You are an expert QA Test Architect..."
task = "Create a concise, actionable Test Plan..."
context = "Jira ABC-123: User can sign in...\n\nFigma: Auth Flow..."
```

**Chain Execution:**
1. Prompt interpolates context.
2. LLM receives:
```
System: You are an expert QA Test Architect...
Human: Context:
Jira ABC-123: User can sign in...

Task:
Create a concise, actionable Test Plan...

Constraints: Be precise; return only the structured output.
```
3. LLM returns JSON conforming to `TestPlan` schema (e.g., title, scope, objectives, strategy, etc.).
4. Parser validates and returns a `TestPlan` instance.

## Related Code
- **Schemas** (expected outputs): [src/models/schemas.py](src/models/schemas.py)
- **Prompts** (system/task directives): [src/prompts/templates.py](src/prompts/templates.py)
- **LLM Factory** (model selection): [src/rag/pipeline.py#L34-L50](src/rag/pipeline.py#L34-L50) (see `_make_llm()`)
- **Usage** (orchestration): [src/rag/pipeline.py#L66-L81](src/rag/pipeline.py#L66-L81) (see `generate_all()`)
