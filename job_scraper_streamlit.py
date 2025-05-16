import streamlit as st
import requests
import os
import pandas as pd
from openai import OpenAI
import logging
from datetime import datetime, timedelta

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

client = OpenAI(api_key=OPENAI_API_KEY)

# Helper function to parse relative dates (e.g., "2 days ago")
def parse_relative_date(date_str):
    if "day" in date_str:
        days = int(date_str.split()[0])
        return datetime.now() - timedelta(days=days)
    elif "week" in date_str:
        weeks = int(date_str.split()[0])
        return datetime.now() - timedelta(weeks=weeks)
    elif "month" in date_str:
        months = int(date_str.split()[0])
        return datetime.now() - timedelta(days=months * 30)
    elif "year" in date_str:
        years = int(date_str.split()[0])
        return datetime.now() - timedelta(days=years * 365)
    else:
        return datetime.now()  # Default to now if parsing fails

# Function to fetch the latest job postings from SerpAPI
def fetch_latest_jobs(query: str, location: str, num_results: int = 10):
    if not query.strip() or not location.strip():
        return "Job Title and Location cannot be empty."

    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": SERPAPI_API_KEY,
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        job_results = data.get("jobs_results", [])[:num_results]
        if not job_results:
            return "No job postings found for the given query and location."

        job_listings = []
        for job in job_results:
            title = job.get("title", "N/A")
            company = job.get("company_name", "N/A")
            portal = job.get("via", "Unknown Portal")
            job_location = job.get("location", "N/A")
            posting_date_str = job.get("detected_extensions", {}).get("posted_at", "N/A")
            posting_date = parse_relative_date(posting_date_str) if posting_date_str != "N/A" else datetime.min
            job_listings.append({
                "Title": title,
                "Company": company,
                "Portal": portal,
                "Location": job_location,
                "Posting Date": posting_date,
                "Posting Date (Raw)": posting_date_str  # Keep raw date for display
            })

        # Sort job listings by posting date (latest first)
        job_listings = sorted(job_listings, key=lambda x: x["Posting Date"], reverse=True)
        return job_listings
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching job data: {e}")
        return f"Error fetching job data: {e}"

# Function to calculate compatibility score and suggestions
def calculate_compatibility(job_description: str, resume_text: str):
    prompt = (
        "Given the following job description and resume, calculate a compatibility score (out of 100) "
        "and provide suggestions to improve the resume for this job:\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Resume:\n{resume_text}\n\n"
        "Provide the output in the following format:\n"
        "- Compatibility Score: <score>\n"
        "- Suggestions: <suggestions>"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error calculating compatibility: {e}")
        return f"Error calculating compatibility: {e}"

# Streamlit App
st.title("Job Search and Resume Compatibility Checker")

# Initialize session state for navigation and selected job
if "page" not in st.session_state:
    st.session_state["page"] = "job_listings"
if "selected_job" not in st.session_state:
    st.session_state["selected_job"] = None

# Job Listings Page
if st.session_state["page"] == "job_listings":
    # Input fields for job title and location
    job_title = st.text_input("Enter Job Title", placeholder="e.g., Data Scientist")
    location = st.text_input("Enter Location", placeholder="e.g., New York")

    if st.button("Search Jobs"):
        if job_title and location:
            with st.spinner("Fetching the latest job postings..."):
                job_data = fetch_latest_jobs(query=job_title, location=location)
            st.subheader("Latest Job Postings")
            if isinstance(job_data, list) and job_data:
                # Display job listings with clickable titles
                for i, job in enumerate(job_data):
                    if st.button(f"{job['Title']} at {job['Company']}"):
                        st.session_state["selected_job"] = job
                        st.session_state["page"] = "resume_checker"
                        st.experimental_rerun()
            else:
                st.write(job_data)  # Display error or no data message
        else:
            st.error("Please enter both Job Title and Location.")

# Resume Compatibility Page
elif st.session_state["page"] == "resume_checker":
    selected_job = st.session_state["selected_job"]
    if selected_job:
        st.subheader(f"Job: {selected_job['Title']} at {selected_job['Company']}")
        st.write(f"**Location:** {selected_job['Location']}")
        st.write(f"**Portal:** {selected_job['Portal']}")
        st.write(f"**Posted:** {selected_job['Posting Date (Raw)']}")

        # Upload resume
        resume_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
        if resume_file:
            # Read resume content
            if resume_file.type == "application/pdf":
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(resume_file)
                resume_text = " ".join(page.extract_text() for page in pdf_reader.pages)
            else:
                resume_text = resume_file.read().decode("utf-8")

            # Calculate compatibility
            with st.spinner("Calculating compatibility..."):
                compatibility_result = calculate_compatibility(selected_job["Title"], resume_text)
            st.subheader("Compatibility Results")
            st.text(compatibility_result)

    # Back button
    if st.button("Back to Job Listings"):
        st.session_state["page"] = "job_listings"
        st.experimental_rerun()