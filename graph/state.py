from typing import TypedDict
from models.schemas import ResumeProfile, JobRequirements, MatchResult


class AgentState(TypedDict):
    resume_profile: ResumeProfile
    jobs: list[JobRequirements]
    matches: list[MatchResult]
    current_job_index: int
    retry_counts: dict[str, int]
    errors: list[str]
    validation_passed: bool 


def initial_state() -> AgentState:
    return AgentState(
        resume_profile=None,
        jobs=[],
        matches=[],
        current_job_index=0,
        retry_counts={},
        errors=[],
    )

def initial_state() -> AgentState:
    return AgentState(
        resume_profile=None,
        jobs=[],
        matches=[],
        current_job_index=0,
        retry_counts={},
        errors=[],
        validation_passed=False,    
    )
