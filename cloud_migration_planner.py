import streamlit as st
import pandas as pd
from openai import OpenAI
import json
import io

st.set_page_config(page_title="AI Cloud Migration Planner", layout="wide")

# ------------------------------
# Sidebar Settings
# ------------------------------
st.sidebar.header("Configuration")

api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")

if api_key:
    st.session_state["api_key"] = api_key

uploaded_file = st.sidebar.file_uploader("📁 Upload Migration File", type=["csv", "xlsx", "json"])

cloud_target = st.sidebar.multiselect(
    "☁ Target Clouds",
    ["AWS", "Azure", "GCP"],
    default=["Azure"]
)

model = st.sidebar.selectbox("🤖 Model", ["gpt-4o", "gpt-4o-mini", "gpt-4o-mini-high"])

# ------------------------------
# App Header
# ------------------------------
st.title("🚀 AI Cloud Migration Planner – Streamlit Cloud")

if not api_key:
    st.warning("⚠ Please enter your OpenAI API Key to continue.")
    st.stop()

# Initialize OpenAI Client
client = OpenAI(api_key=api_key)

# ------------------------------
# File Preview
# ------------------------------
if uploaded_file:
    st.subheader("📄 Uploaded Content Preview")

    file_type = uploaded_file.name.lower()

    extracted_text = ""

    if file_type.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        extracted_text = df.to_csv(index=False)

    elif file_type.endswith(".xlsx"):
        sheets = pd.read_excel(uploaded_file, sheet_name=None)
        st.write("Sheets:", list(sheets.keys()))
        for name, df in sheets.items():
            st.write(f"### Sheet: {name}")
            st.dataframe(df.head())
            extracted_text += f"\n\nSheet {name}:\n{df.to_csv(index=False)}"

    elif file_type.endswith(".json"):
        data = json.load(uploaded_file)
        st.json(data)
        extracted_text = json.dumps(data, indent=2)

# ------------------------------
# Generate Migration Plan
# ------------------------------
st.subheader("🤖 AI Migration Plan Generator")

additional_context = st.text_area("Additional context (RPO/RTO, compliance, budgets, regions)…")

if st.button("Generate Migration Plan"):
    if not uploaded_file:
        st.error("Please upload a file first.")
        st.stop()

    with st.spinner("Generating migration plan…"):

        prompt = f"""
You are a senior Cloud Migration Architect.

Generate a full end-to-end migration strategy based on:

### Client Data
{extracted_text}

### Additional Context
{additional_context}

### Required Sections:
1. Cloud Service Mapping
2. Cost Estimation (monthly + yearly)
3. Migration Phases & Timeline
4. Dependency Analysis
5. Risk Assessment Table
6. Final Migration Roadmap Summary

Target clouds: {cloud_target}
"""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a world-class cloud migration expert."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=3000,
            )

            output = response.choices[0].message.content
            st.subheader("📘 AI Output")
            st.text_area("Migration Plan", output, height=600)

            st.session_state["migration_output"] = output

        except Exception as e:
            st.error(f"❌ Error: {e}")
