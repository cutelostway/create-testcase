# app.py - Streamlit UI
import streamlit as st
from export_to_excel import export_to_excel
from tester_agent import generate_test_cases

st.title("AI Test Case Generator")

user_story = st.text_area("Enter the user story or functionality description:")

if st.button("Generate Test Cases"):
    if user_story.strip():
        test_cases = generate_test_cases(user_story)
        export_to_excel(test_cases)
        st.success("Your test cases have been generated and exported successfully! Check your downloaded file.")
    else:
        st.warning("Please enter a user story to generate test cases.")
