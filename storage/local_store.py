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
        f'## Overall summary\n{report.overall_summary}',
        '',
        '## Interview score by category',
    ]
    for category, score in report.interview_score_by_category.items():
        lines.append(f'- **{category}**: {score}')

    lines.append('')
    lines.append('## Top 3 actions before your real interview')
    for item in report.top_3_actions:
        lines.append(f'- {item}')

    path.write_text('\n'.join(lines), encoding='utf-8')
