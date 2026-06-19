"""
Extracts structured job requirements from job posting text files.
Same pattern as resume_parser.py: read text -> call_claude_structured -> validate.
"""

import os
import glob

from models.schemas import JobRequirements
from utils.llm_client import call_Groq_structured


JOB_REQUIREMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "company": {"type": "string"},
        "required_skills": {"type": "array", "items": {"type": "string"}},
        "nice_to_have_skills": {"type": "array", "items": {"type": "string"}},
        "seniority": {"type": "string"},
        "min_years_experience": {"type": ["number", "null"]},
        "key_responsibilities": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "company", "required_skills", "seniority", "key_responsibilities"],
}

SYSTEM_PROMPT = """You are an expert job posting parser. Extract structured
requirements from the job posting into the JobRequirements tool. Only include
information explicitly stated or clearly implied in the text. If the posting
doesn't mention a minimum years of experience, omit that field rather than guessing."""


def parse_job_posting(file_path: str) -> JobRequirements:
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    if not raw_text.strip():
        raise ValueError(f"No text found in {file_path}")

    extracted = call_Groq_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Job posting text:\n\n{raw_text}",
        schema=JOB_REQUIREMENTS_SCHEMA,
        schema_name="JobRequirements",
    )

    return JobRequirements(**extracted)


def parse_all_jobs(jobs_folder: str = "data/sample_jobs") -> list[JobRequirements]:
    job_files = glob.glob(os.path.join(jobs_folder, "*.txt"))
    if not job_files:
        raise ValueError(f"No .txt files found in {jobs_folder}")

    jobs = []
    errors = []
    for file_path in job_files:
        try:
            jobs.append(parse_job_posting(file_path))
        except Exception as e:
            errors.append(f"{file_path}: {e}")

    if errors:
        print("Some jobs failed to parse:")
        for err in errors:
            print(f"  - {err}")

    return jobs