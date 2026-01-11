from typing import List, Optional
from pydantic import BaseModel, Field

class TestCase(BaseModel):
    id: str = Field(..., description="Unique test case id")
    title: str
    objective: str
    preconditions: List[str] = []
    steps: List[str] = []
    expected_result: str
    priority: str = "Medium"
    traceability: Optional[List[str]] = None  # requirement refs

class TestScenario(BaseModel):
    id: str
    title: str
    description: str
    cases: List[TestCase] = []

class TestPlan(BaseModel):
    title: str
    scope: str
    objectives: List[str]
    in_scope: List[str] = []
    out_of_scope: List[str] = []
    assumptions: List[str] = []
    risks: List[str] = []
    strategy: str
    metrics: List[str] = []

class GenerationBundle(BaseModel):
    test_plan: TestPlan
    scenarios: List[TestScenario]
    cases: List[TestCase]
