from utils.resume_parser import parse_resume

RESUME_FILE_PATH = "data/Aditya Jaiswal Resume.pdf"  # adjust to wherever your resume actually is


def parse_resume_node(state):
    try:
        profile = parse_resume(RESUME_FILE_PATH)
        return {"resume_profile": profile}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"parse_resume_node failed: {e}"]}