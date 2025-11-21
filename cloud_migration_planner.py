"""
AI Cloud Migration Planner — SSL Bypass Edition (For Zscaler Users)
"""

# ============================================================
# 🔥 ZSCALER FIX — DISABLE SSL VERIFICATION
# ============================================================

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import urllib3
urllib3.disable_warnings()

import requests
requests.packages.urllib3.disable_warnings()

# ============================================================
# IMPORTS
# ============================================================

import os
import io
import json
import tempfile

import streamlit as st
import pandas as pd
from PIL import Image

try:
    import pdfplumber
except:
    pdfplumber = None

try:
    import pytesseract
except:
    pytesseract = None

try:
    from fpdf import FPDF
except:
    FPDF = None

try:
    from openai import OpenAI
except:
    OpenAI = None


# ============================================================
# FILE PARSERS
# ============================================================

def extract_text_from_pdf(blob: bytes):
    if pdfplumber is None:
        return "[pdfplumber not installed]"
    pages = []
    with pdfplumber.open(io.BytesIO(blob)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def extract_text_from_image(blob: bytes):
    if pytesseract is None:
        return "[pytesseract not installed]"
    img = Image.open(io.BytesIO(blob)).convert("RGB")
    return pytesseract.image_to_string(img)


def parse_csv(blob: bytes):
    return pd.read_csv(io.BytesIO(blob))


def parse_excel(blob: bytes):
    return pd.read_excel(io.BytesIO(blob), sheet_name=None)


def parse_json(blob: bytes):
    return json.loads(blob.decode("utf-8"))


# ============================================================
# OPENAI CALL — SSL BYPASSED
# ============================================================

def call_openai(system_prompt, user_prompt, model):
    api_key = st.session_state.get("OPENAI_API_KEY")

    if not api_key:
        return "[Missing API Key — enter it in the sidebar]"

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        return response.choices[0].message["content"]

    except Exception as e:
        return f"[OpenAI API call failed] {e}"


# ============================================================
# PDF GENERATOR
# ============================================================

class PDFReport:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.add_page()
        self.pdf.set_auto_page_break(auto=True, margin=15)

    def add_section(self, title, content):
        self.pdf.set_font("Arial", "B", 14)
        self.pdf.cell(0, 10, title, ln=True)
        self.pdf.set_font("Arial", "", 11)
        for line in content.split("\n"):
            self.pdf.multi_cell(0, 7, line)
        self.pdf.ln(4)

    def save(self, path):
        self.pdf.output(path)


# ============================================================
# UI THEME — DARK (Theme B)
# ============================================================

st.set_page_config(page_title="AI Cloud Migration Planner", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0f172a; color: #e2e8f0; }
h1, h2, h3, label { color: #e2e8f0 !important; }
.card { background: #1e293b; padding: 20px; border-radius: 16px; }
.stButton>button { background: #38bdf8; color: black; font-weight: 600; border-radius: 8px; }
.stDownloadButton>button { background: #34d399; color: black; font-weight: 600; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("🌙 AI Cloud Migration Planner — Zscaler Compatible Edition")


# ============================================================
# SIDEBAR — API Key + File Upload
# ============================================================

with st.sidebar:
    st.header("⚙️ Configuration")

    key_input = st.text_input("🔑 OpenAI API Key", type="password")

    if key_input:
        st.session_state["OPENAI_API_KEY"] = key_input
        st.success("API Key saved!")

    elif "OPENAI_API_KEY" not in st.session_state:
        st.warning("Please enter your OpenAI API key.")

    if st.button("🔍 Test API Key"):
        try:
            key = st.session_state.get("OPENAI_API_KEY")
            client = OpenAI(api_key=key)
            client.models.list()
            st.success("API key is valid!")
        except Exception as e:
            st.error(f"Connection error: {e}")

    uploaded_files = st.file_uploader("📤 Upload Files", accept_multiple_files=True)

    file_type = st.selectbox("Input Type", ["auto", "csv", "excel", "json", "pdf", "image", "text"])
    clouds = st.multiselect("☁ Target Clouds", ["AWS", "Azure", "GCP"], default=["Azure"])
    model = st.selectbox("🤖 Model", ["gpt-4o", "gpt-4"])


# ============================================================
# MAIN UI
# ============================================================

col1, col2 = st.columns([1, 2])
all_text = []


# File preview area
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📁 Uploaded Content Preview")

    if uploaded_files:
        for f in uploaded_files:
            blob = f.read()
            name = f.name.lower()

            if file_type == "auto":
                if name.endswith(".csv"): detected = "csv"
                elif name.endswith((".xls", ".xlsx")): detected = "excel"
                elif name.endswith(".json"): detected = "json"
                elif name.endswith(".pdf"): detected = "pdf"
                elif f.type.startswith("image/"): detected = "image"
                else: detected = "text"
            else:
                detected = file_type

            try:
                if detected == "csv":
                    df = parse_csv(blob)
                    st.dataframe(df)
                    all_text.append(df.to_csv(index=False))

                elif detected == "excel":
                    sheets = parse_excel(blob)
                    for sh, df in sheets.items():
                        st.write(f"Sheet: {sh}")
                        st.dataframe(df)
                        all_text.append(df.to_csv(index=False))

                elif detected == "json":
                    js = parse_json(blob)
                    st.json(js)
                    all_text.append(json.dumps(js))

                elif detected == "pdf":
                    txt = extract_text_from_pdf(blob)
                    st.text_area("PDF Text", txt, height=150)
                    all_text.append(txt)

                elif detected == "image":
                    st.image(Image.open(io.BytesIO(blob)))
                    txt = extract_text_from_image(blob)
                    st.text_area("OCR", txt, height=150)
                    all_text.append(txt)

                else:
                    txt = blob.decode("utf-8")
                    st.text_area("Text File", txt, height=150)
                    all_text.append(txt)

            except Exception as e:
                st.error(f"Error reading {f.name}: {e}")
    else:
        st.info("Upload files to begin.")

    st.markdown('</div>', unsafe_allow_html=True)


# MIGRATION PLAN GENERATOR
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🤖 AI Migration Plan Generator")

    ctx = st.text_area("Additional Context", height=120)

    if st.button("Generate Migration Plan"):
        combined = "\n\n---\n\n".join(all_text)

        system_prompt = """
        You are an Enterprise Cloud Migration Architect.
        Produce a full migration strategy including:
        - Cloud service mapping
        - Migration phases
        - Cost estimation
        - Timeline
        - Dependencies
        - Risks & mitigations
        - Final roadmap
        """

        user_prompt = f"""
        Input Data:
        {combined}

        Business Context:
        {ctx}

        Target Clouds: {", ".join(clouds)}
        """

        result = call_openai(system_prompt, user_prompt, model)
        st.session_state["AI_OUTPUT"] = result
        st.text_area("AI Output", result, height=400)

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PDF EXPORT
# ============================================================

st.subheader("📄 Download Report")

if "AI_OUTPUT" in st.session_state:
    if st.button("Generate PDF"):
        if FPDF is None:
            st.error("FPDF not installed.")
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

            pdf = PDFReport()
            pdf.add_section("Migration Plan", st.session_state["AI_OUTPUT"])
            pdf.save(tmp.name)

            with open(tmp.name, "rb") as f:
                st.download_button("Download PDF", f, "migration_report.pdf",
                                   mime="application/pdf")
else:
    st.info("Generate a migration plan first.")
