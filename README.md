# 🎯 Job Hunt Agent

An end-to-end AI-powered pipeline that scores your resume against real job postings, identifies skill gaps, and generates grounded, hallucination-free tailored pitches — built with LangGraph, Groq (Llama 3.3 70B), and FastAPI, containerised with Docker.

**[Try the live demo →](https://job-huntagent-production.up.railway.app)**

---

## What it does

Most job application tools either blindly match keywords or use an LLM that invents skills you don't have. This project does neither.

It runs your resume and a set of job descriptions through a **multi-node LangGraph pipeline** that:
1. Extracts structured data from your resume and each job posting using an LLM
2. Scores match quality using a **weighted Jaccard similarity** on skill sets (embedding-based scoring)
3. Generates a tailored pitch grounded only in your actual resume
4. **Validates the pitch** against your real skill list and retries with targeted feedback if the model hallucinated anything
5. Saves results to SQLite and generates a ranked markdown report with a skill gap summary

---

## Architecture

```
resume.pdf + job_descriptions
        │
        ▼
┌──────────────────────────────────────────────────────┐
│                  LangGraph Pipeline                   │
│                                                      │
│  parse_resume → parse_jobs → score_match             │
│                                   │                  │
│                            validate_pitch            │
│                           ╱              ╲           │
│                     [invalid]          [valid]       │
│                    retry ≤2x        aggregate        │
│                      │                   │           │
│               score_match ◄──────────────┘           │
│                                          │           │
│                                    results.db        │
│                                    report.md         │
└──────────────────────────────────────────────────────┘
        │
        ▼
   FastAPI REST API
   POST /analyze
   GET  /results
   GET  /report
```

The **validate → retry conditional edge** is the core agentic behaviour — if the model's pitch references a skill not in the candidate's resume, the graph routes back to `score_match` with specific feedback rather than accepting hallucinated output. This is implemented as a real LangGraph `add_conditional_edges` call, not a Python `if` statement.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Orchestration | LangGraph | Stateful multi-node graph with conditional edges |
| LLM | Groq — Llama 3.3 70B | Free tier, fast, strong instruction following |
| Schemas | Pydantic v2 | Validates every LLM output before it enters the graph |
| Skill matching | Jaccard similarity (weighted) | Deterministic, explainable, zero cost |
| Resume parsing | pdfplumber | Reliable text extraction from PDF |
| API | FastAPI | Auto-generated Swagger UI, async, production-grade |
| Containerisation | Docker + docker-compose | Reproducible deployment anywhere |
| Storage | SQLite | Persistent run history, no setup required |

---

## Project Structure

```
job-hunt-agent/
├── app.py                  # FastAPI entrypoint (3 endpoints)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── graph/
│   ├── state.py            # LangGraph AgentState (TypedDict)
│   ├── nodes.py            # Node functions (parse, match, validate, aggregate)
│   └── build_graph.py      # Graph wiring + conditional edge definition
├── models/
│   └── schemas.py          # Pydantic models (ResumeProfile, JobRequirements, MatchResult)
├── utils/
│   ├── llm_client.py       # Groq API wrapper with retry/backoff + usage logging
│   ├── resume_parser.py    # PDF → text → structured ResumeProfile
│   ├── job_parser.py       # .txt → structured JobRequirements (loops over all jobs)
│   ├── matcher.py          # Embedding score + LLM judgment → MatchResult
│   ├── embeddings.py       # Weighted Jaccard similarity with partial skill matching
│   ├── validator.py        # Hallucination guard + pitch scrubber
│   └── report.py           # SQLite persistence + markdown report generation
├── data/
│   ├── sample_jobs/        # Paste job descriptions here as .txt files
│   └── results.db          # SQLite run history
├── eval/
│   ├── eval_set.json       # Hand-labelled test cases
│   └── run_eval.py         # Evaluation harness
└── tests/
    └── test_nodes.py
```

---

## Quickstart

### Prerequisites
- Docker Desktop installed and running
- A free [Groq API key](https://console.groq.com)

### Setup

```bash
git clone https://github.com/yourusername/job-hunt-agent.git
cd job-hunt-agent

cp .env.example .env
# edit .env and add your GROQ_API_KEY

docker-compose up --build
```

API is now live at `http://localhost:8000`
Interactive Swagger UI at `http://localhost:8000/docs`

---

## API Endpoints

### `POST /analyze`
Upload your resume and paste job descriptions — runs the full pipeline and returns ranked results.

**Inputs:**
- `resume` — your resume as a PDF file
- `job_descriptions` — one or more job postings pasted as text (add multiple with **Add string item** in Swagger)

**Response:**
```json
{
  "status": "success",
  "total_jobs_analyzed": 3,
  "errors": [],
  "matches": [
    {
      "job_title": "Junior Data Scientist",
      "match_score": 80.0,
      "matching_skills": ["Python", "SQL", "Scikit-learn"],
      "missing_skills": ["Tableau"],
      "rationale": "Strong alignment on core ML and Python skills...",
      "tailored_pitch": "Built predictive ML pipelines using Python and Scikit-learn..."
    }
  ]
}
```

### `GET /results`
Returns all past pipeline runs stored in `results.db`, ordered by most recent.

### `GET /report`
Returns the latest run as a ranked markdown report with a skill gap summary.

---

## Key Design Decisions

**Why Jaccard similarity instead of raw LLM scoring?**
LLM-judged scores are non-deterministic and can be inflated. Jaccard gives a reproducible, explainable baseline. The LLM then adds qualitative judgment on top — blending both is more reliable than trusting either alone.

**Why partial skill matching?**
A job posting says `Machine Learning`; your resume says `Machine Learning and Statistics`. Exact matching would mark this as a gap. The partial matching logic in `embeddings.py` catches these semantic overlaps without needing an embedding model.

**Why a validation loop instead of just prompting carefully?**
Prompt engineering alone doesn't guarantee constraint adherence — especially with smaller models. The `validate_pitch` node programmatically checks every claimed skill against the resume and routes back with targeted feedback if anything was invented. A `scrub_pitch` function removes hallucinated sentences as a final safety net.

**Why SQLite instead of a heavier database?**
Zero setup, zero cost, sufficient for a single-user tool. The schema is simple enough that migrating to Postgres later is a one-line connection string change.

---

## What I'd improve with more time

- **Semantic skill matching** — use a sentence-transformer model to catch cases where `PyTorch` implies `Deep Learning` even without an exact string match
- **Real job ingestion** — integrate the Adzuna or USAJobs API instead of paste-in, so the pipeline can pull live postings automatically
- **Parallel job processing** — use LangGraph's `Send` API to process all jobs concurrently instead of sequentially, reducing total latency
- **Frontend** — a minimal React UI with a drag-and-drop resume upload and a results dashboard
- **Confidence scores** — expose the raw embedding score alongside the LLM score so the user can see both signals

---

## Resume Bullet (earned after building this)

> Built a multi-agent job-matching pipeline using LangGraph and Groq (Llama 3.3 70B), featuring a self-correcting hallucination guard that validates generated pitches against the candidate's actual resume and retries with targeted feedback — containerised with FastAPI and Docker, with persistent SQLite result logging.

---

## Author

**Aditya Jaiswal**
SDE Intern @ Auxiliobits Technologies | BCA-MCA, Amity University Noida
[LinkedIn](https://www.linkedin.com/in/aditya-jaiswal-898523224/) · [GitHub](https://github.com/Aditya-j101)