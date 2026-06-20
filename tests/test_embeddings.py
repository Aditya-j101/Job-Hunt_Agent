"""
Tests for embedding-based skill similarity scoring.
Pure math — no API calls, runs instantly.
"""

import pytest
from models.schemas import ResumeProfile, JobRequirements
from utils.embeddings import (
    normalise,
    skills_overlap,
    compute_skill_similarity,
)


def make_resume(skills: list[str]) -> ResumeProfile:
    return ResumeProfile(
        skills=skills,
        years_experience=1.0,
        past_roles=["Intern"],
        education="B.Tech",
        notable_projects=["Project A"],
    )


def make_job(required: list[str], nice: list[str] = []) -> JobRequirements:
    return JobRequirements(
        title="Data Scientist",
        company="Test Corp",
        required_skills=required,
        nice_to_have_skills=nice,
        seniority="Entry-level",
        key_responsibilities=["Build models"],
    )


class TestNormalise:
    def test_lowercases_skills(self):
        result = normalise(["Python", "SQL", "MACHINE LEARNING"])
        assert "python" in result
        assert "sql" in result
        assert "machine learning" in result

    def test_strips_whitespace(self):
        result = normalise(["  Python  ", " SQL "])
        assert "python" in result
        assert "sql" in result

    def test_empty_list(self):
        assert normalise([]) == set()


class TestSkillsOverlap:
    def test_exact_match(self):
        resume = {"python", "sql", "machine learning"}
        job = {"python", "sql"}
        matching, missing = skills_overlap(resume, job)
        assert "python" in matching
        assert "sql" in matching
        assert len(missing) == 0

    def test_partial_match(self):
        # "machine learning" should match "machine learning and statistics"
        resume = {"machine learning and statistics", "python"}
        job = {"machine learning", "python"}
        matching, missing = skills_overlap(resume, job)
        assert "machine learning" in matching
        assert "python" in matching
        assert len(missing) == 0

    def test_no_match(self):
        resume = {"python", "sql"}
        job = {"tableau", "powerpoint"}
        matching, missing = skills_overlap(resume, job)
        assert len(matching) == 0
        assert "tableau" in missing
        assert "powerpoint" in missing


class TestComputeSkillSimilarity:
    def test_perfect_required_match(self):
        resume = make_resume(["Python", "SQL", "Machine Learning"])
        job = make_job(required=["Python", "SQL", "Machine Learning"])
        score, matching, missing = compute_skill_similarity(resume, job)
        assert score > 0.7
        assert len(missing) == 0

    def test_no_match_returns_low_score(self):
        resume = make_resume(["Excel", "PowerPoint"])
        job = make_job(required=["Python", "SQL", "TensorFlow"])
        score, matching, missing = compute_skill_similarity(resume, job)
        assert score < 0.2
        assert len(missing) > 0

    def test_required_skills_weighted_more_than_nice_to_have(self):
        # resume has all nice-to-have but no required skills
        resume = make_resume(["Docker", "AWS"])
        job = make_job(
            required=["Python", "SQL"],
            nice=["Docker", "AWS"]
        )
        score, _, _ = compute_skill_similarity(resume, job)
        # score should be low since required skills are missing
        assert score < 0.5

    def test_empty_job_skills_returns_zero(self):
        resume = make_resume(["Python"])
        job = make_job(required=[])
        score, matching, missing = compute_skill_similarity(resume, job)
        assert score == 0.0