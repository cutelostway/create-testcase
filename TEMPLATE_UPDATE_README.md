# Cập nhật Logic Export File với Dynamic Environment Support

## Tổng quan
Đã cập nhật logic export file để xử lý dynamic environment dựa trên số lượng và giá trị environment thực tế được chọn:

1. **Cover sheet**: Giữ nguyên logic hiện tại
2. **Module 1 sheet**: Thay đổi tên environment và thêm/xóa rows dựa trên số lượng environment

## Các thay đổi chính

### 1. Cover Sheet
- **Giữ nguyên logic hiện tại** như yêu cầu
- Cập nhật thông tin project: Project Name, Phase, Record of Change

### 2. Template Selection Logic
- **1 environment**: Sử dụng `TPL_TestResult_v1.0_1En.xlsm`
- **2 environments**: Sử dụng `TPL_TestResult_v1.0_2En.xlsm`  
- **3+ environments**: Sử dụng `TPL_TestResult_v1.0_3En.xlsm`

### 3. Dynamic Environment Processing
- **Thay đổi tên environment**: Chrome → Edge, Firefox → Safari, etc.
- **Xóa rows thừa**: Nếu chọn ít hơn 3 environments
- **Thêm rows mới**: Nếu chọn nhiều hơn 3 environments
- **Giữ nguyên format**: Font chữ, màu sắc, merge cells

## Các hàm chính

### `update_template_with_values(project_settings, test_cases)`
- Chọn template phù hợp dựa trên số lượng environment
- Copy file template gốc
- Cập nhật Cover sheet, Module 1 sheet và environment info

### `update_environment_info(wb, project_settings)`
- Cập nhật tên environment trong tất cả sheets
- Xử lý thêm/xóa rows dựa trên số lượng environment

### `replace_environment_names(text, environments)`
- Thay thế tên environment cũ bằng tên mới
- Mapping: Chrome → environments[0], Edge → environments[1], etc.

### `remove_extra_environment_rows(ws, target_count)`
- Xóa các rows environment thừa khi chọn ít hơn 3 environments

### `add_extra_environment_rows(ws, environments, num_environments)`
- Thêm rows cho các environment bổ sung khi chọn nhiều hơn 3 environments
- Copy format từ row trước đó

## Cách sử dụng

Logic này được tích hợp vào hàm `export_original_template_bytes()` trong `export_to_excel.py`:

```python
# Sử dụng template mẫu với dynamic environment support
data = export_original_template_bytes(test_cases, project_settings)
```

## Test Results

Đã test với các scenario:
- ✅ 1 environment (Edge): Generated 80,549 bytes
- ✅ 2 environments (Android, iOS): Generated 83,110 bytes  
- ✅ 4 environments (Android, iOS, Chrome, Firefox): Generated 85,543 bytes

## Lưu ý

- Cần có 3 file template mẫu trong thư mục dự án:
  - `TPL_TestResult_v1.0_1En.xlsm`
  - `TPL_TestResult_v1.0_2En.xlsm`
  - `TPL_TestResult_v1.0_3En.xlsm`
- Format được giữ nguyên 100% từ template mẫu
- Tên environment được thay đổi chính xác theo lựa chọn
- Rows được thêm/xóa tự động dựa trên số lượng environment
