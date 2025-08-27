# app.py - Streamlit UI
import streamlit as st
from export_to_excel import export_to_excel
from tester_agent import generate_test_cases

st.title("AI Test Case Generator")

user_story = st.text_area("Enter the user story or functionality description:", height=150)

if st.button("Generate Test Cases"):
    if user_story.strip():
        with st.spinner("Generating test cases..."):
            test_cases = generate_test_cases(user_story)
            
        if test_cases:
            st.success(f"Generated {len(test_cases)} test cases!")
            
            # Display the test cases
            for i, case in enumerate(test_cases, 1):
                with st.expander(f"Test Case {i}: {case.test_title}"):
                    st.write(f"**ID:** {case.test_case_id}")
                    st.write(f"**Description:** {case.description}")
                    st.write(f"**Preconditions:** {case.preconditions}")
                    st.write(f"**Test Steps:** {case.test_steps}")
                    st.write(f"**Test Data:** {case.test_data}")
                    st.write(f"**Expected Result:** {case.expected_result}")
                    st.write(f"**Comments:** {case.comments}")
            
            # Export to Excel
            try:
                export_to_excel(test_cases)
                st.success("Test cases have been exported to test_cases.xlsx!")
            except Exception as e:
                st.error(f"Error exporting to Excel: {e}")
        else:
            st.error("Failed to generate test cases. Please try again with a different user story.")
    else:
        st.warning("Please enter a user story to generate test cases.")
