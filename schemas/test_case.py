from pydantic import BaseModel, Field
from typing import List

class TestCase(BaseModel):
    test_case_id: str = Field(description="Unique identifier for the test case", alias="ID")
    title: str = Field(description="Title of the test case")
    preconditions: str = Field(description="Preconditions for the test case")
    steps: List[str] = Field(description="List of steps for the test case")
    expected_results: List[str] = Field(description="Expected results of the test case")
    priority: str = Field(description="Priority of the test case")

class TestCasesSchema(BaseModel):
    test_cases: List[TestCase] = Field(description="List of test cases")