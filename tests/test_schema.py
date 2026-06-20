"""
Tests for Pydantic schema validation.
These run instantly with no API calls — pure data validation.
"""

import pytest
from pydantic import ValidationError
from models.schemas import ResumeProfile, JobRequirements, MatchResult


class TestResumeProfile:
    def test_valid_resume_profile(self):
        profile = ResumeProfile(
            skills=["Python", "SQL", "Machine Learning"],
            years_experience=1.0,
            past_roles=["SDE Intern"],
            education="BCA-MCA, Amity University",
            notable_projects=["Student Performance Metrics"],
        )
        assert profile.skills == ["Python", "SQL", "Machine Learning"]
        assert profile.years_experience == 1.0

    def test_empty_skills_list_is_valid(self):
        # empty list is valid — parser might return empty for a sparse resume
        profile = ResumeProfile(
            skills=[],
            years_experience=0.0,
            past_roles=[],
            education="BCA-MCA, Amity University",
            notable_projects=[],
        )
        assert profile.skills == []

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            ResumeProfile(
                skills=["Python"],
                years_experience=1.0,
                # missing past_roles, education, notable_projects
            )

    def test_invalid_years_experience_type_raises(self):
        with pytest.raises(ValidationError):
            ResumeProfile(
                skills=["Python"],
                years_experience="not-a-number",  # should be float
                past_roles=["Intern"],
                education="B.Tech",
                notable_projects=[],
            )


class TestJobRequirements:
    def test_valid_job_requirements(self):
        job = JobRequirements(
            title="Data Scientist",
            company="Test Corp",
            required_skills=["Python", "SQL"],
            seniority="Entry-level",
            key_responsibilities=["Build models", "Analyse data"],
        )
        assert job.title == "Data Scientist"
        assert job.nice_to_have_skills == []  # default
        assert job.min_years_experience is None  # default

    def test_optional_fields_default_correctly(self):
        job = JobRequirements(
            title="Analyst",
            company="Corp",
            required_skills=["Excel"],
            seniority="Junior",
            key_responsibilities=["Report"],
        )
        assert job.nice_to_have_skills == []
        assert job.min_years_experience is None

    def test_missing_company_raises(self):
        with pytest.raises(ValidationError):
            JobRequirements(
                title="Data Scientist",
                # missing company
                required_skills=["Python"],
                seniority="Junior",
                key_responsibilities=["Analyse"],
            )


class TestMatchResult:
    def test_valid_match_result(self):
        result = MatchResult(
            job_title="Data Scientist",
            match_score=75.0,
            matching_skills=["Python", "SQL"],
            missing_skills=["Tableau"],
            rationale="Good match on core skills.",
            tailored_pitch="Built ML pipelines using Python.",
        )
        assert result.match_score == 75.0
        assert result.job_title == "Data Scientist"
        assert "Python" in result.matching_skills

    def test_score_above_100_raises(self):
        with pytest.raises(ValidationError):
            MatchResult(
                job_title="DS",
                match_score=150.0,  # should be 0-100
                matching_skills=[],
                missing_skills=[],
                rationale="Test",
                tailored_pitch="Test",
            )

    def test_score_below_0_raises(self):
        with pytest.raises(ValidationError):
            MatchResult(
                job_title="DS",
                match_score=-5.0,  # invalid
                matching_skills=[],
                missing_skills=[],
                rationale="Test",
                tailored_pitch="Test",
            )