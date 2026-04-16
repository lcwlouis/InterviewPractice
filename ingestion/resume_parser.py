from pathlib import Path

from models.schemas import CandidateProfile


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ''

    reader = PdfReader(str(path))
    return '\n'.join(page.extract_text() or '' for page in reader.pages)


def _extract_docx_text(path: Path) -> str:
    try:
        from docx import Document
    except Exception:
        return ''

    doc = Document(str(path))
    return '\n'.join(p.text for p in doc.paragraphs)


def extract_resume_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return ''
    if path.suffix.lower() == '.pdf':
        return _extract_pdf_text(path)
    if path.suffix.lower() == '.docx':
        return _extract_docx_text(path)
    return path.read_text(encoding='utf-8', errors='ignore')


def parse_resume_to_profile(raw_text: str) -> CandidateProfile:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    def collect_keywords(keywords: list[str]) -> list[str]:
        return [line for line in lines if any(k in line.lower() for k in keywords)]

    profile = CandidateProfile(
        name=lines[0] if lines else '',
        summary=lines[1] if len(lines) > 1 else '',
        education=collect_keywords(['university', 'college', 'bachelor', 'master', 'phd']),
        work_experience=collect_keywords(['engineer', 'developer', 'manager', 'intern']),
        projects=collect_keywords(['project', 'built', 'developed', 'launched']),
        skills=collect_keywords(['python', 'java', 'sql', 'aws', 'docker', 'kubernetes']),
        leadership=collect_keywords(['lead', 'managed', 'mentored', 'owned']),
        achievements=collect_keywords(['improved', 'reduced', 'increased', '%', 'award']),
    )

    lower = raw_text.lower()
    if 'target role:' in lower:
        marker = 'target role:'
        marker_idx = lower.find(marker)
        target_section = raw_text[marker_idx + len(marker):].strip()
        if target_section:
            profile.target_role = target_section.splitlines()[0].strip()
    return profile
