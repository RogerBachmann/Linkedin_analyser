import streamlit as st
import pdfplumber
import google.generativeai as genai
import re
import io

# --- Configuration & Security ---
APP_PASSWORD = "swisscareer"

# --- Page Configuration ---
st.set_page_config(
    page_title="Swiss LinkedIn Brand Optimizer", 
    page_icon="🔗", 
    layout="wide"
)

# Branded Styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #0073b1; 
        color: white; 
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #005582;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- API Initialization (Streamlit Secrets) ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception:
    st.error("🔑 GEMINI_API_KEY not found in Streamlit Secrets. Please add it to your dashboard.")
    st.stop()

@st.cache_resource
def get_best_model():
    """Finds the best available Gemini model for the user's API key (2026 Ready)."""
    priority_list = ["gemini-3-flash", "gemini-2.5-flash", "gemini-1.5-flash-latest"]
    try:
        available_models = [m.name.split('/')[-1] for m in genai.list_models() 
                           if 'generateContent' in m.supported_generation_methods]
        for model_name in priority_list:
            if model_name in available_models:
                return genai.GenerativeModel(model_name)
        return genai.GenerativeModel(available_models[0])
    except Exception:
        return genai.GenerativeModel("gemini-1.5-flash")

model_instance = get_best_model()

# --- Core Logic Functions ---

def extract_text_safe(uploaded_file):
    """Safely extracts text from the uploaded PDF stream."""
    text = ""
    try:
        # Using io.BytesIO to handle Streamlit's UploadedFile object properly
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return None

# --- User Interface ---

st.title("🇨🇭 Branded LinkedIn Profile Audit & Strategy")
st.markdown("### Specialized Swiss Life Sciences Recruiter Insights")

# Sidebar Authentication
with st.sidebar:
    st.image("https://www.linkedin.com/favicon.ico", width=50)
    st.title("Admin Access")
    auth_pass = st.text_input("Enter App Password", type="password")
    
    if auth_pass != APP_PASSWORD:
        if auth_pass:
            st.error("Incorrect Password")
        st.info("Unlock the engine to generate the branded audit.")
        st.stop()
    
    st.success("✅ Engine Connected")
    st.caption(f"Active Model: {model_instance.model_name}")

# Main Upload Area
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Profile Data")
    li_file = st.file_uploader("Upload LinkedIn PDF Export", type=["pdf"], help="Go to Profile > More > Save to PDF")

with col2:
    st.subheader("2. Target Market")
    jd_file = st.file_uploader("Upload Job Description (Optional)", type=["pdf"])
    jd_text_manual = st.text_area("Or paste JD text manually")

# Action Button
if st.button("🚀 GENERATE COMPREHENSIVE BRANDED AUDIT"):
    if not li_file:
        st.warning("Please upload a LinkedIn PDF file to begin.")
    else:
        with st.status("Recruiter AI is performing deep-dive audit...", expanded=True) as status:
            
            st.write("Reading LinkedIn Profile...")
            li_content = extract_text_safe(li_file)
            
            jd_content = ""
            if jd_file:
                jd_content = extract_text_safe(jd_file)
            elif jd_text_manual:
                jd_content = jd_text_manual
            
            if not li_content:
                st.error("Could not extract text from the LinkedIn PDF.")
                st.stop()

            st.write("Mapping LinkedIn Algorithm & Recruiter Psychologies...")
            
            # THE PROMPT - Engineered for Word Template Placeholders
            prompt = f"""
            You are a Senior Swiss Life Sciences Recruiter and Personal Branding Expert.
            Perform a professional, exhaustive audit of the provided LinkedIn Profile.

            FOR EACH SECTION BELOW, you must provide three distinct sub-sections:
            1. RECRUITER VIEW: Why human recruiters use this section (psychology, trust, verification).
            2. ALGORITHM LOGIC: How the LinkedIn search engine uses this for ranking (SEO, filters).
            3. AUDIT & STRENGTHENING: Specific, critical feedback and improvements for the candidate.

            STRUCTURE YOUR OUTPUT AS FOLLOWS:

            ## OVERALL SEARCHABILITY SCORE: [Score]/100

            ## 1. PICTURE & BANNER
            [Analysis here]

            ## 2. HEADLINE
            [Provide 3 specific optimized headline options]

            ## 3. ABOUT SECTION (SUMMARY)
            [In-depth rewrite advice]

            ## 4. EXPERIENCE (JOB DESCRIPTIONS & KPIS)
            [Focus on Life Sciences metrics: GMP, Clinical Phases, FDA/EMA, etc.]

            ## 5. SKILLS & ENDORSEMENTS
            [List 10 priority skills for the algorithm]

            ## 6. RECOMMENDATIONS
            [Strategy for social proof]

            ## 7. PUBLICATIONS, PROJECTS & EDUCATION
            [Academic and research credibility audit]

            ## 8. LANGUAGES, VOLUNTEERING & PERMITS
            [Crucial for the Swiss market: Nationality/Permit/Language levels]

            ## 9. SEO KEYWORD MATRIX
            - TOP MISSING KEYWORDS: [List from JD]
            - RECRUITER SEARCH STRINGS: [3 Boolean strings to find this person]

            ## 10. TOP 3 STRATEGIC ACTION ITEMS
            1. [Priority 1]
            2. [Priority 2]
            3. [Priority 3]

            ---
            LINKEDIN PROFILE DATA:
            {li_content[:8000]}

            TARGET JOB DESCRIPTION:
            {jd_content if jd_content else "General Swiss Life Sciences Market Standard (Pharma/Biotech/Medtech)"}
            """

            try:
                response = model_instance.generate_content(prompt)
                status.update(label="Audit Complete!", state="complete", expanded=False)
                
                st.divider()
                st.subheader("Personalized Branding Report")
                
                # Render report
                st.markdown(response.text)
                
                # Download for Word
                st.download_button(
                    label="📩 Download Report for Word Template",
                    data=response.text,
                    file_name="LinkedIn_Branded_Audit.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"AI Generation Error: {e}")
