#!/usr/bin/env python3
# update_api_key.py - Script để cập nhật API key dễ dàng

import os
import sys

def update_api_key():
    """Cập nhật API key trong file .env"""
    print("🔑 CẬP NHẬT GROQ API KEY")
    print("=" * 30)
    
    # Đọc file .env hiện tại
    env_path = ".env"
    if not os.path.exists(env_path):
        print("❌ File .env không tồn tại!")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Tìm và thay thế API key
    if "GROQ_API_KEY=" in content:
        print("📝 Nhập API key mới (bắt đầu bằng 'gsk_'):")
        print("💡 Ví dụ: gsk_1234567890abcdef1234567890abcdef12345678")
        
        # Trong môi trường này, tôi sẽ tạo một template
        new_api_key = "gsk_your_actual_api_key_here"
        
        # Thay thế trong content
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('GROQ_API_KEY='):
                lines[i] = f'GROQ_API_KEY={new_api_key}'
                break
        
        new_content = '\n'.join(lines)
        
        with open(env_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Đã cập nhật file .env!")
        print("📝 Vui lòng thay thế 'gsk_your_actual_api_key_here' bằng API key thật của bạn")
        return True
    else:
        print("❌ Không tìm thấy GROQ_API_KEY trong file .env!")
        return False

def test_api_key():
    """Test API key hiện tại"""
    print("\n🧪 TEST API KEY")
    print("=" * 20)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key or api_key == 'gsk_your_actual_api_key_here':
            print("❌ API key chưa được thiết lập!")
            print("💡 Vui lòng cập nhật API key thật trong file .env")
            return False
        
        from langchain_groq import ChatGroq
        
        print("🔄 Đang test API key...")
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
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_api_key()
        elif sys.argv[1] == "update":
            update_api_key()
        else:
            print("❌ Lệnh không hợp lệ!")
            print("💡 Sử dụng: python3 update_api_key.py [test|update]")
    else:
        print("🔑 GROQ API KEY HELPER")
        print("=" * 25)
        print("📋 Các lệnh có sẵn:")
        print("  python3 update_api_key.py test   - Test API key hiện tại")
        print("  python3 update_api_key.py update - Cập nhật API key")
        print()
        print("🌐 Để lấy API key:")
        print("  1. Truy cập: https://console.groq.com/")
        print("  2. Đăng ký/Đăng nhập tài khoản")
        print("  3. Tạo API key mới")
        print("  4. Copy API key (bắt đầu bằng 'gsk_')")
        print("  5. Cập nhật vào file .env")

if __name__ == "__main__":
    main()
