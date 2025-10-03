#!/usr/bin/env python3
# auto_setup_groq.py - Script tự động mở Groq Console và hướng dẫn

import os
import webbrowser
import subprocess
import sys

def print_banner():
    print("=" * 60)
    print("🔑 GROQ API KEY SETUP - AI Test Case Generator")
    print("=" * 60)
    print()

def open_groq_console():
    """Mở Groq Console trong trình duyệt"""
    print("🌐 Đang mở Groq Console...")
    webbrowser.open("https://console.groq.com/")
    print("✅ Đã mở Groq Console trong trình duyệt!")
    print()

def print_instructions():
    """In hướng dẫn chi tiết"""
    print("📋 HƯỚNG DẪN LẤY API KEY:")
    print("=" * 40)
    print("1. 🌐 Truy cập: https://console.groq.com/")
    print("2. 👤 Đăng ký/Đăng nhập tài khoản (miễn phí)")
    print("3. 🔑 Nhấn 'API Keys' hoặc 'Keys' trong menu")
    print("4. ➕ Nhấn 'Create API Key' hoặc '+ New Key'")
    print("5. 📝 Đặt tên cho key (ví dụ: 'AI Test Case Generator')")
    print("6. 📋 Copy API key (bắt đầu bằng 'gsk_')")
    print("7. 💾 Lưu API key vào file .env")
    print()
    print("🔍 API KEY CÓ DẠNG:")
    print("   gsk_1234567890abcdef1234567890abcdef12345678")
    print()

def create_env_template():
    """Tạo template file .env"""
    env_content = """# Groq API Key - Get your API key from https://console.groq.com/
GROQ_API_KEY=gsk_your_actual_api_key_here

# Optional: Jira Configuration (if using Jira integration)
# JIRA_SERVER=https://yourcompany.atlassian.net
# JIRA_USERNAME=your_email@company.com
# JIRA_PASSWORD=your_password_or_app_password
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Đã tạo file .env template!")

def install_dependencies():
    """Cài đặt dependencies nếu cần"""
    print("📦 Kiểm tra dependencies...")
    
    try:
        import langchain_groq
        print("✅ langchain-groq đã được cài đặt!")
        return True
    except ImportError:
        print("📥 Đang cài đặt langchain-groq...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain-groq"])
            print("✅ Đã cài đặt langchain-groq!")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi cài đặt: {e}")
            return False

def test_current_api_key():
    """Test API key hiện tại"""
    print("🧪 Kiểm tra API key hiện tại...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key or api_key == 'gsk_your_actual_api_key_here':
            print("❌ API key chưa được thiết lập!")
            return False
        
        from langchain_groq import ChatGroq
        
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

def main():
    print_banner()
    
    # Cài đặt dependencies
    if not install_dependencies():
        print("❌ Không thể cài đặt dependencies!")
        return
    
    # Kiểm tra API key hiện tại
    if test_current_api_key():
        print("\n🎉 API key đã hoạt động!")
        print("✅ Bạn có thể sử dụng ứng dụng ngay!")
        return
    
    # Mở Groq Console
    open_groq_console()
    
    # In hướng dẫn
    print_instructions()
    
    # Tạo file .env template
    create_env_template()
    
    print("📝 BƯỚC TIẾP THEO:")
    print("=" * 30)
    print("1. Lấy API key từ Groq Console (đã mở)")
    print("2. Mở file .env trong editor")
    print("3. Thay thế 'gsk_your_actual_api_key_here' bằng API key thật")
    print("4. Lưu file .env")
    print("5. Restart ứng dụng Streamlit")
    print()
    print("💡 Ví dụ:")
    print("   GROQ_API_KEY=gsk_1234567890abcdef1234567890abcdef12345678")
    print()
    print("🚀 Sau khi cập nhật API key, chạy lại script này để test!")

if __name__ == "__main__":
    main()
