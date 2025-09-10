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
        
        # Initialize Groq LLM for spec analysis
        analysis_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,  # Lower temperature for more focused analysis
            max_tokens=2000,
            timeout=None,
            max_retries=2,
        )
        
        # Create a comprehensive prompt for spec analysis
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
        
        # Format the final user story
        formatted_story = f"""
# 📋 AI-Generated User Story from Specification

{ai_analysis}

---

**📄 Original Specification Summary:**
{spec_text[:300]}{'...' if len(spec_text) > 300 else ''}

**💡 Note:** This user story was automatically generated from your specification document. Please review and modify as needed before generating test cases.
        """
        
        return formatted_story
        
    except Exception as e:
        st.error(f"Error analyzing spec with AI: {str(e)}")
        return f"""
# 📋 Specification Analysis (Fallback)

**⚠️ AI Analysis Error:** {str(e)}

**📄 Specification Content:**
{spec_text[:500]}{'...' if len(spec_text) > 500 else ''}

**💡 Manual Review Required:** Please review the specification content above and manually create a user story for test case generation.
        """

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
