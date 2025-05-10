import streamlit as st
import requests
import os
from openai import OpenAI

# Load API keys from environment variables
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")  # SerpAPI key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API key

client = OpenAI(api_key=OPENAI_API_KEY)

# Function to fetch job data from SerpAPI
def fetch_google_jobs(query: str, location: str, num_results: int = 10):
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": SERPAPI_API_KEY,
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()  # Raise an error for HTTP issues
        data = response.json()

        job_results = data.get("jobs_results", [])[:num_results]
        if not job_results:
            return "No job postings found for the given query and location."

        job_listings = []
        for job in job_results:
            title = job.get("title", "N/A")
            company = job.get("company_name", "N/A")
            portal = job.get("detected_extensions", {}).get("source", "Unknown Portal")  # Fallback for portal
            job_listings.append(f"**Title:** {title}\n**Company:** {company}\n**Job Portal:** {portal}\n")

        return "\n\n---\n\n".join(job_listings)
    except requests.exceptions.RequestException as e:
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
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# Streamlit App
st.title("Job Search and Summarizer")

# Input fields for job title and location
job_title = st.text_input("Enter Job Title", placeholder="e.g., Data Scientist")
location = st.text_input("Enter Location", placeholder="e.g., New York")

# Button to trigger the search and summarization
if st.button("Search and Summarize"):
    if job_title and location:
        with st.spinner("Fetching job data..."):
            job_data = fetch_google_jobs(query=job_title, location=location)
        st.subheader("Job Listings")
        st.text(job_data)

        if "No job postings found" not in job_data and "Error" not in job_data:
            with st.spinner("Summarizing job descriptions..."):
                summary = summarize_with_gpt(job_data)
            st.subheader("Summary")
            st.text(summary)
    else:
        st.error("Please enter both Job Title and Location.")