"""
Tests for LangGraph node functions.
All LLM calls and file I/O are mocked so:
  - tests run instantly with no API cost
  - tests are deterministic (no LLM variance)
  - the conditional retry edge is tested without needing real retries
"""

import pytest
from unittest.mock import patch, MagicMock
from models.schemas import ResumeProfile, JobRequirements, MatchResult
from graph.state import initial_state


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_resume():
    return ResumeProfile(
        skills=["Python", "SQL", "Machine Learning", "Docker"],
        years_experience=1.0,
        past_roles=["SDE Intern at Auxiliobits"],
        education="BCA-MCA, Amity University",
        notable_projects=["Student Performance Metrics"],
    )


@pytest.fixture
def sample_job():
    return JobRequirements(
        title="Data Scientist",
        company="Test Corp",
        required_skills=["Python", "SQL", "Machine Learning"],
        nice_to_have_skills=["Docker", "AWS"],
        seniority="Entry-level",
        key_responsibilities=["Build ML models", "Analyse data"],
    )


@pytest.fixture
def sample_match(sample_job):
    return MatchResult(
        job_title=sample_job.title,
        match_score=75.0,
        matching_skills=["Python", "SQL", "Machine Learning"],
        missing_skills=["AWS"],
        rationale="Good match on core skills.",
        tailored_pitch="Built ML pipelines using Python and Scikit-learn.",
    )


# ── parse_resume_node ──────────────────────────────────────────────────────────

class TestParseResumeNode:
    def test_successful_parse(self, sample_resume):
        from graph.nodes import parse_resume_node

        with patch("graph.nodes.parse_resume", return_value=sample_resume):
            state = initial_state()
            result = parse_resume_node(state)

        assert result["resume_profile"] == sample_resume

    def test_parse_failure_adds_to_errors(self):
        from graph.nodes import parse_resume_node

        with patch("graph.nodes.parse_resume", side_effect=Exception("PDF read error")):
            state = initial_state()
            result = parse_resume_node(state)

        assert len(result["errors"]) == 1
        assert "parse_resume_node failed" in result["errors"][0]

    def test_parse_failure_does_not_crash_graph(self):
        from graph.nodes import parse_resume_node

        with patch("graph.nodes.parse_resume", side_effect=Exception("fail")):
            state = initial_state()
            result = parse_resume_node(state)

        # graph should continue — error collected, not raised
        assert "errors" in result


# ── parse_jobs_node ────────────────────────────────────────────────────────────

class TestParseJobsNode:
    def test_successful_parse(self, sample_job):
        from graph.nodes import parse_jobs_node

        with patch("graph.nodes.parse_all_jobs", return_value=[sample_job]):
            state = initial_state()
            result = parse_jobs_node(state)

        assert len(result["jobs"]) == 1
        assert result["jobs"][0].title == "Data Scientist"

    def test_multiple_jobs_parsed(self, sample_job):
        from graph.nodes import parse_jobs_node

        with patch("graph.nodes.parse_all_jobs", return_value=[sample_job, sample_job]):
            state = initial_state()
            result = parse_jobs_node(state)

        assert len(result["jobs"]) == 2

    def test_parse_failure_adds_to_errors(self):
        from graph.nodes import parse_jobs_node

        with patch("graph.nodes.parse_all_jobs", side_effect=Exception("No .txt files found")):
            state = initial_state()
            result = parse_jobs_node(state)

        assert len(result["errors"]) == 1
        assert "parse_jobs_node failed" in result["errors"][0]


# ── score_match_node ───────────────────────────────────────────────────────────

class TestScoreMatchNode:
    def test_produces_match_per_job(self, sample_resume, sample_job, sample_match):
        from graph.nodes import score_match_node

        with patch("graph.nodes.match_resume_to_job", return_value=sample_match):
            state = initial_state()
            state["resume_profile"] = sample_resume
            state["jobs"] = [sample_job, sample_job]
            result = score_match_node(state)

        assert len(result["matches"]) == 2

    def test_failed_match_adds_error_not_crash(self, sample_resume, sample_job):
        from graph.nodes import score_match_node

        with patch("graph.nodes.match_resume_to_job", side_effect=Exception("LLM error")):
            state = initial_state()
            state["resume_profile"] = sample_resume
            state["jobs"] = [sample_job]
            result = score_match_node(state)

        assert len(result["errors"]) == 1
        assert len(result["matches"]) == 0


# ── validate_pitch_node ────────────────────────────────────────────────────────

class TestValidatePitchNode:
    def test_valid_pitch_sets_validation_passed(self, sample_resume, sample_match):
        from graph.nodes import validate_pitch_node

        # mock validator to return valid
        with patch("graph.nodes.validate_match_result", return_value=(True, "")):
            state = initial_state()
            state["resume_profile"] = sample_resume
            state["matches"] = [sample_match]
            result = validate_pitch_node(state)

        assert result["validation_passed"] is True
        assert result["errors"] == []

    def test_invalid_pitch_sets_validation_failed(self, sample_resume, sample_match):
        from graph.nodes import validate_pitch_node

        with patch(
            "graph.nodes.validate_match_result",
            return_value=(False, "Skill 'Kubernetes' not in resume")
        ):
            state = initial_state()
            state["resume_profile"] = sample_resume
            state["matches"] = [sample_match]
            result = validate_pitch_node(state)

        assert result["validation_passed"] is False
        assert len(result["errors"]) == 1

    def test_retry_count_increments(self, sample_resume, sample_match):
        from graph.nodes import validate_pitch_node

        with patch(
            "graph.nodes.validate_match_result",
            return_value=(False, "hallucinated skill")
        ):
            state = initial_state()
            state["resume_profile"] = sample_resume
            state["matches"] = [sample_match]
            state["retry_counts"] = {"Data Scientist_0": 1}
            result = validate_pitch_node(state)

        assert result["retry_counts"]["Data Scientist_0"] == 2

    def test_max_retries_exhausted_keeps_best_attempt(self, sample_resume, sample_match):
        from graph.nodes import validate_pitch_node

        with patch(
            "graph.nodes.validate_match_result",
            return_value=(False, "hallucinated skill")
        ):
            state = initial_state()
            state["resume_profile"] = sample_resume
            state["matches"] = [sample_match]
            # already at max retries
            state["retry_counts"] = {"Data Scientist_0": 2}
            result = validate_pitch_node(state)

        # should not increment further, should log exhaustion message
        assert any("keeping best attempt" in e for e in result["errors"])


# ── graph conditional edge ─────────────────────────────────────────────────────

class TestConditionalEdge:
    def test_routes_to_done_when_valid(self):
        from graph.build_graph import should_retry

        state = initial_state()
        state["validation_passed"] = True
        assert should_retry(state) == "done"

    def test_routes_to_retry_when_invalid(self):
        from graph.build_graph import should_retry

        state = initial_state()
        state["validation_passed"] = False
        assert should_retry(state) == "retry"

    def test_defaults_to_done_when_key_missing(self):
        from graph.build_graph import should_retry

        # pass a plain dict without validation_passed to test the true default
        state = {"errors": [], "matches": [], "retry_counts": {}}
        assert should_retry(state) == "done"