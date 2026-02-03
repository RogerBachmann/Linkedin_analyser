import streamlit as st
import pdfplumber
import google.generativeai as genai
import re
import io

# --- Page Configuration ---
st.set_page_config(page_title="Swiss LinkedIn Brand Optimizer", page_icon="🔗", layout="wide")

# --- API & Security Initialization (Using Secrets) ---
try:
    # Fetch credentials from Streamlit Secrets
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # Configure Gemini
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError as e:
    st.error(f"🔑 Secret missing: {e}. Please add it to the Streamlit Secrets dashboard.")
    st.stop()
except Exception as e:
    st.error(f"❌ Initialization Error: {e}")
    st.stop()

@st.cache_resource
def get_model():
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

# --- UI Layout ---
st.title("🇨🇭 Branded LinkedIn Audit: Data-Driven Strategy")

# Sidebar Authentication using the secret
auth_pass = st.sidebar.text_input("App Password", type="password")
if auth_pass != APP_PASSWORD:
    if auth_pass: st.sidebar.error("Incorrect Password")
    st.info("Please enter the password in the sidebar to unlock.")
    st.stop()

st.sidebar.success(f"AI Engine: {model_instance.model_name}")

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
        - **The Fact:** Profiles with professional photos receive 21x more views and 9x more connection requests than those without.
        - **Recruiter View:** Used for instant credibility and personal brand alignment.
        - **Algorithm Logic:** Affects Click-Through Rate (CTR) in search results.
        - **Strengthening Actions:** [Specific tips for banner and photo]

        ### 2.2 HEADLINE
        - **The Fact:** The headline is the #1 weighted field for the LinkedIn Recruiter search algorithm; keywords here carry 3x more weight than in the 'Experience' section.
        - **Recruiter View:** Determines if they click your profile or keep scrolling.
        - **Algorithm Logic:** Primary keyword indexing field.
        - **Strengthening Actions:** [Provide 3 tiered options]

        ### 2.3 ABOUT SECTION
        - **The Fact:** Eye-tracking studies confirm recruiters spend 80% of their "scan time" on the top fold; the first 3 lines are your only 'conversion zone'.
        - **Recruiter View:** Assesses tone, motivation, and culture fit.
        - **Algorithm Logic:** Indexed for long-tail keywords.
        - **Strengthening Actions:** [Detailed rewrite advice]

        ### 2.4 PROFESSIONAL EXPERIENCE
        - **The Fact:** Job descriptions that include quantifiable KPIs see a 40% higher response rate in the Swiss Life Sciences hub.
        - **Recruiter View:** Verification of GMP, Clinical, or Regulatory impact.
        - **Algorithm Logic:** Confirms years of experience for specific job filters.
        - **Strengthening Actions:** [Provide 5 specific KPI suggestions]

        ### 2.5 SKILLS, PUBLICATIONS & EDUCATION
        - **The Fact:** LinkedIn reports that users with at least 5 relevant skills are 33x more likely to be messaged by recruiters.
        - **Recruiter View:** Verification of technical stack.
        - **Algorithm Logic:** Core filter matching for search queries.
        - **Strengthening Actions:** [List 10 priority skills]

        ### 2.6 RECOMMENDATIONS & VOLUNTEERING
        - **The Fact:** Social proof serves as a 'risk mitigator'; 3+ recent recommendations from superiors create a "trust multiplier" in the Swiss market.
        - **Audit & Strengthening:** [Who to contact and what to ask for]

        ### 2.7 LANGUAGES, PERMITS & VOLUNTEERING
        - **The Fact:** 85% of Swiss recruiters filter by 'Language Proficiency' and 'Work Permit' (B, C, EU) status immediately.
        - **Audit:** [Specific feedback on Swiss market compliance]

        ## 3. SEO KEYWORD MATRIX (JD TARGETING)
        - **Top Missing Keywords:** [List keywords missing compared to JD]
        - **Recruiter Search Strings:** [Provide 3 Boolean strings]

        ## 4. TOP 3 STRATEGIC ACTION ITEMS
        1. [Most urgent change]
        2. [High impact change]
        3. [Long-term brand change]

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
