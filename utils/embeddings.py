"""
Computes a skill similarity score between a resume profile and a job posting.
Uses Jaccard similarity on normalised skill sets — no API call needed.

In a v2 you could swap this for vector embeddings (sentence-transformers or
Voyage AI), but Jaccard is fast, free, explainable, and good enough for v1.
Being able to explain WHY you chose this and what you'd upgrade to is the
interview-worthy part.
"""

from models.schemas import ResumeProfile, JobRequirements


def normalise(skills: list[str]) -> set[str]:
    """Lowercase and strip whitespace."""
    return {s.lower().strip() for s in skills}


def skills_overlap(resume_skills: set[str], job_skills: set[str]) -> tuple[set, set]:
    """
    Partial matching — 'machine learning' matches 'machine learning and statistics'.
    Returns (matching, missing) sets.
    """
    matching = set()
    missing = set()

    for job_skill in job_skills:
        matched = any(
            job_skill in rs or rs in job_skill
            for rs in resume_skills
        )
        if matched:
            matching.add(job_skill)
        else:
            missing.add(job_skill)

    return matching, missing


def compute_skill_similarity(
    resume: ResumeProfile,
    job: JobRequirements,
) -> tuple[float, list[str], list[str]]:
    resume_skills = normalise(resume.skills)
    required_skills = normalise(job.required_skills)
    nice_to_have = normalise(job.nice_to_have_skills)

    req_matching, req_missing = skills_overlap(resume_skills, required_skills)
    nice_matching, _ = skills_overlap(resume_skills, nice_to_have)

    # weighted score: required skills matter more
    required_score = len(req_matching) / len(required_skills) if required_skills else 0
    nice_score = len(nice_matching) / len(nice_to_have) if nice_to_have else 0
    weighted_score = round((required_score * 0.8) + (nice_score * 0.2), 4)

    return weighted_score, sorted(req_matching), sorted(req_missing)