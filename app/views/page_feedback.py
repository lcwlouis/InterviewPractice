"""Feedback page — per-question evaluations, session report, answer retry with diff.

Implements Suggestion 13: answer retry with diff highlighting.
"""

from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.pipeline import EvaluationPipeline
from services.provider_registry import build_provider_bundle
from storage.local_store import save_report_json, save_report_markdown


def _render_diff(original: str, retry: str) -> str:
    """Generate a coloured HTML diff between original and retry answers."""
    original_lines = original.splitlines(keepends=True)
    retry_lines = retry.splitlines(keepends=True)
    diff = difflib.HtmlDiff(tabsize=2)
    table = diff.make_table(
        original_lines, retry_lines,
        fromdesc='Original Answer', todesc='Retry Answer',
        context=True, numlines=3,
    )
    return table


def _render_inline_diff(original: str, retry: str) -> str:
    """Generate a simple inline diff with colour markers."""
    sm = difflib.SequenceMatcher(None, original.split(), retry.split())
    parts = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            parts.append(' '.join(original.split()[i1:i2]))
        elif tag == 'replace':
            parts.append(f'~~{" ".join(original.split()[i1:i2])}~~')
            parts.append(f'**{" ".join(retry.split()[j1:j2])}**')
        elif tag == 'delete':
            parts.append(f'~~{" ".join(original.split()[i1:i2])}~~')
        elif tag == 'insert':
            parts.append(f'**{" ".join(retry.split()[j1:j2])}**')
    return ' '.join(parts)


def render() -> None:
    st.header('📊 Feedback & Report')
    evaluations = st.session_state.evaluations

    if not evaluations:
        st.info('No evaluations yet — run an interview first.')
        return

    # Build evaluation pipeline with the same provider used in the session.
    bundle = st.session_state.get('provider_bundle')
    text_provider = bundle.text_provider if bundle else None
    pipeline = EvaluationPipeline(text_provider=text_provider)

    if text_provider is None:
        st.warning(
            '⚠️ No LLM provider available — retry evaluations will use heuristic scoring only. '
            'Configure OPENAI_API_KEY or GEMINI_API_KEY for LLM-powered feedback.'
        )

    # Per-question breakdown with retry
    with st.expander('Question-by-Question Breakdown', expanded=True):
        for evaluation in evaluations:
            st.subheader(f'Question: {evaluation.question_id}')
            col1, col2 = st.columns(2)
            col1.metric('Score', f'{evaluation.rubric_score.weighted_total:.1f}')
            col2.write(f'**Evidence:** {evaluation.answer_analysis.transcript_evidence[:2]}')

            st.markdown(pipeline.to_human_critique(evaluation))

            # ── Answer Retry with Diff Highlighting (Suggestion 13) ──
            with st.expander(f'🔄 Retry Answer — {evaluation.question_id}'):
                # Show the original answer
                original_answer = ' '.join(evaluation.answer_analysis.transcript_evidence)
                st.markdown('**Original answer evidence:**')
                st.text(original_answer[:500] if original_answer else 'No evidence captured.')

                retry_key = f'retry_{evaluation.question_id}'
                retry_text = st.text_area(
                    'Try a better answer:',
                    height=120,
                    key=retry_key,
                    placeholder='Re-answer using the coaching feedback above...',
                )

                if st.button(f'Submit Retry — {evaluation.question_id}', key=f'btn_retry_{evaluation.question_id}'):
                    if retry_text:
                        # Store retry
                        if evaluation.question_id not in st.session_state.retry_answers:
                            st.session_state.retry_answers[evaluation.question_id] = []
                        st.session_state.retry_answers[evaluation.question_id].append(retry_text)

                        # Re-evaluate using session interview type when available
                        state = st.session_state.session_state
                        from models.schemas import InterviewType
                        interview_type = (
                            state.interview_type
                            if state
                            else InterviewType.BEHAVIOURAL
                        )
                        retry_eval = pipeline.evaluate_answer(
                            evaluation.question_id, retry_text, interview_type,
                        )

                        # Show improvement
                        delta = retry_eval.rubric_score.weighted_total - evaluation.rubric_score.weighted_total
                        col_a, col_b = st.columns(2)
                        col_a.metric('Original Score', f'{evaluation.rubric_score.weighted_total:.1f}')
                        col_b.metric('Retry Score', f'{retry_eval.rubric_score.weighted_total:.1f}',
                                     delta=f'{delta:+.1f}')

                        # Diff highlighting
                        st.markdown('### Improvements Highlighted')
                        diff_text = _render_inline_diff(original_answer, retry_text)
                        st.markdown(diff_text)

                        st.markdown(pipeline.to_human_critique(retry_eval))
                    else:
                        st.warning('Please enter a retry answer.')

                # Show previous retries
                retries = st.session_state.retry_answers.get(evaluation.question_id, [])
                if retries:
                    st.markdown(f'**Previous retries:** {len(retries)}')
                    for idx, r in enumerate(retries):
                        st.caption(f'Retry {idx + 1}: {r[:100]}...' if len(r) > 100 else f'Retry {idx + 1}: {r}')

            with st.expander('Raw JSON analysis'):
                st.json(json.loads(pipeline.to_structured_json(evaluation)))
            st.divider()

    # Full session report
    with st.expander('Full Session Report', expanded=False):
        state = st.session_state.session_state
        competency_map = state.competency_coverage if state else {}
        report = pipeline.build_session_report(evaluations, competency_map, interviewer_feedback={})
        st.json(report.model_dump(mode='json'))

        col_json, col_md = st.columns(2)
        if col_json.button('Export JSON'):
            save_report_json(report, '/tmp/interview_report.json')
            st.success('Saved to /tmp/interview_report.json')
        if col_md.button('Export Markdown'):
            save_report_markdown(report, '/tmp/interview_report.md')
            st.success('Saved to /tmp/interview_report.md')
