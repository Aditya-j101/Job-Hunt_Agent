from utils.resume_parser import parse_resume
from utils.job_parser import parse_all_jobs
from utils.matcher import match_resume_to_job
from utils.validator import validate_match_result
from utils.report import save_results_to_db, generate_markdown_report, save_report

RESUME_FILE_PATH = "data/resume.pdf"  # adjust to wherever your resume actually is
MAX_RETRIES = 2


def parse_resume_node(state):
    try:
        profile = parse_resume(RESUME_FILE_PATH)
        return {"resume_profile": profile}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"parse_resume_node failed: {e}"]}
    
def parse_jobs_node(state):
    try:
        jobs = parse_all_jobs()
        return {"jobs": jobs}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"parse_jobs_node failed: {e}"]}
    
def score_match_node(state):
    resume = state["resume_profile"]
    jobs = state["jobs"]
    matches = []
    errors = state.get("errors", [])

    for job in jobs:
        try:
            result = match_resume_to_job(resume, job)
            matches.append(result)
        except Exception as e:
            errors.append(f"score_match_node failed for {job.title} at {job.company}: {e}")

    return {"matches": matches, "errors": errors}

def validate_pitch_node(state):
    resume = state["resume_profile"]
    matches = state["matches"]
    retry_counts = state.get("retry_counts", {})
    errors = state.get("errors", [])
    all_valid = True

    for i, match in enumerate(matches):
        is_valid, feedback = validate_match_result(match, resume)
        if not is_valid:
            job_key = f"{match.job_title}_{i}"
            retries = retry_counts.get(job_key, 0)

            if retries < MAX_RETRIES:
                retry_counts[job_key] = retries + 1
                all_valid = False
                errors.append(
                    f"Pitch for {match.job_title} failed validation "
                    f"(attempt {retries + 1}/{MAX_RETRIES}): {feedback}"
                )
            else:
                errors.append(
                    f"Pitch for {match.job_title} failed validation after "
                    f"{MAX_RETRIES} retries — keeping best attempt."
                )

    return {
        "matches": matches,
        "retry_counts": retry_counts,
        "errors": errors,
        "validation_passed": all_valid,
    }

def aggregate_results_node(state):
    matches = state["matches"]
    resume = state["resume_profile"]
    errors = state.get("errors", [])

    try:
        # save to SQLite
        save_results_to_db(matches)

        # generate and save markdown report
        report_content = generate_markdown_report(matches, resume)
        report_path = save_report(report_content)

        print(f"\nReport saved to: {report_path}")
        print(f"Results saved to: data/results.db")

    except Exception as e:
        errors.append(f"aggregate_results_node failed: {e}")

    return {"errors": errors}

