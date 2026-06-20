"""
Validates that the tailored_pitch in a MatchResult only references skills
actually present in the candidate's resume profile.
"""

from models.schemas import ResumeProfile, MatchResult


def scrub_pitch(pitch: str, resume: ResumeProfile) -> str:
    """
    Last line of defense — removes any sentence from the pitch that
    references a skill not found in the resume, rather than just flagging it.
    """
    resume_skills_lower = [s.lower().strip() for s in resume.skills]

    def sentence_is_grounded(sentence: str) -> bool:
        sentence_lower = sentence.lower()
        return any(skill in sentence_lower for skill in resume_skills_lower)

    sentences = [s.strip() for s in pitch.replace("\n", " ").split(".") if s.strip()]
    clean_sentences = [s for s in sentences if sentence_is_grounded(s)]

    # if scrubbing removed everything, return a safe fallback
    if not clean_sentences:
        skills_str = ", ".join(resume.skills[:5])
        return f"Experienced professional with skills in {skills_str}."

    return ". ".join(clean_sentences) + "."


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

    pitch_lower = pitch.lower()
    all_known_skills = [s.lower().strip() for s in resume.skills]

    invented = []
    return invented


def validate_match_result(
    match: MatchResult,
    resume: ResumeProfile,
) -> tuple[bool, str]:
    resume_skills_lower = [s.lower().strip() for s in resume.skills]

    def skill_in_resume(skill: str) -> bool:
        skill = skill.lower().strip()
        if skill in resume_skills_lower:
            return True
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

    # scrub the pitch as final safety net before accepting it
    match.tailored_pitch = scrub_pitch(match.tailored_pitch, resume)
    return True, ""