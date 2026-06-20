"""
FastAPI entrypoint for the Job Hunt Agent.
Exposes 3 endpoints:
  POST /analyze  — upload resume PDF + paste job descriptions as text
  GET  /results  — fetch all past results from results.db
  GET  /report   — return the latest markdown report
"""

import os
import shutil
import sqlite3
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import List
from graph.build_graph import build_graph
from graph.state import initial_state
from utils.report import REPORT_PATH, DB_PATH

app = FastAPI(
    title="Job Hunt Agent",
    description="AI-powered resume matcher and pitch generator using LangGraph + Groq",
    version="1.0.0",
)

RESUME_UPLOAD_PATH = "data/resume.pdf"
JOBS_FOLDER = "data/sample_jobs"


@app.get("/")
def root():
    return {
        "message": "Job Hunt Agent API is running",
        "endpoints": {
            "POST /analyze": "Upload resume PDF and paste job descriptions",
            "GET /results": "Fetch all past results from the database",
            "GET /report": "Get the latest markdown report",
        },
    }


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(..., description="Your resume as a PDF"),
    job_descriptions: List[str] = Form(..., description="Paste each job description as a separate field"),
):
    """
    Accepts a resume PDF and one or more job descriptions pasted as text,
    runs the full LangGraph pipeline, and returns ranked match results.
    """
    # validate resume type
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Resume must be a PDF file.")

    if not job_descriptions:
        raise HTTPException(status_code=400, detail="At least one job description is required.")

    # save uploaded resume
    os.makedirs("data", exist_ok=True)
    with open(RESUME_UPLOAD_PATH, "wb") as f:
        shutil.copyfileobj(resume.file, f)

    # clear old job files and save new ones as .txt
    os.makedirs(JOBS_FOLDER, exist_ok=True)
    for old_file in os.listdir(JOBS_FOLDER):
        os.remove(os.path.join(JOBS_FOLDER, old_file))

    for i, job_text in enumerate(job_descriptions):
        if not job_text.strip():
            continue
        job_path = os.path.join(JOBS_FOLDER, f"job_{i+1}.txt")
        with open(job_path, "w", encoding="utf-8") as f:
            f.write(job_text)

    # run the pipeline
    try:
        pipeline = build_graph()
        result = pipeline.invoke(initial_state())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

    # format response ranked by score
    matches = [
        {
            "job_title": m.job_title,
            "match_score": m.match_score,
            "matching_skills": m.matching_skills,
            "missing_skills": m.missing_skills,
            "rationale": m.rationale,
            "tailored_pitch": m.tailored_pitch,
        }
        for m in sorted(result["matches"], key=lambda x: x.match_score, reverse=True)
    ]

    return JSONResponse(content={
        "status": "success",
        "total_jobs_analyzed": len(matches),
        "errors": result.get("errors", []),
        "matches": matches,
    })


@app.get("/results")
def get_results():
    """Returns all past match results stored in results.db."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=404,
            detail="No results found yet. Run /analyze first."
        )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM match_results ORDER BY run_timestamp DESC")
    rows = cursor.fetchall()
    cols = [desc[0] for desc in cursor.description]
    conn.close()

    results = []
    for row in rows:
        data = dict(zip(cols, row))
        data["matching_skills"] = json.loads(data["matching_skills"])
        data["missing_skills"] = json.loads(data["missing_skills"])
        results.append(data)

    return JSONResponse(content={"total": len(results), "results": results})


@app.get("/report")
def get_report():
    """Returns the latest generated markdown report as plain text."""
    if not os.path.exists(REPORT_PATH):
        raise HTTPException(
            status_code=404,
            detail="No report found yet. Run /analyze first."
        )

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    return PlainTextResponse(content=content)