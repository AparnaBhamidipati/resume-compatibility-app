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

# Function to summarize job descriptions using OpenAI
def summarize_with_gpt(job_descriptions: str):
    prompt = (
        "Based on the following job descriptions, summarize the most common "
        "skills, qualifications, years of experience, and leadership expectations:\n\n"
        f"{job_descriptions}\n\n"
        "Provide the summary in bullet points under relevant categories."
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
        logging.error(f"Error summarizing job descriptions: {e}")
        return f"Error summarizing job descriptions: {e}"

# Function to generate relevant interview preparation links based on the job summary
def get_interview_links(summary: str):
    prompt = (
        "Based on the following job summary, suggest useful and relevant links for preparing for interviews. "
        "Include links for technical preparation, behavioral interviews, and general interview tips:\n\n"
        f"{summary}\n\n"
        "Provide the links in the following format:\n"
        "- Topic: [Link]\n"
        "For example:\n"
        "- Behavioral Interviews: https://example.com/behavioral\n"
        "- Technical Interviews: https://example.com/technical\n"
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
        logging.error(f"Error generating interview links: {e}")
        return f"Error generating interview links: {e}"

# Streamlit App
st.title("Job Search and Interview Preparation")

# Input fields for job title and location
job_title = st.text_input("Enter Job Title", placeholder="e.g., Data Scientist")
location = st.text_input("Enter Location", placeholder="e.g., New York")

# Button to trigger the search and interview preparation links
if st.button("Search and Get Interview Preparation Links"):
    if job_title and location:
        with st.spinner("Fetching the latest job postings..."):
            job_data = fetch_latest_jobs(query=job_title, location=location)
        st.subheader("Latest Job Postings")
        if isinstance(job_data, list) and job_data:
            # Convert job data to a pandas DataFrame for tabular display
            job_df = pd.DataFrame(job_data)
            job_df = job_df.drop(columns=["Posting Date"])  # Drop parsed date for cleaner display
            st.table(job_df)  # Display the job data in a table

            # Summarize job descriptions
            with st.spinner("Summarizing job descriptions..."):
                job_descriptions = "\n".join([f"{job['Title']} at {job['Company']}" for job in job_data])
                summary = summarize_with_gpt(job_descriptions)
            st.subheader("Job Summary")
            st.text(summary)

            # Generate useful links for interview preparation
            with st.spinner("Fetching useful links for interview preparation..."):
                interview_links = get_interview_links(summary)
            st.subheader("Useful Links for Interview Preparation")
            st.text(interview_links)
        else:
            st.write(job_data)  # Display error or no data message
    else:
        st.error("Please enter both Job Title and Location.")