#!/usr/bin/env python3
# setup_groq.py - Script tự động thiết lập Groq API key

import os
import webbrowser
import subprocess
import sys

def print_banner():
    print("=" * 60)
    print("🔑 GROQ API KEY SETUP - AI Test Case Generator")
    print("=" * 60)
    print()

def check_env_file():
    """Kiểm tra file .env hiện tại"""
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
            if "GROQ_API_KEY" in content and "your_groq_api_key_here" not in content:
                print("✅ File .env đã có API key!")
                return True
    return False

def open_groq_console():
    """Mở Groq Console trong trình duyệt"""
    print("🌐 Đang mở Groq Console...")
    webbrowser.open("https://console.groq.com/")
    print("✅ Đã mở Groq Console trong trình duyệt!")
    print()

def get_api_key_from_user():
    """Lấy API key từ người dùng"""
    print("📋 Hướng dẫn lấy API key:")
    print("1. Đăng ký/Đăng nhập tài khoản Groq")
    print("2. Nhấn 'API Keys' hoặc 'Keys' trong menu")
    print("3. Nhấn 'Create API Key' hoặc '+ New Key'")
    print("4. Đặt tên cho key (ví dụ: 'AI Test Case Generator')")
    print("5. Copy API key (bắt đầu bằng 'gsk_')")
    print()
    
    while True:
        api_key = input("🔑 Nhập API key của bạn (bắt đầu bằng 'gsk_'): ").strip()
        
        if not api_key:
            print("❌ Vui lòng nhập API key!")
            continue
            
        if not api_key.startswith('gsk_'):
            print("❌ API key phải bắt đầu bằng 'gsk_'!")
            continue
            
        if len(api_key) < 20:
            print("❌ API key quá ngắn! Vui lòng kiểm tra lại.")
            continue
            
        return api_key

def save_api_key(api_key):
    """Lưu API key vào file .env"""
    env_content = f"""# Groq API Key - Get your API key from https://console.groq.com/
GROQ_API_KEY={api_key}

# Optional: Jira Configuration (if using Jira integration)
# JIRA_SERVER=https://yourcompany.atlassian.net
# JIRA_USERNAME=your_email@company.com
# JIRA_PASSWORD=your_password_or_app_password
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Đã lưu API key vào file .env!")

def test_api_key(api_key):
    """Test API key bằng cách gọi Groq API"""
    print("🧪 Đang test API key...")
    
    try:
        from langchain_groq import ChatGroq
        
        # Test với một câu hỏi đơn giản
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.1,
            groq_api_key=api_key
        )
        
        response = llm.invoke("Hello, this is a test. Please respond with 'API key working!'")
        
        if response and response.content:
            print("✅ API key hoạt động tốt!")
            print(f"📝 Response: {response.content}")
            return True
        else:
            print("❌ API key không hoạt động!")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi khi test API key: {str(e)}")
        return False

def install_dependencies():
    """Cài đặt dependencies nếu cần"""
    print("📦 Kiểm tra dependencies...")
    
    try:
        import langchain_groq
        print("✅ langchain-groq đã được cài đặt!")
    except ImportError:
        print("📥 Đang cài đặt langchain-groq...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain-groq"])
        print("✅ Đã cài đặt langchain-groq!")

def restart_streamlit():
    """Hướng dẫn restart Streamlit"""
    print("\n🔄 Để áp dụng API key mới:")
    print("1. Dừng ứng dụng Streamlit hiện tại (Ctrl+C)")
    print("2. Chạy lại: python3 -m streamlit run app.py --server.port 8501")
    print("3. Test tạo test cases mới để xem API key hoạt động")

def main():
    print_banner()
    
    # Kiểm tra file .env hiện tại
    if check_env_file():
        choice = input("File .env đã có API key. Bạn có muốn cập nhật không? (y/n): ").lower()
        if choice != 'y':
            print("👋 Tạm biệt!")
            return
    
    # Cài đặt dependencies
    install_dependencies()
    
    # Mở Groq Console
    open_groq_console()
    
    # Lấy API key từ người dùng
    api_key = get_api_key_from_user()
    
    # Test API key
    if test_api_key(api_key):
        # Lưu API key
        save_api_key(api_key)
        
        print("\n🎉 Thiết lập thành công!")
        print("✅ API key đã được lưu và test thành công")
        print("✅ Bây giờ bạn có thể tạo test cases bằng AI!")
        
        restart_streamlit()
    else:
        print("\n❌ Thiết lập thất bại!")
        print("💡 Vui lòng kiểm tra lại API key và thử lại")

if __name__ == "__main__":
    main()
