# tester_agent.py - LangGraph/LLM logic
from typing import TypedDict, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
import json

# System prompt for the test case generator
GENERATOR_PROMPT = """
You are an expert software tester. Analyze the given user story in depth and generate a comprehensive set of test cases,
including functional, edge, and boundary cases, to ensure complete test coverage of the functionality.

Generate your response as a JSON object with the following structure:
{
  "test_cases": [
    {
      "test_case_id": 1,
      "test_title": "Test case title",
      "description": "Description of the test case",
      "preconditions": "Setup required",
      "test_steps": "Step by step instructions",
      "test_data": "Input data needed",
      "expected_result": "Expected outcome",
      "comments": "Additional notes"
    }
  ]
}
"""

# Pydantic schema for a single test case
class TestCase(BaseModel):
    test_case_id: int = Field(..., description="Unique identifier for the test case")
    test_title: str = Field(..., description="Title of the test case")
    description: str = Field(..., description="Detailed description of what the test case covers")
    preconditions: str = Field(..., description="Any setup required before execution")
    test_steps: str = Field(..., description="Step-by-step execution guide")
    test_data: str = Field(..., description="Input values required for the test")
    expected_result: str = Field(..., description="The anticipated outcome")
    comments: str = Field(..., description="Additional notes or observations")

# Output schema containing list of test cases
class OutputSchema(BaseModel):
    test_cases: List[TestCase] = Field(..., description="List of generated test cases")

# LangGraph State definition
class State(TypedDict):
    test_cases: List[TestCase]
    user_story: str

# Load environment variables
load_dotenv()

# Initialize the LLM (without structured output)
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=4000,
    timeout=None,
    max_retries=2,
)

def test_cases_generator(state: State):
    """Generate test cases based on user story."""
    prompt = f"{GENERATOR_PROMPT}\n\nHere is the user story:\n\n{state['user_story']}\n\nProvide only the JSON response:"
    
    try:
        # Use regular invoke instead of structured output
        response = llm.invoke(prompt)
        response_text = response.content
        
        # Clean the response to extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.rfind("```")
            response_text = response_text[json_start:json_end].strip()
        
        # Parse JSON and create TestCase objects
        parsed_data = json.loads(response_text)
        test_cases = [TestCase(**case) for case in parsed_data["test_cases"]]
        
        return {"test_cases": test_cases}
        
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error parsing response: {e}")
        # Return fallback test cases
        fallback_cases = [
            TestCase(
                test_case_id=1,
                test_title="Basic Functionality Test",
                description="Test the basic functionality described in the user story",
                preconditions="System is ready and user has access",
                test_steps="Follow the main workflow described in the user story",
                test_data="Valid input data",
                expected_result="System behaves as expected",
                comments="Generated due to parsing error - please regenerate"
            )
        ]
        return {"test_cases": fallback_cases}

# Build the LangGraph
graph_builder = StateGraph(State)
graph_builder.add_node("generator", test_cases_generator)
graph_builder.set_entry_point("generator")
graph_builder.set_finish_point("generator")
graph = graph_builder.compile()

def generate_test_cases(user_input: str) -> List[TestCase]:
    """
    Generate test cases from user story input.
    
    Args:
        user_input: The user story or functionality description
        
    Returns:
        List of TestCase objects
    """
    try:
        result = graph.invoke({"test_cases": [], "user_story": user_input})
        return result.get("test_cases", [])
    except Exception as e:
        print(f"Error generating test cases: {e}")
        return []
