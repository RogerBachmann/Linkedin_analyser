import streamlit as st
import pdfplumber
import google.generativeai as genai
import re
import io

# --- Configuration ---
APP_PASSWORD = "swisscareer"

st.set_page_config(page_title="Swiss LinkedIn Brand Optimizer", page_icon="🔗", layout="wide")

# --- API Initialization ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception:
    st.error("🔑 API Key missing in Streamlit Secrets.")
    st.stop()

@st.cache_resource
def get_model():
    # Attempt to load the highest performing model available to the key
    priority = ["gemini-3-flash", "gemini-2.5-flash", "gemini-1.5-flash-latest"]
    try:
        available = [m.name.split('/')[-1] for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for opt in priority:
            if opt in available: return genai.GenerativeModel(opt)
        return genai.GenerativeModel(available[0])
    except:
        return genai.GenerativeModel("gemini-1.5-flash")

model_instance = get_model()

def extract_text_safe(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text: text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# --- UI ---
st.title("🇨🇭 Branded LinkedIn Audit: Fact-Based Strategy")

# Sidebar Auth
auth_pass = st.sidebar.text_input("App Password", type="password")
if auth_pass != APP_PASSWORD:
    if auth_pass: st.sidebar.error("Incorrect Password")
    st.info("Please enter the password in the sidebar to unlock.")
    st.stop()

st.sidebar.success(f"AI Engine: {model_instance.model_name}")

# Inputs
col1, col2 = st.columns(2)
with col1:
    st.subheader("LinkedIn Profile")
    li_file = st.file_uploader("Upload Profile PDF", type=["pdf"])

with col2:
    st.subheader("Job Description")
    jd_file = st.file_uploader("Upload JD PDF (Optional)", type=["pdf"])
    jd_text_manual = st.text_area("Or paste JD text here", height=200)

if st.button("🚀 Generate Fact-Based Audit"):
    if not li_file:
        st.warning("Please upload a LinkedIn PDF.")
    else:
        status = st.empty()
        status.info("⏳ Analyzing profile against Swiss Life Sciences benchmarks...")
        
        li_content = extract_text_safe(li_file)
        
        # Logic to handle both file and text area for JD
        if jd_file:
            jd_content = extract_text_safe(jd_file)
        else:
            jd_content = jd_text_manual if jd_text_manual.strip() else "Standard Swiss Pharma/Biotech Requirements"

        # FACT-DRIVEN PROMPT
        prompt = f"""
        You are a Senior Swiss Life Sciences Recruiter. Audit this LinkedIn profile using only facts and data-driven arguments.
        
        CRITICAL: For every section, you must start with a 'The Fact' statement (industry statistics or recruiter behavior data).
        
        STRUCTURE FOR WORD TEMPLATE:
        
        ## 1. EXECUTIVE SCORECARD
        **OVERALL SCORE: [Score]/100**
        (Based on Keyword Density, SEO ranking factors, and Swiss market conversion rates.)

        ## 2. COMPREHENSIVE SECTION AUDIT
        
        ### 2.1 PICTURE & BANNER
        - **The Fact:** Profiles with professional photos receive 21x more views and 9x more connection requests.
        - **Recruiter View:** [Audit]
        - **Algorithm Logic:** Affects Click-Through Rate (CTR).
        - **Strengthening Actions:** [Specific tips]

        ### 2.2 HEADLINE
        - **The Fact:** The headline is the #1 weighted field for the LinkedIn Recruiter search algorithm; keywords here carry 3x more weight than in the 'Experience' section.
        - **Recruiter View:** [Audit]
        - **Algorithm Logic:** Keyword matching.
        - **Strengthening Actions:** [3 Options]

        ### 2.3 ABOUT SECTION
        - **The Fact:** Heatmap studies show recruiters spend 80% of their "scan time" on the top fold of a profile; the first 3 lines are the 'conversion zone'.
        - **Recruiter View:** [Audit]
        - **Algorithm Logic:** Long-tail indexing.
        - **Strengthening Actions:** [Drafting instructions]

        ### 2.4 EXPERIENCE
        - **The Fact:** Profiles using the 'Action-Result-Impact' framework with quantifiable metrics (KPIs) see a 40% higher response rate in the Swiss Life Sciences hub.
        - **Recruiter View:** [Focus on GMP/Reg Affairs/Clinical specifics]
        - **Algorithm Logic:** Verification of years of experience filters.
        - **Strengthening Actions:** [KPI suggestions]

        ### 2.5 SKILLS, PUBLICATIONS & EDUCATION
        - **The Fact:** LinkedIn reports that users with at least 5 relevant skills are 33x more likely to be contacted by recruiters.
        - **Recruiter View:** Technical validation.
        - **Algorithm Logic:** Direct filter matching.
        - **Strengthening Actions:** [List 10 priority skills]

        ### 2.6 RECOMMENDATIONS
        - **The Fact:** Social proof serves as a 'risk mitigator'; profiles with 3+ recommendations from superiors have a significantly higher trust score in Swiss hiring.
        - **Audit & Strengthening:** [Who to ask]

        ### 2.7 LANGUAGES, PERMITS & VOLUNTEERING
        - **The Fact:** 85% of Swiss recruiters filter by 'Language Proficiency' (A1-C2) and 'Work Permit' status immediately to avoid legal/logistic bottlenecks.
        - **Audit:** [Strengthen based on Swiss standards]

        ## 3. SEO KEYWORD MATRIX (JD TARGETING)
        - **Top Missing Keywords:** [List keywords missing compared to JD]
        - **Recruiter Search Strings:** [3 Boolean strings to find this person]

        ## 4. TOP 3 STRATEGIC ACTION ITEMS
        1. [Most urgent]
        2. [Second most urgent]
        3. [Long-term brand tip]

        PROFILE: {li_content[:7000]}
        JD: {jd_content[:3000]}
        """

        try:
            response = model_instance.generate_content(prompt)
            status.empty()
            st.success("✅ Analysis Complete")
            st.markdown(response.text)
            st.download_button("📩 Download Report", response.text, "LinkedIn_Audit_Report.txt")
        except Exception as e:
            st.error(f"❌ AI Error: {e}")
