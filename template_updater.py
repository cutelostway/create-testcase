# template_updater.py - Cập nhật template Excel gốc với giá trị mới
import shutil
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from datetime import datetime
from io import BytesIO
import os

def update_template_with_values(project_settings, test_cases):
    """
    Copy template file gốc và cập nhật dựa trên số lượng environment thực tế
    
    Args:
        project_settings: dict chứa thông tin project
        test_cases: list các test case
    
    Returns:
        bytes: Excel file đã được cập nhật
    """
    # Lấy số lượng environment
    environments = project_settings.get('environment', ['Chrome'])
    num_environments = len(environments)
    
    # Chọn template file dựa trên số lượng environment
    if num_environments == 1:
        template_path = "TPL_TestResult_v1.0_1En.xlsm"
    elif num_environments == 2:
        template_path = "TPL_TestResult_v1.0_2En.xlsm"
    else:  # 3+ environments
        template_path = "TPL_TestResult_v1.0_3En.xlsm"
    
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
    update_module1_sheet(wb, project_settings, test_cases)
    
    # Cập nhật environment names và thêm/xóa rows nếu cần
    update_environment_info(wb, project_settings)
    
    # Lưu lại vào buffer mới
    output_buffer = BytesIO()
    wb.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer.read()

def update_cover_sheet(wb, project_settings):
    """Cập nhật sheet Cover với thông tin project - giữ nguyên logic hiện tại"""
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

def update_module1_sheet(wb, project_settings, test_cases):
    """Cập nhật sheet Module 1 với test cases"""
    try:
        ws = wb["Module 1"]
    except KeyError:
        # Nếu không có sheet Module 1, tạo mới
        ws = wb.create_sheet("Module 1")
    
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
        print(f"Lỗi khi cập nhật Module 1 sheet: {e}")

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

def update_environment_info(wb, project_settings):
    """Cập nhật tên environment và thêm/xóa rows dựa trên số lượng environment thực tế"""
    environments = project_settings.get('environment', ['Chrome'])
    num_environments = len(environments)
    
    # Cập nhật tất cả sheets có chứa thông tin environment
    for sheet_name in wb.sheetnames:
        if sheet_name in ["Cover", "Module 1", "Report"]:
            ws = wb[sheet_name]
            update_environment_in_sheet(ws, environments, num_environments)

def update_environment_in_sheet(ws, environments, num_environments):
    """Cập nhật environment trong một sheet cụ thể"""
    try:
        # Tìm và thay thế tên environment trong tất cả cells
        for row in range(1, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                if cell.value and isinstance(cell.value, str):
                    original_value = cell.value
                    new_value = replace_environment_names(cell.value, environments)
                    if original_value != new_value:
                        cell.value = new_value
        
        # Xử lý thêm/xóa rows dựa trên số lượng environment
        if num_environments == 1:
            # Nếu chỉ có 1 environment, xóa các rows thừa
            remove_extra_environment_rows(ws, 1)
        elif num_environments == 2:
            # Nếu có 2 environments, xóa row thứ 3 nếu có
            remove_extra_environment_rows(ws, 2)
        elif num_environments > 3:
            # Nếu có nhiều hơn 3 environments, thêm rows
            add_extra_environment_rows(ws, environments, num_environments)
            
    except Exception as e:
        print(f"Lỗi khi cập nhật environment trong sheet: {e}")

def replace_environment_names(text, environments):
    """Thay thế tên environment trong text"""
    # Mapping các tên environment phổ biến
    old_names = ["Chrome", "Edge", "Firefox", "Safari"]
    
    # Thay thế từng tên cũ bằng tên mới tương ứng
    for i, old_name in enumerate(old_names):
        if i < len(environments):
            text = text.replace(old_name, environments[i])
        else:
            # Nếu không có environment tương ứng, xóa tên cũ
            text = text.replace(old_name, "")
    
    # Xử lý trường hợp đặc biệt: nếu chỉ có 1 environment, thay thế tất cả tên cũ còn lại bằng tên mới
    if len(environments) == 1:
        for old_name in old_names:
            if old_name in text and old_name != environments[0]:
                text = text.replace(old_name, environments[0])
    
    
    # Xử lý trường hợp đặc biệt: nếu text chứa nhiều environment names
    # Ví dụ: "Chrome, Edge" -> "Android, iOS"
    if len(environments) >= 2:
        # Thay thế pattern "Chrome, Edge" bằng environments[0], environments[1]
        if "Chrome" in text and "Edge" in text:
            text = text.replace("Chrome, Edge", f"{environments[0]}, {environments[1]}")
        elif "Chrome" in text and "Firefox" in text:
            text = text.replace("Chrome, Firefox", f"{environments[0]}, {environments[1]}")
        elif "Chrome" in text and "Edge" in text and "Firefox" in text:
            if len(environments) >= 3:
                text = text.replace("Chrome, Edge, Firefox", f"{environments[0]}, {environments[1]}, {environments[2]}")
    
    return text

def remove_extra_environment_rows(ws, target_count):
    """Xóa các rows environment thừa"""
    try:
        # Tìm các rows chứa thông tin environment và xóa nếu cần
        # Dựa trên cấu trúc template, tìm các rows có chứa tên environment
        
        # Tìm rows cần xóa dựa trên pattern
        rows_to_delete = []
        
        for row in range(1, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell_value = ws.cell(row=row, column=col).value
                if cell_value and isinstance(cell_value, str):
                    # Kiểm tra nếu row này chứa thông tin environment
                    if any(env in cell_value for env in ["Chrome", "Edge", "Firefox", "Safari"]):
                        # Đếm số environment trong row này
                        env_count = sum(1 for env in ["Chrome", "Edge", "Firefox", "Safari"] if env in cell_value)
                        if env_count > target_count:
                            rows_to_delete.append(row)
                            break
        
        # Xóa các rows thừa (từ dưới lên để tránh lỗi index)
        for row in sorted(rows_to_delete, reverse=True):
            ws.delete_rows(row)
            
    except Exception as e:
        print(f"Lỗi khi xóa rows environment thừa: {e}")

def add_extra_environment_rows(ws, environments, num_environments):
    """Thêm rows cho các environment bổ sung"""
    if num_environments <= 3:
        return
    
    try:
        # Tìm vị trí để thêm rows mới
        # Thường là sau row cuối cùng có chứa environment
        
        last_env_row = 0
        for row in range(1, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell_value = ws.cell(row=row, column=col).value
                if cell_value and isinstance(cell_value, str):
                    if any(env in cell_value for env in ["Chrome", "Edge", "Firefox", "Safari"]):
                        last_env_row = max(last_env_row, row)
        
        if last_env_row > 0:
            # Thêm rows cho các environment bổ sung
            for i in range(3, num_environments):
                # Thêm row mới
                ws.insert_rows(last_env_row + 1 + (i - 3))
                
                # Copy format từ row trước đó
                copy_row_format(ws, last_env_row, last_env_row + 1 + (i - 3))
                
                # Cập nhật tên environment
                for col in range(1, ws.max_column + 1):
                    cell = ws.cell(row=last_env_row + 1 + (i - 3), column=col)
                    if cell.value and isinstance(cell.value, str):
                        # Thay thế tên environment cũ bằng tên mới
                        old_envs = ["Chrome", "Edge", "Firefox", "Safari"]
                        for j, old_env in enumerate(old_envs):
                            if j < len(environments):
                                cell.value = cell.value.replace(old_env, environments[j])
                            else:
                                cell.value = cell.value.replace(old_env, "")
                
    except Exception as e:
        print(f"Lỗi khi thêm rows environment bổ sung: {e}")

def copy_row_format(ws, source_row, target_row):
    """Copy format từ source row sang target row"""
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    
    for col in range(1, ws.max_column + 1):
        source_cell = ws.cell(row=source_row, column=col)
        target_cell = ws.cell(row=target_row, column=col)
        
        # Copy format
        if source_cell.font:
            target_cell.font = Font(
                name=source_cell.font.name,
                size=source_cell.font.size,
                bold=source_cell.font.bold,
                italic=source_cell.font.italic,
                color=source_cell.font.color
            )
        
        if source_cell.alignment:
            target_cell.alignment = Alignment(
                horizontal=source_cell.alignment.horizontal,
                vertical=source_cell.alignment.vertical,
                wrap_text=source_cell.alignment.wrap_text
            )
        
        if source_cell.fill:
            target_cell.fill = PatternFill(
                start_color=source_cell.fill.start_color,
                end_color=source_cell.fill.end_color,
                fill_type=source_cell.fill.fill_type
            )
        
        if source_cell.border:
            target_cell.border = Border(
                left=source_cell.border.left,
                right=source_cell.border.right,
                top=source_cell.border.top,
                bottom=source_cell.border.bottom
            )

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