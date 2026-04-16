# Suggestions & TODOs

Prioritised improvements and open items for the InterviewPractice MVP.

---

## High Priority

### 1. LLM-Powered Follow-Up Questions
Currently the interview engine selects from a static question bank. The next
highest-value feature is generating **dynamic follow-up questions** from the
candidate's actual answer using the LLM provider.

- Wire `FOLLOW_UP_PROMPT` from `prompts/templates.py` through the providers
- Call `text_provider.generate_text()` after each answer to produce a contextual follow-up
- Add a `follow_up_count` parameter to `SessionState` to cap the depth

### 2. Real Web Research Integration
The `research/service.py` pipeline architecture is complete (search → extract →
summarize → confidence gating) but the `search()` method returns an empty list.

Options to implement:
- **SerpAPI** — structured Google search results
- **Tavily** — AI-optimised search API, returns clean extracts
- **Perplexity API** — returns synthesised answers with citations

Add a `SEARCH_API_KEY` to `.env.example` and implement the connector.

### 3. Audio Recording & Transcription Pipeline
The recording service (`services/recording.py`) has start/stop scaffolding but
does not capture actual audio.

- Use Streamlit's `st.audio_input()` or a WebRTC component for browser mic capture
- Pipe audio bytes to `transcription_provider.transcribe_audio()`
- Store audio files alongside the transcript

### 4. Expand Question Bank to 100+
Current bank has 22 questions. A production system needs at least 100 per
role family, with coverage across all 12 competencies and 5 difficulty levels.

Consider loading from a YAML/JSON file instead of hardcoding in Python.

---

## Medium Priority

### 5. LLM-Enhanced Evaluation Pipeline
The current evaluation pipeline uses deterministic heuristics (keyword matching,
regex) which is good for reliability but limited in depth. Add an **optional**
LLM-enhanced mode:

- Send the answer + `ANSWER_DECOMPOSITION_PROMPT` to the LLM
- Parse structured JSON response into `AnswerAnalysis`
- Fall back to the heuristic pipeline if the LLM call fails

This gives the best of both worlds: reliable baseline + richer analysis.

### 6. Session Persistence & History
Currently all state is in-memory. Add:
- SQLite or JSON file-based session storage
- Session replay / review
- Progress tracking across multiple practice sessions
- Spaced repetition for weak competencies

### 7. Video Recording & Body Language Analysis
The multimodal evaluation interface exists. To use it:
- Add a webcam recording component (e.g. streamlit-webrtc)
- Save video clips per question
- Send to OpenAI GPT-4o or Gemini with vision for body language analysis
- Populate `body_language_observations` in the session report

### 8. Panel Turn-Taking with Multiple TTS Voices
When in panel mode with Edge TTS:
- Assign different voices per panel member (e.g. `en-US-AriaNeural`, `en-US-GuyNeural`)
- Add verbal speaker introductions: "[HR Interviewer — Sarah]: ..."
- Map `PanelMember.role_type` to voice presets

### 9. Export to PDF
The markdown report could be rendered to PDF using `weasyprint` or `fpdf2`
for a more polished deliverable.

---

## Low Priority / Nice-to-Have

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

### 13. Answer Retry with Diff Highlighting
In Answer Coaching mode, after the candidate retries, show a diff between
the original and retry answers highlighting improvements.

### 14. Streamlit Multi-Page App Refactor
As the UI grows, consider migrating from the current single-file sidebar
navigation to Streamlit's native multi-page app structure (`pages/` directory).

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
