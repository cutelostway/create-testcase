# tester_agent.py - LangGraph/LLM logic
from typing import TypedDict, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import Any, Dict
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
import json
import re

# System prompt for the test case generator
GENERATOR_PROMPT = """
You are an expert software tester. Analyze the given user story in depth and generate a comprehensive set of test cases,
including functional, edge, and boundary cases, to ensure complete test coverage of the functionality.

🚨🚨🚨 CRITICAL VIETNAMESE LANGUAGE REQUIREMENT 🚨🚨🚨
MANDATORY: If Vietnamese is selected in project settings, write ALL test case content in Vietnamese (Tiếng Việt).
- test_title: Use Vietnamese field names (e.g., "Trường Email", "Trường Mật khẩu", "Nút Đăng nhập")
- description: Write in Vietnamese
- test_steps: Write COMPLETE test flow step-by-step instructions in Vietnamese (include all steps from start to finish)
- expected_result: Write expected outcomes in Vietnamese
- comments: Write additional notes in Vietnamese
- preconditions: Write setup requirements in Vietnamese
- test_data: Provide ACTUAL test data examples in Vietnamese (e.g., 'test@example.com', 'matkhau123', 'Nguyễn Văn A')

VIETNAMESE EXAMPLES FOR ALL FIELDS:
- test_title: "Trường Email", "Trường Mật khẩu", "Nút Đăng nhập", "Thông báo Lỗi"
- description: "Kiểm tra định dạng email hợp lệ", "Kiểm tra xác thực mật khẩu"
- test_steps: "1. Mở trang đăng nhập\n2. Nhập email hợp lệ\n3. Nhập mật khẩu\n4. Nhấp nút đăng nhập\n5. Xác minh đăng nhập thành công"
- expected_result: "Hệ thống hiển thị trang chủ", "Hệ thống hiển thị thông báo lỗi"
- test_data: "test@example.com, matkhau123", "nguyenvana@test.com, password456"
- preconditions: "Người dùng đã mở trang đăng nhập", "Hệ thống đang hoạt động bình thường"
- comments: "Kiểm tra trường hợp thành công", "Kiểm tra trường hợp thất bại"

This is NON-NEGOTIABLE - every single word must be in Vietnamese when Vietnamese is selected!
🚨🚨🚨 END VIETNAMESE REQUIREMENT 🚨🚨🚨

CRITICAL REQUIREMENTS FOR TEST TITLES AND DESCRIPTIONS:
- Group test cases by UI fields/components
- test_title: ONLY the field/component name, NO additional text (e.g., "Trường Email", "Trường Mật khẩu", "Nút Đăng nhập", "Thông báo Lỗi")
- description: Detailed summary of what is being tested for that field
- STRICT FORMAT: test_title must be exactly the field name only
- test_steps: Include ALL steps needed to complete the test, not just field-specific steps
- ERROR MESSAGES: Create separate test cases for error messages of each field/component
- Examples for Vietnamese: 
  * test_title: "Trường Email", description: "Kiểm tra định dạng email hợp lệ"
  * test_title: "Lỗi Trường Email", description: "Kiểm tra thông báo lỗi xác thực email"
  * test_title: "Trường Mật khẩu", description: "Kiểm tra xác thực mật khẩu"
  * test_title: "Lỗi Trường Mật khẩu", description: "Kiểm tra thông báo lỗi xác thực mật khẩu"

Generate your response as a JSON object with the following structure:
{
  "test_cases": [
    {
      "test_case_id": 1,
      "test_title": "[Tên Trường/Thành phần]",
      "description": "Mô tả chi tiết trường hợp kiểm thử",
      "preconditions": "Điều kiện tiên quyết",
      "test_steps": "1. Mở trang đăng nhập\n2. Nhập email hợp lệ\n3. Nhập mật khẩu\n4. Nhấp nút đăng nhập\n5. Xác minh đăng nhập thành công",
      "test_data": "test@example.com, matkhau123",
      "expected_result": "Kết quả mong đợi",
      "comments": "Ghi chú bổ sung"
    }
  ]
}
"""

# Pydantic schema for a single test case
class TestCase(BaseModel):
    test_case_id: int = Field(..., description="Unique identifier for the test case")
    test_title: str = Field(..., description="Title of the test case")
    description: str = Field(..., description="Detailed description of what the test case covers")
    preconditions: str = Field(..., description="Any setup required before execution")
    test_steps: str = Field(..., description="Step-by-step execution guide")
    test_data: str = Field(..., description="Input values required for the test")
    expected_result: str = Field(..., description="The anticipated outcome")
    comments: str = Field(..., description="Additional notes or observations")

# Output schema containing list of test cases
class OutputSchema(BaseModel):
    test_cases: List[TestCase] = Field(..., description="List of generated test cases")

# LangGraph State definition
class State(TypedDict):
    test_cases: List[TestCase]
    user_story: str
    num_cases: int
    project_settings: Dict[str, Any]

# Load environment variables
load_dotenv()

# Initialize the LLM (slightly higher temperature for diversity)
def get_llm():
    """Get LLM instance with proper error handling"""
    try:
        return ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.4,
            max_tokens=4000,
            timeout=None,
            max_retries=2,
        )
    except Exception as e:
        print(f"Warning: Could not initialize Groq LLM: {e}")
        print("Please set GROQ_API_KEY environment variable")
        return None

# Try preparing a structured LLM for OutputSchema when available
structured_llm = None
try:
    # Newer langchain-groq supports structured output via Pydantic
    llm_instance = get_llm()
    if llm_instance:
        structured_llm = llm_instance.with_structured_output(OutputSchema)
except Exception:
    structured_llm = None

def _robust_json_extract(text: str) -> Dict[str, Any]:
    """Attempt to robustly extract a JSON object from a text blob."""
    # Handle fenced code blocks first
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.rfind("```")
        if end != -1:
            text = text[start:end].strip()

    # Clean up common issues
    text = text.strip()
    
    # Try to find JSON object boundaries
    if "{" in text and "}" in text:
        first = text.find("{")
        last = text.rfind("}")
        candidate = text[first:last + 1]
        
        # Try parsing with different error handling
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            # Fix missing commas
            candidate = re.sub(r'"\s*\n\s*"', '",\n"', candidate)
            # Fix trailing commas
            candidate = re.sub(r',\s*}', '}', candidate)
            candidate = re.sub(r',\s*]', ']', candidate)
            
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # If still fails, try to extract just the test_cases array
                if '"test_cases"' in candidate:
                    start = candidate.find('"test_cases"')
                    start = candidate.find('[', start)
                    end = candidate.rfind(']') + 1
                    if start != -1 and end != -1:
                        test_cases_json = candidate[start:end]
                        try:
                            test_cases = json.loads(test_cases_json)
                            return {"test_cases": test_cases}
                        except json.JSONDecodeError:
                            pass

    # Final try: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"test_cases": []}


def _build_context_prompt(project_settings: Dict[str, Any]) -> str:
    if not project_settings:
        return ""
    try:
        languages = ", ".join(project_settings.get("languages", []) or [])
        testing_types = ", ".join(project_settings.get("testing_types", []) or [])
        writing_style = project_settings.get("writing_style", "") or ""
        detail_level = project_settings.get("detail_level", "") or ""
        steps_detail = project_settings.get("steps_detail", "") or ""
        exclusion_rules = ", ".join(project_settings.get("exclusion_rules", []) or [])
        priorities = project_settings.get("priority_levels", {}) or {}
        priorities_str = ", ".join([f"{k}:{v}" for k, v in priorities.items() if v])
        return (
            "Context for diversification:"\
            f"\n- Languages: {languages}"\
            f"\n- Testing Types: {testing_types}"\
            f"\n- Writing Style: {writing_style}"\
            f"\n- Detail Level: {detail_level}"\
            f"\n- Steps Detail: {steps_detail}"\
            f"\n- Exclusion Rules: {exclusion_rules}"\
            f"\n- Priority Levels: {priorities_str}"
        )
    except Exception:
        return ""


def test_cases_generator(state: State):
    """Generate test cases based on user story."""
    target_num = max(1, int(state.get('num_cases', 10)))
    context_note = _build_context_prompt(state.get('project_settings', {}))
    # Extract language setting from project settings
    project_settings = state.get('project_settings', {})
    languages = project_settings.get("languages", [])
    is_vietnamese = "Vietnamese" in languages or "Tiếng Việt" in languages
    
    # Create language-specific instruction
    language_instruction = ""
    if is_vietnamese:
        language_instruction = """
🚨🚨🚨 CRITICAL VIETNAMESE LANGUAGE REQUIREMENT 🚨🚨🚨
MANDATORY: Generate ALL test case content in Vietnamese (Tiếng Việt).
- test_title: Use Vietnamese field names (e.g., "Trường Email", "Trường Mật khẩu", "Nút Đăng nhập")
- description: Write in Vietnamese
- test_steps: Write COMPLETE test flow step-by-step instructions in Vietnamese (include all steps from start to finish)
- expected_result: Write expected outcomes in Vietnamese
- comments: Write additional notes in Vietnamese
- preconditions: Write setup requirements in Vietnamese
- test_data: Write input data descriptions in Vietnamese

EXAMPLES OF VIETNAMESE FIELD NAMES:
- "Trường Email" (Email Field)
- "Trường Mật khẩu" (Password Field) 
- "Nút Đăng nhập" (Login Button)
- "Thông báo Lỗi" (Error Messages)
- "Lỗi Trường Email" (Email Field Error)

This is NON-NEGOTIABLE - every single word must be in Vietnamese!
🚨🚨🚨 END VIETNAMESE REQUIREMENT 🚨🚨🚨
"""
    else:
        language_instruction = "Generate test cases in the specified language from project settings."

    # Create a super explicit Vietnamese instruction if Vietnamese is selected
    vietnamese_header = ""
    if is_vietnamese:
        vietnamese_header = """
🚨🚨🚨 VIETNAMESE LANGUAGE MANDATORY 🚨🚨🚨
YOU MUST WRITE EVERYTHING IN VIETNAMESE (TIẾNG VIỆT)!
- test_title: Vietnamese field names (Trường Email, Trường Mật khẩu, Nút Đăng nhập)
- description: Vietnamese descriptions (Kiểm tra định dạng email hợp lệ)
- test_steps: Vietnamese COMPLETE test flow instructions (Mở trang đăng nhập, Nhập email hợp lệ, Nhập mật khẩu, Nhấp nút đăng nhập, Xác minh đăng nhập thành công)
- expected_result: Vietnamese expected results (Hệ thống hiển thị trang chủ)
- test_data: Vietnamese COMPLETE test data for entire flow (test@example.com, matkhau123)
- preconditions: Vietnamese preconditions (Người dùng đã mở trang đăng nhập)
- comments: Vietnamese comments (Kiểm tra trường hợp thành công)

VIETNAMESE FIELD NAMES EXAMPLES:
- "Trường Email" (Email Field)
- "Trường Mật khẩu" (Password Field)
- "Nút Đăng nhập" (Login Button)
- "Nút Gửi" (Submit Button)
- "Nút Hủy" (Cancel Button)
- "Thông báo Lỗi" (Error Messages)
- "Lỗi Trường Email" (Email Field Error)

VIETNAMESE TEST STEPS EXAMPLES:
"1. Mở trang đăng nhập
2. Nhập email hợp lệ vào trường email
3. Nhập mật khẩu hợp lệ vào trường mật khẩu
4. Nhấp nút đăng nhập
5. Xác minh đăng nhập thành công"

🚨🚨🚨 END VIETNAMESE MANDATE 🚨🚨🚨

"""

    prompt = (
        f"{vietnamese_header}"
        f"{language_instruction}\n\n"
        f"{GENERATOR_PROMPT}\n\n"
        f"CRITICAL: You must create test cases that DIRECTLY MATCH and test the functionality described in the user story below.\n\n"
        f"USER STORY TO TEST:\n{state['user_story']}\n\n"
        f"ANALYSIS REQUIREMENTS:\n"
        f"1. Read the user story carefully and identify the main functionality being described\n"
        f"2. Extract the specific user actions, inputs, and expected outcomes mentioned\n"
        f"3. Identify the UI components, fields, and buttons that will be involved\n"
        f"4. Create test cases that cover the exact scenarios described in the user story\n"
        f"5. Ensure each test case directly relates to the functionality in the user story\n\n"
        f"{context_note}\n\n"
        f"{language_instruction}\n\n"
        f"Generate up to {target_num} test cases that DIRECTLY TEST the functionality described in the user story above. "
        f"Each test case must be relevant to the user story and test specific aspects of the described functionality. "
        f"Include positive scenarios (happy path), negative scenarios (error cases), and edge cases based on the user story. "
        f"ORGANIZE TEST CASES BY UI FIELDS/COMPONENTS: Group test cases by specific fields, buttons, or UI elements mentioned in the user story. "
        f"STRICT FORMAT: test_title must be EXACTLY the field/component name only. "
        f"NO additional text in test_title. description should contain the detailed summary of what is being tested for that field. "
        f"test_steps: Include COMPLETE test flow from start to finish, not just field-specific steps. "
        f"For each test case, provide ALL steps needed to complete the entire test scenario. "
        f"Example: For a login test, include steps like: 1. Open login page, 2. Enter email, 3. Enter password, 4. Click login button, 5. Verify success. "
        f"test_steps should be general steps without specific examples or data values. "
        f"IMPORTANT: test_steps must be a single string with numbered steps separated by newlines (e.g., '1. Step one\\n2. Step two\\n3. Step three'), NOT an array. "
        f"test_data: Must contain ALL test data needed for the complete test scenario (e.g., 'test@example.com, password123' for login test). "
        f"Provide specific data values that can be used for testing the entire flow, not just individual fields. "
        f"DO NOT use generic descriptions like 'Valid email' or 'Valid password' - provide specific data values. "
        f"ERROR MESSAGES: Create separate test cases for error messages of each field/component. "
        f"🚨 FINAL REMINDER: If Vietnamese is selected, EVERY SINGLE WORD in the JSON response must be in Vietnamese! 🚨 "
        f"Always respond ONLY with the JSON object described above."
    )
    
    try:
        # Use text mode with robust JSON extraction for better compatibility
        llm_instance = get_llm()
        if not llm_instance:
            raise Exception("LLM not available. Please set GROQ_API_KEY environment variable.")
        
        response = llm_instance.invoke(prompt)
        response_text = response.content
        
        # AGGRESSIVE VIETNAMESE ENFORCEMENT: If Vietnamese is selected, force translation
        if is_vietnamese:
            # Check if response contains English patterns and force Vietnamese
            english_patterns = [
                "Email Field", "Password Field", "Login Button", "Submit Button",
                "Test valid", "Test invalid", "Enter valid", "Click button",
                "Verify message", "Expected result", "Test data", "Preconditions"
            ]
            
            contains_english = any(pattern in response_text for pattern in english_patterns)
            
            if contains_english:
                print("🚨 DETECTED ENGLISH IN RESPONSE - FORCING VIETNAMESE TRANSLATION 🚨")
                # Force Vietnamese translation by replacing English patterns (only content, not JSON keys)
                vietnamese_replacements = {
                    '"Email Field"': '"Trường Email"',
                    '"Password Field"': '"Trường Mật khẩu"',
                    '"Login Button"': '"Nút Đăng nhập"',
                    '"Submit Button"': '"Nút Gửi"',
                    '"Cancel Button"': '"Nút Hủy"',
                    '"Save Button"': '"Nút Lưu"',
                    '"Delete Button"': '"Nút Xóa"',
                    '"Edit Button"': '"Nút Chỉnh sửa"',
                    '"Search Field"': '"Trường Tìm kiếm"',
                    '"Name Field"': '"Trường Tên"',
                    '"Phone Field"': '"Trường Số điện thoại"',
                    '"Address Field"': '"Trường Địa chỉ"',
                    '"Error Messages"': '"Thông báo Lỗi"',
                    '"Email Field Error"': '"Lỗi Trường Email"',
                    '"Password Field Error"': '"Lỗi Trường Mật khẩu"',
                    '"Name Field Error"': '"Lỗi Trường Tên"',
                    '"Phone Field Error"': '"Lỗi Trường Số điện thoại"',
                    'Test valid': 'Kiểm tra hợp lệ',
                    'Test invalid': 'Kiểm tra không hợp lệ',
                    'Test empty': 'Kiểm tra trống',
                    'Test required': 'Kiểm tra bắt buộc',
                    'Test format': 'Kiểm tra định dạng',
                    'Test length': 'Kiểm tra độ dài',
                    'Test boundary': 'Kiểm tra giới hạn',
                    'Test error': 'Kiểm tra lỗi',
                    'Test success': 'Kiểm tra thành công',
                    'Test failure': 'Kiểm tra thất bại',
                    'Enter valid': 'Nhập hợp lệ',
                    'Enter invalid': 'Nhập không hợp lệ',
                    'Click button': 'Nhấp nút',
                    'Verify message': 'Xác minh thông báo',
                    'Check validation': 'Kiểm tra xác thực',
                    'Expected result': 'Kết quả mong đợi',
                    'Test data': 'Dữ liệu kiểm thử',
                    'Preconditions': 'Điều kiện tiên quyết',
                    'Comments': 'Ghi chú',
                    'Open login page': 'Mở trang đăng nhập',
                    'Enter email': 'Nhập email',
                    'Enter password': 'Nhập mật khẩu',
                    'Click login': 'Nhấp đăng nhập',
                    'Verify success': 'Xác minh thành công',
                    'Verify error': 'Xác minh lỗi',
                    'System displays': 'Hệ thống hiển thị',
                    'Error message': 'Thông báo lỗi',
                    'Success message': 'Thông báo thành công',
                    'Login successful': 'Đăng nhập thành công',
                    'Login failed': 'Đăng nhập thất bại',
                    'Invalid email': 'Email không hợp lệ',
                    'Invalid password': 'Mật khẩu không hợp lệ',
                    'Required field': 'Trường bắt buộc',
                    'Field validation': 'Xác thực trường',
                    'Input validation': 'Xác thực đầu vào',
                    'Form validation': 'Xác thực biểu mẫu'
                }
                
                # Apply replacements
                for eng, viet in vietnamese_replacements.items():
                    response_text = response_text.replace(eng, viet)
                
                print("✅ APPLIED AGGRESSIVE VIETNAMESE TRANSLATION ✅")
        
        parsed_data = _robust_json_extract(response_text)
        
        # Preprocess test cases to ensure proper data types and Vietnamese language
        processed_cases = []
        for case in parsed_data.get("test_cases", []):
            # Convert test_steps from list to properly formatted string
            if isinstance(case.get("test_steps"), list):
                # Format as numbered steps, filtering out empty steps
                steps = case["test_steps"]
                formatted_steps = []
                step_num = 1
                for step in steps:
                    # Remove any existing numbering and clean the step
                    clean_step = str(step).strip()
                    # Remove patterns like "1.", "Bước 1:", etc.
                    clean_step = re.sub(r'^\d+\.\s*', '', clean_step)
                    clean_step = re.sub(r'^Bước\s+\d+[:\-\.]\s*', '', clean_step, flags=re.IGNORECASE)
                    clean_step = re.sub(r'^Step\s+\d+[:\-\.]\s*', '', clean_step, flags=re.IGNORECASE)
                    
                    # Only add non-empty steps
                    if clean_step and len(clean_step) > 3:  # Filter out very short/empty steps
                        formatted_steps.append(f"{step_num}. {clean_step}")
                        step_num += 1
                case["test_steps"] = "\n".join(formatted_steps)
            elif isinstance(case.get("test_steps"), str):
                # If it's already a string, ensure it has proper numbering
                steps_text = case["test_steps"]
                # Split by common delimiters and renumber
                steps = re.split(r'[;\n]|(?<=\d\.)\s+', steps_text)
                steps = [s.strip() for s in steps if s.strip()]
                if steps:
                    formatted_steps = []
                    step_num = 1
                    for step in steps:
                        # Remove existing numbering
                        clean_step = re.sub(r'^\d+\.\s*', '', step)
                        clean_step = re.sub(r'^Bước\s+\d+[:\-\.]\s*', '', clean_step, flags=re.IGNORECASE)
                        clean_step = re.sub(r'^Step\s+\d+[:\-\.]\s*', '', clean_step, flags=re.IGNORECASE)
                        
                        # Only add non-empty steps
                        if clean_step and len(clean_step) > 3:  # Filter out very short/empty steps
                            formatted_steps.append(f"{step_num}. {clean_step}")
                            step_num += 1
                    case["test_steps"] = "\n".join(formatted_steps)
            
            # Ensure all string fields are strings
            for field in ["test_title", "description", "preconditions", "test_data", "expected_result", "comments"]:
                if field in case and not isinstance(case[field], str):
                    case[field] = str(case[field])
            
            # Force Vietnamese language if Vietnamese is selected
            if is_vietnamese:
                # Convert common English field names to Vietnamese
                english_to_vietnamese = {
                    "Email Field": "Trường Email",
                    "Password Field": "Trường Mật khẩu", 
                    "Login Button": "Nút Đăng nhập",
                    "Submit Button": "Nút Gửi",
                    "Cancel Button": "Nút Hủy",
                    "Save Button": "Nút Lưu",
                    "Delete Button": "Nút Xóa",
                    "Edit Button": "Nút Chỉnh sửa",
                    "Search Field": "Trường Tìm kiếm",
                    "Name Field": "Trường Tên",
                    "Phone Field": "Trường Số điện thoại",
                    "Address Field": "Trường Địa chỉ",
                    "Error Messages": "Thông báo Lỗi",
                    "Email Field Error": "Lỗi Trường Email",
                    "Password Field Error": "Lỗi Trường Mật khẩu",
                    "Name Field Error": "Lỗi Trường Tên",
                    "Phone Field Error": "Lỗi Trường Số điện thoại"
                }
                
                # Convert test_title if it's in English
                if case.get("test_title") in english_to_vietnamese:
                    case["test_title"] = english_to_vietnamese[case["test_title"]]
                
                # Convert common English phrases in description and other fields
                english_phrases = {
                    "Test valid": "Kiểm tra hợp lệ",
                    "Test invalid": "Kiểm tra không hợp lệ", 
                    "Test empty": "Kiểm tra trống",
                    "Test required": "Kiểm tra bắt buộc",
                    "Test format": "Kiểm tra định dạng",
                    "Test length": "Kiểm tra độ dài",
                    "Test boundary": "Kiểm tra giới hạn",
                    "Test error": "Kiểm tra lỗi",
                    "Test success": "Kiểm tra thành công",
                    "Test failure": "Kiểm tra thất bại",
                    "Enter valid": "Nhập hợp lệ",
                    "Enter invalid": "Nhập không hợp lệ",
                    "Click button": "Nhấp nút",
                    "Verify message": "Xác minh thông báo",
                    "Check validation": "Kiểm tra xác thực",
                    "Expected result": "Kết quả mong đợi",
                    "Test data": "Dữ liệu kiểm thử",
                    "Preconditions": "Điều kiện tiên quyết",
                    "Comments": "Ghi chú"
                }
                
                # Apply Vietnamese translations to all text fields
                for field in ["description", "preconditions", "expected_result", "comments"]:
                    if field in case and case[field]:
                        text = case[field]
                        for eng, viet in english_phrases.items():
                            text = text.replace(eng, viet)
                        case[field] = text
            
            processed_cases.append(case)
        
        test_cases = [TestCase(**case) for case in processed_cases]
        
        # Ensure we got non-empty list, otherwise trigger fallback
        if not test_cases:
            print("⚠️ Empty test cases from model - generating Vietnamese fallback")
            # Generate Vietnamese fallback test cases
            fallback_cases = []
            if is_vietnamese:
                fallback_cases = [
                    TestCase(
                        test_case_id=1,
                        test_title="Trường Email",
                        description="Kiểm tra định dạng email hợp lệ",
                        preconditions="Người dùng đã mở trang đăng nhập",
                        test_steps="1. Mở trang đăng nhập\n2. Nhập email hợp lệ vào trường email (test@example.com)\n3. Nhập mật khẩu hợp lệ vào trường mật khẩu\n4. Nhấp nút đăng nhập\n5. Xác minh đăng nhập thành công và chuyển đến trang chủ",
                        test_data="test@example.com",
                        expected_result="Hệ thống chấp nhận email và cho phép đăng nhập thành công",
                        comments="Kiểm tra trường hợp email hợp lệ"
                    ),
                    TestCase(
                        test_case_id=2,
                        test_title="Trường Mật khẩu",
                        description="Kiểm tra xác thực mật khẩu",
                        preconditions="Người dùng đã mở trang đăng nhập",
                        test_steps="1. Mở trang đăng nhập\n2. Nhập email hợp lệ vào trường email\n3. Nhập mật khẩu hợp lệ vào trường mật khẩu (matkhau123)\n4. Nhấp nút đăng nhập\n5. Xác minh đăng nhập thành công và chuyển đến trang chủ",
                        test_data="matkhau123",
                        expected_result="Hệ thống chấp nhận mật khẩu và cho phép đăng nhập thành công",
                        comments="Kiểm tra trường hợp mật khẩu hợp lệ"
                    ),
                    TestCase(
                        test_case_id=3,
                        test_title="Nút Đăng nhập",
                        description="Kiểm tra chức năng nút đăng nhập",
                        preconditions="Người dùng đã nhập email và mật khẩu",
                        test_steps="1. Mở trang đăng nhập\n2. Nhập email hợp lệ vào trường email\n3. Nhập mật khẩu hợp lệ vào trường mật khẩu\n4. Nhấp nút đăng nhập\n5. Xác minh đăng nhập thành công và chuyển hướng đến trang chủ",
                        test_data="test@example.com, matkhau123",
                        expected_result="Hệ thống xử lý đăng nhập và chuyển hướng đến trang chủ",
                        comments="Kiểm tra chức năng đăng nhập cơ bản"
                    )
                ]
            else:
                fallback_cases = [
                    TestCase(
                        test_case_id=1,
                        test_title="Email Field",
                        description="Test valid email format",
                        preconditions="User has opened login page",
                        test_steps="1. Open login page\n2. Enter valid email in email field (test@example.com)\n3. Enter valid password in password field\n4. Click login button\n5. Verify successful login and redirect to dashboard",
                        test_data="test@example.com",
                        expected_result="System accepts email and allows successful login",
                        comments="Test valid email case"
                    )
                ]
            return {"test_cases": fallback_cases}

        # Trim to requested number if needed
        if len(test_cases) > target_num:
            test_cases = test_cases[:target_num]
        
        return {"test_cases": test_cases}
        
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error parsing response: {e}")
        # Return diversified fallback test cases (multiple)
        fallback_count = max(3, target_num)
        
        # Check if Vietnamese is selected for fallback cases
        project_settings = state.get('project_settings', {})
        languages = project_settings.get("languages", [])
        is_vietnamese = "Vietnamese" in languages or "Tiếng Việt" in languages
        
        if is_vietnamese:
            # Vietnamese fallback test cases with detailed steps
            archetypes = [
                ("Luồng Tích Cực", "Kiểm tra chức năng với dữ liệu hợp lệ và hành vi mong đợi", 
                 "1. Mở trang đăng nhập\n2. Nhập email hợp lệ vào trường email\n3. Nhập mật khẩu hợp lệ vào trường mật khẩu\n4. Nhấp nút đăng nhập\n5. Xác minh đăng nhập thành công và chuyển đến trang chủ", 
                 "test@example.com, matkhau123", "Hệ thống trả về thành công và dữ liệu chính xác"),
                ("Thông Tin Xác Thực Không Hợp Lệ", "Kiểm tra với thông tin xác thực không hợp lệ hoặc thiếu quyền", 
                 "1. Mở trang đăng nhập\n2. Nhập email không hợp lệ\n3. Nhập mật khẩu sai\n4. Nhấp nút đăng nhập\n5. Xác minh thông báo lỗi hiển thị", 
                 "email_sai@test.com, matkhau_sai", "Hệ thống từ chối hành động với thông báo lỗi phù hợp"),
                ("Giá Trị Biên", "Kiểm tra giá trị biên tối thiểu/tối đa và đầu vào ngoài phạm vi", 
                 "1. Mở trang đăng nhập\n2. Nhập email với độ dài tối đa\n3. Nhập mật khẩu với độ dài tối thiểu\n4. Nhấp nút đăng nhập\n5. Xác minh hệ thống xử lý đúng", 
                 "email_rat_dai@test.com, 123", "Hệ thống xử lý biên mà không có lỗi"),
                ("Xử Lý Lỗi", "Xử lý lỗi mạng hoặc phía máy chủ", 
                 "1. Mở trang đăng nhập\n2. Nhập thông tin hợp lệ\n3. Ngắt kết nối mạng\n4. Nhấp nút đăng nhập\n5. Xác minh thông báo lỗi kết nối", 
                 "test@example.com, matkhau123", "Lỗi nhẹ nhàng và phục hồi khi có thể"),
                ("Xác Thực Dữ Liệu", "Định dạng dữ liệu không chính xác và vi phạm ràng buộc", 
                 "1. Mở trang đăng nhập\n2. Nhập email sai định dạng\n3. Nhập mật khẩu với ký tự đặc biệt\n4. Nhấp nút đăng nhập\n5. Xác minh thông báo lỗi định dạng", 
                 "email_khong_hop_le, matkhau@#$%", "Hiển thị thông báo xác thực, không làm hỏng dữ liệu"),
            ]
        else:
            # English fallback test cases with detailed steps
            archetypes = [
                ("Positive Flow", "Valid inputs and expected happy-path behavior", 
                 "1. Open login page\n2. Enter valid email in email field\n3. Enter valid password in password field\n4. Click login button\n5. Verify successful login and redirect to dashboard", 
                 "test@example.com, password123", "System returns success and correct data"),
                ("Negative Credentials", "Invalid or missing credentials/permissions", 
                 "1. Open login page\n2. Enter invalid email\n3. Enter wrong password\n4. Click login button\n5. Verify error message is displayed", 
                 "wrong@test.com, wrongpass", "System denies action with proper error message"),
                ("Boundary Values", "Min/Max boundary and off-by-one inputs", 
                 "1. Open login page\n2. Enter email with maximum length\n3. Enter password with minimum length\n4. Click login button\n5. Verify system handles correctly", 
                 "very_long_email@test.com, 123", "System handles boundaries without errors"),
                ("Error Handling", "Network or server-side error handling", 
                 "1. Open login page\n2. Enter valid credentials\n3. Disconnect network\n4. Click login button\n5. Verify connection error message", 
                 "test@example.com, password123", "Graceful error and recovery where applicable"),
                ("Data Validation", "Incorrect data format and constraint violations", 
                 "1. Open login page\n2. Enter malformed email\n3. Enter password with special characters\n4. Click login button\n5. Verify format error message", 
                 "invalid_email_format, pass@#$%", "Validation messages shown, no data corruption"),
            ]
        
        fallback_cases: List[TestCase] = []
        for i in range(1, fallback_count + 1):
            kind = archetypes[(i - 1) % len(archetypes)]
            fallback_cases.append(
                TestCase(
                    test_case_id=i,
                    test_title=f"{kind[0]} Scenario #{i}",
                    description=kind[1],
                    preconditions="System operational; environment configured as per project settings" if not is_vietnamese else "Hệ thống hoạt động; môi trường được cấu hình theo cài đặt dự án",
                    test_steps=kind[2],
                    test_data=kind[3],
                    expected_result=kind[4],
                    comments="Fallback generated due to parsing/model error" if not is_vietnamese else "Được tạo tự động do lỗi phân tích/mô hình"
                )
            )
        return {"test_cases": fallback_cases}

# Build the LangGraph
graph_builder = StateGraph(State)
graph_builder.add_node("generator", test_cases_generator)
graph_builder.set_entry_point("generator")
graph_builder.set_finish_point("generator")
graph = graph_builder.compile()

def validate_test_cases_match_user_story(test_cases: List[TestCase], user_story: str) -> List[TestCase]:
    """
    Validate that test cases match the user story and improve them if needed
    """
    if not test_cases or not user_story:
        return test_cases
    
    # Extract key terms from user story
    user_story_lower = user_story.lower()
    key_terms = []
    
    # Look for common functionality keywords
    functionality_keywords = [
        'login', 'register', 'submit', 'click', 'enter', 'select', 'upload', 'download',
        'search', 'filter', 'sort', 'delete', 'edit', 'save', 'cancel', 'confirm',
        'đăng nhập', 'đăng ký', 'gửi', 'nhấp', 'nhập', 'chọn', 'tải lên', 'tải xuống',
        'tìm kiếm', 'lọc', 'sắp xếp', 'xóa', 'chỉnh sửa', 'lưu', 'hủy', 'xác nhận'
    ]
    
    for keyword in functionality_keywords:
        if keyword in user_story_lower:
            key_terms.append(keyword)
    
    # If we found key terms, ensure test cases cover them
    if key_terms:
        improved_cases = []
        for case in test_cases:
            # Check if test case covers any key functionality
            case_text = f"{case.test_title} {case.description} {case.test_steps}".lower()
            if any(term in case_text for term in key_terms):
                improved_cases.append(case)
            else:
                # Try to improve the test case to match user story
                if 'login' in key_terms and 'đăng nhập' not in case_text:
                    case.test_title = "Trường Email" if "email" in case_text else case.test_title
                    case.description = f"Kiểm tra chức năng đăng nhập - {case.description}"
                    improved_cases.append(case)
                else:
                    improved_cases.append(case)
        
        return improved_cases
    
    return test_cases


def _build_local_fallback_cases(
    num_cases: int,
    project_settings: Dict[str, Any] | None = None
) -> List[TestCase]:
    """Generate deterministic fallback cases when LLM results are unavailable."""
    languages = (project_settings or {}).get("languages", []) or []
    is_vietnamese = "Vietnamese" in languages or "Tiếng Việt" in languages
    
    if is_vietnamese:
        archetypes = [
            ("Luồng Tích Cực", "Kiểm tra chức năng với dữ liệu hợp lệ và hành vi mong đợi", 
             "1. Mở trang đăng nhập\n2. Nhập email hợp lệ vào trường email\n3. Nhập mật khẩu hợp lệ vào trường mật khẩu\n4. Nhấp nút đăng nhập\n5. Xác minh đăng nhập thành công và chuyển đến trang chủ", 
             "test@example.com, matkhau123", "Hệ thống trả về thành công và dữ liệu chính xác"),
            ("Thông Tin Xác Thực Không Hợp Lệ", "Kiểm tra với thông tin xác thực không hợp lệ hoặc thiếu quyền", 
             "1. Mở trang đăng nhập\n2. Nhập email không hợp lệ\n3. Nhập mật khẩu sai\n4. Nhấp nút đăng nhập\n5. Xác minh thông báo lỗi hiển thị", 
             "email_sai@test.com, matkhau_sai", "Hệ thống từ chối hành động với thông báo lỗi phù hợp"),
            ("Giá Trị Biên", "Kiểm tra giá trị biên tối thiểu/tối đa và đầu vào ngoài phạm vi", 
             "1. Mở trang đăng nhập\n2. Nhập email với độ dài tối đa\n3. Nhập mật khẩu với độ dài tối thiểu\n4. Nhấp nút đăng nhập\n5. Xác minh hệ thống xử lý đúng", 
             "email_rat_dai@test.com, 123", "Hệ thống xử lý biên mà không có lỗi"),
            ("Xử Lý Lỗi", "Xử lý lỗi mạng hoặc phía máy chủ", 
             "1. Mở trang đăng nhập\n2. Nhập thông tin hợp lệ\n3. Ngắt kết nối mạng\n4. Nhấp nút đăng nhập\n5. Xác minh thông báo lỗi kết nối", 
             "test@example.com, matkhau123", "Lỗi nhẹ nhàng và phục hồi khi có thể"),
            ("Xác Thực Dữ Liệu", "Định dạng dữ liệu không chính xác và vi phạm ràng buộc", 
             "1. Mở trang đăng nhập\n2. Nhập email sai định dạng\n3. Nhập mật khẩu với ký tự đặc biệt\n4. Nhấp nút đăng nhập\n5. Xác minh thông báo lỗi định dạng", 
             "email_khong_hop_le, matkhau@#$%", "Hiển thị thông báo xác thực, không làm hỏng dữ liệu"),
        ]
    else:
        archetypes = [
            ("Positive Flow", "Valid inputs and expected happy-path behavior", 
             "1. Open login page\n2. Enter valid email in email field\n3. Enter valid password in password field\n4. Click login button\n5. Verify successful login and redirect to dashboard", 
             "test@example.com, password123", "System returns success and correct data"),
            ("Negative Credentials", "Invalid or missing credentials/permissions", 
             "1. Open login page\n2. Enter invalid email\n3. Enter wrong password\n4. Click login button\n5. Verify error message is displayed", 
             "wrong@test.com, wrongpass", "System denies action with proper error message"),
            ("Boundary Values", "Min/Max boundary and off-by-one inputs", 
             "1. Open login page\n2. Enter email with maximum length\n3. Enter password with minimum length\n4. Click login button\n5. Verify system handles correctly", 
             "very_long_email@test.com, 123", "System handles boundaries without errors"),
            ("Error Handling", "Network or server-side error handling", 
             "1. Open login page\n2. Enter valid credentials\n3. Disconnect network\n4. Click login button\n5. Verify connection error message", 
             "test@example.com, password123", "Graceful error and recovery where applicable"),
            ("Data Validation", "Incorrect data format and constraint violations", 
             "1. Open login page\n2. Enter malformed email\n3. Enter password with special characters\n4. Click login button\n5. Verify format error message", 
             "invalid_email_format, pass@#$%", "Validation messages shown, no data corruption"),
        ]
    
    total = max(3 if is_vietnamese else 1, int(num_cases))
    fallback_cases: List[TestCase] = []
    for i in range(1, total + 1):
        archetype = archetypes[(i - 1) % len(archetypes)]
        fallback_cases.append(
            TestCase(
                test_case_id=i,
                test_title=f"{archetype[0]} Scenario #{i}",
                description=archetype[1],
                preconditions="Hệ thống đang hoạt động bình thường" if is_vietnamese else "System is operational",
                test_steps=archetype[2],
                test_data=archetype[3],
                expected_result=archetype[4],
                comments="Được tạo tự động do lỗi khi gọi AI" if is_vietnamese else "Auto-generated due to AI error"
            )
        )
    return fallback_cases

def generate_test_cases(user_input: str, num_cases: int = 10, project_settings: Dict[str, Any] | None = None) -> List[TestCase]:
    """
    Generate test cases from user story input.
    
    Args:
        user_input: The user story or functionality description
        num_cases: Desired maximum number of test cases to generate
        project_settings: Additional context to diversify generation
        
    Returns:
        List of TestCase objects
    """
    try:
        # Remove cache buster from user input if present
        clean_input = user_input
        if "[Cache Buster:" in user_input:
            clean_input = user_input.split("[Cache Buster:")[0].strip()
        
        print(f"🔄 Generating test cases for: {clean_input[:100]}...")
        
        result = graph.invoke({
            "test_cases": [],
            "user_story": clean_input,
            "num_cases": int(num_cases),
            "project_settings": project_settings or {},
        })
        
        test_cases = result.get("test_cases", [])
        
        # Validate and improve test cases to match user story
        improved_cases = validate_test_cases_match_user_story(test_cases, clean_input)
        
        print(f"✅ Generated {len(improved_cases)} test cases successfully!")
        if improved_cases:
            return improved_cases
        
        print("⚠️ No test cases returned from AI, using local fallback cases.")
        return _build_local_fallback_cases(num_cases, project_settings)
    except Exception as e:
        print(f"Error generating test cases: {e}")
        return _build_local_fallback_cases(num_cases, project_settings)
