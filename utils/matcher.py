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

SYSTEM_PROMPT = """You are a career coach writing tailored job application content.

STRICT RULES — violating these makes your output useless:
1. The tailored_pitch must ONLY mention skills, tools, and experiences 
   explicitly listed in the candidate's resume profile below.
2. Do NOT invent skills, experiences, or qualities not in the resume.
3. Do NOT use vague claims like "strong leadership" or "excellent communication" 
   unless explicitly listed in the resume skills.
4. If the candidate lacks a required skill, acknowledge it honestly in 
   missing_skills — do not compensate by inventing it in the pitch.
5. Every bullet in tailored_pitch must map to something real in the resume."""


def match_resume_to_job(
    resume: ResumeProfile,
    job: JobRequirements,
) -> MatchResult:
    embedding_score, matching, missing = compute_skill_similarity(resume, job)

    user_prompt = f"""
CANDIDATE RESUME PROFILE:
{resume.model_dump_json(indent=2)}

ALLOWED SKILLS FOR PITCH (use ONLY these, nothing else):
{resume.skills}

JOB POSTING:
{job.model_dump_json(indent=2)}

Embedding similarity score: {embedding_score}
Pre-computed matching skills: {matching}
Pre-computed missing required skills: {missing}

Write the tailored_pitch using ONLY skills from the ALLOWED SKILLS list above.
If a job requirement is not in the ALLOWED SKILLS list, put it in missing_skills.
Do not mention it in the pitch.
"""

    extracted = call_Groq_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=MATCH_SCHEMA,
        schema_name="MatchResult",
    )

    extracted = call_Groq_structured(
    system_prompt=SYSTEM_PROMPT,
    user_prompt=user_prompt,
    schema=MATCH_SCHEMA,
    schema_name="MatchResult",
)

    # normalise score to 0-100 range if model returned a 0-1 float
    if extracted.get("match_score", 0) <= 1.0:
        extracted["match_score"] = round(extracted["match_score"] * 100, 1)

    return MatchResult(**extracted)

    