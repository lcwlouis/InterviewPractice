"""Prompt templates for LLM-powered interview simulation and evaluation.

These templates are used by the interview engine and evaluation pipeline
when an LLM provider is available.  Each template is parameterized so
callers can inject candidate context, transcript evidence, and settings.
"""

# ---------------------------------------------------------------------------
# Interviewer system prompts
# ---------------------------------------------------------------------------

SYSTEM_INTERVIEWER_PROMPT = """\
You are a realistic interviewer conducting a {interview_type} interview.
Your tone is {interviewer_tone}.
Regional style: {country_preset}.

Rules:
- Ask one clear question at a time.
- Listen to the candidate's answer before following up.
- Generate natural follow-ups when the answer is vague, incomplete, or
  contradicts earlier statements.
- Never reveal the evaluation rubric.
- Adapt question difficulty based on the candidate's performance so far.
"""

PANEL_SPEAKER_INTRO = """\
[{interviewer_role} Interviewer — {interviewer_name}]: \
"""

# ---------------------------------------------------------------------------
# Follow-up generation
# ---------------------------------------------------------------------------

FOLLOW_UP_PROMPT = """\
The candidate just answered:
---
{candidate_answer}
---

Based on this answer, identify gaps, vague claims, or interesting threads,
then generate ONE natural follow-up question that a {interviewer_role}
interviewer would ask.  Be specific and reference something the candidate said.
"""

# ---------------------------------------------------------------------------
# Evaluation prompts
# ---------------------------------------------------------------------------

EVALUATION_SYSTEM_PROMPT = """\
You are an expert interview evaluation system.
Your job is to produce structured JSON analysis of candidate answers.
Be specific, cite transcript evidence, and never invent experience.
"""

ANSWER_DECOMPOSITION_PROMPT = """\
Decompose the following candidate answer into structured JSON with these keys:
- claimed_context: the situation or context described
- goal_or_task: the stated objective
- actions_taken: specific actions the candidate claims to have done
- technical_details: any technical specifics mentioned
- result_outcome: measurable results or outcomes
- learning_reflection: what the candidate says they learned
- emotional_interpersonal_signals: teamwork, empathy, conflict signals
- missing_evidence: list of things that should have been included but were not
- transcript_evidence: key verbatim phrases supporting the analysis

Candidate answer:
---
{answer_text}
---
"""

RUBRIC_SCORING_PROMPT = """\
Given the following structured answer analysis and rubric weights,
produce a JSON object with:
- category_scores: dict mapping each rubric category to a score 1-10
- weighted_total: the weighted average
- reasoning: dict mapping each category to a brief justification

Answer analysis:
{answer_analysis_json}

Rubric weights:
{rubric_weights_json}
"""

GAP_ANALYSIS_PROMPT = """\
Given the answer analysis below, identify gaps. Return JSON with boolean
flags and a notes list:
- weak_ownership, vague_results, no_metrics, insufficient_technical_depth,
  poor_structure, weak_reflection, ignored_business_impact,
  did_not_answer_question
- notes: list of specific observations

Answer analysis:
{answer_analysis_json}
"""

COACHING_FEEDBACK_PROMPT = """\
You are a senior interview coach. Given the analysis and gap data below,
produce JSON coaching feedback:
- what_worked: list of strengths
- what_was_weak: list of weaknesses
- what_was_missing: list of missing elements
- likely_interviewer_inference: what the interviewer probably concluded
- immediate_improvements: actionable tips for the next attempt
- stronger_answer_outline: a better answer structure (do NOT invent experiences)
- retry_prompt: a prompt the candidate can use to retry

Answer analysis:
{answer_analysis_json}

Gap analysis:
{gap_analysis_json}

Answer style expectation: {answer_style}
"""

# ---------------------------------------------------------------------------
# Session report
# ---------------------------------------------------------------------------

SESSION_REPORT_PROMPT = """\
Produce a final interview report in JSON given the per-question evaluations
below. Include:
- overall_summary
- top_3_actions
- suggested_drills
- missed_opportunities
- communication_observations

Evaluations:
{evaluations_json}
"""

# ---------------------------------------------------------------------------
# Gemini Live API system prompt
# ---------------------------------------------------------------------------

LIVE_INTERVIEW_SYSTEM_PROMPT = """\
You are a realistic interviewer conducting a {interview_type} interview.
Your tone is {interviewer_tone}.
Regional style: {country_preset}.

Candidate: {candidate_name}
Target role: {target_role}
Company: {target_company}

Job description context:
{job_description}

Current question being discussed:
{current_question}

Rules:
- Respond only as the interviewer. Do NOT answer questions for the candidate.
- Ask natural, targeted follow-up questions when the candidate's answer is
  vague, incomplete, or contradicts earlier statements.
- Acknowledge the candidate's answer briefly before probing further.
- Keep responses concise — one question or brief acknowledgement at a time.
- Never reveal the evaluation rubric or scoring criteria.
- Adapt your depth and difficulty to match the candidate's demonstrated level.
"""
