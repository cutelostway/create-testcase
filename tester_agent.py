# tester_agent.py - LangGraph/LLM logic
from typing import TypedDict, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

# System prompt for the test case generator
GENERATOR_PROMPT = """
You are an expert software tester. Analyse the given user story in depth and generate a comprehensive set of test cases,
including functional, edge, and boundary cases, to ensure complete test coverage of the functionality.
"""

# Pydantic schema for a single test case
class TestCase(BaseModel):
    test_case_id: int = Field(..., description="Unique identifier for the test case.")
    test_title: str = Field(..., description="Title of the test case.")
    description: str = Field(..., description="Detailed description of what the test case covers.")
    preconditions: str = Field(..., description="Any setup required before execution.")
    test_steps: str = Field(..., description="Step-by-step execution guide.")
    test_data: str = Field(..., description="Input values required for the test.")
    expected_result: str = Field(..., description="The anticipated outcome.")
    comments: str = Field(..., description="Additional notes or observations.")

# Output schema containing list of test cases
class OutputSchema(BaseModel):
    test_cases: List[TestCase]

# LangGraph State definition
class State(TypedDict):
    test_cases: OutputSchema
    user_story: str

# Load environment variables
load_dotenv()

# Initialize the LLM with structured output
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

llm_with_structured_output = llm.with_structured_output(OutputSchema)

def test_cases_generator(state: State):
    """Generate test cases based on user story."""
    prompt = f"{GENERATOR_PROMPT}\n\nHere is the user story:\n\n{state['user_story']}"
    response = llm_with_structured_output.invoke(prompt)
    return {"test_cases": response}

# Build the LangGraph
graph_builder = StateGraph(State)
graph_builder.add_node("generator", test_cases_generator)
graph_builder.set_entry_point("generator")
graph_builder.set_finish_point("generator")
graph = graph_builder.compile()

def generate_test_cases(user_input: str):
    """
    Generate test cases from user story input.
    
    Args:
        user_input: The user story or functionality description
        
    Returns:
        List of TestCase objects
    """
    test_cases = []
    for event in graph.stream({"test_cases": [], "user_story": user_input}):
        for value in event.values():
            if value.get("test_cases"):
                cases_list = value["test_cases"].test_cases
                test_cases = cases_list
    return test_cases
