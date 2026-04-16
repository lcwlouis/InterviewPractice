# InterviewPractice

Production-minded MVP for AI-powered mock interview practice with structured, evidence-grounded critique.

## Architecture

```text
InterviewPractice/
├── app/                     # Streamlit multi-page UI
│   ├── main.py              # Entry point with sidebar navigation
│   ├── streamlit_app.py     # Backwards-compatible entry (delegates to main.py)
│   └── pages/               # Page modules (Suggestion 14)
│       ├── page_setup.py    # Resume, profile, company, panel, settings
│       ├── page_interview.py# Live session: audio/video, TTS, auto-submit
│       ├── page_feedback.py # Per-Q critique, retry with diff (Suggestion 13)
│       ├── page_history.py  # Session replay, spaced repetition (Suggestion 6)
│       └── page_settings.py # Provider status, env vars
├── backend/                 # Config (pydantic-settings) and logging
├── models/                  # Pydantic schemas + enum definitions
│   ├── enums.py             # InterviewType, Mode, Phase, Tone, Style, etc.
│   └── schemas.py           # Typed artifacts: AnswerAnalysis, RubricScore, ...
├── providers/               # LLM / audio / TTS abstraction layer
│   ├── base.py              # Abstract interfaces
│   ├── openai_provider.py   # OpenAI ChatCompletion + Whisper + multimodal
│   ├── gemini_provider.py   # Google Gemini GenerativeModel
│   └── tts_edge.py          # Microsoft Edge TTS (free, no API key)
├── services/                # Provider registry, recording service
│   ├── provider_registry.py # Build ProviderBundle from settings
│   └── recording.py         # Audio/video capture, transcription, TTS (Suggestion 3 & 7)
├── data/                    # External data files
│   └── questions.yaml       # 101 tagged questions (Suggestion 4)
├── ingestion/               # Resume parsing (PDF / DOCX → CandidateProfile)
├── research/                # Tavily-powered web research (Suggestion 2)
├── interview_engine/        # Question bank, planner, session orchestrator
│   ├── question_bank.py     # YAML-loaded 101 questions across phases & competencies
│   ├── planner.py           # Phase-aware selection, coverage tracking, difficulty adaptation
│   └── session.py           # Transcript, LLM follow-ups (Suggestion 1), phase flow
├── evaluation/              # Structured critique pipeline
│   ├── pipeline.py          # LLM-enhanced eval with heuristic fallback (Suggestion 5)
│   └── rubrics.py           # Per-type weighted rubric definitions
├── prompts/                 # LLM prompt templates (interviewer, follow-up, eval)
├── storage/                 # Persistence layer
│   ├── local_store.py       # JSON + Markdown report writers
│   └── session_store.py     # SQLite session persistence (Suggestion 6)
├── utils/                   # Retry helper
└── tests/                   # 56 unit tests
```

## End-to-End Interview Flow

```
Setup → Configure profile, company, panel, settings
  ↓
Interview → Start → Mic/text input → Whisper transcription → Auto-submit
  ↓                                                            ↓
  ← TTS audio playback ← LLM follow-up ← Evaluation pipeline ←
  ↓
Feedback → Per-question critique → Retry with diff → Session report
  ↓
History → Browse past sessions → Spaced repetition → Weak area focus
```

**Audio mode (default):** Mic input → Whisper transcription → LLM evaluation → Edge TTS playback → `st.audio()`. Auto-submit triggers on transcription completion when silence detection is enabled.

**Video mode (optional):** WebRTC webcam capture → save clips per question → multimodal body language analysis via GPT-4o / Gemini Vision at session end.

## Critique Pipeline Design

For every answer evaluation the system runs an **explicit structured pipeline** — not a single monolithic LLM call:

1. **Answer Decomposition** → `AnswerAnalysis` (context, actions, results, evidence, missing)
2. **Rubric Scoring** → `RubricScore` (weighted per-category scores with reasoning)
3. **Gap Analysis** → `GapAnalysis` (boolean flags: weak ownership, no metrics, etc.)
4. **Rewrite Synthesis** → outline of a stronger answer
5. **Coaching Feedback** → `CoachingFeedback` (what worked, weak, missing, improvements)

When an LLM provider is available, each step attempts LLM-enhanced analysis first
and falls back to the deterministic heuristic pipeline on failure.

## Interview Flow

Full Mock mode follows realistic phases:
- **Opening** → introductory remarks
- **Warm-up** → low-stakes questions to ease in
- **Main rounds** → competency-driven questions with difficulty adaptation
- **Follow-up probing** → LLM-generated contextual follow-ups based on actual answers
- **Candidate questions** → "Do you have any questions for us?"
- **Wrap-up** → closing remarks + session saved to SQLite

Other modes: Quick-Fire, Only Follow-Ups, Final-Round Panel, Answer Coaching.

## Run Locally

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set OPENAI_API_KEY and/or GEMINI_API_KEY
# Optionally set SEARCH_API_KEY for Tavily web research

# 4. Launch Streamlit
streamlit run app/streamlit_app.py
```

Run tests:

```bash
python -m pytest tests/ -v
```

## External API Setup

| Provider | Required env var | When needed |
|----------|-----------------|-------------|
| OpenAI | `OPENAI_API_KEY` | LLM text generation, Whisper transcription, multimodal eval |
| Gemini | `GEMINI_API_KEY` | Alternative LLM provider |
| Edge TTS | *(none)* | Free TTS fallback — `pip install edge-tts` |
| Tavily | `SEARCH_API_KEY` | Web research for interviewer background |

Set `INTERVIEW_PROVIDER=openai` or `INTERVIEW_PROVIDER=gemini` in `.env`.
Default country preset is **Singapore (SG)**.

## Safety & Privacy Notes

- **Resume uploads** may contain sensitive PII (address, phone, email). Files are processed in temp storage and not persisted beyond the session.
- **Audio/video recording** — obtain explicit user consent before recording. Apply retention and deletion controls before any production deployment.
- **LLM API calls** — candidate answers and resume content are sent to third-party APIs (OpenAI / Google). Review provider data usage policies.
- **Session data** is stored locally in SQLite (`storage/db/sessions.sqlite3`). No data is sent to remote servers beyond LLM API calls.
