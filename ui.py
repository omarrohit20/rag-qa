import os
import streamlit as st
from src.rag_test_generator import generate_test_bundle, render_plan_md, render_scenarios_md, render_cases_md

st.title("RAG Test Generator UI")

st.header("Configuration")

model_provider = st.selectbox("Model Provider", ["groq", "cohere", "openai", "anthropic"], index=0)

groq_api_key = st.text_input("Groq API Key", type="password")
cohere_api_key = st.text_input("Cohere API Key", type="password")
openai_api_key = st.text_input("OpenAI API Key", type="password")
anthropic_api_key = st.text_input("Anthropic API Key", type="password")

jira_base_url = st.text_input("Jira Base URL")
jira_email = st.text_input("Jira Email")
jira_api_token = st.text_input("Jira API Token", type="password")

figma_token = st.text_input("Figma Token", type="password")

st.header("Inputs")

jira_jql = st.text_input("Jira JQL")
jira_project = st.text_input("Jira Project")
figma_file = st.text_input("Figma File")

demo = st.checkbox("Use Demo Data")
dry_run = st.checkbox("Dry Run (show context only)")

if st.button("Generate"):
    # Set env vars
    os.environ["MODEL_PROVIDER"] = model_provider
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
    if cohere_api_key:
        os.environ["COHERE_API_KEY"] = cohere_api_key
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    if anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    if jira_base_url:
        os.environ["JIRA_BASE_URL"] = jira_base_url
    if jira_email:
        os.environ["JIRA_EMAIL"] = jira_email
    if jira_api_token:
        os.environ["JIRA_API_TOKEN"] = jira_api_token
    if figma_token:
        os.environ["FIGMA_TOKEN"] = figma_token

    try:
        result = generate_test_bundle(jira_jql=jira_jql, jira_project=jira_project, figma_file=figma_file, demo=demo, dry_run=dry_run)
        if dry_run:
            st.subheader("Retrieved Context")
            st.text_area("Context", result, height=300)
        else:
            st.subheader("Test Plan")
            st.markdown(render_plan_md(result))
            st.subheader("Test Scenarios")
            st.markdown(render_scenarios_md(result))
            st.subheader("Test Cases")
            st.markdown(render_cases_md(result))
    except Exception as e:
        st.error(str(e))