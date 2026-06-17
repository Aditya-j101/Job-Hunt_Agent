"""
Extracts raw text from a resume file (PDF or .txt), then uses Claude
(via forced tool-use) to convert it into a structured ResumeProfile,
validated against the Pydantic schema.
"""

import pdfplumber

from models.schemas import ResumeProfile
from utils.llm_client import call_claude_structured


def extract_text_from_file(file_path: str) -> str:
    if file_path.lower().endswith(".pdf"):
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    elif file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported resume file type: {file_path}")


RESUME_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "skills": {"type": "array", "items": {"type": "string"}},
        "years_experience": {"type": "number"},
        "past_titles": {"type": "array", "items": {"type": "string"}},
        "key_projects": {"type": "array", "items": {"type": "string"}},
        "education": {"type": "string"},
    },
    "required": ["skills", "years_experience", "past_titles", "key_projects", "education"],
}

SYSTEM_PROMPT = """You are an expert resume parser. Extract structured information
from the candidate's resume into the ResumeProfile tool. Be accurate — only include
skills, titles, and projects explicitly stated in the resume text. Do not infer or
add anything not present in the text."""


def parse_resume(file_path: str) -> ResumeProfile:
    raw_text = extract_text_from_file(file_path)
    if not raw_text.strip():
        raise ValueError(f"No text could be extracted from {file_path}")

    extracted = call_claude_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Resume text:\n\n{raw_text}",
        schema=RESUME_PROFILE_SCHEMA,
        schema_name="ResumeProfile",
    )

    return ResumeProfile(**extracted)