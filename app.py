# app.py - Streamlit UI with Project Creation Modal
import streamlit as st
from export_to_excel import export_to_excel
from tester_agent import generate_test_cases

# Initialize session state
if 'show_create_modal' not in st.session_state:
    st.session_state.show_create_modal = False
if 'project_created' not in st.session_state:
    st.session_state.project_created = False
if 'show_template_modal' not in st.session_state:
    st.session_state.show_template_modal = False
if 'template_type' not in st.session_state:
    st.session_state.template_type = None
if 'show_priority_modal' not in st.session_state:
    st.session_state.show_priority_modal = False

# Page configuration
st.set_page_config(page_title="AI Test Case Generator", page_icon="🧪", layout="wide")

# Load custom CSS
def load_css():
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS file not found, continue without styling

load_css()

def show_create_project_modal():
    """Display the create project modal"""
    st.markdown("""
    <div class="modal-container">
        <h2>📑 Create New Project</h2>
        <p>Configure your project settings to generate customized test cases</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize form data in session state if not exists
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'project_name': '',
            'description': '',
            'languages': ['English'],
            'writing_style': st.session_state.get('writing_style_value', ''),
            'detail_level': st.session_state.get('detail_level_value', ''),
            'testing_types': ['Functional Testing'],
            'priority_values': st.session_state.get('priority_values', {}),
            'exclusion_rules': [],
            'steps_detail': 1  # Integer index for radio button
        }
    
    # Basic Information Section
    st.markdown('<div class="section-header">📝 Basic Information</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        # A.1 Project Name (Required)
        project_name = st.text_input("Project Name *", help="Enter project name (required)", 
                                   value=st.session_state.form_data['project_name'])
        
        # A.2 Description
        description = st.text_area("Description", max_chars=500, height=100, 
                                 help="Enter project description (max 500 characters)",
                                 value=st.session_state.form_data['description'])
        
        # A.3 Test Cases Languages
        languages = st.multiselect(
            "Test Cases Languages",
            options=["Vietnamese", "English", "Chinese", "Japanese", "French", "Spanish", "German"],
            default=st.session_state.form_data['languages'],
            help="Select languages for test cases"
        )
    
    with col2:
        # A.4 Writing Style & Tone
        st.markdown("**Writing Style & Tone**")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("� Template", key="style_template", help="Choose from predefined templates"):
                st.session_state.show_template_modal = True
                st.session_state.template_type = "writing_style"
                st.rerun()
        with col_b:
            if st.button("🎯 Default", key="style_default", help="Use default settings"):
                st.session_state.writing_style_value = "Professional and context-appropriate language with clear, concise descriptions."
                st.rerun()
        with col_c:
            if st.button("🗑️ Clear", key="style_clear", help="Clear all content"):
                st.session_state.writing_style_value = ""
                st.rerun()
        
        writing_style = st.text_area("Writing Style & Tone", height=80, key="writing_style_area",
                                   value=st.session_state.get('writing_style_value', ''))
    
    # Testing Configuration Section
    st.markdown("---")
    st.markdown('<div class="section-header">🧪 Testing Configuration</div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # A.6 Testing Type
        st.markdown("**Testing Types**")
        testing_types = []
        
        test_options = [
            ("�️ UI Testing", "UI Testing"),
            ("⚙️ Functional Testing", "Functional Testing"),
            ("✅ Data Validation Testing", "Data Validation Testing"),
            ("🔒 Security Testing", "Security Testing"),
            ("⚡ Performance Testing", "Performance Testing"),
            ("♿ Accessibility Testing", "Accessibility Testing"),
            ("🔗 API/Integration Testing", "API/Integration Testing"),
            ("📱 Responsive Testing", "Responsive Testing")
        ]
        
        for display_name, value in test_options:
            if st.checkbox(display_name, value=(value in st.session_state.form_data.get('testing_types', []))):
                testing_types.append(value)
    
    with col4:
        # A.5 Detail Level
        st.markdown("**Checklist Setting - Detail Level**")
        col_d, col_e, col_f = st.columns(3)
        with col_d:
            if st.button("📋 Template", key="detail_template", help="Choose detail level template"):
                st.session_state.show_template_modal = True
                st.session_state.template_type = "detail_level"
                st.rerun()
        with col_e:
            if st.button("🎯 Default", key="detail_default", help="Use default settings"):
                st.session_state.detail_level_value = "Standard testing approach covering main scenarios and common edge cases."
                st.rerun()
        with col_f:
            if st.button("🗑️ Clear", key="detail_clear", help="Clear all content"):
                st.session_state.detail_level_value = ""
                st.rerun()
        
        detail_level = st.text_area("Detail Level", height=80, key="detail_level_area",
                                  value=st.session_state.get('detail_level_value', ''))
        
        # A.9 Test Steps Detail Level
        st.markdown("**Test Steps Detail Level**")
        steps_detail = st.radio(
            "Select detail level:",
            options=[
                "🔍 Low Detail - Key actions & results only",
                "⚖️ Medium Detail - Balanced main actions & outcomes", 
                "📋 High Detail - Comprehensive step-by-step"
            ],
            index=1,  # Default to medium detail
            help="Choose how detailed your test steps should be"
        )
    
    # A.7 Priority Levels (Full width)
    st.markdown("---")
    st.markdown('<div class="section-header">🎯 Priority Configuration</div>', unsafe_allow_html=True)
    
    col_priority = st.columns([1, 1, 1, 4])
    with col_priority[0]:
        if st.button("📋 Priority Template", key="priority_template", help="Choose priority template"):
            st.session_state.show_priority_modal = True
            st.rerun()
    with col_priority[1]:
        if st.button("🎯 Default", key="priority_default", help="Use default priority settings"):
            st.session_state.priority_values = {
                'critical': 'System blocking, data corruption, security issues',
                'high': 'Major functionality broken, significant user impact',
                'medium': 'Minor issues with workarounds available',
                'low': 'Cosmetic issues, nice-to-have improvements'
            }
            st.rerun()
    with col_priority[2]:
        if st.button("🗑️ Clear All", key="priority_clear", help="Clear all priority settings"):
            st.session_state.priority_values = {}
            st.rerun()
    
    priority_cols = st.columns(4)
    priority_values = st.session_state.get('priority_values', {})
    
    with priority_cols[0]:
        critical_priority = st.text_area("🔴 Critical Priority", height=80, key="critical",
                                        value=priority_values.get('critical', ''))
    with priority_cols[1]:
        high_priority = st.text_area("🟠 High Priority", height=80, key="high",
                                   value=priority_values.get('high', ''))
    with priority_cols[2]:
        medium_priority = st.text_area("🟢 Medium Priority", height=80, key="medium",
                                     value=priority_values.get('medium', ''))
    with priority_cols[3]:
        low_priority = st.text_area("🔵 Low Priority", height=80, key="low",
                                  value=priority_values.get('low', ''))
    
    # A.8 Exclusion Rules
    st.markdown("---")
    st.markdown('<div class="section-header">🚫 Exclusion Rules</div>', unsafe_allow_html=True)
    st.markdown("**Select what to exclude from test case generation:**")
    
    exclusion_rules = []
    exclusion_cols = st.columns(3)
    
    exclusion_options = [
        ("🖼️ Skip Common UI Sections", "Skip Common UI Sections"),
        ("⚙️ Skip Non-functional Areas", "Skip Non-functional Areas"),
        ("🔗 Skip Third-party Integrations", "Skip Third-party Integrations"),
        ("🔄 Skip Redundant Test Cases", "Skip Redundant Test Cases"),
        ("👁️ Skip Obvious Actions", "Skip Obvious Actions"),
        ("🎨 Skip Minor Visual Issues", "Skip Minor Visual Issues")
    ]
    
    for i, (display_name, value) in enumerate(exclusion_options):
        col_idx = i % 3
        with exclusion_cols[col_idx]:
            if st.checkbox(display_name, value=(value in st.session_state.form_data.get('exclusion_rules', []))):
                exclusion_rules.append(value)
    
    # Update form data in session state
    st.session_state.form_data.update({
        'project_name': project_name,
        'description': description,
        'languages': languages,
        'writing_style': writing_style,
        'detail_level': detail_level,
        'testing_types': testing_types,
        'priority_values': {
            'critical': critical_priority,
            'high': high_priority,
            'medium': medium_priority,
            'low': low_priority
        },
        'exclusion_rules': exclusion_rules,
        'steps_detail': steps_detail
    })
    
    # Form submit buttons
    st.markdown("---")
    col_submit = st.columns([1, 1, 3])
    with col_submit[0]:
        if st.button("✅ Create Project", type="primary", help="Create project with these settings"):
            if project_name.strip():
                # Save project settings to session state
                st.session_state.project_settings = {
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
                    'steps_detail': steps_detail
                }
                st.session_state.project_created = True
                st.session_state.show_create_modal = False
                # Clear form data
                del st.session_state.form_data
                st.success(f"🎉 Project '{project_name}' created successfully!")
                st.balloons()  # Add celebration effect
                st.rerun()
            else:
                st.error("❗ Project name is required!")
    
    with col_submit[1]:
        if st.button("❌ Cancel", help="Cancel and return to main page"):
            st.session_state.show_create_modal = False
            # Clear form data
            if 'form_data' in st.session_state:
                del st.session_state.form_data
            st.rerun()

def show_template_modal():
    """Show template selection modal"""
    if st.session_state.template_type == "writing_style":
        st.markdown("""
        <div class="modal-container">
            <h3>✍️ Choose Writing Style Template</h3>
            <p>Select a predefined writing style for your test cases</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show template options with descriptions
        template_choice = st.radio(
            "Select a template:",
            options=["Natural and Clear", "Professional and Context-Appropriate", "Concise and Direct"],
            index=0,
            help="Choose the writing style that best fits your project needs"
        )
        
        # Template descriptions
        templates = {
            "Natural and Clear": "Use natural, conversational language that is easy to understand. Focus on clarity and readability while maintaining a friendly tone.",
            "Professional and Context-Appropriate": "Maintain a professional tone appropriate for business environments. Use precise terminology and formal language structure.",
            "Concise and Direct": "Keep descriptions brief and to the point. Use direct language without unnecessary elaboration."
        }
        
        # Show preview
        st.info(f"**Preview:** {templates[template_choice]}")
        
        col_template = st.columns([1, 1, 3])
        with col_template[0]:
            if st.button("✅ Apply Template"):
                st.session_state.writing_style_value = templates[template_choice]
                st.session_state.show_template_modal = False
                st.success("Writing style template applied!")
                st.rerun()
        with col_template[1]:
            if st.button("❌ Cancel"):
                st.session_state.show_template_modal = False
                st.rerun()
    
    elif st.session_state.template_type == "detail_level":
        st.markdown("""
        <div class="modal-container">
            <h3>🔍 Choose Detail Level Template</h3>
            <p>Select the appropriate testing detail level for your project</p>
        </div>
        """, unsafe_allow_html=True)
        
        template_choice = st.radio(
            "Select a template:",
            options=["Comprehensive Testing (Thorough)", "Standard Testing (Balanced)", "Minimal Testing (Essential)"],
            index=1,
            help="Choose the testing depth that matches your project requirements"
        )
        
        # Template descriptions
        templates = {
            "Comprehensive Testing (Thorough)": "Include comprehensive testing with edge cases, negative testing scenarios, boundary conditions, and error handling validation.",
            "Standard Testing (Balanced)": "Cover main scenarios and common edge cases. Include positive and negative test cases for core functionality.",
            "Minimal Testing (Essential)": "Focus only on core functionality and critical paths. Test essential features and basic user workflows."
        }
        
        # Show preview
        st.info(f"**Preview:** {templates[template_choice]}")
        
        col_template = st.columns([1, 1, 3])
        with col_template[0]:
            if st.button("✅ Apply Template"):
                st.session_state.detail_level_value = templates[template_choice]
                st.session_state.show_template_modal = False
                st.success("Detail level template applied!")
                st.rerun()
        with col_template[1]:
            if st.button("❌ Cancel"):
                st.session_state.show_template_modal = False
                st.rerun()

def show_priority_modal():
    """Show priority template modal"""
    st.markdown("""
    <div class="modal-container">
        <h3>🎯 Choose Priority Template</h3>
        <p>Select the impact type that best fits your project priorities</p>
    </div>
    """, unsafe_allow_html=True)
    
    template_choice = st.radio(
        "Select impact type:",
        options=["Business Impact", "User Impact", "Data Integrity Focus"],
        index=0,
        help="Choose the priority framework that aligns with your project goals"
    )
    
    # Template definitions
    templates = {
        "Business Impact": {
            "critical": "Revenue affecting, system down, security breach, data loss",
            "high": "Major feature broken, significant user impact, business process disruption", 
            "medium": "Minor feature issues, workaround available, limited business impact",
            "low": "Cosmetic issues, nice-to-have features, minimal business impact"
        },
        "User Impact": {
            "critical": "Blocks user from completing core tasks, system unusable",
            "high": "Significantly impacts user experience, major workflow disruption",
            "medium": "Minor inconvenience to users, alternative paths available", 
            "low": "Barely noticeable to end users, cosmetic improvements"
        },
        "Data Integrity Focus": {
            "critical": "Data corruption, loss, or security vulnerability, compliance issues",
            "high": "Incorrect data processing or storage, significant data inconsistencies",
            "medium": "Data display issues or minor inconsistencies, no data loss",
            "low": "Data formatting or presentation issues, visual inconsistencies"
        }
    }
    
    # Show preview
    if template_choice:
        st.markdown("**Preview:**")
        template_data = templates[template_choice]
        
        preview_cols = st.columns(4)
        with preview_cols[0]:
            st.markdown("🔴 **Critical**")
            st.info(template_data['critical'])
        with preview_cols[1]:
            st.markdown("🟠 **High**") 
            st.info(template_data['high'])
        with preview_cols[2]:
            st.markdown("🟢 **Medium**")
            st.info(template_data['medium'])
        with preview_cols[3]:
            st.markdown("🔵 **Low**")
            st.info(template_data['low'])
    
    col_template = st.columns([1, 1, 3])
    with col_template[0]:
        if st.button("✅ Apply Template"):
            st.session_state.priority_values = templates[template_choice]
            st.session_state.show_priority_modal = False
            st.success("Priority template applied!")
            st.rerun()
    with col_template[1]:
        if st.button("❌ Cancel"):
            st.session_state.show_priority_modal = False
            st.rerun()

# Main application
st.title("🧪 AI Test Case Generator")

# Check if we need to show modals
if st.session_state.show_template_modal:
    show_template_modal()
elif st.session_state.show_priority_modal:
    show_priority_modal()
elif st.session_state.show_create_modal:
    show_create_project_modal()
else:
    # Main page content
    if not st.session_state.project_created:
        # Landing page - show create project button
        st.markdown("""
        <div class="landing-container">
            <h1 class="landing-title">🧪 AI Test Case Generator</h1>
            <p class="landing-subtitle">Create comprehensive test cases with AI-powered intelligence</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ✨ Get Started")
        st.markdown("Create your first project with customized settings to generate tailored test cases for your needs.")
        
        # Features overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **🎯 Smart Configuration**
            - Multiple languages support
            - Customizable testing types
            - Flexible detail levels
            """)
        with col2:
            st.markdown("""
            **🔧 Advanced Settings**  
            - Priority-based testing
            - Exclusion rules
            - Writing style templates
            """)
        with col3:
            st.markdown("""
            **📊 Export Options**
            - Excel export ready
            - Organized test cases
            - Professional formatting
            """)
        
        st.markdown("---")
        col_center = st.columns([2, 1, 2])
        with col_center[1]:
            if st.button("🚀 Create Project", type="primary", use_container_width=True):
                st.session_state.show_create_modal = True
                st.rerun()
    else:
        # Project created - show main functionality
        project_name = st.session_state.project_settings['name']
        st.markdown(f"# 🎯 Project: {project_name}")
        
        # Project action buttons
        col_actions = st.columns([1, 1, 1, 4])
        with col_actions[0]:
            if st.button("⚙️ Settings", help="View project configuration"):
                st.session_state.show_settings = not st.session_state.get('show_settings', False)
        with col_actions[1]:
            if st.button("📝 Edit Project", help="Modify project settings"):
                st.session_state.show_create_modal = True
                st.rerun()
        with col_actions[2]:
            if st.button("🆕 New Project", help="Create a new project"):
                st.session_state.project_created = False
                st.session_state.project_settings = {}
                st.rerun()
        
        # Show project settings if requested
        if st.session_state.get('show_settings', False):
            with st.expander("📋 Project Configuration", expanded=True):
                settings = st.session_state.project_settings
                
                col_set1, col_set2 = st.columns(2)
                with col_set1:
                    st.markdown("**📝 Basic Information**")
                    st.write(f"**Name:** {settings['name']}")
                    st.write(f"**Description:** {settings.get('description', 'No description')}")
                    st.write(f"**Languages:** {', '.join(settings.get('languages', []))}")
                    
                    st.markdown("**🧪 Testing Configuration**")
                    st.write(f"**Testing Types:** {', '.join(settings.get('testing_types', []))}")
                    st.write(f"**Steps Detail:** {settings.get('steps_detail', 'Not specified')}")
                
                with col_set2:
                    st.markdown("**✍️ Style Settings**")
                    if settings.get('writing_style'):
                        st.info(settings['writing_style'])
                    if settings.get('detail_level'):
                        st.info(settings['detail_level'])
                    
                    st.markdown("**🎯 Priority Levels**")
                    priorities = settings.get('priority_levels', {})
                    if any(priorities.values()):
                        for level, desc in priorities.items():
                            if desc:
                                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟢', 'low': '🔵'}
                                st.write(f"{emoji.get(level, '•')} **{level.title()}:** {desc}")
                
                if settings.get('exclusion_rules'):
                    st.markdown("**🚫 Exclusion Rules**")
                    st.write(', '.join(settings['exclusion_rules']))
        
        st.markdown("---")
        
        # Test case generation interface
        st.markdown("## 🚀 Generate Test Cases")
        
        # Input area with better styling
        user_story = st.text_area(
            "📋 Enter User Story or Functionality Description:",
            height=150,
            help="Describe the functionality you want to create test cases for",
            placeholder="Example: As a user, I want to login to the system so that I can access my dashboard..."
        )
        
        # Generation options
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
                    # Show progress
                    progress_bar = st.progress(0)
                    for i in range(100):
                        progress_bar.progress(i + 1)
                        
                    test_cases = generate_test_cases(user_story)
                    
                if test_cases:
                    st.success(f"✅ Generated {len(test_cases)} test cases successfully!")
                    
                    # Summary statistics
                    col_stats = st.columns(4)
                    with col_stats[0]:
                        st.metric("Total Cases", len(test_cases))
                    with col_stats[1]:
                        st.metric("Critical", len([tc for tc in test_cases if 'critical' in tc.test_case_id.lower()]))
                    with col_stats[2]:
                        st.metric("High Priority", len([tc for tc in test_cases if 'high' in tc.test_case_id.lower()]))
                    with col_stats[3]:
                        st.metric("Medium/Low", len(test_cases) - len([tc for tc in test_cases if 'critical' in tc.test_case_id.lower() or 'high' in tc.test_case_id.lower()]))
                    
                    st.markdown("---")
                    
                    # Display the test cases with better formatting
                    for i, case in enumerate(test_cases, 1):
                        # Determine priority color
                        priority_colors = {
                            'critical': '🔴',
                            'high': '🟠', 
                            'medium': '🟢',
                            'low': '🔵'
                        }
                        
                        priority_icon = '🧪'
                        for priority, icon in priority_colors.items():
                            if priority in case.test_case_id.lower():
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
                    
                    # Export section with better UI
                    col_export = st.columns([1, 2, 1])
                    with col_export[1]:
                        if st.button("📥 Export Test Cases", type="secondary", use_container_width=True):
                            try:
                                export_to_excel(test_cases)
                                st.success("🎉 Test cases exported to test_cases.xlsx successfully!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"❌ Export failed: {e}")
                else:
                    st.error("❌ Failed to generate test cases. Please try again with a different user story.")
            else:
                st.warning("⚠️ Please enter a user story to generate test cases.")
