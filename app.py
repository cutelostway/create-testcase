# app.py - Streamlit UI with Project Creation Modal
import streamlit as st
from export_to_excel import export_to_excel, export_to_excel_bytes
from tester_agent import generate_test_cases
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
    render_project_form(mode="create")

def view_edit_project(project_id: int | None):
    if not project_id:
        st.error("Không tìm thấy project để chỉnh sửa")
        return
    project = get_project(project_id)
    if not project:
        st.error("Project không tồn tại")
        return
    render_project_form(mode="edit", project=project)

def view_create_test_case(project_id: int | None):
    # Load selected project if available
    if project_id:
        project = get_project(project_id)
        if project:
            st.session_state.project_settings = project.get('settings', {})
    settings = st.session_state.get('project_settings', {})

    st.markdown(f"# 🎯 Project: {settings.get('name', 'Unnamed Project')}")

    # Test case generation interface
    st.markdown("## 🚀 Generate Test Cases")
    user_story = st.text_area(
        "📋 Enter User Story or Functionality Description:",
        height=150,
        help="Describe the functionality you want to create test cases for",
        placeholder="Example: As a user, I want to login to the system so that I can access my dashboard..."
    )
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
