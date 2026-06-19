# utils/mock_llm.py
def mock_call_Groq_structured(system_prompt, user_prompt, schema, schema_name, **kwargs):
    if schema_name == "JobRequirements":
        return {
            "title": "Data Scientist",
            "company": "Test Company",
            "required_skills": ["Python", "SQL", "Machine Learning"],
            "nice_to_have_skills": ["Docker", "AWS"],
            "seniority": "Entry-level",
            "min_years_experience": 1.0,
            "key_responsibilities": ["Build ML models", "Analyze data"],
        }
    if schema_name == "ResumeProfile":
        return {
            "skills": ["Python", "SQL", "Machine Learning"],
            "years_experience": 1.0,
            "past_roles": ["SDE Intern"],
            "education": "BCA-MCA, Amity University",
            "notable_projects": ["Student Performance Metrics"],
        }
    if schema_name == "MatchResult":
        return {
            "job_title": "Data Scientist",
            "match_score": 78.0,
            "matching_skills": ["Python", "SQL", "Machine Learning"],
            "missing_skills": ["AWS"],
            "rationale": "Strong Python and SQL match the core requirements. AWS experience is missing but not critical for entry level.",
            "tailored_pitch": "Built predictive ML pipelines using Python and Scikit-learn. Developed SQL-based data pipelines for ETL workflows. Deployed models using Flask and FastAPI in internship projects.",
        }
    return {}