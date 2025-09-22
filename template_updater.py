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
    Chỉ sử dụng file TPL-QA-01-04_Testcase_v1.3(1).xlsm
    
    Args:
        project_settings: dict chứa thông tin project
        test_cases: list các test case
    
    Returns:
        bytes: Excel file đã được cập nhật
    """
    # Lấy số lượng environment
    environments = project_settings.get('environment', ['Chrome'])
    num_environments = len(environments)
    
    # Chỉ sử dụng file TPL-QA-01-04_Testcase_v1.3(1).xlsm
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
    update_module_sheets(wb, project_settings, test_cases)
    
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

def update_report_sheet(wb, project_settings, test_cases):
    """Cập nhật sheet Report theo hướng dẫn chi tiết"""
    try:
        ws = wb["Report"]
    except KeyError:
        print("Không tìm thấy sheet Report")
        return
    
    try:
        # Bước 1: Giữ nguyên toàn bộ format (không làm gì)
        
        # Bước 2: Lấy số environment đã chọn
        environments = project_settings.get('environment', ['Chrome'])
        x = len(environments)
        
        # Bước 3: Tìm vị trí "General statistic" và ghi tên môi trường
        row1 = find_cell_by_text(ws, "General statistic")
        print(f"row1 old: {row1}")

        if not row1:
            print("Không tìm thấy 'General statistic'")
            return
        
        # Ghi tên môi trường từ C{row1+1} đến C{row1+x}
        for i, env in enumerate(environments):
            ws[f"C{row1 + 1 + i}"] = env
        
        # Bước 4: Tìm "Round 1 base statistic" và xóa rows
        row2 = find_cell_by_text(ws, "Round 1 base statistic")
        print(f"row2 old: {row2}")
        if not row2:
            print("Không tìm thấy 'Round 1 base statistic'")
            return
        
        # Bước 4: Merge A{row1+1} ~ B{row1+x} trước khi xóa
        merge_start_row = row1 + 1
        merge_end_row = row1 + x
        merge_range = f"A{merge_start_row}:B{merge_end_row}"
        print(f"Bước 4: Merge {merge_range} trước khi xóa")
        try:
            # Kiểm tra xung đột trước khi merge
            if not check_merge_conflict(ws, merge_start_row, merge_end_row, 1, 2):
                ws.merge_cells(merge_range)
                print(f"  Đã merge {merge_range}")
            else:
                print(f"  Bỏ qua merge {merge_range} do xung đột")
        except Exception as e:
            print(f"  Lỗi khi merge {merge_range}: {e}")
        
        # Xóa rows từ {row1 + 1 + x} đến {row2 - 2}
        start_delete = row1 + 1 + x
        end_delete = row2 - 2
        print(f"Bước 4: Xóa rows từ {start_delete} đến {end_delete}")
        if start_delete <= end_delete:
            # Xóa từ dưới lên để tránh lỗi index
            for row in range(end_delete, start_delete - 1, -1):
                print(f"  Xóa row {row}")
                ws.delete_rows(row)
        
        # Sau khi xóa dòng ở bước 4, merge các cells để khôi phục format title table
        print("Bước 4: Khôi phục format title table sau khi xóa")
        merge_ranges_after_4 = [
            f"A{row2+1}:C{row2+3}",
            f"D{row2+1}:R{row2+1}",
            f"D{row2+2}:H{row2+2}",
            f"I{row2+2}:M{row2+2}",
            f"N{row2+2}:R{row2+2}",
            f"S{row2+1}:U{row2+1}",
            f"V{row2+1}:X{row2+1}",
            f"S{row2+2}:S{row2+3}",
            f"T{row2+2}:T{row2+3}",
            f"U{row2+2}:U{row2+3}",
            f"V{row2+2}:V{row2+3}",
            f"W{row2+2}:W{row2+3}",
            f"X{row2+2}:X{row2+3}"
        ]
        safe_merge_cells(ws, merge_ranges_after_4)
        
        # Bước 5: Tìm lại vị trí "Round 1 base statistic" sau khi xóa
        row2 = find_cell_by_text(ws, "Round 1 base statistic")
        print(f"row2 new: {row2}")
        if not row2:
            print("Không tìm thấy 'Round 1 base statistic' sau khi xóa")
            return
        
        # Bước 6: Tìm "Round 2 base statistic" và xóa rows
        row3 = find_cell_by_text(ws, "Round 2 base statistic")
        print(f"row3 old: {row3}")
        if not row3:
            print("Không tìm thấy 'Round 2 base statistic'")
            return
        
        # Bước 6: Merge A{row2+4} ~ B{row2+3+x} trước khi xóa
        merge_start_row = row2 + 4
        merge_end_row = row2 + 3 + x
        merge_range = f"A{merge_start_row}:B{merge_end_row}"
        print(f"Bước 6: Merge {merge_range} trước khi xóa")
        try:
            # Kiểm tra xung đột trước khi merge
            if not check_merge_conflict(ws, merge_start_row, merge_end_row, 1, 2):
                ws.merge_cells(merge_range)
                print(f"  Đã merge {merge_range}")
            else:
                print(f"  Bỏ qua merge {merge_range} do xung đột")
        except Exception as e:
            print(f"  Lỗi khi merge {merge_range}: {e}")
        
        # Xóa rows từ {row2 + 4 + x} đến {row3 - 3}
        start_delete = row2 + 4 + x
        end_delete = row3 - 3
        print(f"Bước 6: Xóa rows từ {start_delete} đến {end_delete}")
        if start_delete <= end_delete:
            for row in range(end_delete, start_delete - 1, -1):
                print(f"  Xóa row {row}")
                ws.delete_rows(row)
        
        # Sau khi xóa dòng ở bước 6, merge các cells để khôi phục format title table
        print("Bước 6: Khôi phục format title table sau khi xóa")
        merge_ranges_after_6 = [
            f"A{row3+1}:C{row3+3}",
            f"D{row3+1}:R{row3+1}",
            f"D{row3+2}:H{row3+2}",
            f"I{row3+2}:M{row3+2}",
            f"N{row3+2}:R{row3+2}",
            f"S{row3+1}:U{row3+1}",
            f"V{row3+1}:X{row3+1}",
            f"S{row3+2}:S{row3+3}",
            f"T{row3+2}:T{row3+3}",
            f"U{row3+2}:U{row3+3}",
            f"V{row3+2}:V{row3+3}",
            f"W{row3+2}:W{row3+3}",
            f"X{row3+2}:X{row3+3}"
        ]
        safe_merge_cells(ws, merge_ranges_after_6)
        
        # Bước 7: Tìm lại vị trí "Round 2 base statistic" sau khi xóa
        row3 = find_cell_by_text(ws, "Round 2 base statistic")
        print(f"row3 new: {row3}")
        if not row3:
            print("Không tìm thấy 'Round 2 base statistic' sau khi xóa")
            return
        
        # Bước 8: Tìm "Round 1 in detail" và xóa rows
        row4 = find_cell_by_text(ws, "Round 1 in detail")
        if not row4:
            print("Không tìm thấy 'Round 1 in detail'")
            return
        
        # Bước 8: Merge A{row3+4} ~ B{row3+3+x} trước khi xóa
        merge_start_row = row3 + 4
        merge_end_row = row3 + 3 + x
        merge_range = f"A{merge_start_row}:B{merge_end_row}"
        print(f"Bước 8: Merge {merge_range} trước khi xóa")
        try:
            # Kiểm tra xung đột trước khi merge
            if not check_merge_conflict(ws, merge_start_row, merge_end_row, 1, 2):
                ws.merge_cells(merge_range)
                print(f"  Đã merge {merge_range}")
            else:
                print(f"  Bỏ qua merge {merge_range} do xung đột")
        except Exception as e:
            print(f"  Lỗi khi merge {merge_range}: {e}")
        
        # Xóa rows từ {row3 + 4 + x} đến {row4 - 3}
        start_delete = row3 + 4 + x
        end_delete = row4 - 3
        if start_delete <= end_delete:
            for row in range(end_delete, start_delete - 1, -1):
                ws.delete_rows(row)
        
        # Bước 9: Tìm lại vị trí "Round 1 in detail" sau khi xóa
        row4 = find_cell_by_text(ws, "Round 1 in detail")
        if not row4:
            print("Không tìm thấy 'Round 1 in detail' sau khi xóa")
            return
        
        # Bước 10: Tìm "Round 2 in detail" và xóa rows
        row5 = find_cell_by_text(ws, "Round 2 in detail")
        if not row5:
            print("Không tìm thấy 'Round 2 in detail' - bỏ qua bước 10-12")
            # Bước 10 (fallback): Merge B{row4+2} ~ B{row4+1+x} trước khi xóa
            merge_start_row = row4 + 2
            merge_end_row = row4 + 1 + x
            merge_range = f"B{merge_start_row}:B{merge_end_row}"
            print(f"Bước 10 (fallback): Merge {merge_range} trước khi xóa")
            try:
                # Kiểm tra xung đột trước khi merge
                if not check_merge_conflict(ws, merge_start_row, merge_end_row, 2, 2):
                    ws.merge_cells(merge_range)
                    print(f"  Đã merge {merge_range}")
                else:
                    print(f"  Bỏ qua merge {merge_range} do xung đột")
            except Exception as e:
                print(f"  Lỗi khi merge {merge_range}: {e}")
            
            # Nếu không tìm thấy Round 2 in detail, xóa rows từ row4 + 2 + x đến cuối sheet
            start_delete = row4 + 2 + x
            end_delete = ws.max_row
            print(f"Bước 10 (fallback): Xóa rows từ {start_delete} đến {end_delete}")
            if start_delete <= end_delete:
                for row in range(end_delete, start_delete - 1, -1):
                    print(f"  Xóa row {row}")
                    ws.delete_rows(row)
        else:
            # Bước 10: Merge B{row4+2} ~ B{row4+1+x} trước khi xóa
            merge_start_row = row4 + 2
            merge_end_row = row4 + 1 + x
            merge_range = f"B{merge_start_row}:B{merge_end_row}"
            print(f"Bước 10: Merge {merge_range} trước khi xóa")
            try:
                # Kiểm tra xung đột trước khi merge
                if not check_merge_conflict(ws, merge_start_row, merge_end_row, 2, 2):
                    ws.merge_cells(merge_range)
                    print(f"  Đã merge {merge_range}")
                else:
                    print(f"  Bỏ qua merge {merge_range} do xung đột")
            except Exception as e:
                print(f"  Lỗi khi merge {merge_range}: {e}")
            
            # Xóa rows từ {row4 + 2 + x} đến {row5 - 2}
            start_delete = row4 + 2 + x
            end_delete = row5 - 2
            print(f"Bước 10: Xóa rows từ {start_delete} đến {end_delete}")
            if start_delete <= end_delete:
                for row in range(end_delete, start_delete - 1, -1):
                    print(f"  Xóa row {row}")
                    ws.delete_rows(row)
            
            # Bước 11: Tìm lại vị trí "Round 2 in detail" sau khi xóa
            row5 = find_cell_by_text(ws, "Round 2 in detail")
            print(f"row5 new: {row5}")
            if not row5:
                print("Không tìm thấy 'Round 2 in detail' sau khi xóa")
                return
            
            # Bước 12: Merge B{row5+2} ~ B{row5+1+x} trước khi xóa
            merge_start_row = row5 + 2
            merge_end_row = row5 + 1 + x
            merge_range = f"B{merge_start_row}:B{merge_end_row}"
            print(f"Bước 12: Merge {merge_range} trước khi xóa")
            try:
                # Kiểm tra xung đột trước khi merge
                if not check_merge_conflict(ws, merge_start_row, merge_end_row, 2, 2):
                    ws.merge_cells(merge_range)
                    print(f"  Đã merge {merge_range}")
                else:
                    print(f"  Bỏ qua merge {merge_range} do xung đột")
            except Exception as e:
                print(f"  Lỗi khi merge {merge_range}: {e}")
            
            start_delete = row5 + 2 + x
            end_delete = row5 + 10
            print(f"Bước 12: Xóa rows từ {start_delete} đến {end_delete}")
            if start_delete <= end_delete:
                for row in range(end_delete, start_delete - 1, -1):
                    print(f"  Xóa row {row}")
                    ws.delete_rows(row)
        
        print(f"Đã cập nhật Report sheet với {x} environments: {environments}")
        
    except Exception as e:
        print(f"Lỗi khi cập nhật Report sheet: {e}")

def update_module_sheets(wb, project_settings, test_cases):
    """Cập nhật các sheet Module - giữ nguyên format"""
    try:
        environments = project_settings.get('environment', ['Chrome'])
        num_environments = len(environments)
        
        # Lấy danh sách các sheet Module (bỏ qua Cover và Report)
        module_sheets = [name for name in wb.sheetnames if name not in ["Cover", "Report"]]
        
        for sheet_name in module_sheets:
            ws = wb[sheet_name]
            print(f"Đã cập nhật Module sheet: {sheet_name}")
            
    except Exception as e:
        print(f"Lỗi khi cập nhật Module sheets: {e}")



# ===== HELPER FUNCTIONS FOR VBA CONVERSION =====

def find_cell_by_text(ws, text):
    """Tìm cell chứa text cụ thể và trả về row number"""
    for row in range(1, ws.max_row + 1):
        for col in range(1, ws.max_column + 1):
            cell_value = ws.cell(row=row, column=col).value
            if cell_value and text.lower() in str(cell_value).lower():
                return row
    return None

def column_number_to_letter(column_number):
    """Chuyển đổi số cột thành chữ cái (A, B, C, ...)"""
    result = ""
    while column_number > 0:
        column_number -= 1
        result = chr(65 + column_number % 26) + result
        column_number //= 26
    return result

def check_merge_conflict(ws, start_row, end_row, start_col, end_col):
    """
    Kiểm tra xem có xung đột với merged cells hiện có không
    """
    for merged_range in ws.merged_cells.ranges:
        # Kiểm tra xem có overlap không
        if (merged_range.min_row <= end_row and merged_range.max_row >= start_row and
            merged_range.min_col <= end_col and merged_range.max_col >= start_col):
            return True
    return False

def safe_merge_cells(ws, merge_ranges):
    """
    Merge nhiều cells một cách an toàn, bỏ qua nếu có xung đột
    """
    for merge_range in merge_ranges:
        try:
            # Parse range để lấy thông tin
            start_cell, end_cell = merge_range.split(':')
            start_col = ord(start_cell[0]) - ord('A') + 1
            start_row = int(start_cell[1:])
            end_col = ord(end_cell[0]) - ord('A') + 1
            end_row = int(end_cell[1:])
            
            # Kiểm tra xung đột
            if not check_merge_conflict(ws, start_row, end_row, start_col, end_col):
                ws.merge_cells(merge_range)
                print(f"    ✅ Merged {merge_range}")
            else:
                print(f"    ⚠️ Bỏ qua {merge_range} do xung đột")
        except Exception as e:
            print(f"    ❌ Lỗi merge {merge_range}: {e}")


