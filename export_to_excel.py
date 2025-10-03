# export_to_excel.py - Excel export helper
import pandas as pd
from io import BytesIO
import re

def convert_test_case_to_dict(test_case) -> dict:
    """Convert TestCase object to dictionary"""
    # Suppress all Pydantic deprecation warnings
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        
        try:
            # Prefer Pydantic v2 API when available
            if hasattr(test_case, 'model_dump'):
                return test_case.model_dump()
            elif hasattr(test_case, 'dict'):
                return test_case.dict()
            elif hasattr(test_case, '__dict__'):
                return test_case.__dict__
            else:
                return dict(test_case)
        except Exception as e:
            # Fallback to basic conversion if all else fails
            if hasattr(test_case, '__dict__'):
                return test_case.__dict__
            else:
                return {}

def format_test_steps(test_steps: str) -> str:
    """
    Format test steps with numbered list and line breaks.
    
    Args:
        test_steps: Raw test steps string
        
    Returns:
        Formatted test steps with numbered list
    """
    if not test_steps:
        return ""
    
    # Check if steps are already properly numbered (like "1. Step\n2. Step")
    if re.search(r'^\d+\.\s+.*\n\d+\.\s+', test_steps, re.MULTILINE):
        # Steps are already properly numbered, just clean up and return
        lines = test_steps.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    # Check if steps are already numbered but need cleaning
    if re.search(r'\d+\.\s+', test_steps):
        # Split by numbered patterns and clean up
        steps = re.split(r'\d+\.\s+', test_steps)
        steps = [step.strip() for step in steps if step.strip()]
        
        # Format as numbered list
        formatted_steps = []
        for i, step in enumerate(steps, 1):
            step = step.strip()
            if step:
                formatted_steps.append(f"{i}. {step}")
        return '\n'.join(formatted_steps)
    
    # If not numbered, try to split and number
    # First try to split by common separators
    steps = re.split(r'[;,\n]', test_steps)
    steps = [step.strip() for step in steps if step.strip()]
    
    # If we only got 1 step, try more sophisticated splitting
    if len(steps) == 1:
        # Try action words
        if re.search(r'(Nhập|Nhấp|Kiểm tra|Chọn|Click|Enter|Verify|Check|Select|Click on|Fill|Input|Type|Press|Wait|Navigate|Go to|Open|Close|Log in|Log out|Sign in|Sign out)', test_steps):
            # Split by action words but keep them
            steps = re.split(r'(?=(?:Nhập|Nhấp|Kiểm tra|Chọn|Click|Enter|Verify|Check|Select|Click on|Fill|Input|Type|Press|Wait|Navigate|Go to|Open|Close|Log in|Log out|Sign in|Sign out))', test_steps)
            steps = [step.strip() for step in steps if step.strip()]
        # Finally try sentence splitting
        else:
            steps = re.split(r'[.!?]\s+', test_steps)
            steps = [step.strip() for step in steps if step.strip()]
    
    # Format as numbered list
    formatted_steps = []
    for i, step in enumerate(steps, 1):
        # Clean up the step
        step = step.strip()
        if step:
            formatted_steps.append(f"{i}. {step}")
    
    return '\n'.join(formatted_steps)

def export_to_excel(test_cases, path: str = "test_cases.xlsx"):
    """
    Export test cases to an Excel file.
    
    Args:
        test_cases: list of Pydantic models (or dicts)
        path: Output file path (default: "test_cases.xlsx")
    """
    # Convert test cases to dictionaries if they are Pydantic models
    rows = []
    for tc in test_cases:
        if hasattr(tc, "dict"):
            row = convert_test_case_to_dict(tc)
        else:
            row = dict(tc)
        
        # Format test_steps with numbered list
        if 'test_steps' in row:
            row['test_steps'] = format_test_steps(row['test_steps'])
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)


def export_to_excel_bytes(test_cases) -> bytes:
    """
    Create an Excel file in-memory and return bytes for download.
    """
    # Convert test cases to dictionaries if they are Pydantic models
    rows = []
    for tc in test_cases:
        if hasattr(tc, "dict"):
            row = convert_test_case_to_dict(tc)
        else:
            row = dict(tc)
        
        # Format test_steps with numbered list
        if 'test_steps' in row:
            row['test_steps'] = format_test_steps(row['test_steps'])
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer.read()
