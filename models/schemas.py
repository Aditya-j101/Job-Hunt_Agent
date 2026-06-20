from pydantic import BaseModel, Field
from typing import List, Optional


class ResumeProfile(BaseModel):
    skills: List[str]
    years_experience: float
    past_roles: List[str]
    education: str
    notable_projects: List[str]

class JobRequirements(BaseModel):
    title: str
    company: str
    required_skills: List[str]
    nice_to_have_skills: List[str] = []
    seniority: str
    min_years_experience: Optional[float] = None
    key_responsibilities: List[str]


class MatchResult(BaseModel):
    job_title: str
    match_score: float = Field(ge=0.0, le=100.0)    
    matching_skills: List[str]
    missing_skills: List[str]
    rationale: str              
    tailored_pitch: str          