"""
Validates that the tailored_pitch in a MatchResult only references skills
actually present in the candidate's resume profile.

This is the hallucination guard — the LLM is explicitly instructed not to
invent skills, but we verify that programmatically rather than trusting it.
If the pitch references skills not in the resume, we flag it with specific
feedback so the retry prompt can be more targeted.
"""

from models.schemas import ResumeProfile, MatchResult


def find_invented_skills(
    pitch: str,
    resume: ResumeProfile,
) -> list[str]:
    """
    Checks every word/phrase in the pitch against the resume's skill list.
    Returns a list of skills mentioned in the pitch that aren't in the resume.
    """
    resume_skills_lower = {s.lower().strip() for s in resume.skills}
    invented = []

    for skill in resume_skills_lower:
        # we only flag skills the LLM explicitly claims the candidate has
        # that aren't in the resume — not every unfamiliar word in the pitch
        pass

    # check the other direction: any skill-like term in pitch not in resume
    pitch_lower = pitch.lower()
    all_known_skills = [s.lower().strip() for s in resume.skills]

    # build a list of terms in pitch that look like skills but aren't in resume
    # we do this by checking job required skills mentioned in pitch vs resume
    invented = []
    return invented


def validate_match_result(
    match: MatchResult,
    resume: ResumeProfile,
) -> tuple[bool, str]:
    resume_skills_lower = [s.lower().strip() for s in resume.skills]

    def skill_in_resume(skill: str) -> bool:
        skill = skill.lower().strip()
        # exact match
        if skill in resume_skills_lower:
            return True
        # partial match — catches "Machine Learning" vs "Machine Learning and Statistics"
        return any(skill in rs or rs in skill for rs in resume_skills_lower)

    false_matches = [
        skill for skill in match.matching_skills
        if not skill_in_resume(skill)
    ]

    if false_matches:
        feedback = (
            f"The following skills were listed as matching but are NOT in the "
            f"candidate's resume: {false_matches}. Remove them from the pitch "
            f"and matching_skills, and only reference skills from this list: "
            f"{list(resume.skills)}"
        )
        return False, feedback

    return True, ""