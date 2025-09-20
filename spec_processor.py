# spec_processor.py - File spec processing and AI analysis
import streamlit as st
import pandas as pd
import pypdf
from docx import Document
import io
import tempfile
import os
from typing import Optional, Dict, Any
from tester_agent import generate_test_cases

def extract_text_from_file(file_content: bytes, file_type: str, analysis_instructions: str = "") -> str:
    """
    Extract text content from uploaded file based on file type
    """
    try:
        if file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            # Excel file
            excel_file = pd.ExcelFile(io.BytesIO(file_content))
            text_content = ""
            
            # Check if user specified specific sheets
            if analysis_instructions and any(keyword in analysis_instructions.lower() for keyword in ['sheet', 'tab', 'worksheet']):
                # Try to extract sheet names/numbers from instructions
                import re
                sheet_instructions = analysis_instructions.lower()
                
                # Look for sheet numbers (Sheet2, Sheet3, etc.)
                sheet_numbers = re.findall(r'sheet\s*(\d+)', sheet_instructions)
                # Look for sheet names
                sheet_names = re.findall(r'sheet\s*["\']([^"\']+)["\']', sheet_instructions)
                
                selected_sheets = []
                if sheet_numbers:
                    for num in sheet_numbers:
                        try:
                            sheet_name = excel_file.sheet_names[int(num) - 1]
                            selected_sheets.append(sheet_name)
                        except IndexError:
                            continue
                
                if sheet_names:
                    for name in sheet_names:
                        if name in excel_file.sheet_names:
                            selected_sheets.append(name)
                
                # If no specific sheets found, use all sheets
                if not selected_sheets:
                    selected_sheets = excel_file.sheet_names
            else:
                # Use all sheets if no specific instructions
                selected_sheets = excel_file.sheet_names
            
            # Process selected sheets
            for sheet_name in selected_sheets:
                try:
                    df = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_name)
                    text_content += f"\n=== SHEET: {sheet_name} ===\n"
                    for column in df.columns:
                        text_content += f"\n{column}:\n"
                        text_content += df[column].astype(str).str.cat(sep="\n")
                except Exception as e:
                    text_content += f"\n=== ERROR reading sheet {sheet_name}: {str(e)} ===\n"
            
            return text_content
            
        elif file_type == "application/pdf":
            # PDF file
            text_content = ""
            try:
                # Try with pypdf first (newer)
                pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
                total_pages = len(pdf_reader.pages)
                
                # Check if user specified specific pages
                selected_pages = list(range(total_pages))
                if analysis_instructions and any(keyword in analysis_instructions.lower() for keyword in ['page', 'pages']):
                    import re
                    page_instructions = analysis_instructions.lower()
                    
                    # Look for page ranges (pages 3-4, pages 7-8, etc.)
                    page_ranges = re.findall(r'pages?\s*(\d+)\s*-\s*(\d+)', page_instructions)
                    # Look for individual pages (page 3, page 4, etc.)
                    individual_pages = re.findall(r'page\s*(\d+)', page_instructions)
                    
                    selected_pages = []
                    if page_ranges:
                        for start, end in page_ranges:
                            start_page = int(start) - 1  # Convert to 0-based index
                            end_page = int(end) - 1
                            selected_pages.extend(range(start_page, min(end_page + 1, total_pages)))
                    
                    if individual_pages:
                        for page_num in individual_pages:
                            page_idx = int(page_num) - 1  # Convert to 0-based index
                            if 0 <= page_idx < total_pages:
                                selected_pages.append(page_idx)
                    
                    # Remove duplicates and sort
                    selected_pages = sorted(list(set(selected_pages)))
                
                # Extract text from selected pages
                for page_num in selected_pages:
                    if 0 <= page_num < total_pages:
                        page_text = pdf_reader.pages[page_num].extract_text()
                        text_content += f"\n=== PAGE {page_num + 1} ===\n"
                        text_content += page_text + "\n"
                        
            except Exception:
                # Fallback to pypdf (same as main)
                pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
                total_pages = len(pdf_reader.pages)
                
                # Apply same page selection logic for pypdf
                selected_pages = list(range(total_pages))
                if analysis_instructions and any(keyword in analysis_instructions.lower() for keyword in ['page', 'pages']):
                    import re
                    page_instructions = analysis_instructions.lower()
                    
                    page_ranges = re.findall(r'pages?\s*(\d+)\s*-\s*(\d+)', page_instructions)
                    individual_pages = re.findall(r'page\s*(\d+)', page_instructions)
                    
                    selected_pages = []
                    if page_ranges:
                        for start, end in page_ranges:
                            start_page = int(start) - 1
                            end_page = int(end) - 1
                            selected_pages.extend(range(start_page, min(end_page + 1, total_pages)))
                    
                    if individual_pages:
                        for page_num in individual_pages:
                            page_idx = int(page_num) - 1
                            if 0 <= page_idx < total_pages:
                                selected_pages.append(page_idx)
                    
                    selected_pages = sorted(list(set(selected_pages)))
                
                for page_num in selected_pages:
                    if 0 <= page_num < total_pages:
                        page_text = pdf_reader.pages[page_num].extract_text()
                        text_content += f"\n=== PAGE {page_num + 1} ===\n"
                        text_content += page_text + "\n"
                        
            return text_content
            
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Word document
            doc = Document(io.BytesIO(file_content))
            text_content = ""
            
            # Check if user specified specific sections
            if analysis_instructions and any(keyword in analysis_instructions.lower() for keyword in ['section', 'chapter', 'part']):
                import re
                section_instructions = analysis_instructions.lower()
                
                # Look for section numbers (section 2.1, section 2.1-2.5, etc.)
                section_patterns = re.findall(r'section\s*(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?', section_instructions)
                
                # Process all paragraphs and filter by section
                current_section = None
                for paragraph in doc.paragraphs:
                    para_text = paragraph.text.strip()
                    
                    # Check if this paragraph is a section header
                    section_match = re.match(r'^(\d+(?:\.\d+)*)', para_text)
                    if section_match:
                        current_section = section_match.group(1)
                    
                    # Include paragraph if it matches section criteria
                    include_paragraph = True
                    if section_patterns:
                        include_paragraph = False
                        for start_section, end_section in section_patterns:
                            if current_section:
                                if end_section:
                                    # Range check
                                    if start_section <= current_section <= end_section:
                                        include_paragraph = True
                                        break
                                else:
                                    # Exact match
                                    if current_section.startswith(start_section):
                                        include_paragraph = True
                                        break
                    
                    if include_paragraph:
                        text_content += f"\n=== SECTION {current_section or 'UNKNOWN'} ===\n" if current_section else ""
                        text_content += para_text + "\n"
            else:
                # Process all paragraphs if no specific instructions
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
            
            return text_content
            
        else:
            return "Unsupported file type"
            
    except Exception as e:
        st.error(f"Error extracting text from file: {str(e)}")
        return ""

def analyze_spec_with_ai(spec_text: str, project_settings: Dict[str, Any], analysis_instructions: str = "") -> str:
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
        instructions_note = ""
        if analysis_instructions:
            instructions_note = f"""
        
        **SPECIFIC ANALYSIS INSTRUCTIONS:**
        The user has provided specific instructions for analyzing this document:
        "{analysis_instructions}"
        
        Please follow these instructions carefully when analyzing the specification. Focus on the parts of the document that the user specifically mentioned.
        """
        
        analysis_prompt = f"""
        You are an expert business analyst and software tester. Analyze the following specification document and extract key functionality requirements to create a comprehensive user story.

        Project Context:
        - Testing Types: {', '.join(project_settings.get('testing_types', []))}
        - Languages: {', '.join(project_settings.get('languages', []))}
        - Writing Style: {project_settings.get('writing_style', 'Professional and clear')}
        {instructions_note}

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

def process_uploaded_spec(file_content: bytes, file_type: str, project_settings: Dict[str, Any], analysis_instructions: str = "") -> str:
    """
    Main function to process uploaded spec file and return user story
    """
    # Extract text from file with analysis instructions
    spec_text = extract_text_from_file(file_content, file_type, analysis_instructions)
    
    if not spec_text or spec_text == "Unsupported file type":
        return "Could not extract text from the uploaded file. Please try a different file format."
    
    # Analyze with AI including analysis instructions
    user_story = analyze_spec_with_ai(spec_text, project_settings, analysis_instructions)
    
    return user_story
