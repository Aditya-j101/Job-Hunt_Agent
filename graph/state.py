# graph/state.py
from typing import TypedDict
from models.schemas import ResumeProfile, JobProfile, MatchResult, TailoredPitch   # ← changed this line


class AgentState(TypedDict):
    resume_profile: ResumeProfile
    jobs: list[JobProfile]
    matches: list[MatchResult]
    pitches: list[TailoredPitch]
    current_job_index: int
    retry_counts: dict[str, int]
    errors: list[str]


def initial_state() -> AgentState:
    return AgentState(
        resume_profile=None,
        jobs=[],
        matches=[],
        pitches=[],
        current_job_index=0,
        retry_counts={},
        errors=[],
    )