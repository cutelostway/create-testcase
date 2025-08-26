# export_to_excel.py - Excel export helper
import pandas as pd

def export_to_excel(test_cases, path: str = "test_cases.xlsx"):
    """
    Export test cases to an Excel file.
    
    Args:
        test_cases: list of Pydantic models (or dicts)
        path: Output file path (default: "test_cases.xlsx")
    """
    # Convert test cases to dictionaries if they are Pydantic models
    rows = [tc.dict() if hasattr(tc, "dict") else dict(tc) for tc in test_cases]
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
