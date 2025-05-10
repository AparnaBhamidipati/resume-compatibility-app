import streamlit as st
import requests
import os
import pandas as pd  # Import pandas for tabular data handling
from openai import OpenAI

# Load API keys from environment variables
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")  # SerpAPI key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API key

client = OpenAI(api_key=OPENAI_API_KEY)

# Function to fetch the latest job postings from SerpAPI
def fetch_latest_jobs(query: str, location: str, num_results: int = 10):
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": SERPAPI_API_KEY,
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    job_results = data.get("jobs_results", [])[:num_results]
    job_listings = []
    for job in job_results:
        title = job.get("title", "N/A")
        company = job.get("company_name", "N/A")
        portal = job.get("via", "Unknown Portal")
        job_location = job.get("location", "N/A")  # Extract job location
        posting_date = job.get("detected_extensions", {}).get("posted_at", "N/A")  # Extract job posting date
        job_listings.append({
            "Title": title,
            "Company": company,
            "Portal": portal,
            "Location": job_location,
            "Posting Date": posting_date
        })

    return job_listings

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
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

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
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

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
        if job_data:
            # Convert job data to a pandas DataFrame for tabular display
            job_df = pd.DataFrame(job_data)
            st.table(job_df)  # Display the job data in a table
        else:
            st.write("No job postings found for the given query and location.")

        with st.spinner("Summarizing job descriptions..."):
            job_descriptions = "\n".join([f"{job['Title']} at {job['Company']}" for job in job_data])
            summary = summarize_with_gpt(job_descriptions)
        st.subheader("Job Summary")
        st.text(summary)

        with st.spinner("Fetching useful links for interview preparation..."):
            interview_links = get_interview_links(summary)
        st.subheader("Useful Links for Interview Preparation")
        st.text(interview_links)  # Display the links as plain text
    else:
        st.error("Please enter both Job Title and Location.")