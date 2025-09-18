# template_updater.py - Cập nhật template Excel gốc với giá trị mới
import shutil
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from datetime import datetime
from io import BytesIO
import os

def update_template_with_values(project_settings, test_cases):
    """
    Copy template file gốc và chỉ cập nhật các giá trị cần thiết
    
    Args:
        project_settings: dict chứa thông tin project
        test_cases: list các test case
    
    Returns:
        bytes: Excel file đã được cập nhật
    """
    # Đường dẫn đến template file gốc
    template_path = "TPL-QA-01-04_Testcase_v1.3 (1).xlsm"
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file không tồn tại: {template_path}")
    
    # Tạo bản copy trong memory
    buffer = BytesIO()
    
    # Copy file gốc
    with open(template_path, 'rb') as source_file:
        buffer.write(source_file.read())
    
    buffer.seek(0)
    
    # Load workbook từ buffer
    wb = load_workbook(buffer, keep_vba=True)
    
    # Cập nhật các sheet theo yêu cầu
    update_cover_sheet(wb, project_settings)
    update_report_sheet(wb, project_settings, test_cases)
    
    # Lưu lại vào buffer mới
    output_buffer = BytesIO()
    wb.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer.read()

def update_cover_sheet(wb, project_settings):
    """Cập nhật sheet Cover với thông tin project"""
    try:
        ws = wb["Cover"]
    except KeyError:
        # Nếu không có sheet Cover, tạo mới
        ws = wb.create_sheet("Cover")
    
    try:
        # Cập nhật các cell theo yêu cầu mới
        # Cell D3 = Project Name
        ws['D3'] = project_settings.get('name', '')
        
        # Cell D4 = Phase
        ws['D4'] = project_settings.get('phase', '')
        
        # Cell G3 = blank
        ws['G3'] = ""
        
        # Dòng 8 - Record of Change
        today = datetime.now().strftime("%Y-%m-%d")
        ws['B8'] = today  # Date
        ws['C8'] = "1.0"  # Version
        ws['D8'] = "Add new"  # Change Description
        ws['E8'] = "A"  # A/M/D
        ws['F8'] = "All sheet"  # Change Item
            
    except Exception as e:
        print(f"Lỗi khi cập nhật Cover sheet: {e}")


def update_report_sheet(wb, project_settings, test_cases):
    """Cập nhật sheet Report với test cases"""
    try:
        ws = wb["Report"]
    except KeyError:
        ws = wb.create_sheet("Report")
    
    try:
        # Tìm vị trí bắt đầu của bảng test case
        start_row = find_test_case_start_row(ws)
        
        if start_row == -1:
            print("Không tìm thấy vị trí bắt đầu của bảng test case")
            return
        
        # Xóa dữ liệu cũ nếu có
        clear_old_test_cases(ws, start_row)
        
        # Thêm test cases mới
        for idx, case in enumerate(test_cases, 1):
            row = start_row + idx
            
            # Chuyển đổi case thành dict nếu cần
            if hasattr(case, 'dict'):
                case_dict = case.dict()
            else:
                case_dict = dict(case)
            
            # Xác định priority từ test_case_id
            priority = "Medium"
            if 'critical' in str(case_dict.get('test_case_id', '')).lower():
                priority = "Critical"
            elif 'high' in str(case_dict.get('test_case_id', '')).lower():
                priority = "High"
            elif 'low' in str(case_dict.get('test_case_id', '')).lower():
                priority = "Low"
            
            # Điền dữ liệu vào các cột theo template gốc
            # Giả sử cấu trúc cột: A=No, B=Test Case ID, C=Test Title, D=Description, E=Preconditions, F=Test Data, G=Test Steps, H=Expected Result, I=Priority, J=Status, K=Comments
            ws.cell(row=row, column=1, value=idx)  # No
            ws.cell(row=row, column=2, value=case_dict.get('test_case_id', ''))  # Test Case ID
            ws.cell(row=row, column=3, value=case_dict.get('test_title', ''))  # Test Title
            ws.cell(row=row, column=4, value=case_dict.get('description', ''))  # Description
            ws.cell(row=row, column=5, value=case_dict.get('preconditions', ''))  # Preconditions
            ws.cell(row=row, column=6, value=case_dict.get('test_data', ''))  # Test Data
            ws.cell(row=row, column=7, value=case_dict.get('test_steps', ''))  # Test Steps
            ws.cell(row=row, column=8, value=case_dict.get('expected_result', ''))  # Expected Result
            ws.cell(row=row, column=9, value=priority)  # Priority
            ws.cell(row=row, column=10, value="Not Executed")  # Status
            ws.cell(row=row, column=11, value=case_dict.get('comments', ''))  # Comments
            
    except Exception as e:
        print(f"Lỗi khi cập nhật Report sheet: {e}")


def find_test_case_start_row(ws):
    """Tìm dòng bắt đầu của bảng test case"""
    # Tìm dòng có header "Test Case ID" hoặc tương tự
    for row in range(1, ws.max_row + 1):
        for col in range(1, 15):
            cell_value = ws.cell(row=row, column=col).value
            if cell_value and "test case" in str(cell_value).lower():
                return row + 1  # Dòng bắt đầu dữ liệu
    return -1

def clear_old_test_cases(ws, start_row):
    """Xóa dữ liệu test case cũ"""
    # Xóa từ dòng start_row đến cuối sheet
    for row in range(start_row, ws.max_row + 1):
        for col in range(1, 15):
            ws.cell(row=row, column=col).value = None

def export_template_with_values(project_settings, test_cases):
    """
    Export test cases với template gốc đã được cập nhật
    
    Args:
        project_settings: dict chứa thông tin project
        test_cases: list các test case
    
    Returns:
        bytes: Excel file với template gốc đã được cập nhật
    """
    return update_template_with_values(project_settings, test_cases)
