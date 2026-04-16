# Suggestions & TODOs

Prioritised improvements and open items for the InterviewPractice MVP.

---

## High Priority

### 8. Panel Turn-Taking with Multiple TTS Voices
When in panel mode with Edge TTS:
- Assign different voices per panel member (e.g. `en-US-AriaNeural`, `en-US-GuyNeural`)
- Add verbal speaker introductions: "[HR Interviewer — Sarah]: ..."
- Map `PanelMember.role_type` to voice presets

### 9. Export to PDF
The markdown report could be rendered to PDF using `weasyprint` or `fpdf2`
for a more polished deliverable.

---

## Medium Priority

### 10. Difficulty Calibration Model
Track candidate performance across sessions and build a simple calibration
model that adjusts starting difficulty for returning users.

### 11. Role-Specific Question Packs
Add separate question packs for:
- Product Management
- Data Science / ML Engineering
- Design / UX
- Sales / Business Development
- Executive / C-suite

### 12. Internationalisation
- Translate question bank and UI strings
- Adjust rubric weights per `CountryPreset`
- Add country-specific interview norms (e.g. Japan: more formal, less direct)

### 15. CI/CD & Testing
- Add GitHub Actions workflow for tests + linting
- Add integration tests that mock LLM responses
- Add Streamlit app smoke test using `streamlit run --headless`

---

## Completed ✅

- [x] Condensed 8-tab UI into 4-page sidebar navigation
- [x] Added AnswerStyle, InterviewerTone, CountryPreset settings
- [x] Added InterviewPhase-based session orchestration
- [x] Expanded question bank from 5 → 22 questions
- [x] Implemented real OpenAI API calls with retry + fallback
- [x] Implemented real Gemini API calls with retry + fallback
- [x] Implemented Edge TTS via edge-tts package
- [x] Added competency coverage progress display
- [x] Added session timer
- [x] Added Answer Coaching mode in-session feedback
- [x] Expanded prompt templates
- [x] Enriched markdown report export
- [x] Documented .env.example with all settings
- [x] **Suggestion 1** — LLM-powered follow-up questions via FOLLOW_UP_PROMPT + text provider
- [x] **Suggestion 2** — Real web research via Tavily API (SEARCH_API_KEY)
- [x] **Suggestion 3** — Audio recording & transcription pipeline (st.audio_input → Whisper → TTS playback)
- [x] **Suggestion 4** — Expanded question bank to 101 questions loaded from YAML (data/questions.yaml)
- [x] **Suggestion 5** — LLM-enhanced evaluation pipeline with heuristic fallback
- [x] **Suggestion 6** — Session persistence via SQLite (storage/session_store.py) with spaced repetition
- [x] **Suggestion 7** — Video recording & body language analysis via streamlit-webrtc + multimodal eval
- [x] **Suggestion 13** — Answer retry with inline diff highlighting in Feedback page
- [x] **Suggestion 14** — Streamlit multi-page app refactor (app/pages/ modules)
- [x] Default country preset changed from US to Singapore (SG)
- [x] Tests expanded from 24 → 56
