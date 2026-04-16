# InterviewPractice

Production-minded MVP for AI-powered mock interview practice with structured, evidence-grounded critique.

## Recommended Architecture

```text
InterviewPractice/
├── app/                     # Streamlit UI (sidebar-navigated pages)
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
├── ingestion/               # Resume parsing (PDF / DOCX → CandidateProfile)
├── research/                # Optional interviewer / company web research pipeline
├── interview_engine/        # Question bank, planner, session orchestrator
│   ├── question_bank.py     # 22+ tagged questions across phases & competencies
│   ├── planner.py           # Phase-aware selection, coverage tracking, difficulty adaptation
│   └── session.py           # Transcript, opening/warmup/main/wrapup flow
├── evaluation/              # Structured critique pipeline
│   ├── pipeline.py          # Decompose → Score → Gap → Rewrite → Coach
│   └── rubrics.py           # Per-type weighted rubric definitions
├── prompts/                 # LLM prompt templates (interviewer, follow-up, eval)
├── storage/                 # JSON + Markdown report writers
├── utils/                   # Retry helper
└── tests/                   # Unit tests for planner, evaluation, ingestion
```

## Critique Pipeline Design

For every answer evaluation the system runs an **explicit structured pipeline** — not a single monolithic LLM call:

1. **Answer Decomposition** → `AnswerAnalysis` (context, actions, results, evidence, missing)
2. **Rubric Scoring** → `RubricScore` (weighted per-category scores with reasoning)
3. **Gap Analysis** → `GapAnalysis` (boolean flags: weak ownership, no metrics, etc.)
4. **Rewrite Synthesis** → outline of a stronger answer
5. **Coaching Feedback** → `CoachingFeedback` (what worked, weak, missing, improvements)

Human-readable critique is then generated **from** these structured artifacts.

## Interview Flow

Full Mock mode follows realistic phases:
- **Opening** → introductory remarks
- **Warm-up** → low-stakes questions to ease in
- **Main rounds** → competency-driven questions with difficulty adaptation
- **Follow-up probing** → targeted follow-ups based on gaps
- **Candidate questions** → "Do you have any questions for us?"
- **Wrap-up** → closing remarks

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

# 4. Launch Streamlit
streamlit run app/streamlit_app.py
```

Run tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## External API Setup

| Provider | Required env var | When needed |
|----------|-----------------|-------------|
| OpenAI | `OPENAI_API_KEY` | LLM text generation, Whisper transcription, multimodal eval |
| Gemini | `GEMINI_API_KEY` | Alternative LLM provider |
| Edge TTS | *(none)* | Free TTS fallback — `pip install edge-tts` |

Set `INTERVIEW_PROVIDER=openai` or `INTERVIEW_PROVIDER=gemini` in `.env`.

## Known Limitations

- **Live audio conversation mode** — requires OpenAI Realtime API or Gemini Live API which are currently in limited access. The provider supports_live_audio() check will report availability. Whisper transcription works for audio-in → text-out flows.
- **Web research** — the research pipeline architecture exists (search → extract → summarize → confidence) but the actual web search connector is stubbed. Set `ENABLE_WEB_RESEARCH=false` unless you implement a search backend.
- **Video/body language analysis** — the multimodal evaluation interface is defined but deep video analysis requires passing video to a multimodal model, which is provider-dependent.
- **Question bank** — 22 questions cover the main competencies; a production system would have 200+ per role family.

## Future Improvements

- Larger question bank with role-specific variants (PM, design, data science)
- LLM-generated follow-up questions based on actual candidate answers
- Real web research via SerpAPI / Tavily / Perplexity integration
- WebRTC-based live audio streaming for true conversational mode
- Video recording with MediaRecorder API + body language analysis
- Session persistence (database / cloud storage)
- Multi-session progress tracking and spaced repetition
- Difficulty calibration based on historical performance

## Safety & Privacy Notes

- **Resume uploads** may contain sensitive PII (address, phone, email). Files are processed in temp storage and not persisted beyond the session.
- **Audio/video recording** — obtain explicit user consent before recording. Apply retention and deletion controls before any production deployment.
- **LLM API calls** — candidate answers and resume content are sent to third-party APIs (OpenAI / Google). Review provider data usage policies.
- **No data is stored remotely** in this MVP — all state is in-memory within the Streamlit session.
