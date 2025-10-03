#!/usr/bin/env python3
# start_app.py - Script khởi động ứng dụng với kiểm tra API key

import os
import sys
import subprocess
import time

def check_api_key():
    """Kiểm tra API key"""
    print("🔍 Kiểm tra API key...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key or api_key == 'gsk_your_actual_api_key_here':
            print("❌ API key chưa được thiết lập!")
            print("💡 Chạy: python3 auto_setup_groq.py để thiết lập")
            return False
        
        print("✅ API key đã được thiết lập!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra API key: {e}")
        return False

def start_streamlit():
    """Khởi động Streamlit"""
    print("🚀 Khởi động ứng dụng...")
    
    try:
        # Chạy Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py", 
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\n👋 Đã dừng ứng dụng!")
    except Exception as e:
        print(f"❌ Lỗi khi khởi động: {e}")

def main():
    print("=" * 50)
    print("🧪 AI TEST CASE GENERATOR")
    print("=" * 50)
    print()
    
    # Kiểm tra API key
    if not check_api_key():
        print("\n📋 Để thiết lập API key:")
        print("1. Chạy: python3 auto_setup_groq.py")
        print("2. Lấy API key từ Groq Console")
        print("3. Cập nhật file .env")
        print("4. Chạy lại script này")
        return
    
    print("\n✅ Sẵn sàng khởi động!")
    print("🌐 Ứng dụng sẽ chạy tại: http://localhost:8501")
    print("⏹️  Nhấn Ctrl+C để dừng")
    print()
    
    # Đợi 2 giây
    time.sleep(2)
    
    # Khởi động Streamlit
    start_streamlit()

if __name__ == "__main__":
    main()
