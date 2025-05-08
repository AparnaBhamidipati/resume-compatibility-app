from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from openai import OpenAI

# Replace with your actual API keys
SERPAPI_API_KEY = os.environ["SERPAPI_API_KEY"]  # SerpAPI key
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]  # OpenAI API key

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to fetch job data from SerpAPI
def fetch_google_jobs(query: str, location: str, num_results: int = 5):
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": SERPAPI_API_KEY,
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    job_results = data.get("jobs_results", [])[:num_results]
    summaries = []
    for job in job_results:
        title = job.get("title", "N/A")
        company = job.get("company_name", "N/A")
        desc = job.get("description", "N/A")
        summaries.append(f"<strong>Title:</strong> {title}<br><strong>Company:</strong> {company}<br><strong>Description:</strong> {desc}<br><br>")

    return "<hr>".join(summaries)

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
        # Correctly access the content attribute
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# FastAPI route for the frontend
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Job Search and Summarizer</title>
    </head>
    <body>
        <h1>Job Search and Summarizer</h1>
        <form action="/search" method="post">
            <label for="job_title">Job Title:</label><br>
            <input type="text" id="job_title" name="job_title" required><br><br>
            <label for="location">Location:</label><br>
            <input type="text" id="location" name="location" required><br><br>
            <button type="submit">Search and Summarize</button>
        </form>
    </body>
    </html>
    """

# FastAPI route to handle job search and summarization
@app.post("/search", response_class=HTMLResponse)
def search_and_summarize(job_title: str = Form(...), location: str = Form(...)):
    job_data = fetch_google_jobs(query=job_title, location=location)
    summary = summarize_with_gpt(job_data)
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Job Search Results</title>
    </head>
    <body>
        <h1>Job Search Results</h1>
        <h2>Job Listings</h2>
        <div>{job_data}</div>
        <h2>Summary</h2>
        <pre>{summary}</pre>
        <br>
        <a href="/">Go Back</a>
    </body>
    </html>
    """