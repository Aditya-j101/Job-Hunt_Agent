import { useState, useRef } from 'react'

// ── Score Ring ────────────────────────────────────────────────────────────────
function ScoreRing({ score }) {
  const radius = 36
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 70 ? '#00D4AA' : score >= 45 ? '#FFB347' : '#FF6B6B'

  return (
    <div className="score-ring-wrapper">
      <svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r={radius} fill="none" stroke="#2D3148" strokeWidth="8" />
        <circle
          cx="45" cy="45" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 45 45)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div className="score-text" style={{ color }}>
        <span className="score-number">{score}</span>
        <span className="score-label">/100</span>
      </div>
    </div>
  )
}

// ── Skill Badge ───────────────────────────────────────────────────────────────
function SkillBadge({ skill, type }) {
  return <span className={`skill-badge skill-badge--${type}`}>{skill}</span>
}

// ── Result Card ───────────────────────────────────────────────────────────────
function ResultCard({ match, index }) {
  const [expanded, setExpanded] = useState(false)
  const score = Math.round(match.match_score)
  const label = score >= 70 ? '🟢 Strong Match' : score >= 45 ? '🟡 Partial Match' : '🔴 Weak Match'

  return (
    <div className="result-card" style={{ animationDelay: `${index * 0.12}s` }}>
      <div className="result-card__header">
        <ScoreRing score={score} />
        <div className="result-card__meta">
          <div className="result-card__title">{match.job_title}</div>
          <div className="result-card__label">{label}</div>
          <div className="result-card__rationale">{match.rationale}</div>
        </div>
      </div>

      <div className="result-card__skills">
        {match.matching_skills.length > 0 && (
          <div className="skills-group">
            <span className="skills-group__label">Matching</span>
            <div className="skills-group__list">
              {match.matching_skills.map(s => (
                <SkillBadge key={s} skill={s} type="match" />
              ))}
            </div>
          </div>
        )}
        {match.missing_skills.length > 0 && (
          <div className="skills-group">
            <span className="skills-group__label">To Develop</span>
            <div className="skills-group__list">
              {match.missing_skills.map(s => (
                <SkillBadge key={s} skill={s} type="missing" />
              ))}
            </div>
          </div>
        )}
      </div>

      <button className="pitch-toggle" onClick={() => setExpanded(!expanded)}>
        {expanded ? 'Hide Pitch ▲' : 'View Tailored Pitch ▼'}
      </button>

      {expanded && (
        <div className="result-card__pitch">
          <div className="pitch-label">Tailored Pitch</div>
          <p>{match.tailored_pitch}</p>
        </div>
      )}
    </div>
  )
}

// ── Skill Gap Summary ─────────────────────────────────────────────────────────
function SkillGapSummary({ matches }) {
  const gapCount = {}
  matches.forEach(m => {
    m.missing_skills.forEach(s => {
      gapCount[s] = (gapCount[s] || 0) + 1
    })
  })

  const sorted = Object.entries(gapCount).sort((a, b) => b[1] - a[1])
  if (sorted.length === 0) return null

  return (
    <div className="skill-gap-summary">
      <h3>Skill Gap Summary</h3>
      <p className="skill-gap-summary__desc">
        Skills missing across your job postings — prioritise these for learning
      </p>
      <div className="gap-list">
        {sorted.map(([skill, count]) => (
          <div key={skill} className="gap-item">
            <span className="gap-item__skill">{skill}</span>
            <span className="gap-item__count">
              missing in {count} job{count > 1 ? 's' : ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [resume, setResume] = useState(null)
  const [jobDescriptions, setJobDescriptions] = useState([''])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  const handleResumeUpload = (file) => {
    if (file && file.type === 'application/pdf') {
      setResume(file)
      setError(null)
    } else {
      setError('Please upload a PDF file.')
    }
  }

  const updateJob = (index, value) => {
    const updated = [...jobDescriptions]
    updated[index] = value
    setJobDescriptions(updated)
  }

  const removeJob = (index) => {
    setJobDescriptions(jobDescriptions.filter((_, i) => i !== index))
  }

  const handleAnalyze = async () => {
    if (!resume) { setError('Please upload your resume PDF.'); return }
    const validJobs = jobDescriptions.filter(j => j.trim())
    if (!validJobs.length) { setError('Please add at least one job description.'); return }

    setLoading(true)
    setError(null)
    setResults(null)

    const formData = new FormData()
    formData.append('resume', resume)
    validJobs.forEach(job => formData.append('job_descriptions', job))

    try {
      const res = await fetch('/analyze', { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Analysis failed.')
      }
      setResults(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header__inner">
          <div className="header__logo">🎯 Job Hunt Agent</div>
          <div className="header__sub">
            AI-powered resume matching · LangGraph + Groq + FastAPI
          </div>
        </div>
      </header>

      <main className="main">
        {/* ── Upload Section ── */}
        <section className="upload-section">
          <div className="upload-grid">

            {/* Resume */}
            <div className="panel">
              <h2 className="panel__title">Your Resume</h2>
              <div
                className={`drop-zone ${dragOver ? 'drop-zone--active' : ''} ${resume ? 'drop-zone--filled' : ''}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={e => {
                  e.preventDefault()
                  setDragOver(false)
                  handleResumeUpload(e.dataTransfer.files[0])
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  style={{ display: 'none' }}
                  onChange={e => handleResumeUpload(e.target.files[0])}
                />
                {resume ? (
                  <>
                    <span className="drop-zone__icon">📄</span>
                    <span className="drop-zone__filename">{resume.name}</span>
                    <span className="drop-zone__hint">Click to change</span>
                  </>
                ) : (
                  <>
                    <span className="drop-zone__icon">⬆️</span>
                    <span className="drop-zone__text">Drop PDF here or click to upload</span>
                  </>
                )}
              </div>
            </div>

            {/* Jobs */}
            <div className="panel">
              <h2 className="panel__title">
                Job Descriptions
                <span className="panel__count">
                  {jobDescriptions.filter(j => j.trim()).length} added
                </span>
              </h2>
              <div className="jobs-list">
                {jobDescriptions.map((job, i) => (
                  <div key={i} className="job-input-row">
                    <textarea
                      className="job-textarea"
                      placeholder={`Paste job description ${i + 1} here…`}
                      value={job}
                      onChange={e => updateJob(i, e.target.value)}
                      rows={5}
                    />
                    {jobDescriptions.length > 1 && (
                      <button className="remove-job-btn" onClick={() => removeJob(i)}>✕</button>
                    )}
                  </div>
                ))}
                <button
                  className="add-job-btn"
                  onClick={() => setJobDescriptions([...jobDescriptions, ''])}
                >
                  + Add Another Job
                </button>
              </div>
            </div>

          </div>

          {error && <div className="error-banner">⚠️ {error}</div>}

          <button
            className={`analyze-btn ${loading ? 'analyze-btn--loading' : ''}`}
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading
              ? <><span className="spinner" /> Analyzing your profile…</>
              : 'Analyze My Profile →'
            }
          </button>

          {loading && (
            <p className="loading-note">
              Takes 30–60 seconds — the AI is parsing your resume, scoring each job,
              and generating grounded pitches with a hallucination guard.
            </p>
          )}
        </section>

        {/* ── Results Section ── */}
        {results && (
          <section className="results-section">
            <div className="results-header">
              <h2>Results</h2>
              <span className="results-meta">
                {results.total_jobs_analyzed} job{results.total_jobs_analyzed !== 1 ? 's' : ''} analyzed
              </span>
            </div>

            <div className="results-list">
              {results.matches.map((match, i) => (
                <ResultCard key={i} match={match} index={i} />
              ))}
            </div>

            <SkillGapSummary matches={results.matches} />
          </section>
        )}
      </main>

      <footer className="footer">
        Built by <strong>Aditya Jaiswal</strong> ·{' '}
        <a href="https://github.com/Aditya-j101/job-hunt-agent" target="_blank" rel="noreferrer">
          GitHub
        </a>
      </footer>
    </div>
  )
}