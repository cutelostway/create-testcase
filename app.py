# app.py - Streamlit UI with Project Creation Modal
import streamlit as st
from export_to_excel import export_to_excel, export_to_excel_bytes
from tester_agent import generate_test_cases
from spec_processor import process_uploaded_spec
from jira_sync import sync_test_cases_to_jira
import os
import json
from typing import Dict, Any, List

# Storage helpers
PROJECTS_FILE = os.path.join(os.getcwd(), "projects.json")

def load_projects() -> List[Dict[str, Any]]:
    try:
        if not os.path.exists(PROJECTS_FILE):
            return []
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def save_projects(projects: List[Dict[str, Any]]):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)

def upsert_project(project: Dict[str, Any]) -> Dict[str, Any]:
    projects = load_projects()
    if 'id' not in project or project['id'] is None:
        project['id'] = (max([p.get('id', 0) for p in projects], default=0) + 1)
    updated = False
    for i, p in enumerate(projects):
        if p.get('id') == project['id']:
            projects[i] = project
            updated = True
            break
    if not updated:
        projects.append(project)
    save_projects(projects)
    return project

def get_project(project_id: int) -> Dict[str, Any] | None:
    for p in load_projects():
        if p.get('id') == project_id:
            return p
    return None

def render_back_button():
    """Render back button at the top of the page"""
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("← Back", type="secondary", use_container_width=False):
            go_to('home')

# Test case storage helpers
TEST_CASES_FILE = os.path.join(os.getcwd(), "test_cases.json")

def load_test_cases(project_id: int) -> List[Dict[str, Any]]:
    """Load saved test cases for a project"""
    try:
        if not os.path.exists(TEST_CASES_FILE):
            return []
        with open(TEST_CASES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get(str(project_id), [])
            return []
    except Exception:
        return []

def save_test_cases(project_id: int, test_cases: List[Dict[str, Any]]):
    """Save test cases for a project"""
    try:
        # Load existing data
        existing_data = {}
        if os.path.exists(TEST_CASES_FILE):
            with open(TEST_CASES_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        
        # Update with new test cases
        existing_data[str(project_id)] = test_cases
        
        # Save back to file
        with open(TEST_CASES_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Lỗi khi lưu test cases: {e}")

def convert_test_case_to_dict(test_case) -> Dict[str, Any]:
    """Convert TestCase object to dictionary"""
    # Suppress all Pydantic deprecation warnings
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        
        try:
            # Prefer Pydantic v2 API when available
            if hasattr(test_case, 'model_dump'):
                return test_case.model_dump()
            elif hasattr(test_case, 'dict'):
                return test_case.dict()
            elif hasattr(test_case, '__dict__'):
                return test_case.__dict__
            else:
                return dict(test_case)
        except Exception as e:
            # Fallback to basic conversion if all else fails
            if hasattr(test_case, '__dict__'):
                return test_case.__dict__
            else:
                return {}

def render_test_case_editor(test_case_dict: Dict[str, Any], test_case_index: int, project_id: int = None):
    """Render test case editor form"""
    st.markdown(f"### ✏️ Chỉnh sửa Test Case {test_case_index + 1}")
    
    # Create form with current values
    # Use simpler form key to avoid conflicts
    unique_key = f"edit_form_{project_id}_{test_case_index}" if project_id else f"edit_form_{test_case_index}"
    with st.form(key=unique_key):
        col1, col2 = st.columns(2)
        
        with col1:
            test_case_id = st.number_input(
                "🆔 Test Case ID",
                value=test_case_dict.get('test_case_id', test_case_index + 1),
                min_value=1,
                key=f"tc_id_{test_case_index}"
            )
            test_title = st.text_input(
                "📝 Tiêu đề Test Case",
                value=test_case_dict.get('test_title', ''),
                key=f"tc_title_{test_case_index}"
            )
            description = st.text_area(
                "📄 Mô tả",
                value=test_case_dict.get('description', ''),
                height=100,
                key=f"tc_desc_{test_case_index}"
            )
            preconditions = st.text_area(
                "⚙️ Điều kiện tiên quyết",
                value=test_case_dict.get('preconditions', ''),
                height=80,
                key=f"tc_pre_{test_case_index}"
            )
        
        with col2:
            test_data = st.text_area(
                "📊 Dữ liệu kiểm thử",
                value=test_case_dict.get('test_data', ''),
                height=80,
                key=f"tc_data_{test_case_index}"
            )
            expected_result = st.text_area(
                "✅ Kết quả mong đợi",
                value=test_case_dict.get('expected_result', ''),
                height=100,
                key=f"tc_result_{test_case_index}"
            )
            comments = st.text_area(
                "💬 Ghi chú",
                value=test_case_dict.get('comments', ''),
                height=80,
                key=f"tc_comments_{test_case_index}"
            )
        
        test_steps = st.text_area(
            "📋 Các bước kiểm thử",
            value=test_case_dict.get('test_steps', ''),
            height=150,
            help="Nhập từng bước trên một dòng riêng biệt",
            key=f"tc_steps_{test_case_index}"
        )
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            save_btn = st.form_submit_button("💾 Lưu thay đổi", type="primary")
        with col_cancel:
            cancel_btn = st.form_submit_button("❌ Hủy")
        
        if save_btn:
            # Update test case with new values
            updated_test_case = {
                'test_case_id': test_case_id,
                'test_title': test_title,
                'description': description,
                'preconditions': preconditions,
                'test_steps': test_steps,
                'test_data': test_data,
                'expected_result': expected_result,
                'comments': comments
            }
            
            # Update in session state
            try:
                if 'generated_test_cases' in st.session_state:
                    test_cases = st.session_state.generated_test_cases
                    if test_case_index < len(test_cases):
                        # Convert to dict if it's a TestCase object
                        current_case = test_cases[test_case_index]
                        
                        # Check if it's a TestCase object (Pydantic model)
                        if hasattr(current_case, 'model_dump') or hasattr(current_case, 'dict'):
                            # It's a TestCase object, create new instance with updated data
                            from tester_agent import TestCase
                            test_cases[test_case_index] = TestCase(**updated_test_case)
                        else:
                            # It's already a dict, just update it
                            test_cases[test_case_index] = updated_test_case
                        
                        st.session_state.generated_test_cases = test_cases
                        
                        # Clear editing state
                        st.session_state.editing_test_case = None
                        st.success("✅ Đã lưu thay đổi test case!")
                        st.rerun()
                    else:
                        st.error(f"❌ Test case index {test_case_index} không hợp lệ!")
                else:
                    st.error("❌ Không tìm thấy test cases trong session state!")
            except Exception as e:
                st.error(f"❌ Lỗi khi lưu test case: {str(e)}")
                st.exception(e)
        
        if cancel_btn:
            st.session_state.editing_test_case = None
            st.rerun()

# Router helpers (prefer stable API, fallback to experimental for old versions)

def get_query_params() -> Dict[str, List[str]]:
    try:
        # st.query_params is available on newer Streamlit versions
        qp = st.query_params  # type: ignore[attr-defined]
        # Cast to plain dict[list[str]] for downstream usage
        return {k: (v if isinstance(v, list) else [v]) for k, v in qp.items()}
    except Exception:
        try:
            return st.experimental_get_query_params()
        except Exception:
            return {}


def set_query_params(**kwargs):
    try:
        qp = st.query_params  # type: ignore[attr-defined]
        qp.clear()
        for k, v in kwargs.items():
            qp[k] = v if isinstance(v, list) else [str(v)]
    except Exception:
        try:
            st.experimental_set_query_params(**kwargs)
        except Exception:
            pass

def go_to(page: str, project_id: int | None = None):
    params = {'page': page}
    if project_id is not None:
        params['id'] = project_id
    set_query_params(**params)
    st.rerun()

# Initialize session state
if 'generated_test_cases' not in st.session_state:
    st.session_state.generated_test_cases = []
if 'project_created' not in st.session_state:
    st.session_state.project_created = False
if 'project_settings' not in st.session_state:
    st.session_state.project_settings = {}
if 'editing_test_case' not in st.session_state:
    st.session_state.editing_test_case = None
if 'saved_test_cases' not in st.session_state:
    st.session_state.saved_test_cases = {}
if 'show_delete_confirmation' not in st.session_state:
    st.session_state.show_delete_confirmation = False
if 'delete_test_case_index' not in st.session_state:
    st.session_state.delete_test_case_index = None

# Page configuration
st.set_page_config(page_title="AI Test Case Generator", page_icon="🧪", layout="wide")

# Load custom CSS
def load_css():
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# CREATE / EDIT FORMS ---------------------------------------------------------
def render_project_form(mode: str = "create", project: Dict[str, Any] | None = None):
    is_edit = (mode == "edit")
    title = "📑 Edit Project" if is_edit else "📑 Create New Project"
    st.markdown(f"<div class=\"modal-container\"><h2>{title}</h2><p>Configure your project settings</p></div>", unsafe_allow_html=True)

    # Prefill values
    defaults = project.get('settings', {}) if (project and project.get('settings')) else {}

    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name *", value=defaults.get('name', ''), help="Enter project name (required)")
        description = st.text_area("Description", max_chars=500, height=100, value=defaults.get('description', ''))
        languages = st.multiselect(
            "Test Cases Languages",
            options=["Vietnamese", "English", "Chinese", "Japanese", "French", "Spanish", "German"],
            default=defaults.get('languages', ['English']),
        )
    with col2:
        st.markdown("**Writing Style & Tone**")
        writing_style = st.text_area("Writing Style & Tone", height=80, value=defaults.get('writing_style', ''))
        st.markdown("**🔗 Jira Integration**")
        jira_project_key = st.text_input(
            "Jira Project Key", 
            value=defaults.get('jira_project_key', ''), 
            help="Enter Jira Project Key (e.g., PROJ) for test case synchronization",
            placeholder="PROJ"
        )
        
        # Jira Credentials
        with st.expander("🔐 Jira Credentials", expanded=False):
            st.markdown("**Configure Jira server connection:**")
            
            col_jira1, col_jira2 = st.columns(2)
            with col_jira1:
                jira_server = st.text_input(
                    "Jira Server URL",
                    value=defaults.get('jira_server', ''),
                    help="Enter your Jira server URL (e.g., https://yourcompany.atlassian.net)",
                    placeholder="https://yourcompany.atlassian.net"
                )
                jira_username = st.text_input(
                    "Username/Email",
                    value=defaults.get('jira_username', ''),
                    help="Enter your Jira username or email",
                    placeholder="user@company.com"
                )
            
            with col_jira2:
                jira_password = st.text_input(
                    "Password",
                    value=defaults.get('jira_password', ''),
                    type="password",
                    help="Enter your Jira password or App Password"
                )
                st.markdown("")
                st.markdown("")
            
            # Test connection button
            col_test_conn = st.columns([1, 1, 1])
            with col_test_conn[1]:
                if st.button("🔍 Test Jira Connection", help="Test connection to Jira server"):
                    if jira_server and jira_username and jira_password:
                        from jira_sync import test_jira_connection
                        with st.spinner("Testing Jira connection..."):
                            if test_jira_connection(jira_server, jira_username, jira_password):
                                st.success("✅ Jira connection successful!")
                            else:
                                st.error("❌ Jira connection failed!")
                    else:
                        st.warning("⚠️ Please fill in all Jira credentials first")
            
            # Xray Field Mapping
            with st.expander("⚙️ Xray Field Mapping", expanded=False):
                st.markdown("**Configure Xray custom field IDs:**")
                
                xray_test_steps_field = st.text_input(
                    "Test Steps Field ID",
                    value=defaults.get('xray_test_steps_field', 'customfield_11203'),
                    help="Custom field ID cho Manual Test Steps (bao gồm cả Test Data)"
                )

    st.markdown("---")
    st.markdown('<div class="section-header">🧪 Testing Configuration</div>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Testing Types**")
        testing_types = []
        test_options = [
            ("🖼️ UI Testing", "UI Testing"),
            ("⚙️ Functional Testing", "Functional Testing"),
            ("✅ Data Validation Testing", "Data Validation Testing"),
            ("🔒 Security Testing", "Security Testing"),
            ("⚡ Performance Testing", "Performance Testing"),
            ("♿ Accessibility Testing", "Accessibility Testing"),
            ("🔗 API/Integration Testing", "API/Integration Testing"),
            ("📱 Responsive Testing", "Responsive Testing")
        ]
        defaults_testing = set(defaults.get('testing_types', ['Functional Testing']))
        for display_name, value in test_options:
            if st.checkbox(display_name, value=(value in defaults_testing)):
                testing_types.append(value)
    with col4:
        st.markdown("**Checklist Setting - Detail Level**")
        detail_level = st.text_area("Detail Level", height=80, value=defaults.get('detail_level', ''))
        st.markdown("**Test Steps Detail Level**")
        steps_options = [
            "🔍 Low Detail - Key actions & results only",
            "⚖️ Medium Detail - Balanced main actions & outcomes",
            "📋 High Detail - Comprehensive step-by-step",
        ]
        steps_default = defaults.get('steps_detail', steps_options[1])
        steps_detail = st.radio("Select detail level:", options=steps_options, index=steps_options.index(steps_default) if steps_default in steps_options else 1)

    st.markdown("---")
    st.markdown('<div class="section-header">🎯 Priority Configuration</div>', unsafe_allow_html=True)
    priority_cols = st.columns(4)
    priorities = defaults.get('priority_levels', {})
    with priority_cols[0]:
        critical_priority = st.text_area("🔴 Critical Priority", height=80, value=priorities.get('critical', ''))
    with priority_cols[1]:
        high_priority = st.text_area("🟠 High Priority", height=80, value=priorities.get('high', ''))
    with priority_cols[2]:
        medium_priority = st.text_area("🟢 Medium Priority", height=80, value=priorities.get('medium', ''))
    with priority_cols[3]:
        low_priority = st.text_area("🔵 Low Priority", height=80, value=priorities.get('low', ''))

    st.markdown("---")
    st.markdown('<div class="section-header">🚫 Exclusion Rules</div>', unsafe_allow_html=True)
    exclusion_options = [
        ("🖼️ Skip Common UI Sections", "Skip Common UI Sections"),
        ("⚙️ Skip Non-functional Areas", "Skip Non-functional Areas"),
        ("🔗 Skip Third-party Integrations", "Skip Third-party Integrations"),
        ("🔄 Skip Redundant Test Cases", "Skip Redundant Test Cases"),
        ("👁️ Skip Obvious Actions", "Skip Obvious Actions"),
        ("🎨 Skip Minor Visual Issues", "Skip Minor Visual Issues")
    ]
    cols = st.columns(3)
    defaults_exclusion = set(defaults.get('exclusion_rules', []))
    exclusion_rules = []
    for i, (display_name, value) in enumerate(exclusion_options):
        col_idx = i % 3
        with cols[col_idx]:
            if st.checkbox(display_name, value=(value in defaults_exclusion)):
                exclusion_rules.append(value)

    st.markdown("---")
    col_submit = st.columns([1, 1, 3])
    btn_label = "💾 Save Project" if is_edit else "✅ Create Project"
    with col_submit[0]:
        if st.button(btn_label, type="primary"):
            if project_name.strip():
                settings = {
                    'name': project_name,
                    'description': description,
                    'languages': languages,
                    'writing_style': writing_style,
                    'jira_project_key': jira_project_key,
                    # Jira Credentials
                    'jira_server': jira_server,
                    'jira_username': jira_username,
                    'jira_password': jira_password,
                    # Xray Field Mapping
                    'xray_test_steps_field': xray_test_steps_field,
                    'detail_level': detail_level,
                    'testing_types': testing_types,
                    'priority_levels': {
                        'critical': critical_priority,
                        'high': high_priority,
                        'medium': medium_priority,
                        'low': low_priority
                    },
                    'exclusion_rules': exclusion_rules,
                    'steps_detail': steps_detail,
                }
                record = {'id': project.get('id') if project else None, 'settings': settings}
                saved = upsert_project(record)
                st.session_state.project_settings = settings
                st.session_state.project_created = True
                go_to('create-test-case', saved['id'])
            else:
                st.error("❗ Project name is required!")
    with col_submit[1]:
        if st.button("❌ Cancel"):
            go_to('home')

# VIEWS -----------------------------------------------------------------------
def view_home():
    st.title("🧪 AI Test Case Generator")
    st.markdown("### ✨ Get Started")
    st.markdown("Create your first project with customized settings to generate tailored test cases for your needs.")
    col_center = st.columns([2, 1, 2])
    with col_center[1]:
        if st.button("🚀 Create Project", type="primary", use_container_width=True):
            go_to('create-project')
    st.markdown("---")
    st.markdown("### 📚 Projects")
    projects = load_projects()
    if not projects:
        st.info("Chưa có project nào. Hãy tạo mới để bắt đầu.")
        return
    for p in projects:
        s = p.get('settings', {})
        with st.container(border=True):
            cols = st.columns([4, 2, 2])
            with cols[0]:
                st.markdown(f"**{s.get('name','(no name)')}**")
                st.caption(s.get('description', ''))
            with cols[1]:
                if st.button("📝 Edit", key=f"edit_{p['id']}"):
                    go_to('edit-project', p['id'])
            with cols[2]:
                if st.button("🧪 Create Testcase", key=f"tc_{p['id']}"):
                    st.session_state.project_settings = s
                    go_to('create-test-case', p['id'])


def view_create_project():
    render_back_button()
    render_project_form(mode="create")

def view_edit_project(project_id: int | None):
    render_back_button()
    if not project_id:
        st.error("Không tìm thấy project để chỉnh sửa")
        return
    project = get_project(project_id)
    if not project:
        st.error("Project không tồn tại")
        return
    render_project_form(mode="edit", project=project)

def view_create_test_case(project_id: int | None):
    render_back_button()
    # Load selected project if available
    if project_id:
        project = get_project(project_id)
        if project:
            st.session_state.project_settings = project.get('settings', {})
        
        # Auto-load saved test cases if none are currently loaded
        if not st.session_state.get('generated_test_cases') and project_id:
            saved_cases = load_test_cases(project_id)
            if saved_cases:
                # Convert back to TestCase objects if needed
                from tester_agent import TestCase
                loaded_test_cases = []
                for case_dict in saved_cases:
                    try:
                        loaded_test_cases.append(TestCase(**case_dict))
                    except:
                        loaded_test_cases.append(case_dict)
                st.session_state.generated_test_cases = loaded_test_cases
                st.info(f"ℹ️ Đã tự động tải {len(loaded_test_cases)} test cases đã lưu cho project này")
    
    settings = st.session_state.get('project_settings', {})

    st.markdown(f"# 🎯 Project: {settings.get('name', 'Unnamed Project')}")
    
    # Show usage instructions
    with st.expander("ℹ️ Hướng dẫn sử dụng tính năng chỉnh sửa", expanded=False):
        st.markdown("""
        **✨ Tính năng mới: Chỉnh sửa và lưu trữ Test Cases**
        
        🎯 **Cách sử dụng:**
        1. **Tạo test cases:** Nhập user story và nhấn "Generate Test Cases"
        2. **Chỉnh sửa:** Nhấn nút "✏️ Chỉnh sửa" trên test case muốn sửa
        3. **Lưu trữ:** Nhấn "💾 Lưu Test Cases" để lưu vào file
        4. **Tải lại:** Nhấn "📂 Tải Test Cases" để tải test cases đã lưu
        5. **Đồng bộ Jira:** Nhấn "🔗 Đồng bộ Jira" để tải test cases lên Jira
        6. **Xuất file:** Sử dụng các nút Download để xuất Excel/CSV/JSON
        
        💡 **Lưu ý:** Test cases sẽ được tự động tải khi bạn vào lại project này
        """)
    
    # Store current project key for Jira debug
    st.session_state.current_project_key = settings.get('jira_project_key', '')

    # Test case generation interface
    st.markdown("## 🚀 Generate Test Cases")
    
    # File upload section
    st.markdown("### 📄 Upload Specification Document (Optional)")
    st.markdown("Upload a specification document to automatically generate user story from your requirements using AI analysis.")
    
    # Create expandable section for file upload
    with st.expander("📤 Upload & Analyze Specification", expanded=False):
        col_upload1, col_upload2 = st.columns([3, 1])
        
        with col_upload1:
            uploaded_file = st.file_uploader(
                "Choose a specification file",
                type=['xlsx', 'pdf', 'docx'],
                help="Supported formats: Excel (.xlsx), PDF (.pdf), Word (.docx)",
                key="spec_uploader"
            )
        
        with col_upload2:
            analyze_btn = st.button("🔍 Analyze Spec", type="secondary", use_container_width=True)
        
        # Show file info if uploaded
        if uploaded_file:
            st.info(f"📎 **File selected:** {uploaded_file.name} ({uploaded_file.size} bytes)")
            
        # Show analysis status
        if st.session_state.get('generated_user_story'):
            st.success("✅ Specification analyzed! User story generated below.")
    
    # Process uploaded file
    if uploaded_file and analyze_btn:
        with st.spinner("🔄 Analyzing specification document..."):
            try:
                file_content = uploaded_file.read()
                file_type = uploaded_file.type
                
                # Process the spec file
                generated_story = process_uploaded_spec(file_content, file_type, settings)
                
                # Store in session state for auto-fill
                st.session_state.generated_user_story = generated_story
                st.success("✅ Specification analyzed successfully! User story generated below.")
                
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
    
    # User story input section
    st.markdown("### 📋 User Story or Functionality Description")
    
    # Auto-fill with generated story if available
    default_story = st.session_state.get('generated_user_story', '')
    
    # Show different UI based on whether we have AI-generated content
    if default_story:
        # Check if it's Vietnamese content
        is_vietnamese_content = any(keyword in default_story for keyword in ["Câu Chuyện Người Dùng", "Đặc Tả", "Tính năng", "Người dùng"])
        
        if is_vietnamese_content:
            st.markdown("**🤖 Câu Chuyện Người Dùng Được Tạo Bởi AI:**")
            st.markdown("Câu chuyện người dùng dưới đây được tạo từ tài liệu đặc tả của bạn. Bạn có thể chỉnh sửa trước khi tạo test case.")
        else:
            st.markdown("**🤖 AI-Generated User Story:**")
            st.markdown("The user story below was generated from your specification document. You can edit it before generating test cases.")
        
        col_clear, col_edit = st.columns([1, 3])
        with col_clear:
            if st.button("🗑️ Clear AI Story", type="secondary"):
                st.session_state.generated_user_story = ""
                st.rerun()
        with col_edit:
            if is_vietnamese_content:
                st.markdown("💡 *Chỉnh sửa câu chuyện bên dưới để tùy chỉnh theo nhu cầu của bạn*")
            else:
                st.markdown("💡 *Edit the story below to customize it for your needs*")
    
    # Determine if we should show Vietnamese labels
    is_vietnamese_content = any(keyword in default_story for keyword in ["Câu Chuyện Người Dùng", "Đặc Tả", "Tính năng", "Người dùng"]) if default_story else False
    
    user_story = st.text_area(
        "📋 Enter User Story or Functionality Description:" if not is_vietnamese_content else "📋 Nhập Câu Chuyện Người Dùng hoặc Mô Tả Chức Năng:",
        height=250,
        value=default_story,
        help="Describe the functionality you want to create test cases for. You can edit the AI-generated story above or write your own." if not is_vietnamese_content else "Mô tả chức năng bạn muốn tạo test case. Bạn có thể chỉnh sửa câu chuyện được tạo bởi AI ở trên hoặc viết câu chuyện của riêng bạn.",
        placeholder="Example: As a user, I want to login to the system so that I can access my dashboard..." if not is_vietnamese_content else "Ví dụ: Là một người dùng, tôi muốn đăng nhập vào hệ thống để có thể truy cập bảng điều khiển của mình..."
    )
    
    # Test case generation controls
    st.markdown("### 🎯 Test Case Generation")
    col_gen = st.columns([2, 1, 1, 1])
    with col_gen[0]:
        generate_btn = st.button("🎯 Generate Test Cases", type="primary", use_container_width=True)
    with col_gen[1]:
        num_cases = st.number_input("Max Cases", min_value=1, max_value=50, value=10)
    with col_gen[2]:
        export_format = st.selectbox("Export", ["Excel", "CSV", "JSON"])
    with col_gen[3]:
        if st.button("🗑️ Clear Cache", type="secondary", help="Clear all cached data and restart"):
            st.session_state.clear()
            st.rerun()

    if generate_btn:
        if user_story.strip():
            with st.spinner("🔄 Generating test cases with AI..."):
                try:
                    # Clean up user story if it's too long or has formatting issues
                    cleaned_story = user_story.strip()
                    
                    # If it's an AI-generated story with headers, extract the main content
                    if cleaned_story.startswith("#"):
                        lines = cleaned_story.split('\n')
                        # Find the main content after headers
                        main_content = []
                        in_main_content = False
                        for line in lines:
                            if line.startswith("---") or line.startswith("**📄") or line.startswith("**💡") or line.startswith("**Tóm Tắt") or line.startswith("**Lưu Ý"):
                                break
                            if in_main_content or (line.strip() and not line.startswith("#")):
                                in_main_content = True
                                main_content.append(line)
                        cleaned_story = '\n'.join(main_content).strip()
                    
                    # Extract key functionality from user story for better matching
                    key_functionality = []
                    lines = cleaned_story.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('**'):
                            # Look for user actions and functionality
                            if any(keyword in line.lower() for keyword in ['want', 'need', 'should', 'can', 'must', 'muốn', 'cần', 'có thể', 'phải', 'login', 'register', 'submit', 'click', 'enter', 'select']):
                                key_functionality.append(line)
                    
                    # If we found key functionality, use it as context
                    if key_functionality:
                        cleaned_story = '\n'.join(key_functionality[:5])  # Take first 5 key points
                        st.info("ℹ️ Extracted key functionality from user story for better test case generation.")
                    
                    # Limit story length to prevent API issues
                    if len(cleaned_story) > 2000:
                        cleaned_story = cleaned_story[:2000] + "..."
                        st.info("ℹ️ User story was truncated to prevent API issues.")
                    
                    # Generate test cases with cache busting
                    import time
                    cache_buster = int(time.time())
                    generated = generate_test_cases(
                        f"{cleaned_story}\n\n[Cache Buster: {cache_buster}]",
                        int(num_cases),
                        settings,
                    )
                    
                    if generated and len(generated) > 0:
                        st.session_state.generated_test_cases = generated
                        st.success(f"✅ Generated {len(generated)} test cases successfully!")
                    else:
                        st.error("❌ Failed to generate test cases. Please try again.")
                        
                except Exception as e:
                    st.error(f"❌ Error generating test cases: {str(e)}")
                    st.info("💡 Try shortening your user story or check your API key.")
        else:
            st.warning("⚠️ Please enter a user story to generate test cases.")

    test_cases = st.session_state.get('generated_test_cases', [])
    if test_cases:
        st.success(f"✅ Generated {len(test_cases)} test cases successfully!")
        
        # Lưu ý: Form chỉnh sửa được render inline bên trong từng expander để tránh trùng key
        
        col_stats = st.columns(4)
        with col_stats[0]:
            st.metric("Total Cases", len(test_cases))
        with col_stats[1]:
            st.metric("Critical", len([tc for tc in test_cases if 'critical' in str(tc.test_case_id).lower()]))
        with col_stats[2]:
            st.metric("High Priority", len([tc for tc in test_cases if 'high' in str(tc.test_case_id).lower()]))
        with col_stats[3]:
            st.metric("Medium/Low", len(test_cases) - len([tc for tc in test_cases if 'critical' in str(tc.test_case_id).lower() or 'high' in str(tc.test_case_id).lower()]))
        
        # Add save/load controls
        st.markdown("### 💾 Quản lý Test Cases")
        col_save_load = st.columns([1, 1, 1, 1, 1])
        with col_save_load[0]:
            if st.button("💾 Lưu Test Cases", type="primary", help="Lưu test cases vào file"):
                if project_id:
                    # Convert test cases to dict format for saving
                    test_cases_dict = [convert_test_case_to_dict(tc) for tc in test_cases]
                    save_test_cases(project_id, test_cases_dict)
                    st.success("✅ Đã lưu test cases thành công!")
                else:
                    st.error("❌ Không thể lưu: Project ID không hợp lệ")
        
        with col_save_load[1]:
            if st.button("📂 Tải Test Cases", help="Tải test cases đã lưu"):
                if project_id:
                    saved_cases = load_test_cases(project_id)
                    if saved_cases:
                        # Convert back to TestCase objects if needed
                        from tester_agent import TestCase
                        loaded_test_cases = []
                        for case_dict in saved_cases:
                            try:
                                loaded_test_cases.append(TestCase(**case_dict))
                            except:
                                loaded_test_cases.append(case_dict)
                        st.session_state.generated_test_cases = loaded_test_cases
                        st.success(f"✅ Đã tải {len(loaded_test_cases)} test cases!")
                        st.rerun()
                    else:
                        st.info("ℹ️ Chưa có test cases nào được lưu cho project này")
                else:
                    st.error("❌ Không thể tải: Project ID không hợp lệ")
        
        with col_save_load[2]:
            if st.button("🔗 Đồng bộ Jira", help="Đồng bộ test cases lên Jira"):
                jira_project_key = settings.get('jira_project_key', '')
                if jira_project_key:
                    # Convert test cases to dict format for syncing
                    test_cases_dict = [convert_test_case_to_dict(tc) for tc in test_cases]
                    
                    with st.spinner("🔄 Đang đồng bộ test cases lên Jira..."):
                        result = sync_test_cases_to_jira(test_cases_dict, jira_project_key, settings)
                        
                        if result['success']:
                            st.success(result['message'])
                        else:
                            st.error(result['message'])
                else:
                    st.error("❌ Jira Project Key chưa được cấu hình. Vui lòng cấu hình trong project settings.")
        
        with col_save_load[3]:
            if st.button("🗑️ Xóa tất cả", help="Xóa tất cả test cases"):
                st.session_state.generated_test_cases = []
                st.session_state.editing_test_case = None
                st.success("✅ Đã xóa tất cả test cases!")
                st.rerun()
        
        with col_save_load[4]:
            if st.button("🔄 Làm mới", help="Làm mới trang"):
                st.rerun()
        
        st.markdown("---")
        
        # Display test cases with edit buttons
        for i, case in enumerate(test_cases, 1):
            priority_colors = {'critical': '🔴','high': '🟠','medium': '🟢','low': '🔵'}
            priority_icon = '🧪'
            
            # Convert case to dict for display
            case_dict = convert_test_case_to_dict(case)
            
            # Check priority based on test_case_id
            test_case_id_str = str(case_dict.get('test_case_id', ''))
            for priority, icon in priority_colors.items():
                if priority in test_case_id_str.lower():
                    priority_icon = icon
                    break
            
            # Check if this test case is being edited to determine if expander should be open
            index_zero_based = i - 1
            is_editing = st.session_state.get('editing_test_case') == index_zero_based
            
            with st.expander(f"{priority_icon} Test Case {i}: {case_dict.get('test_title', 'Untitled')}", expanded=is_editing):
                # If this is the one being edited, render the editor inline
                if is_editing:
                    # Dùng key form duy nhất theo project + index để tránh trùng
                    with st.container():
                        render_test_case_editor(case_dict, index_zero_based, project_id)
                else:
                    col_case1, col_case2, col_case3 = st.columns([2, 2, 1])
                    with col_case1:
                        st.markdown(f"**🆔 ID:** `{case_dict.get('test_case_id', i)}`")
                        st.markdown(f"**📝 Description:** {case_dict.get('description', '')}")
                        st.markdown(f"**⚙️ Preconditions:** {case_dict.get('preconditions', '')}")
                    with col_case2:
                        st.markdown(f"**📊 Test Data:** {case_dict.get('test_data', '')}")
                        st.markdown(f"**✅ Expected Result:** {case_dict.get('expected_result', '')}")
                        st.markdown(f"**💬 Comments:** {case_dict.get('comments', '')}")
                    with col_case3:
                        col_edit, col_delete = st.columns(2)
                        with col_edit:
                            if st.button("✏️ Chỉnh sửa", key=f"edit_btn_{i-1}", help="Chỉnh sửa test case này"):
                                st.session_state.editing_test_case = index_zero_based
                                st.rerun()
                        with col_delete:
                            if st.button("🗑️ Xóa", key=f"delete_btn_{i-1}", help="Xóa test case này", type="secondary"):
                                # Store the test case index to delete
                                st.session_state.delete_test_case_index = index_zero_based
                                st.session_state.show_delete_confirmation = True
                                st.rerun()
                    
                    st.markdown("**📋 Test Steps:**")
                    st.info(case_dict.get('test_steps', ''))
        
        # Show delete confirmation dialog
        if st.session_state.get('show_delete_confirmation', False):
            delete_index = st.session_state.get('delete_test_case_index', -1)
            if delete_index >= 0 and delete_index < len(test_cases):
                test_case_to_delete = test_cases[delete_index]
                test_case_dict = convert_test_case_to_dict(test_case_to_delete)
                
                st.warning("⚠️ Xác nhận xóa Test Case")
                st.markdown(f"**Bạn có chắc chắn muốn xóa Test Case:** `{test_case_dict.get('test_title', 'Untitled')}`?")
                
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("✅ Xác nhận xóa", type="primary"):
                        # Delete the test case
                        del test_cases[delete_index]
                        # Reset editing state if this was being edited
                        if st.session_state.get('editing_test_case') == delete_index:
                            st.session_state.editing_test_case = None
                        # Clear confirmation state
                        st.session_state.show_delete_confirmation = False
                        st.session_state.delete_test_case_index = None
                        st.success(f"✅ Đã xóa Test Case thành công!")
                        st.rerun()
                
                with col_cancel:
                    if st.button("❌ Hủy", type="secondary"):
                        st.session_state.show_delete_confirmation = False
                        st.session_state.delete_test_case_index = None
                        st.rerun()
        
        st.markdown("---")
        col_export = st.columns([1, 2, 1])
        with col_export[1]:
            try:
                if export_format == "Excel":
                    data = export_to_excel_bytes(test_cases)
                    st.download_button(
                        label="📥 Download Excel",
                        data=data,
                        file_name="test_cases.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                elif export_format == "CSV":
                    import pandas as pd
                    rows = [convert_test_case_to_dict(tc) for tc in test_cases]
                    csv_data = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name="test_cases.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    rows = [convert_test_case_to_dict(tc) for tc in test_cases]
                    json_data = json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name="test_cases.json",
                        mime="application/json",
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"❌ Export failed: {e}")

# ROUTER ----------------------------------------------------------------------
params = get_query_params()
page = None
pid = None
try:
    page = (params.get('page', ["home"]) or ["home"])[0]
    pid = params.get('id', [None])[0]
    pid = int(pid) if pid not in (None, "", []) else None
except Exception:
    page = "home"
    pid = None

if page == 'home':
    view_home()
elif page == 'create-project':
    view_create_project()
elif page == 'edit-project':
    view_edit_project(pid)
elif page == 'create-test-case':
    view_create_test_case(pid)
else:
    view_home()
