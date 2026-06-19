"""
Handles two jobs:
1. Saves match results to data/results.db (SQLite) for persistent logging
2. Generates a ranked markdown report the candidate can actually use
"""
import sqlite3
import json
from datetime import datetime
from models.schemas import ResumeProfile, MatchResult

DB_PATH = "data/results.db"
REPORT_PATH = "data/report.db"

def init_db():
    """Creates the results table if it doesn't already exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT,
            job_title TEXT,
            match_score REAL,
            matching_skills TEXT,
            missing_skills TEXT,
            rationale TEXT,
            tailored_pitch TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_results_to_db(matches: list[MatchResult]):
    """Saves all match results from a single run into the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    for match in matches:
        cursor.execute("""
            INSERT INTO match_results (
                run_timestamp, job_title, match_score,
                matching_skills, missing_skills, rationale, tailored_pitch
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            match.job_title,
            match.match_score,
            json.dumps(match.matching_skills),
            json.dumps(match.missing_skills),
            match.rationale,
            match.tailored_pitch,
        ))

    conn.commit()
    conn.close()

def generate_markdown_report(
    matches: list[MatchResult],
    resume: ResumeProfile,
) -> str:
    """
    Generates a clean markdown report ranked by match score.
    This is the actual useful output you use for your job search.
    """
    sorted_matches = sorted(matches, key=lambda m: m.match_score, reverse=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    lines.append(f"# Job Match Report")
    lines.append(f"Generated: {timestamp}\n")

    lines.append("## Your Profile Summary")
    lines.append(f"- **Experience:** {resume.years_experience} years")
    lines.append(f"- **Roles:** {', '.join(resume.past_roles)}")
    lines.append(f"- **Education:** {resume.education}")
    lines.append(f"- **Skills:** {', '.join(resume.skills[:10])}{'...' if len(resume.skills) > 10 else ''}\n")

    lines.append("## Ranked Job Matches\n")

    for i, match in enumerate(sorted_matches, 1):
        score = match.match_score
        if score >= 70:
            indicator = "🟢 Strong Match"
        elif score >= 45:
            indicator = "🟡 Partial Match"
        else:
            indicator = "🔴 Weak Match"

        lines.append(f"### {i}. {match.job_title} — {score}/100 {indicator}")
        lines.append(f"\n**Why this score:** {match.rationale}\n")

        lines.append("**Matching Skills:**")
        for skill in match.matching_skills:
            lines.append(f"  - {skill}")

        if match.missing_skills:
            lines.append("\n**Skills to Develop:**")
            for skill in match.missing_skills:
                lines.append(f"  - {skill}")

        lines.append("\n**Tailored Pitch:**")
        lines.append(f"{match.tailored_pitch}\n")
        lines.append("---\n")

    # skill gap summary across all jobs
    all_missing = {}
    for match in sorted_matches:
        for skill in match.missing_skills:
            all_missing[skill] = all_missing.get(skill, 0) + 1

    if all_missing:
        lines.append("## Skill Gap Summary")
        lines.append("Skills missing across multiple job postings (prioritise learning these):\n")
        for skill, count in sorted(all_missing.items(), key=lambda x: -x[1]):
            lines.append(f"- **{skill}** — missing in {count} job(s)")

    return "\n".join(lines)


def save_report(report_content: str) -> str:
    """Writes the markdown report to disk and returns the file path."""
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
    return REPORT_PATH