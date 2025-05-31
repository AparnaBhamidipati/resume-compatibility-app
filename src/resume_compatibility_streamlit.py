import streamlit as st
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load API keys from Streamlit Secrets
try:
    SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except KeyError as e:
    logging.error(f"Missing key in secrets: {e}")
    st.error(f"Missing key in secrets: {e}")
    st.stop()

import PyPDF2

# Initialize OpenAI API key

def check_resume_compatibility(job_description: str, resume: str) -> str:
    """
    Calculates the compatibility score between a resume and a job description
    and provides suggestions to improve the resume.Updated code

    Args:
        job_description (str): The text content of the job description.
        resume (str): The text content of the resume.

    Returns:
        str: A formatted string containing the compatibility score and suggestions.
    """
    prompt = (
        "Given the following job description and resume, calculate a compatibility score (out of 100) "
        "and provide suggestions to improve the resume for this job:\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Resume:\n{resume}\n\n"
        "Provide the output in the following format:\n"
        "- Compatibility Score: <score>\n"
        "- Suggestions: <suggestions>"
    )

    try:
        # Call OpenAI API to calculate compatibility and provide suggestions
        response = OPENAI_API_KEY.chat.completions.create(model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calculating compatibility: {e}"

# Streamlit App
st.title("Resume Compatibility Checker")

# Input: Job Description
st.subheader("Step 1: Enter Job Description")
job_description = st.text_area("Paste the job description here", height=200)

# Input: Resume Upload
st.subheader("Step 2: Upload Your Resume")
resume_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])

# Process Resume File
resume_text = ""
if resume_file:
    if resume_file.type == "application/pdf":
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(resume_file)
        resume_text = " ".join(page.extract_text() for page in pdf_reader.pages)
    else:
        # Extract text from TXT file
        resume_text = resume_file.read().decode("utf-8")

# Button to Calculate Compatibility
if st.button("Check Compatibility"):
    if job_description.strip() and resume_text.strip():
        with st.spinner("Calculating compatibility..."):
            result = check_resume_compatibility(job_description, resume_text)
        st.subheader("Results")
        st.text(result)
    else:
        st.error("Please provide both a job description and a resume.")

# Footer
st.write("---")
st.write("Powered by OpenAI GPT-4")