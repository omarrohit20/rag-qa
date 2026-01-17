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
    cases: List[TestCase] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
        extra = "ignore"

    @model_validator(mode='before')
    @classmethod
    def normalize_model(cls, data):
        """Normalize alternate field names from LLM output for scenarios"""
        if isinstance(data, dict):
            # Map scenarioId -> id
            if 'scenarioId' in data and 'id' not in data:
                data['id'] = data['scenarioId']
            if 'scenario_id' in data and 'id' not in data:
                data['id'] = data['scenario_id']

            # Normalize title/name variants
            # Accept 'name', 'title', 'scenarioName', 'scenarioTitle'
            if 'name' in data and 'title' not in data:
                data['title'] = data['name']
            if 'scenarioName' in data and 'title' not in data:
                data['title'] = data['scenarioName']
            if 'scenarioTitle' in data and 'title' not in data:
                data['title'] = data['scenarioTitle']
            if 'title' in data and not data['title'] and data.get('name'):
                data['title'] = data['name']

            # Normalize description variants
            for alt in ['details', 'scenarioDescription', 'desc']:
                if alt in data and 'description' not in data:
                    data['description'] = data[alt]

            # Ensure cases is a list and strip nested cases if incorrectly provided
            if 'cases' in data:
                if isinstance(data['cases'], dict):
                    # Some providers may return {'testCases': [...]} under cases
                    for k in ['testCases', 'test_cases']:
                        if k in data['cases'] and isinstance(data['cases'][k], list):
                            data['cases'] = data['cases'][k]
                            break
                elif isinstance(data['cases'], str) and data['cases']:
                    data['cases'] = []  # scenarios should not include cases per instructions
                elif not isinstance(data['cases'], list):
                    data['cases'] = []

            # If title is still missing but id exists, synthesize a title
            if not data.get('title') and data.get('id'):
                data['title'] = f"Scenario {data['id']}"

        return data

class TestPlan(BaseModel):
    title: str = Field(default="Test Plan", description="Test plan title")
    scope: str
    objectives: List[str] = Field(default_factory=list)
    in_scope: List[str] = []
    out_of_scope: List[str] = []
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    strategy: str
    metrics: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True
    
    @model_validator(mode='before')
    @classmethod
    def normalize_list_fields(cls, data):
        """Convert string fields to lists when needed"""
        if isinstance(data, dict):
            # Handle string/dict fields that should be strings
            for field in ['scope', 'strategy']:
                if field in data:
                    value = data[field]
                    if isinstance(value, dict):
                        # Try to extract a string from dict
                        if 'value' in value:
                            data[field] = value['value']
                        elif 'text' in value:
                            data[field] = value['text']
                        else:
                            # Join all dict values as string
                            data[field] = '; '.join(str(v) for v in value.values())
            
            # Handle list fields
            for field in ['objectives', 'assumptions', 'risks', 'metrics', 'in_scope', 'out_of_scope']:
                if field in data:
                    value = data[field]
                    if isinstance(value, str) and value:
                        if '\n' in value:
                            data[field] = [item.strip() for item in value.split('\n') if item.strip()]
                        elif ',' in value:
                            data[field] = [item.strip() for item in value.split(',') if item.strip()]
                        else:
                            data[field] = [value]
                    elif isinstance(value, dict):
                        data[field] = []
        return data

class GenerationBundle(BaseModel):
    test_plan: TestPlan
    scenarios: List[TestScenario]
    cases: List[TestCase]
