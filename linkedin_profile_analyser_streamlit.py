import streamlit as st
import pdfplumber
import google.generativeai as genai
import re
from collections import Counter
import io

# --- Configuration ---
APP_PASSWORD = "swisscareer"

# --- Page Config ---
st.set_page_config(page_title="Swiss LinkedIn Optimizer", page_icon="🔗", layout="wide")

# --- API Initialization ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception:
    st.error("🔑 API Key missing. Please add it to Streamlit Secrets.")
    st.stop()

@st.cache_resource
def get_model():
    # Attempting to find the best 2026-era model
    priority = ["gemini-3-flash", "gemini-2.5-flash", "gemini-1.5-flash-latest"]
    try:
        available = [m.name.split('/')[-1] for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for opt in priority:
            if opt in available: return genai.GenerativeModel(opt)
        return genai.GenerativeModel(available[0])
    except:
        return genai.GenerativeModel("gemini-1.5-flash") # Universal fallback

model = get_model()

# --- Helper Functions ---

def extract_text_safe(uploaded_file):
    """Handles file streams safely to prevent hangs."""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def get_keywords(text):
    if not text: return []
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    common = {"the","and","for","with","will","this","that","from","your","team","role"}
    return [w for w, _ in Counter(words).most_common(30) if w not in common]

# --- UI Layout ---

st.title("🇨🇭 Swiss LinkedIn & Job Fit Optimizer")
st.markdown("---")

# Sidebar Auth
auth_pass = st.sidebar.text_input("Application Password", type="password")
if auth_pass != APP_PASSWORD:
    if auth_pass: st.sidebar.error("Incorrect Password")
    st.info("Please enter the password in the sidebar to unlock.")
    st.stop()

st.sidebar.success(f"AI Engine Active: {model.model_name}")

# Inputs
col1, col2 = st.columns(2)
with col1:
    li_file = st.file_uploader("1. Upload LinkedIn Profile (PDF)", type=["pdf"])
with col2:
    jd_file = st.file_uploader("2. Upload Job Description (PDF)", type=["pdf"])

jd_text_manual = st.text_area("Or paste JD text here (optional)")

# Analysis Button
if st.button("🚀 Analyze Now"):
    if not li_file:
        st.warning("Please upload your LinkedIn PDF.")
    else:
        # Step 1: Extraction
        status = st.empty()
        status.info("⏳ Step 1: Extracting text from PDF...")
        
        li_text = extract_text_safe(li_file)
        
        if not li_text:
            st.error("❌ Could not extract text. Is the PDF scanned or empty?")
            st.stop()
            
        jd_content = ""
        if jd_file:
            jd_content = extract_text_safe(jd_file)
        elif jd_text_manual:
            jd_content = jd_text_manual

        # Step 2: Keyword Logic
        status.info("⏳ Step 2: Mapping keywords...")
        jd_keywords = get_keywords(jd_content)
        
        # Step 3: AI Call
        status.info("⏳ Step 3: Consulting Swiss Recruiter AI...")
        
        prompt = f"""
        Context: Senior Swiss Life Sciences Recruiter.
        Task: LinkedIn SEO & Targeting Audit.
        
        PROFILE DATA:
        {li_text[:7000]}
        
        TARGET JOB DATA:
        {jd_content[:3000] if jd_content else "No JD - provide general Swiss Life Sciences optimization."}
        
        Structure:
        ### 1. Headline & SEO Audit
        ### 2. Strategic Keyword Gaps
        ### 3. Experience & Impact Review
        ### 4. Swiss Sourcing Tips
        """

        try:
            response = model.generate_content(prompt)
            status.empty() # Clear the status message
            
            # Display Results
            st.success("✅ Analysis Complete")
            st.markdown(response.text)
            
            if jd_keywords:
                st.subheader("Target Keywords for your 'Skills' section:")
                st.write(", ".join(jd_keywords))
                
            st.download_button("📩 Download Feedback", response.text, "LI_Analysis.md")
            
        except Exception as e:
            st.error(f"❌ AI Error: {e}")
