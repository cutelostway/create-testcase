# app.py - Streamlit UI with Project Creation Modal
import streamlit as st
from export_to_excel import export_to_excel, export_to_excel_bytes, export_to_excel_template_bytes, export_original_template_bytes
from tester_agent import generate_test_cases
from spec_processor import process_uploaded_spec
import os
import json
from typing import Dict, Any, List
from datetime import date, datetime

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

# Router helpers for subdirectory-based routing

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
    """Navigate to a new page using subdirectory URLs"""
    # Map page names to subdirectories
    page_mapping = {
        'home': 'list-project',
        'create-project': 'create-project',
        'edit-project': 'edit-project', 
        'create-test-case': 'create-testcase',
        'create-testcase': 'create-testcase'
    }
    
    subdirectory = page_mapping.get(page, page)
    
    # Build the new URL
    if project_id is not None:
        new_url = f"/{subdirectory}/{project_id}"
    else:
        new_url = f"/{subdirectory}"
    
    # Update session state
    st.session_state.current_path = new_url
    st.session_state.last_url = f"{page}_{project_id}"
    
    # Use query params for actual routing
    params = {'page': page}
    if project_id is not None:
        params['id'] = project_id
    
    set_query_params(**params)
    
    # Use JavaScript to change URL in browser
    navigation_script = f"""
    <script>
    // Change URL without page reload
    window.history.pushState({{}}, '', '{new_url}');
    </script>
    """
    st.components.v1.html(navigation_script, height=0)
    st.rerun()

# Initialize session state
if 'generated_test_cases' not in st.session_state:
    st.session_state.generated_test_cases = []
if 'project_created' not in st.session_state:
    st.session_state.project_created = False
if 'project_settings' not in st.session_state:
    st.session_state.project_settings = {}
if 'current_path' not in st.session_state:
    st.session_state.current_path = "/list-project"

# Page configuration
st.set_page_config(page_title="AI Test Case Generator", page_icon="🧪", layout="wide")

# URL Router Component
def url_router():
    """Component to handle URL routing"""
    # Create a hidden component to handle URL changes
    with st.container():
        st.markdown("""
        <script>
        // Function to update URL based on query params
        function updateURLFromParams() {
            const urlParams = new URLSearchParams(window.location.search);
            const page = urlParams.get('page');
            const id = urlParams.get('id');
            
            if (page) {
                let newPath = '/' + page;
                if (id) {
                    newPath += '/' + id;
                }
                
                // Update URL without reload
                if (window.location.pathname !== newPath) {
                    window.history.pushState({}, '', newPath);
                }
            } else if (window.location.pathname !== '/') {
                // Handle direct URL access
                const path = window.location.pathname;
                const parts = path.split('/').filter(p => p);
                
                if (parts.length > 0) {
                    const page = parts[0];
                    const id = parts.length > 1 ? parts[1] : null;
                    
                    // Update query params
                    const url = new URL(window.location);
                    url.searchParams.set('page', page);
                    if (id) {
                        url.searchParams.set('id', id);
                    }
                    
                    // Reload with new query params
                    window.location.href = url.toString();
                }
            }
        }
        
        // Function to handle browser back/forward
        function handlePopState() {
            // Parse current path and update query params
            const path = window.location.pathname;
            const parts = path.split('/').filter(p => p);
            
            if (parts.length > 0) {
                const page = parts[0];
                const id = parts.length > 1 ? parts[1] : null;
                
                // Update query params
                const url = new URL(window.location);
                url.searchParams.set('page', page);
                if (id) {
                    url.searchParams.set('id', id);
                } else {
                    url.searchParams.delete('id');
                }
                
                // Force reload with new query params
                window.location.href = url.toString();
            } else {
                // Handle root path - go to list-project
                const url = new URL(window.location);
                url.searchParams.set('page', 'list-project');
                url.searchParams.delete('id');
                window.location.href = url.toString();
            }
        }
        
        // Update URL on page load
        updateURLFromParams();
        
        // Listen for browser back/forward
        window.addEventListener('popstate', function(event) {
            // Force reload immediately
            handlePopState();
        });
        
        // Track URL changes for better browser navigation
        let lastPath = window.location.pathname;
        let lastSearch = window.location.search;
        
        // Check for URL changes periodically (fallback)
        setInterval(function() {
            const currentPath = window.location.pathname;
            const currentSearch = window.location.search;
            
            // If URL changed (path or search params)
            if (currentPath !== lastPath || currentSearch !== lastSearch) {
                lastPath = currentPath;
                lastSearch = currentSearch;
                
                // Handle the change
                const urlParams = new URLSearchParams(currentSearch);
                const page = urlParams.get('page');
                
                if (!page && currentPath !== '/') {
                    handlePopState();
                } else if (page) {
                    // URL changed, force reload to update Streamlit
                    window.location.reload();
                }
            }
        }, 100);
        </script>
        """, unsafe_allow_html=True)

# Load custom CSS
def load_css():
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# Initialize URL router
url_router()

# CREATE / EDIT FORMS ---------------------------------------------------------
def render_project_form(mode: str = "create", project: Dict[str, Any] | None = None):
    is_edit = (mode == "edit")
    title = "📑 Edit Project" if is_edit else "📑 Create New Project"
    st.markdown(f"<div class=\"modal-container\"><h2>{title}</h2><p>Configure your project settings</p></div>", unsafe_allow_html=True)

    # Prefill values
    defaults = project.get('settings', {}) if (project and project.get('settings')) else {}

    st.markdown('<div class="section-header">📋 Project Information</div>', unsafe_allow_html=True)
    
    # Project Information fields in 2 columns layout
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        project_name = st.text_input("Project Name *", value=defaults.get('name', ''), help="Enter project name (required)")
        description = st.text_area("Description", max_chars=500, height=100, value=defaults.get('description', ''))
        languages = st.multiselect(
            "Test Cases Languages",
            options=["Vietnamese", "English", "Chinese", "Japanese", "French", "Spanish", "German"],
            default=defaults.get('languages', ['English']),
        )
        environment = st.multiselect(
            "Environment *",
            options=["Chrome", "Firefox", "Edge", "Windows", "MacOS", "Android", "iOS"],
            default=defaults.get('environment', ['Chrome']),
            help="Select testing environments (required)"
        )
    with col_info2:
        phase = st.text_input("Phase", value=defaults.get('phase', ''), help="Project phase (optional)")
        sprint = st.text_input("Sprint", value=defaults.get('sprint', ''), help="Sprint number (optional)")
        member = st.text_input("Member", value=defaults.get('member', ''), help="Team member name (optional)")
        
        # Date range in the same column
        st.markdown("**Date Range**")
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input("Start Date", value=defaults.get('start_date'), help="Project start date (optional)")
        with col_date2:
            end_date = st.date_input("End Date", value=defaults.get('end_date'), help="Project end date (optional)")

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
        defaults_testing = set(defaults.get('testing_types', ['UI Testing', 'Functional Testing', 'Data Validation Testing']))
        for display_name, value in test_options:
            if st.checkbox(display_name, value=(value in defaults_testing)):
                testing_types.append(value)
    with col4:
        st.markdown("**Test Steps Detail Level**")
        steps_options = [
            "🔍 Low Detail - Key actions & results only",
            "⚖️ Medium Detail - Balanced main actions & outcomes",
            "📋 High Detail - Comprehensive step-by-step",
        ]
        steps_default = defaults.get('steps_detail', steps_options[2])
        steps_detail = st.radio("Select detail level:", options=steps_options, index=steps_options.index(steps_default) if steps_default in steps_options else 2)

    st.markdown("---")
    st.markdown('<div class="section-header">🎯 Priority Configuration</div>', unsafe_allow_html=True)
    priority_cols = st.columns(4)
    priorities = defaults.get('priority_levels', {})
    
    # Default priority descriptions
    default_priorities = {
        'critical': 'System crashes, data loss, security vulnerabilities, core functionality broken',
        'high': 'Major features not working, significant performance issues, important bugs',
        'medium': 'Minor features affected, cosmetic issues, non-critical bugs',
        'low': 'Enhancement requests, minor UI improvements, nice-to-have features'
    }
    
    with priority_cols[0]:
        critical_priority = st.text_area("🔴 Critical Priority", height=80, value=priorities.get('critical', default_priorities['critical']))
    with priority_cols[1]:
        high_priority = st.text_area("🟠 High Priority", height=80, value=priorities.get('high', default_priorities['high']))
    with priority_cols[2]:
        medium_priority = st.text_area("🟢 Medium Priority", height=80, value=priorities.get('medium', default_priorities['medium']))
    with priority_cols[3]:
        low_priority = st.text_area("🔵 Low Priority", height=80, value=priorities.get('low', default_priorities['low']))

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
            if project_name.strip() and environment:
                settings = {
                    'name': project_name,
                    'description': description,
                    'languages': languages,
                    'environment': environment,
                    'phase': phase,
                    'sprint': sprint,
                    'member': member,
                    'start_date': start_date,
                    'end_date': end_date,
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
                go_to('create-testcase', saved['id'])
            else:
                if not project_name.strip():
                    st.error("❗ Project name is required!")
                elif not environment:
                    st.error("❗ Environment is required!")
    with col_submit[1]:
        if st.button("❌ Cancel"):
            go_to('list-project')

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
                # Display new project info
                info_parts = []
                if s.get('phase'):
                    info_parts.append(f"Phase: {s.get('phase')}")
                if s.get('sprint'):
                    info_parts.append(f"Sprint: {s.get('sprint')}")
                if s.get('member'):
                    info_parts.append(f"Member: {s.get('member')}")
                if s.get('environment'):
                    env_str = ", ".join(s.get('environment', []))
                    info_parts.append(f"Environment: {env_str}")
                if s.get('start_date') and s.get('end_date'):
                    info_parts.append(f"Duration: {s.get('start_date')} - {s.get('end_date')}")
                if info_parts:
                    st.caption(" | ".join(info_parts))
            with cols[1]:
                if st.button("📝 Edit", key=f"edit_{p['id']}"):
                    go_to('edit-project', p['id'])
            with cols[2]:
                if st.button("🧪 Create Testcase", key=f"tc_{p['id']}"):
                    st.session_state.project_settings = s
                    go_to('create-testcase', p['id'])


def view_create_project():
    # Add Back button
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("← Back", type="secondary"):
            go_to('list-project')
    with col_title:
        st.markdown("")
    
    render_project_form(mode="create")

def view_edit_project(project_id: int | None):
    if not project_id:
        st.error("Không tìm thấy project để chỉnh sửa")
        return
    project = get_project(project_id)
    if not project:
        st.error("Project không tồn tại")
        return
    
    # Add Back button
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("← Back", type="secondary"):
            go_to('list-project')
    with col_title:
        st.markdown("")
    
    render_project_form(mode="edit", project=project)

def view_create_test_case(project_id: int | None):
    # Load selected project if available
    if project_id:
        project = get_project(project_id)
        if project:
            st.session_state.project_settings = project.get('settings', {})
    settings = st.session_state.get('project_settings', {})

    # Add Back button
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("← Back", type="secondary"):
            go_to('list-project')
    with col_title:
        st.markdown(f"# 🎯 Project: {settings.get('name', 'Unnamed Project')}")

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
            
            # Analysis instructions section
            st.markdown("### 🎯 Analysis Instructions (Optional)")
            st.markdown("Provide specific instructions to guide AI analysis of your specification document.")
            
            col_instructions1, col_instructions2 = st.columns([2, 1])
            
            with col_instructions1:
                analysis_instructions = st.text_area(
                    "📝 Analysis Instructions:",
                    height=100,
                    placeholder="Examples:\n• For Excel: Analyze only Sheet2 and Sheet3, skip the summary sheet\n• For PDF: Focus on pages 3-4 and 7-8, ignore the cover page\n• For Word: Read sections 2.1 to 2.5, skip the introduction\n• General: Focus on user authentication features, ignore admin functions",
                    help="Provide specific instructions to guide AI analysis. Examples are shown in the placeholder.",
                    key="analysis_instructions"
                )
            
            with col_instructions2:
                st.markdown("**💡 Tips:**")
                st.markdown("• **Excel:** Specify sheet names or numbers")
                st.markdown("• **PDF:** Mention page ranges")
                st.markdown("• **Word:** Reference section numbers")
                st.markdown("• **General:** Describe what to focus on or ignore")
            
        # Show analysis status
        if st.session_state.get('generated_user_story'):
            st.success("✅ Specification analyzed! User story generated below.")
    
    # Process uploaded file
    if uploaded_file and analyze_btn:
        with st.spinner("🔄 Analyzing specification document..."):
            try:
                file_content = uploaded_file.read()
                file_type = uploaded_file.type
                
                # Get analysis instructions from the form
                analysis_instructions = st.session_state.get('analysis_instructions', '')
                
                # Process the spec file with instructions
                generated_story = process_uploaded_spec(file_content, file_type, settings, analysis_instructions)
                
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
        st.markdown("**🤖 AI-Generated User Story:**")
        st.markdown("The user story below was generated from your specification document. You can edit it before generating test cases.")
        
        col_clear, col_edit = st.columns([1, 3])
        with col_clear:
            if st.button("🗑️ Clear AI Story", type="secondary"):
                st.session_state.generated_user_story = ""
                st.rerun()
        with col_edit:
            st.markdown("💡 *Edit the story below to customize it for your needs*")
    
    user_story = st.text_area(
        "📋 Enter User Story or Functionality Description:",
        height=250,
        value=default_story,
        help="Describe the functionality you want to create test cases for. You can edit the AI-generated story above or write your own.",
        placeholder="Example: As a user, I want to login to the system so that I can access my dashboard..."
    )
    
    # Test case generation controls
    st.markdown("### 🎯 Test Case Generation")
    col_gen = st.columns([2, 1, 1])
    with col_gen[0]:
        generate_btn = st.button("🎯 Generate Test Cases", type="primary", use_container_width=True)
    with col_gen[1]:
        num_cases = st.number_input("Max Cases", min_value=1, max_value=50, value=10)
    with col_gen[2]:
        export_format = st.selectbox("Export", ["Excel", "CSV", "JSON"])

    if generate_btn:
        if user_story.strip():
            with st.spinner("🔄 Generating test cases with AI..."):
                progress_bar = st.progress(0)
                for i in range(100):
                    progress_bar.progress(i + 1)
                generated = generate_test_cases(
                    user_story,
                    int(num_cases),
                    settings,
                )
                st.session_state.generated_test_cases = generated
        else:
            st.warning("⚠️ Please enter a user story to generate test cases.")

    test_cases = st.session_state.get('generated_test_cases', [])
    if test_cases:
        st.success(f"✅ Generated {len(test_cases)} test cases successfully!")
        col_stats = st.columns(4)
        with col_stats[0]:
            st.metric("Total Cases", len(test_cases))
        with col_stats[1]:
            st.metric("Critical", len([tc for tc in test_cases if 'critical' in str(tc.test_case_id).lower()]))
        with col_stats[2]:
            st.metric("High Priority", len([tc for tc in test_cases if 'high' in str(tc.test_case_id).lower()]))
        with col_stats[3]:
            st.metric("Medium/Low", len(test_cases) - len([tc for tc in test_cases if 'critical' in str(tc.test_case_id).lower() or 'high' in str(tc.test_case_id).lower()]))
        st.markdown("---")
        for i, case in enumerate(test_cases, 1):
            priority_colors = {'critical': '🔴','high': '🟠','medium': '🟢','low': '🔵'}
            priority_icon = '🧪'
            for priority, icon in priority_colors.items():
                if priority in str(case.test_case_id).lower():
                    priority_icon = icon
                    break
            with st.expander(f"{priority_icon} Test Case {i}: {case.test_title}", expanded=False):
                col_case1, col_case2 = st.columns([1, 1])
                with col_case1:
                    st.markdown(f"**🆔 ID:** `{case.test_case_id}`")
                    st.markdown(f"**📝 Description:** {case.description}")
                    st.markdown(f"**⚙️ Preconditions:** {case.preconditions}")
                with col_case2:
                    st.markdown(f"**📊 Test Data:** {case.test_data}")
                    st.markdown(f"**✅ Expected Result:** {case.expected_result}")
                    st.markdown(f"**💬 Comments:** {case.comments}")
                st.markdown("**📋 Test Steps:**")
                st.info(case.test_steps)
        st.markdown("---")
        col_export = st.columns([1, 2, 1])
        with col_export[1]:
            try:
                if export_format == "Excel":
                    # Sử dụng template gốc (giữ nguyên format, màu sắc, font...)
                    try:
                        data = export_original_template_bytes(test_cases, settings)
                        st.download_button(
                            label="📥 Download Excel Template",
                            data=data,
                            file_name=f"TPL-QA-01-04_{settings.get('name', 'TestPlan')}_v1.0.xlsm",
                            mime="application/vnd.ms-excel.sheet.macroEnabled.12",
                            use_container_width=True,
                        )
                    except FileNotFoundError:
                        st.error("❌ Template file không tồn tại. Vui lòng đảm bảo file 'TPL-QA-01-04_Testcase_v1.3 (1).xlsm' có trong thư mục dự án.")
                    except Exception as e:
                        st.error(f"❌ Lỗi khi tạo file Excel: {str(e)}")
                        # Fallback về template mới nếu có lỗi
                        data = export_to_excel_template_bytes(test_cases, settings)
                        st.download_button(
                            label="📥 Download Excel Template (Fallback)",
                            data=data,
                            file_name=f"TPL-QA-01-04_{settings.get('name', 'TestPlan')}_v1.0.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                elif export_format == "CSV":
                    import pandas as pd
                    rows = [tc.dict() if hasattr(tc, "dict") else dict(tc) for tc in test_cases]
                    csv_data = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name="test_cases.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    rows = [tc.dict() if hasattr(tc, "dict") else dict(tc) for tc in test_cases]
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
    page = (params.get('page', ["list-project"]) or ["list-project"])[0]
    pid = params.get('id', [None])[0]
    pid = int(pid) if pid not in (None, "", []) else None
except Exception:
    page = "list-project"
    pid = None

# Handle browser back/forward navigation
current_url = f"{page}_{pid}"
if 'last_url' not in st.session_state:
    st.session_state.last_url = current_url

# Check if URL changed (browser navigation)
if st.session_state.last_url != current_url:
    # Update URL tracking
    st.session_state.last_url = current_url
    
    # Clear generated content
    if 'generated_test_cases' in st.session_state:
        del st.session_state.generated_test_cases
    if 'generated_user_story' in st.session_state:
        del st.session_state.generated_user_story
    
    # Force rerun to update the page
    st.rerun()

# Add a hidden component to detect URL changes
st.markdown("""
<script>
// Track URL changes and force reload if needed
let lastUrl = window.location.href;
setInterval(function() {
    const currentUrl = window.location.href;
    if (currentUrl !== lastUrl) {
        lastUrl = currentUrl;
        // Force reload to update Streamlit
        window.location.reload();
    }
}, 200);
</script>
""", unsafe_allow_html=True)

# Route to appropriate view
if page == 'list-project' or page == 'home':
    view_home()
elif page == 'create-project':
    view_create_project()
elif page == 'edit-project':
    view_edit_project(pid)
elif page == 'create-testcase' or page == 'create-test-case':
    view_create_test_case(pid)
else:
    # Default to list-project for unknown routes
    view_home()
