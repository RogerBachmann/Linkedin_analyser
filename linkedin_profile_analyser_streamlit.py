import streamlit as st
import pdfplumber
import google.generativeai as genai
import re
import io

# --- Configuration ---
APP_PASSWORD = "swisscareer"

st.set_page_config(page_title="Swiss LinkedIn Fact-Based Auditor", page_icon="🔗", layout="wide")

# --- API Initialization ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception:
    st.error("🔑 API Key missing in Streamlit Secrets.")
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

# --- UI ---
st.title("🇨🇭 Branded LinkedIn Audit: Data-Driven Strategy")

auth_pass = st.sidebar.text_input("App Password", type="password")
if auth_pass != APP_PASSWORD:
    if auth_pass: st.sidebar.error("Incorrect Password")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    li_file = st.file_uploader("Upload LinkedIn PDF", type=["pdf"])
with col2:
    jd_file = st.file_uploader("Upload JD PDF (Optional)", type=["pdf"])

if st.button("🚀 Generate Fact-Based Audit"):
    if not li_file:
        st.warning("Please upload a LinkedIn PDF.")
    else:
        status = st.empty()
        status.info("⏳ Analyzing profile against Swiss Life Sciences benchmarks...")
        
        li_content = extract_text_safe(li_file)
        jd_content = extract_text_safe(jd_file) if jd_file else "Standard Swiss Pharma/Biotech Requirements"

        # PROMPT ENFORCING FACTUAL ARGUMENTS
        prompt = f"""
        You are a Senior Swiss Life Sciences Recruiter. Your task is to audit this LinkedIn profile.
        
        CRITICAL INSTRUCTION: Do not provide generic advice. Support every recommendation with 
        FACTS, STATISTICS, or RECRUITER BEHAVIOR DATA (e.g., "Profiles with X receive Y% more engagement").
        
        STRUCTURE FOR WORD TEMPLATE:
        
        ## 1. EXECUTIVE SCORECARD
        **OVERALL SCORE: [Score]/100**
        (Based on Keyword Density, SEO ranking factors, and Swiss market conversion rates.)

        ## 2. SECTION-BY-SECTION DATA AUDIT
        
        ### 2.1 VISUAL BRAND (PICTURE & BANNER)
        - **The Fact:** Profiles with professional photos receive 21x more views and 9x more connection requests.
        - **Recruiter View:** [Audit here]
        - **Algorithm Logic:** [Audit here]
        - **Strengthening Actions:** [Specific tips]

        ### 2.2 THE HEADLINE (SEO ENGINE)
        - **The Fact:** The headline is the #1 weighted field for the LinkedIn Recruiter search algorithm. 
        - **Recruiter View:** [Audit here]
        - **Algorithm Logic:** [Audit here]
        - **Strengthening Actions:** [3 Options]

        ### 2.3 ABOUT SECTION (THE CONVERTER)
        - **The Fact:** Recruiters spend an average of only 6-8 seconds on initial profile scans; the first 3 lines must convert.
        - **Recruiter View:** [Audit here]
        - **Algorithm Logic:** [Audit here]
        - **Strengthening Actions:** [Detailed rewrite]

        ### 2.4 EXPERIENCE (PROVEN IMPACT)
        - **The Fact:** Job descriptions with quantifiable KPIs (e.g., "Reduced lead time by 15%") see a 40% higher response rate in Life Sciences.
        - **Recruiter View:** [Focus on GMP, FDA, EMA compliance facts]
        - **Algorithm Logic:** [Audit here]
        - **Strengthening Actions:** [Specific KPI suggestions]

        ### 2.5 SKILLS, PUBLICATIONS & EDUCATION
        - **The Fact:** Having at least 5 relevant skills makes a profile 33x more likely to be messaged by a recruiter.
        - **Audit & Strengthening:** [Review Skill list, Education credibility, and Research/Publications]

        ### 2.6 RECOMMENDATIONS & VOLUNTEERING
        - **The Fact:** Social proof acts as a "trust multiplier" in the Swiss market, reducing perceived hiring risk.
        - **Audit & Strengthening:** [Who to contact and why]

        ## 3. SWISS MARKET SPECIFICS (FACTS ON LOCAL HIRING)
        - **Fact:** 85% of Swiss HR professionals filter by 'Work Permit' status and 'Language Proficiency' (A1-C2) immediately.
        - **Audit:** [Does the profile meet these Swiss standards?]

        ## 4. TOP 3 STRATEGIC ACTION ITEMS
        1. [Action 1]
        2. [Action 2]
        3. [Action 3]

        PROFILE: {li_content[:7000]}
        JD: {jd_content[:3000]}
        """

        try:
            response = model_instance.generate_content(prompt)
            status.empty()
            st.success("✅ Fact-Based Audit Complete")
            st.markdown(response.text)
            st.download_button("📩 Download for Word", response.text, "LinkedIn_Fact_Audit.txt")
        except Exception as e:
            st.error(f"❌ Error: {e}")
