
# Copilot Action Plan — AI‑Powered Test Case Generation (Streamlit + LangGraph + Llama‑3.1)

> Goal: Build the exact app described in the Medium post “AI‑Powered Test Case Generation with LangGraph”.  
> Output: A Streamlit app that accepts a user story, generates structured test cases via LangGraph + LLM, and exports them to an Excel file.

---

## 1) Project Setup
- Initialize a Python project and Git repository.
- Create and activate a virtual environment.
- Add **requirements.txt** with at least:
  ```text
  streamlit
  langgraph
  langchain-groq
  python-dotenv
  pydantic
  pandas
  openpyxl
  ```
- Install dependencies.

## 2) Environment Configuration
- Create a **.env** file with the API key for Groq (for Llama‑3.1):
  ```env
  GROQ_API_KEY=YOUR_KEY_HERE
  ```

## 3) Repository Structure
Create the files below:

```
.
├─ app.py                 # Streamlit UI
├─ tester_agent.py        # LangGraph/LLM logic
├─ export_to_excel.py     # Excel export helper
├─ requirements.txt
└─ .env                   # API keys (excluded from git)
```

## 4) Excel Export Helper (export_to_excel.py)
- Implement a function to persist generated test cases to an Excel file:

```python
# export_to_excel.py
import pandas as pd

def export_to_excel(test_cases, path: str = "test_cases.xlsx"):
    # test_cases: list of Pydantic models (or dicts)
    rows = [tc.dict() if hasattr(tc, "dict") else dict(tc) for tc in test_cases]
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
```

## 5) LangGraph + LLM Logic (tester_agent.py)
- Define the system prompt:
```python
GENERATOR_PROMPT = """
You are an expert software tester. Analyse the given user story in depth and generate a comprehensive set of test cases,
including functional, edge, and boundary cases, to ensure complete test coverage of the functionality.
"""
```
- Define the **Pydantic** schema for a single test case and the output envelope:
```python
from typing import TypedDict, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

class TestCase(BaseModel):
    test_case_id: int = Field(..., description="Unique identifier for the test case.")
    test_title: str = Field(..., description="Title of the test case.")
    description: str = Field(..., description="Detailed description of what the test case covers.")
    preconditions: str = Field(..., description="Any setup required before execution.")
    test_steps: str = Field(..., description="Step-by-step execution guide.")
    test_data: str = Field(..., description="Input values required for the test.")
    expected_result: str = Field(..., description="The anticipated outcome.")
    comments: str = Field(..., description="Additional notes or observations.")

class OutputSchema(BaseModel):
    test_cases: List[TestCase]
```
- Define the LangGraph **State** and build a minimal **StateGraph** with a single node:
```python
class State(TypedDict):
    test_cases: OutputSchema
    user_story: str

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

llm_with_structured_output = llm.with_structured_output(OutputSchema)

def test_cases_generator(state: State):
    prompt = f"{GENERATOR_PROMPT}\n\nHere is the user story:\n\n{state['user_story']}"
    response = llm_with_structured_output.invoke(prompt)
    return {"test_cases": response}

graph_builder = StateGraph(State)
graph_builder.add_node("generator", test_cases_generator)
graph_builder.set_entry_point("generator")
graph_builder.set_finish_point("generator")
graph = graph_builder.compile()

def generate_test_cases(user_input: str):
    test_cases = []
    for event in graph.stream({"test_cases": [], "user_story": user_input}):
        for value in event.values():
            if value.get("test_cases"):
                cases_list = value["test_cases"].test_cases
                test_cases = cases_list
    return test_cases
```

## 6) Streamlit UI (app.py)
- Build the UI with a text area, a button to generate, and Excel export:
```python
import streamlit as st
from export_to_excel import export_to_excel
from tester_agent import generate_test_cases

st.title("AI Test Case Generator")

user_story = st.text_area("Enter the user story or functionality description:")

if st.button("Generate Test Cases"):
    if user_story.strip():
        test_cases = generate_test_cases(user_story)
        export_to_excel(test_cases)
        st.success("Your test cases have been generated and exported successfully! Check your downloaded file.")
    else:
        st.warning("Please enter a user story to generate test cases.")
```

## 7) Run
- Start the app:
  ```bash
  streamlit run app.py
  ```

## 8) Quick Dry‑Run (for validation)
- Use this sample user story to verify output quality:
  - **Title:** User Authentication for Secure Access
  - **As a user, I want** to log in using my email and password, **so that** I can securely access my account and personalized features.
  - **Acceptance criteria (abridged):** email/password fields; email format validation; required password; error messages for invalid format/credentials; disabled login button until fields filled; forgot‑password link; loading indicator; redirect on success; stay + error on failure; optional “remember me”; responsive design.

## 9) Deliverables
- **Streamlit app** that generates structured test cases.
- **test_cases.xlsx** file exported to the project root.

## 10) Optional Enhancements (backlog)
- Add `st.download_button` to serve the produced Excel file directly in-browser.
- Add schema validation & input length checks; handle LLM/API errors gracefully.
- Parameterize model name and temperature via environment vars.
- Append timestamp to Excel file name for runs history.
- Support CSV export as an alternative.
