import os
import re
import pdfplumber
import streamlit as st
import google.generativeai as genai
from collections import Counter

# --- Configuration & Secrets ---
APP_PASSWORD = "swisscareer"

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

# --- Model Discovery ---
@st.cache_resource
def get_model():
    # Priority for 2026 model versions
    options = ["gemini-3-flash", "gemini-2.5-flash", "gemini-1.5-flash-latest"]
    available = [m.name.split('/')[-1] for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    for opt in options:
        if opt in available:
            return genai.GenerativeModel(opt)
    return genai.GenerativeModel(available[0])

model = get_model()

# --- Logic Functions ---

def extract_pdf_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text

def detect_sections(text):
    sections = {"headline": "", "about": "", "experience": "", "skills": "", "education": ""}
    lower = text.lower()
    
    def get_block(start, end_list):
        start_idx = lower.find(start)
        if start_idx == -1: return ""
        end_positions = [lower.find(e, start_idx+len(start)) for e in end_list if lower.find(e, start_idx+len(start)) != -1]
        end_idx = min(end_positions) if end_positions else len(text)
        return text[start_idx:end_idx].strip()

    sections["about"] = get_block("about", ["experience", "skills", "education"])
    sections["experience"] = get_block("experience", ["skills", "education"])
    sections["skills"] = get_block("skills", ["education"])
    sections["education"] = get_block("education", [])
    sections["headline"] = "\n".join(text.split("\n")[0:3])
    return sections

def extract_jd_keywords(jd_text, top_n=40):
    words = re.findall(r"[a-zA-Z]{3,}", jd_text.lower())
    common = {"the","and","with","for","will","this","that","from","you","your","our"}
    filtered = [w for w in words if w not in common]
    return [w for w, _ in Counter(filtered).most_common(top_n)]

def keyword_stats(text, keywords):
    text_lower = text.lower()
    found = {}
    missing = []
    for kw in keywords:
        count = len(re.findall(rf"\b{re.escape(kw)}\b", text_lower))
        if count > 0: found[kw] = count
        else: missing.append(kw)
    return found, missing

# Keyword Libraries
STATIC_KEYWORDS = [
    "junior", "senior", "lead", "gmp", "glp", "gcp", "quality assurance", 
    "regulatory affairs", "clinical operations", "manufacturing", "validation",
    "sap", "project management", "lean", "six sigma", "strategy", "leadership"
]

# --- Streamlit UI ---
st.set_page_config(page_title="Swiss LinkedIn Optimizer", page_icon="🔗")
st.title("🇨🇭 Swiss LinkedIn & Job Fit Optimizer")

# Authentication
auth_pass = st.sidebar.text_input("App Password", type="password")
if auth_pass != APP_PASSWORD:
    if auth_pass: st.sidebar.error("Wrong Password")
    st.stop()

st.sidebar.success(f"AI Engine: {model.model_name}")

# File Uploads
li_file = st.file_uploader("Upload LinkedIn Profile (PDF Export)", type=["pdf"])
jd_file = st.file_uploader("Upload Job Description (PDF)", type=["pdf"])
jd_text_manual = st.text_area("Or paste JD text here")

if st.button("Analyze Searchability"):
    if not li_file:
        st.warning("Please upload your LinkedIn PDF first.")
    else:
        with st.spinner("Analyzing LinkedIn SEO..."):
            li_text = extract_pdf_text(li_file)
            sections = detect_sections(li_text)
            
            jd_text = extract_pdf_text(jd_file) if jd_file else jd_text_manual
            
            # Keywords
            all_keywords = list(set(STATIC_KEYWORDS + (extract_jd_keywords(jd_text) if jd_text else [])))
            found, missing = keyword_stats(li_text, all_keywords)
            
            #
