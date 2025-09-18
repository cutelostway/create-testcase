# export_to_excel.py - Excel export helper
import pandas as pd
from io import BytesIO
from excel_template_processor import export_with_template
from template_updater import export_template_with_values

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


def export_to_excel_bytes(test_cases) -> bytes:
    """
    Create an Excel file in-memory and return bytes for download.
    """
    rows = [tc.dict() if hasattr(tc, "dict") else dict(tc) for tc in test_cases]
    df = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer.read()


def export_to_excel_template_bytes(test_cases, project_settings) -> bytes:
    """
    Export test cases với template Excel theo format TPL-QA-01-04
    
    Args:
        test_cases: list các test case
        project_settings: dict chứa thông tin project
    
    Returns:
        bytes: Excel file với template và VBA code
    """
    return export_with_template(project_settings, test_cases)


def export_original_template_bytes(test_cases, project_settings) -> bytes:
    """
    Export test cases với template Excel gốc (giữ nguyên format, màu sắc, font...)
    
    Args:
        test_cases: list các test case
        project_settings: dict chứa thông tin project
    
    Returns:
        bytes: Excel file với template gốc đã được cập nhật
    """
    return export_template_with_values(project_settings, test_cases)
