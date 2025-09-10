# tester_agent.py - LangGraph/LLM logic
from typing import TypedDict, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import Any, Dict
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
    num_cases: int
    project_settings: Dict[str, Any]

# Load environment variables
load_dotenv()

# Initialize the LLM (slightly higher temperature for diversity)
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.4,
    max_tokens=4000,
    timeout=None,
    max_retries=2,
)

# Try preparing a structured LLM for OutputSchema when available
structured_llm = None
try:
    # Newer langchain-groq supports structured output via Pydantic
    structured_llm = llm.with_structured_output(OutputSchema)
except Exception:
    structured_llm = None

def _robust_json_extract(text: str) -> Dict[str, Any]:
    """Attempt to robustly extract a JSON object from a text blob."""
    # Handle fenced code blocks first
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.rfind("```")
        if end != -1:
            text = text[start:end].strip()

    # Fallback: take the outermost JSON braces
    if "{" in text and "}" in text:
        first = text.find("{")
        last = text.rfind("}")
        candidate = text[first:last + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Final try: direct parse
    return json.loads(text)


def _build_context_prompt(project_settings: Dict[str, Any]) -> str:
    if not project_settings:
        return ""
    try:
        languages = ", ".join(project_settings.get("languages", []) or [])
        testing_types = ", ".join(project_settings.get("testing_types", []) or [])
        writing_style = project_settings.get("writing_style", "") or ""
        detail_level = project_settings.get("detail_level", "") or ""
        steps_detail = project_settings.get("steps_detail", "") or ""
        exclusion_rules = ", ".join(project_settings.get("exclusion_rules", []) or [])
        priorities = project_settings.get("priority_levels", {}) or {}
        priorities_str = ", ".join([f"{k}:{v}" for k, v in priorities.items() if v])
        return (
            "Context for diversification:"\
            f"\n- Languages: {languages}"\
            f"\n- Testing Types: {testing_types}"\
            f"\n- Writing Style: {writing_style}"\
            f"\n- Detail Level: {detail_level}"\
            f"\n- Steps Detail: {steps_detail}"\
            f"\n- Exclusion Rules: {exclusion_rules}"\
            f"\n- Priority Levels: {priorities_str}"
        )
    except Exception:
        return ""


def test_cases_generator(state: State):
    """Generate test cases based on user story."""
    target_num = max(1, int(state.get('num_cases', 10)))
    context_note = _build_context_prompt(state.get('project_settings', {}))
    prompt = (
        f"{GENERATOR_PROMPT}\n\n"
        f"Here is the user story:\n\n{state['user_story']}\n\n"
        f"{context_note}\n\n"
        f"Generate up to {target_num} diverse, non-duplicated test cases distributed across the selected testing types. "
        f"Include positive, negative, boundary, and edge scenarios. Vary inputs, preconditions, and expected outcomes. "
        f"Ensure unique and descriptive test_title for each case. Always respond ONLY with the JSON object described above."
    )
    
    try:
        # Prefer structured output if available
        if structured_llm is not None:
            structured = structured_llm.invoke(prompt)
            # structured may be a Pydantic model or a dict
            if isinstance(structured, OutputSchema):
                test_cases = [TestCase.model_validate(tc.model_dump()) if isinstance(tc, TestCase) else TestCase(**tc) for tc in structured.test_cases]
            else:
                test_cases = [TestCase(**tc) for tc in structured.get("test_cases", [])]
        else:
            # Fallback to text mode and robust JSON extraction
            response = llm.invoke(prompt)
            response_text = response.content
            parsed_data = _robust_json_extract(response_text)
            test_cases = [TestCase(**case) for case in parsed_data.get("test_cases", [])]
        
        # Ensure we got non-empty list, otherwise trigger fallback
        if not test_cases:
            raise ValueError("Empty test cases from model")

        # Trim to requested number if needed
        if len(test_cases) > target_num:
            test_cases = test_cases[:target_num]
        
        return {"test_cases": test_cases}
        
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error parsing response: {e}")
        # Return diversified fallback test cases (multiple)
        fallback_count = max(3, target_num)
        archetypes = [
            ("Positive Flow", "Valid inputs and expected happy-path behavior", "User follows the main flow successfully", "Valid set of inputs", "System returns success and correct data"),
            ("Negative Credentials", "Invalid or missing credentials/permissions", "Attempt action without proper permissions", "Invalid token/role/empty fields", "System denies action with proper error message"),
            ("Boundary Values", "Min/Max boundary and off-by-one inputs", "Use boundary and just-outside values", "Boundary and extreme inputs", "System handles boundaries without errors"),
            ("Error Handling", "Network or server-side error handling", "Simulate failure and retry paths", "Injected failures/timeouts", "Graceful error and recovery where applicable"),
            ("Data Validation", "Incorrect data format and constraint violations", "Submit malformed/constraint-breaking data", "Wrong formats/nulls/oversized", "Validation messages shown, no data corruption"),
        ]
        fallback_cases: List[TestCase] = []
        for i in range(1, fallback_count + 1):
            kind = archetypes[(i - 1) % len(archetypes)]
            fallback_cases.append(
                TestCase(
                    test_case_id=i,
                    test_title=f"{kind[0]} Scenario #{i}",
                    description=kind[1],
                    preconditions="System operational; environment configured as per project settings",
                    test_steps=kind[2],
                    test_data=kind[3],
                    expected_result=kind[4],
                    comments="Fallback generated due to parsing/model error"
                )
            )
        return {"test_cases": fallback_cases}

# Build the LangGraph
graph_builder = StateGraph(State)
graph_builder.add_node("generator", test_cases_generator)
graph_builder.set_entry_point("generator")
graph_builder.set_finish_point("generator")
graph = graph_builder.compile()

def generate_test_cases(user_input: str, num_cases: int = 10, project_settings: Dict[str, Any] | None = None) -> List[TestCase]:
    """
    Generate test cases from user story input.
    
    Args:
        user_input: The user story or functionality description
        num_cases: Desired maximum number of test cases to generate
        project_settings: Additional context to diversify generation
        
    Returns:
        List of TestCase objects
    """
    try:
        result = graph.invoke({
            "test_cases": [],
            "user_story": user_input,
            "num_cases": int(num_cases),
            "project_settings": project_settings or {},
        })
        return result.get("test_cases", [])
    except Exception as e:
        print(f"Error generating test cases: {e}")
        return []
