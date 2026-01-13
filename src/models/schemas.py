from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

class TestCase(BaseModel):
    id: Optional[str] = Field(None, description="Unique test case id")  
    title: Optional[str] = Field(None, description="Test case title", alias="name")
    objective: Optional[str] = Field(None, description="Test objective")
    preconditions: List[str] = Field(default_factory=list, description="Preconditions")
    steps: List[str] = Field(default_factory=list, description="Test steps")
    expected_result: Optional[str] = Field(None, alias="expectedResult", description="Expected result")
    priority: str = Field("Medium", description="Test priority")
    traceability: Optional[List[str]] = None  # requirement refs
    
    class Config:
        populate_by_name = True
        extra = "ignore"  # Ignore extra fields like testCaseId, expectedResults
    
    @model_validator(mode='before')
    @classmethod
    def normalize_model(cls, data):
        """Normalize alternate field names from LLM output"""
        if isinstance(data, dict):
            # Map testCaseId to id
            if 'testCaseId' in data and 'id' not in data:
                data['id'] = data['testCaseId']
            # Map expectedResults to expected_result
            if 'expectedResults' in data and 'expected_result' not in data:
                data['expected_result'] = data['expectedResults']
            # Map expectedResult to expected_result
            if 'expectedResult' in data and 'expected_result' not in data:
                data['expected_result'] = data['expectedResult']
            # Ensure preconditions is a list
            if 'preconditions' in data:
                if isinstance(data['preconditions'], str) and data['preconditions']:
                    data['preconditions'] = [data['preconditions']]
                elif not isinstance(data['preconditions'], list):
                    data['preconditions'] = []
            # Ensure steps is a list
            if 'steps' in data:
                if isinstance(data['steps'], str) and data['steps']:
                    data['steps'] = [data['steps']]
                elif not isinstance(data['steps'], list):
                    data['steps'] = []
            # Generate title from id if missing
            if not data.get('title') and data.get('id'):
                data['title'] = f"Test {data['id']}"
            # Set objective from expectedResults if missing
            if not data.get('objective') and data.get('expected_result'):
                data['objective'] = f"Verify {data.get('expected_result', 'behavior').lower()}"
        return data

class TestScenario(BaseModel):
    id: str
    title: str = Field(..., alias="name")
    description: str
    cases: List[TestCase] = []
    
    class Config:
        populate_by_name = True

class TestPlan(BaseModel):
    title: str = Field(default="Test Plan", description="Test plan title")
    scope: str
    objectives: List[str]
    in_scope: List[str] = []
    out_of_scope: List[str] = []
    assumptions: List[str] = []
    risks: List[str] = []
    strategy: str
    metrics: List[str] = []
    
    class Config:
        populate_by_name = True

class GenerationBundle(BaseModel):
    test_plan: TestPlan
    scenarios: List[TestScenario]
    cases: List[TestCase]
