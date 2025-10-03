# jira_sync.py - Jira synchronization functionality
import streamlit as st
from jira import JIRA
from typing import List, Dict, Any, Optional
import json

def get_jira_credentials(project_settings: dict = None) -> Dict[str, str]:
    """Get Jira credentials from project settings or session state"""
    if project_settings:
        # Get from project settings (preferred)
        credentials = {
            'server': project_settings.get('jira_server', ''),
            'username': project_settings.get('jira_username', ''),
            'password': project_settings.get('jira_password', '')
        }
    else:
        # Fallback to session state
        credentials = st.session_state.get('jira_credentials', {})
        
        if not credentials:
            # Fallback to environment variables
            import os
            credentials = {
                'server': os.getenv('JIRA_SERVER', ''),
                'username': os.getenv('JIRA_USERNAME', ''),
                'password': os.getenv('JIRA_PASSWORD', '')
            }
    
    return credentials

def test_jira_connection(server: str, username: str, password: str) -> bool:
    """Test Jira connection with detailed error reporting"""
    try:
        # Clean server URL
        server = server.strip()
        if not server.startswith('http'):
            server = f"https://{server}"
        
        # Initialize Jira connection with timeout
        jira = JIRA(
            server=server, 
            basic_auth=(username, password),
            options={'timeout': 30}
        )
        
        # Test connection by getting user info
        user = jira.current_user()
        st.success(f"✅ Connected successfully as: {user}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        # Provide specific error messages for common issues
        if "401" in error_msg or "Unauthorized" in error_msg:
            st.error("❌ Authentication failed. Please check your username and password.")
        elif "403" in error_msg or "Forbidden" in error_msg:
            st.error("❌ Access forbidden. Please check your permissions.")
        elif "404" in error_msg or "Not Found" in error_msg:
            st.error("❌ Server not found. Please check your Jira server URL.")
        elif "timeout" in error_msg.lower():
            st.error("❌ Connection timeout. Please check your network connection and server URL.")
        elif "SSL" in error_msg or "certificate" in error_msg.lower():
            st.error("❌ SSL certificate error. Please check your server URL.")
        else:
            st.error(f"❌ Connection failed: {error_msg}")
        
        return False

def sync_test_cases_to_jira(test_cases: List[Dict[str, Any]], project_key: str, project_settings: dict = None) -> Dict[str, Any]:
    """Sync test cases to Jira as Test Execution issues"""
    credentials = get_jira_credentials(project_settings)
    
    if not all([credentials.get('server'), credentials.get('username'), credentials.get('password')]):
        return {
            'success': False,
            'message': '❌ Jira credentials not configured. Please configure in project settings.',
            'created_issues': []
        }
    
    try:
        # Clean server URL
        server = credentials['server'].strip()
        if not server.startswith('http'):
            server = f"https://{server}"
        
        # Initialize Jira connection with timeout
        jira = JIRA(
            server=server, 
            basic_auth=(credentials['username'], credentials['password']),
            options={'timeout': 30}
        )
        
        # Check project info
        test_issue_type, precondition_issue_type = debug_jira_info(jira, project_key)
        
        if not test_issue_type:
            return {
                'success': False,
                'message': f"❌ Test issue type not found in project {project_key}. Please check Xray configuration.",
                'created_issues': []
            }
        
        created_issues = []
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                # Find or create Pre-Condition
                precondition_key = None
                precondition_summary = test_case.get('preconditions', '')
                if precondition_summary and precondition_issue_type:
                    precondition_key = find_or_create_precondition(jira, project_key, precondition_summary, precondition_issue_type)
                
                # Convert test case to Xray Test format
                issue_dict = {
                    'project': {'key': project_key},
                    'summary': test_case.get('description', f'Test Case {i}'),  # Summary = Description
                    'issuetype': {'name': 'Test'},
                    'priority': {'name': get_jira_priority(test_case)},
                    'labels': ['test-case', 'automated-sync', 'xray']
                }
                
                # Add Pre-Condition link if exists
                if precondition_key:
                    issue_dict['customfield_11206'] = [precondition_key]  # Pre-Conditions association with a Test
                
                # Add Xray custom fields
                try:
                    xray_fields = get_xray_fields(test_case, project_settings)
                    issue_dict.update(xray_fields)
                except Exception as field_error:
                    st.warning(f"⚠️ Warning: Could not add custom fields for test case {i}: {str(field_error)}")
                    # Continue without custom fields
                
                # Create issue
                new_issue = jira.create_issue(fields=issue_dict)
                created_issues.append({
                    'key': new_issue.key,
                    'summary': new_issue.fields.summary,
                    'url': f"{server}/browse/{new_issue.key}",
                    'precondition': precondition_key
                })
                
            except Exception as e:
                st.error(f"❌ Failed to create test case {i}: {str(e)}")
                continue
        
        return {
            'success': True,
            'message': f"✅ Successfully synced {len(created_issues)} test cases to Jira project {project_key}",
            'created_issues': created_issues
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"❌ Failed to sync test cases: {str(e)}",
            'created_issues': []
        }

def create_jira_description(test_case: Dict[str, Any]) -> str:
    """Create Jira issue description from test case"""
    description = f"""
*Test Case ID:* {test_case.get('test_case_id', 'N/A')}

*Description:*
{test_case.get('description', 'No description provided')}

*Preconditions:*
{test_case.get('preconditions', 'No preconditions specified')}

*Test Steps:*
{test_case.get('test_steps', 'No test steps provided')}

*Test Data:*
{test_case.get('test_data', 'No test data specified')}

*Expected Result:*
{test_case.get('expected_result', 'No expected result specified')}

*Comments:*
{test_case.get('comments', 'No additional comments')}

---
*This test case was automatically synchronized from AI Test Case Generator*
"""
    return description.strip()

def get_jira_priority(test_case: Dict[str, Any]) -> str:
    """Map test case priority to Jira priority"""
    test_case_id = str(test_case.get('test_case_id', '')).lower()
    
    if 'critical' in test_case_id:
        return 'Highest'
    elif 'high' in test_case_id:
        return 'High'
    elif 'medium' in test_case_id:
        return 'Medium'
    elif 'low' in test_case_id:
        return 'Low'
    else:
        return 'Medium'

def debug_jira_info(jira_instance, project_key: str):
    """Check Jira project and field information"""
    try:
        # Get project info
        project = jira_instance.project(project_key)
        
        # Get issue types for this project
        issue_types = jira_instance.project_issue_types(project_key)
        
        # Check if Test issue type exists
        test_issue_type = None
        precondition_issue_type = None
        for it in issue_types:
            if it.name.lower() == 'test':
                test_issue_type = it
            elif it.name.lower() == 'pre-condition':
                precondition_issue_type = it
            
        return test_issue_type, precondition_issue_type
        
    except Exception as e:
        return None, None

def find_or_create_precondition(jira_instance, project_key: str, precondition_summary: str, precondition_issue_type):
    """Find existing Pre-Condition or create new one"""
    if not precondition_summary or not precondition_summary.strip():
        return None
    
    try:
        # Search for existing Pre-Condition with same summary
        jql = f'project = "{project_key}" AND issuetype = "Pre-Condition" AND summary ~ "{precondition_summary.strip()}"'
        existing_issues = jira_instance.search_issues(jql, maxResults=1)
        
        if existing_issues:
            return existing_issues[0].key
        
        # Create new Pre-Condition if not found
        precondition_dict = {
            'project': {'key': project_key},
            'summary': precondition_summary.strip(),
            'issuetype': {'name': 'Pre-Condition'},
            'labels': ['precondition', 'automated-sync']
        }
        
        new_precondition = jira_instance.create_issue(fields=precondition_dict)
        return new_precondition.key
        
    except Exception as e:
        return None

def get_xray_fields(test_case: Dict[str, Any], project_settings: dict = None) -> Dict[str, Any]:
    """Get Xray custom fields for Jira Test issue"""
    xray_fields = {}
    
    # Default Xray field IDs (based on actual Jira server fields)
    default_mapping = {
        'test_steps': 'customfield_11203'      # Manual Test Steps (any type) - includes both steps and expected results
    }
    
    # Get field mapping from project settings or use defaults
    if project_settings:
        field_mapping = {
            'test_steps': project_settings.get('xray_test_steps_field', default_mapping['test_steps'])
        }
    else:
        # Fallback to session state or defaults
        field_mapping = st.session_state.get('xray_field_mapping', default_mapping)
    
    # Test Steps (Manual Test Steps - any type) - includes both steps, expected results and test data
    test_steps = test_case.get('test_steps', '')
    expected_result = test_case.get('expected_result', '')
    test_data = test_case.get('test_data', '')
    
    if test_steps and field_mapping.get('test_steps'):
        # For Manual Test Steps field, combine steps, expected results and test data
        formatted_steps = format_test_steps_with_expected_result_and_data_for_xray(test_steps, expected_result, test_data)
        xray_fields[field_mapping['test_steps']] = formatted_steps
    
    return xray_fields

def format_test_steps_with_expected_result_and_data_for_xray(test_steps: str, expected_result: str, test_data: str) -> dict:
    """Format test steps with expected results and test data for Xray Manual Test Steps field"""
    if not test_steps and not expected_result and not test_data:
        return {}
    
    # Format test steps for Action field
    formatted_action = ""
    if test_steps:
        step_lines = test_steps.strip().split('\n')
        for i, step_line in enumerate(step_lines, 1):
            step_line = step_line.strip()
            if step_line:
                # Remove step number if present (e.g., "1. " or "1)")
                step_text = step_line
                if step_text.startswith(f"{i}. ") or step_text.startswith(f"{i}) "):
                    step_text = step_text[3:].strip()
                elif step_text.startswith(f"{i}."):
                    step_text = step_text[2:].strip()
                formatted_action += f"{i}. {step_text}\n"
        formatted_action = formatted_action.strip()
    
    # Create single step with separated fields
    step_obj = {
        "id": 1,
        "index": 1,
        "fields": {
            "Action": formatted_action,
            "Data": test_data.strip() if test_data else "",
            "Expected Result": expected_result.strip() if expected_result else ""
        },
        "attachments": [],
        "testVersionId": 1
    }
    
    return {
        "steps": [step_obj]
    }

def format_test_steps_with_expected_result_for_xray(test_steps: str, expected_result: str) -> str:
    """Format test steps with expected results for Xray Manual Test Steps field"""
    if not test_steps and not expected_result:
        return ""
    
    formatted_content = ""
    
    # Add test steps
    if test_steps:
        formatted_content += "**Test Steps:**\n"
        # Split by lines and format each step
        steps = test_steps.strip().split('\n')
        for i, step in enumerate(steps, 1):
            step = step.strip()
            if step:
                formatted_content += f"{i}. {step}\n"
        formatted_content += "\n"
    
    # Add expected result
    if expected_result:
        formatted_content += "**Expected Result:**\n"
        formatted_content += f"{expected_result.strip()}\n"
    
    return formatted_content.strip()

def format_test_steps_for_xray(test_steps: str) -> str:
    """Format test steps for Xray Test Steps field"""
    if not test_steps:
        return ""
    
    # Split by newlines and format as numbered steps
    steps = test_steps.split('\n')
    formatted_steps = []
    
    for i, step in enumerate(steps, 1):
        step = step.strip()
        if step:
            # Remove existing numbering if present
            step = step.lstrip('0123456789. ')
            formatted_steps.append(f"{i}. {step}")
    
    return '\n'.join(formatted_steps)

def get_custom_fields(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Get custom fields for Jira issue (legacy function)"""
    custom_fields = {}
    
    # Add test case specific custom fields if your Jira instance has them
    # Example:
    # custom_fields['customfield_10001'] = test_case.get('test_case_id', '')
    # custom_fields['customfield_10002'] = test_case.get('test_data', '')
    
    return custom_fields

def render_jira_credentials_form():
    """Render Jira credentials configuration form"""
    st.markdown("### 🔗 Jira Configuration")
    
    # Add help information
    with st.expander("ℹ️ Hướng dẫn cấu hình Jira", expanded=False):
        st.markdown("""
        **📋 Cách lấy thông tin Jira:**
        
        1. **Jira Server URL:** 
           - Cloud: `https://yourcompany.atlassian.net`
           - Server: `https://jira.yourcompany.com`
           - Data Center: `https://jira.yourcompany.com`
        
        2. **Username/Email:**
           - Email đăng nhập Jira của bạn
           - Ví dụ: `user@company.com`
        
        3. **Password:**
           - Mật khẩu đăng nhập Jira
           - Hoặc App Password (khuyến nghị)
        
        **🔒 Bảo mật:**
        - Khuyến nghị sử dụng App Password thay vì mật khẩu chính
        - Tạo App Password tại: Jira → Account Settings → Security → App passwords
        
        **📋 Xray Integration:**
        - Test cases sẽ được tạo với Issue Type = "Test"
        - Summary = Description từ test case
        - Action = Test Steps từ test case  
        - Data = Test Data từ test case
        - Expected Result = Expected Result từ test case
        
        **⚠️ Lưu ý:** Custom field IDs có thể khác nhau tùy theo cấu hình Xray của bạn.
        Nếu đồng bộ không thành công, vui lòng kiểm tra custom field IDs trong Jira.
        """)
    
    # Add Xray field mapping configuration
    with st.expander("⚙️ Cấu hình Xray Field Mapping", expanded=False):
        st.markdown("**Cấu hình Custom Field IDs cho Xray:**")
        
        field_mapping = st.session_state.get('xray_field_mapping', {})
        
        with st.form("xray_field_mapping_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                test_steps_field = st.text_input(
                    "Test Steps Field ID",
                    value=field_mapping.get('test_steps', 'customfield_10015'),
                    help="Custom field ID cho Test Steps/Action"
                )
                test_data_field = st.text_input(
                    "Test Data Field ID", 
                    value=field_mapping.get('test_data', 'customfield_10016'),
                    help="Custom field ID cho Test Data"
                )
            
            with col2:
                expected_result_field = st.text_input(
                    "Expected Result Field ID",
                    value=field_mapping.get('expected_result', 'customfield_10017'),
                    help="Custom field ID cho Expected Result"
                )
                test_type_field = st.text_input(
                    "Test Type Field ID",
                    value=field_mapping.get('test_type', 'customfield_10018'),
                    help="Custom field ID cho Test Type"
                )
            
            save_mapping = st.form_submit_button("💾 Lưu Field Mapping")
            
            if save_mapping:
                st.session_state.xray_field_mapping = {
                    'test_steps': test_steps_field,
                    'test_data': test_data_field,
                    'expected_result': expected_result_field,
                    'test_type': test_type_field,
                    'test_case_id': field_mapping.get('test_case_id', 'customfield_10019')
                }
                st.success("✅ Field mapping đã được lưu!")
    
    credentials = get_jira_credentials()
    
    with st.form("jira_credentials_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            server = st.text_input(
                "Jira Server URL *",
                value=credentials.get('server', ''),
                help="Enter your Jira server URL (e.g., https://yourcompany.atlassian.net)",
                placeholder="https://yourcompany.atlassian.net"
            )
            username = st.text_input(
                "Username/Email *",
                value=credentials.get('username', ''),
                help="Enter your Jira username or email",
                placeholder="user@company.com"
            )
        
        with col2:
            password = st.text_input(
                "Password *",
                value=credentials.get('password', ''),
                type="password",
                help="Enter your Jira password or App Password"
            )
            st.markdown("")
            st.markdown("")
        
        col_test, col_save, col_debug = st.columns(3)
        with col_test:
            test_connection = st.form_submit_button("🔍 Test Connection", type="secondary")
        with col_save:
            save_credentials = st.form_submit_button("💾 Save Credentials", type="primary")
        with col_debug:
            debug_project = st.form_submit_button("🔧 Debug Project", help="Check project configuration")
        
        if test_connection:
            if server and username and password:
                with st.spinner("Testing Jira connection..."):
                    if test_jira_connection(server, username, password):
                        st.success("✅ Jira connection successful!")
                    else:
                        st.error("❌ Jira connection failed!")
            else:
                st.warning("⚠️ Please fill in all required fields")
        
        if debug_project:
            if server and username and password:
                project_key = st.session_state.get('current_project_key', '')
                if project_key:
                    with st.spinner("Debugging Jira project..."):
                        try:
                            jira = JIRA(
                                server=server, 
                                basic_auth=(username, password),
                                options={'timeout': 30}
                            )
                            debug_jira_info(jira, project_key)
                        except Exception as e:
                            st.error(f"❌ Debug failed: {str(e)}")
                else:
                    st.warning("⚠️ Please select a project first to debug")
            else:
                st.error("❌ Please fill in all required fields")
        
        if save_credentials:
            if server and username and password:
                st.session_state.jira_credentials = {
                    'server': server,
                    'username': username,
                    'password': password
                }
                st.success("✅ Jira credentials saved!")
            else:
                st.error("❌ Please fill in all required fields")
