import streamlit as st
import requests
import os
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
        portal = job.get("detected_extensions", {}).get("source", "N/A")  # Extract job portal details
        job_listings.append(f"**Title:** {title}\n**Company:** {company}\n**Job Portal:** {portal}\n")

    return "\n\n---\n\n".join(job_listings)

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

# Function to generate a sample draft resume
def generate_resume(summary: str):
    prompt = (
        "Using the following job summary, create a professional resume draft tailored to these job requirements:\n\n"
        f"{summary}\n\n"
        "The resume should include sections for Contact Information, Objective, Skills, Work Experience, and Education."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# Streamlit App
st.title("Job Search and Resume Generator")

# Input fields for job title and location
job_title = st.text_input("Enter Job Title", placeholder="e.g., Data Scientist")
location = st.text_input("Enter Location", placeholder="e.g., New York")

# Button to trigger the search and resume generation
if st.button("Search and Generate Resume"):
    if job_title and location:
        with st.spinner("Fetching the latest job postings..."):
            job_data = fetch_latest_jobs(query=job_title, location=location)
        st.subheader("Latest Job Postings")
        st.text(job_data)

        with st.spinner("Summarizing job descriptions..."):
            summary = summarize_with_gpt(job_data)
        st.subheader("Job Summary")
        st.text(summary)

        with st.spinner("Generating a sample resume..."):
            resume = generate_resume(summary)
        st.subheader("Sample Draft Resume")
        st.text(resume)
    else:
        st.error("Please enter both Job Title and Location.")