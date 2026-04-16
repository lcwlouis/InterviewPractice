"""Local storage helpers for interview session reports — JSON and Markdown."""

import json
from pathlib import Path

from models.schemas import SessionReport


def save_report_json(report: SessionReport, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.model_dump(mode='json'), indent=2), encoding='utf-8')


def save_report_markdown(report: SessionReport, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        '# Interview Feedback Report',
        '',
        f'## Overall Summary\n\n{report.overall_summary}',
        '',
    ]

    # Score table
    if report.interview_score_by_category:
        lines.append('## Scores by Category\n')
        lines.append('| Category | Score |')
        lines.append('|----------|-------|')
        for category, score in report.interview_score_by_category.items():
            lines.append(f'| {category} | {score} |')
        lines.append('')

    # Best / weakest
    if report.best_answer_question_id:
        lines.append(f'**Best answer:** {report.best_answer_question_id}')
    if report.weakest_answer_question_id:
        lines.append(f'**Weakest answer:** {report.weakest_answer_question_id}')
    lines.append('')

    # Communication & presence
    if report.communication_observations:
        lines.append('## Communication Observations\n')
        for obs in report.communication_observations:
            lines.append(f'- {obs}')
        lines.append('')

    if report.confidence_presence_observations:
        lines.append('## Confidence & Presence\n')
        for obs in report.confidence_presence_observations:
            lines.append(f'- {obs}')
        lines.append('')

    # Missed opportunities
    if report.missed_opportunities:
        lines.append('## Missed Opportunities\n')
        for item in report.missed_opportunities:
            lines.append(f'- {item}')
        lines.append('')

    # Drills
    if report.suggested_drills:
        lines.append('## Suggested Drills\n')
        for drill in report.suggested_drills:
            lines.append(f'- {drill}')
        lines.append('')

    # Top 3 actions
    if report.top_3_actions:
        lines.append('## Top 3 Actions Before Your Real Interview\n')
        for idx, action in enumerate(report.top_3_actions, 1):
            lines.append(f'{idx}. {action}')
        lines.append('')

    # Question-by-question breakdown
    if report.question_breakdown:
        lines.append('## Question-by-Question Breakdown\n')
        for qid, evaluation in report.question_breakdown.items():
            lines.append(f'### {qid}\n')
            lines.append(f'- **Score:** {evaluation.rubric_score.weighted_total}')
            lines.append(f'- **What worked:** {", ".join(evaluation.coaching_feedback.what_worked) or "—"}')
            lines.append(f'- **What was weak:** {", ".join(evaluation.coaching_feedback.what_was_weak) or "—"}')
            lines.append(f'- **Missing:** {", ".join(evaluation.coaching_feedback.what_was_missing) or "—"}')
            if evaluation.coaching_feedback.stronger_answer_outline:
                lines.append(f'- **Better outline:** {evaluation.coaching_feedback.stronger_answer_outline}')
            lines.append('')

    path.write_text('\n'.join(lines), encoding='utf-8')
