# spec_processor.py - File spec processing and AI analysis
import streamlit as st
import pandas as pd
import PyPDF2
import pypdf
from docx import Document
import io
import tempfile
import os
from typing import Optional, Dict, Any
from tester_agent import generate_test_cases

def extract_text_from_file(file_content: bytes, file_type: str) -> str:
    """
    Extract text content from uploaded file based on file type
    """
    try:
        if file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            # Excel file
            df = pd.read_excel(io.BytesIO(file_content))
            # Convert all columns to string and join
            text_content = ""
            for column in df.columns:
                text_content += f"\n{column}:\n"
                text_content += df[column].astype(str).str.cat(sep="\n")
            return text_content
            
        elif file_type == "application/pdf":
            # PDF file
            text_content = ""
            try:
                # Try with pypdf first (newer)
                pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except Exception:
                # Fallback to PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            return text_content
            
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Word document
            doc = Document(io.BytesIO(file_content))
            text_content = ""
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            return text_content
            
        else:
            return "Unsupported file type"
            
    except Exception as e:
        st.error(f"Error extracting text from file: {str(e)}")
        return ""

def analyze_spec_with_ai(spec_text: str, project_settings: Dict[str, Any]) -> str:
    """
    Use AI to analyze spec text and generate user story
    """
    try:
        from langchain_groq import ChatGroq
        from dotenv import load_dotenv
        import os
        
        # Load environment variables
        load_dotenv()
        
        # Check if API key is available
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise Exception("GROQ_API_KEY not found in environment variables")
        
        # Initialize Groq LLM for spec analysis
        analysis_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,  # Lower temperature for more focused analysis
            max_tokens=2000,
            timeout=None,
            max_retries=2,
        )
        
        # Check if Vietnamese is selected
        languages = project_settings.get('languages', [])
        is_vietnamese = "Vietnamese" in languages or "Tiếng Việt" in languages
        
        # Create language-specific prompt
        if is_vietnamese:
            analysis_prompt = f"""
Bạn là một chuyên gia phân tích nghiệp vụ và kiểm thử phần mềm. Hãy phân tích tài liệu đặc tả sau và trích xuất các yêu cầu chức năng chính để tạo ra một câu chuyện người dùng toàn diện.

Bối cảnh Dự án:
- Loại Kiểm thử: {', '.join(project_settings.get('testing_types', []))}
- Ngôn ngữ: {', '.join(project_settings.get('languages', []))}
- Phong cách Viết: {project_settings.get('writing_style', 'Chuyên nghiệp và rõ ràng')}

Tài liệu Đặc tả:
{spec_text}

Hãy phân tích đặc tả này và tạo ra một câu chuyện người dùng chi tiết bao gồm:

1. **Personas Người dùng**: Xác định các loại người dùng chính và vai trò của họ
2. **Tính năng Cốt lõi**: Trích xuất chức năng và tính năng chính
3. **Quy trình Người dùng**: Mô tả các hành trình và quy trình chính của người dùng
4. **Tiêu chí Chấp nhận**: Liệt kê các yêu cầu chính và tiêu chí thành công
5. **Quy tắc Nghiệp vụ**: Xác định các ràng buộc, xác thực hoặc logic nghiệp vụ
6. **Điểm Tích hợp**: Ghi chú các hệ thống bên ngoài hoặc phụ thuộc

Định dạng phản hồi của bạn như một câu chuyện người dùng toàn diện có thể được sử dụng để tạo test case. Cấu trúc rõ ràng với các phần cho từng khía cạnh trên.

Tập trung vào việc tạo ra các yêu cầu có thể thực hiện, có thể kiểm thử bao gồm cả các kịch bản tích cực và tiêu cực.

QUAN TRỌNG: Viết toàn bộ phản hồi bằng tiếng Việt!
            """
        else:
            analysis_prompt = f"""
You are an expert business analyst and software tester. Analyze the following specification document and extract key functionality requirements to create a comprehensive user story.

Project Context:
- Testing Types: {', '.join(project_settings.get('testing_types', []))}
- Languages: {', '.join(project_settings.get('languages', []))}
- Writing Style: {project_settings.get('writing_style', 'Professional and clear')}

Specification Document:
{spec_text}

Please analyze this specification and create a detailed user story that includes:

1. **User Personas**: Identify the main user types and their roles
2. **Core Features**: Extract the primary functionality and features
3. **User Workflows**: Describe the main user journeys and processes
4. **Acceptance Criteria**: List the key requirements and success criteria
5. **Business Rules**: Identify any constraints, validations, or business logic
6. **Integration Points**: Note any external systems or dependencies

Format your response as a comprehensive user story that can be used to generate test cases. Structure it clearly with sections for each aspect above.

Focus on creating actionable, testable requirements that cover both positive and negative scenarios.
            """
        
        # Get AI analysis
        response = analysis_llm.invoke(analysis_prompt)
        ai_analysis = response.content
        
        # Format the final user story based on language
        if is_vietnamese:
            formatted_story = f"""# Câu Chuyện Người Dùng Được Tạo Từ Đặc Tả (AI)

{ai_analysis}

---

**Tóm Tắt Đặc Tả Gốc:**
{spec_text[:300]}{'...' if len(spec_text) > 300 else ''}

**Lưu Ý:** Câu chuyện người dùng này được tạo tự động từ tài liệu đặc tả của bạn. Vui lòng xem xét và chỉnh sửa nếu cần trước khi tạo test case."""
        else:
            formatted_story = f"""# AI-Generated User Story from Specification

{ai_analysis}

---

**Original Specification Summary:**
{spec_text[:300]}{'...' if len(spec_text) > 300 else ''}

**Note:** This user story was automatically generated from your specification document. Please review and modify as needed before generating test cases."""
        
        return formatted_story
        
    except Exception as e:
        st.error(f"Error analyzing spec with AI: {str(e)}")
        
        # Create fallback content based on language
        languages = project_settings.get('languages', [])
        is_vietnamese = "Vietnamese" in languages or "Tiếng Việt" in languages
        
        if is_vietnamese:
            return f"""# Phân Tích Đặc Tả (Dự phòng)

**Lỗi Phân Tích AI:** {str(e)}

**Nội dung Đặc tả:**
{spec_text[:500]}{'...' if len(spec_text) > 500 else ''}

**Cần Xem Xét Thủ Công:** Vui lòng xem xét nội dung đặc tả ở trên và tạo thủ công một câu chuyện người dùng để tạo test case."""
        else:
            return f"""# Specification Analysis (Fallback)

**AI Analysis Error:** {str(e)}

**Specification Content:**
{spec_text[:500]}{'...' if len(spec_text) > 500 else ''}

**Manual Review Required:** Please review the specification content above and manually create a user story for test case generation."""

def process_uploaded_spec(file_content: bytes, file_type: str, project_settings: Dict[str, Any]) -> str:
    """
    Main function to process uploaded spec file and return user story
    """
    # Extract text from file
    spec_text = extract_text_from_file(file_content, file_type)
    
    if not spec_text or spec_text == "Unsupported file type":
        return "Could not extract text from the uploaded file. Please try a different file format."
    
    # Analyze with AI
    user_story = analyze_spec_with_ai(spec_text, project_settings)
    
    return user_story
