# InterviewPractice

Production-minded MVP for AI-powered mock interview practice with structured, evidence-grounded critique.

## Recommended architecture

```text
InterviewPractice/
├── app/                     # Streamlit entrypoint/UI
├── backend/                 # Config and logging
├── models/                  # Pydantic schemas and typed artifacts
├── providers/               # OpenAI/Gemini/TTS abstraction + stubs
├── services/                # Provider registry and recording service
├── ingestion/               # Resume ingestion (PDF/DOCX)
├── research/                # Optional interviewer/company research pipeline
├── interview_engine/        # Question bank, planner, session orchestrator
├── evaluation/              # Structured analysis, rubric scoring, gaps, coaching
├── storage/                 # JSON/Markdown report writers
├── prompts/                 # Prompt templates
└── tests/                   # Core logic tests
```

## Critique pipeline design
For every answer evaluation:
1. Produce structured analysis JSON via typed models (`AnswerAnalysis`, `RubricScore`, `GapAnalysis`, `CoachingFeedback`).
2. Generate human-readable critique from those structured artifacts (not a single monolithic prompt).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app/streamlit_app.py
```

Run tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Remaining TODOs / external API setup
- Set `OPENAI_API_KEY` and/or `GEMINI_API_KEY` in `.env`.
- Wire OpenAI Realtime / Gemini Live APIs in provider implementations.
- Integrate real web search connector in `research/service.py` pipeline.
- Implement production media capture + synchronized transcript persistence.

## Known limitations
- Live audio and multimodal analysis are scaffolded with TODOs.
- Research pipeline stages exist, but active search is disabled by default.

## Future improvements
- Larger role/seniority question bank.
- Better resume section extraction.
- Richer multimodal body language analysis.

## Safety/privacy notes
- Resume + recordings may contain sensitive PII.
- Obtain user consent before recording.
- Apply retention/deletion controls before production deployment.
