# 🔑 Hướng dẫn thiết lập Groq API Key

## 🚀 Thiết lập nhanh

### 1. Chạy script tự động thiết lập
```bash
python3 auto_setup_groq.py
```

Script này sẽ:
- ✅ Mở Groq Console trong trình duyệt
- ✅ Hiển thị hướng dẫn chi tiết
- ✅ Tạo file .env template
- ✅ Kiểm tra dependencies

### 2. Lấy API Key từ Groq Console
1. 🌐 Truy cập: https://console.groq.com/
2. 👤 Đăng ký/Đăng nhập tài khoản (miễn phí)
3. 🔑 Nhấn 'API Keys' hoặc 'Keys' trong menu
4. ➕ Nhấn 'Create API Key' hoặc '+ New Key'
5. 📝 Đặt tên cho key (ví dụ: 'AI Test Case Generator')
6. 📋 Copy API key (bắt đầu bằng 'gsk_')

### 3. Cập nhật API Key vào file .env
Mở file `.env` và thay thế:
```
GROQ_API_KEY=gsk_your_actual_api_key_here
```
Thành:
```
GROQ_API_KEY=gsk_1234567890abcdef1234567890abcdef12345678
```

### 4. Test API Key
```bash
python3 update_api_key.py test
```

### 5. Khởi động ứng dụng
```bash
python3 start_app.py
```

## 📋 Các script hỗ trợ

| Script | Mô tả |
|--------|-------|
| `auto_setup_groq.py` | Thiết lập tự động Groq API key |
| `update_api_key.py test` | Test API key hiện tại |
| `update_api_key.py update` | Cập nhật API key |
| `start_app.py` | Khởi động ứng dụng với kiểm tra API key |

## 🔍 Kiểm tra API Key

### Cách 1: Sử dụng script
```bash
python3 update_api_key.py test
```

### Cách 2: Kiểm tra thủ công
```bash
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('GROQ_API_KEY')
print('API Key:', api_key[:10] + '...' if api_key else 'Chưa thiết lập')
"
```

## 🚨 Xử lý lỗi

### Lỗi 403 - Access denied
- ✅ Kiểm tra API key có đúng không
- ✅ Đảm bảo API key bắt đầu bằng 'gsk_'
- ✅ Kiểm tra tài khoản Groq có hoạt động không

### Lỗi ImportError
```bash
pip install langchain-groq python-dotenv
```

### Lỗi file .env không tồn tại
```bash
python3 auto_setup_groq.py
```

## 💡 Lưu ý

- 🔒 **Bảo mật**: Không chia sẻ API key công khai
- 💰 **Miễn phí**: Groq có giới hạn hợp lý cho tài khoản miễn phí
- 🔄 **Restart**: Cần restart ứng dụng sau khi cập nhật API key
- 📝 **Format**: API key phải bắt đầu bằng 'gsk_'

## 🎯 Kết quả mong đợi

Sau khi thiết lập thành công:
- ✅ Không còn lỗi 403 trong terminal
- ✅ Test cases được tạo bởi AI thay vì fallback
- ✅ Không còn comment "Được tạo tự động do lỗi phân tích/mô hình"
- ✅ Test cases phù hợp với user story của bạn
