"""
Combines embedding-based skill similarity with an LLM call to produce
a full MatchResult — score, missing skills, rationale, and tailored pitch.

Blending the two is better than trusting either alone:
- Embedding score is fast, cheap, and deterministic
- LLM adds nuanced reasoning and generates the tailored pitch
"""

import json

from models.schemas import ResumeProfile, JobRequirements, MatchResult
from utils.embeddings import compute_skill_similarity
from utils.llm_client import call_Groq_structured


MATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "job_title": {"type": "string"},
        "match_score": {"type": "number"},
        "matching_skills": {"type": "array", "items": {"type": "string"}},
        "missing_skills": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
        "tailored_pitch": {"type": "string"},
    },
    "required": [
        "job_title", "match_score", "matching_skills",
        "missing_skills", "rationale", "tailored_pitch"
    ],
}

SYSTEM_PROMPT = """You are an expert career coach and recruiter. Given a candidate's
resume profile and a job posting, produce a MatchResult that:
1. Assigns a match_score from 0-100 (use the provided embedding similarity as a
   strong signal but apply your own judgment too)
2. Lists matching and missing skills honestly — do NOT invent skills the candidate
   doesn't have
3. Writes a clear 2-sentence rationale explaining the score
4. Writes a tailored_pitch: 3 resume bullet points using only skills and experience
   from the candidate's actual profile — never invent experience

Be honest about gaps. A lower score with accurate missing skills is more useful
than an inflated score that misleads the candidate."""


def match_resume_to_job(
    resume: ResumeProfile,
    job: JobRequirements,
) -> MatchResult:
    embedding_score, matching, missing = compute_skill_similarity(resume, job)

    user_prompt = f"""
Candidate Resume Profile:
{resume.model_dump_json(indent=2)}

Job Posting:
{job.model_dump_json(indent=2)}

Embedding-based skill similarity score (0.0 to 1.0): {embedding_score}
Pre-computed matching skills: {matching}
Pre-computed missing required skills: {missing}

Use the above as strong signals. Produce the MatchResult now.
"""

    extracted = call_Groq_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=MATCH_SCHEMA,
        schema_name="MatchResult",
    )

    return MatchResult(**extracted)