import json
import logging
import re
from pathlib import Path
from typing import Optional

from models.schemas import CandidateProfile
from providers.base import TextGenerationProvider

logger = logging.getLogger(__name__)

# ── LLM-powered parsing prompt ────────────────────────────────────────────
_RESUME_PARSE_PROMPT = """\
Extract structured information from this resume text. Return ONLY valid JSON
with exactly these keys (use empty string or empty list if not found):

{{
  "name": "Full name of the candidate",
  "summary": "Brief professional summary (2-3 sentences)",
  "education": ["degree / institution / year entries"],
  "work_experience": ["role — company — dates — key responsibilities"],
  "projects": ["project name — description"],
  "skills": ["individual skill or technology"],
  "leadership": ["leadership experience entries"],
  "achievements": ["achievement entries with metrics if available"],
  "target_role": "target role if mentioned, else empty string",
  "target_company": "target company if mentioned, else empty string"
}}

Resume text:
{resume_text}
"""


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.warning(
            'pypdf package not installed — cannot extract PDF text. '
            'Install with: pip install pypdf'
        )
        return ''
    except Exception:
        logger.exception('Unexpected error importing pypdf')
        return ''

    try:
        reader = PdfReader(str(path))
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        if not text.strip():
            logger.warning('PDF extraction returned empty text for: %s', path)
        return text
    except Exception:
        logger.exception('Failed to extract text from PDF: %s', path)
        return ''


def _extract_docx_text(path: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        logger.warning(
            'python-docx package not installed — cannot extract DOCX text. '
            'Install with: pip install python-docx'
        )
        return ''
    except Exception:
        logger.exception('Unexpected error importing python-docx')
        return ''

    try:
        doc = Document(str(path))
        text = '\n'.join(p.text for p in doc.paragraphs)
        if not text.strip():
            logger.warning('DOCX extraction returned empty text for: %s', path)
        return text
    except Exception:
        logger.exception('Failed to extract text from DOCX: %s', path)
        return ''


def extract_resume_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        logger.warning('Resume file not found: %s', file_path)
        return ''
    if path.suffix.lower() == '.pdf':
        return _extract_pdf_text(path)
    if path.suffix.lower() == '.docx':
        return _extract_docx_text(path)
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        logger.exception('Failed to read resume file: %s', file_path)
        return ''


def parse_resume_to_profile(
    raw_text: str,
    text_provider: Optional[TextGenerationProvider] = None,
) -> CandidateProfile:
    """Parse resume text into a CandidateProfile.

    Uses the LLM provider when available for high-quality extraction.
    Falls back to improved heuristic keyword matching otherwise.
    """
    if text_provider is not None:
        profile = _llm_parse(raw_text, text_provider)
        if profile is not None:
            return profile
        logger.warning('LLM resume parsing failed — falling back to heuristic parser.')

    return _heuristic_parse(raw_text)


def _llm_parse(raw_text: str, provider: TextGenerationProvider) -> Optional[CandidateProfile]:
    """Attempt LLM-based resume parsing. Returns None on failure."""
    prompt = _RESUME_PARSE_PROMPT.format(resume_text=raw_text[:6000])
    try:
        result = provider.generate_text(prompt, system_prompt='You are a resume parsing assistant. Return only valid JSON, nothing else.')
        if not result or result.startswith('['):
            return None
        # Strip markdown fences if present
        cleaned = result.strip()
        if cleaned.startswith('```'):
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start == -1 or end == -1:
            return None
        data = json.loads(cleaned[start:end + 1])
        return CandidateProfile(
            name=data.get('name', ''),
            summary=data.get('summary', ''),
            education=data.get('education', []),
            work_experience=data.get('work_experience', []),
            projects=data.get('projects', []),
            skills=data.get('skills', []),
            leadership=data.get('leadership', []),
            achievements=data.get('achievements', []),
            target_role=data.get('target_role', ''),
            target_company=data.get('target_company', ''),
        )
    except Exception:
        logger.exception('LLM resume parse attempt failed')
        return None


# ── Section-header based heuristic parser ──────────────────────────────────

# Common resume section headers (lowercased)
_SECTION_HEADERS = {
    'education': 'education',
    'academic': 'education',
    'qualifications': 'education',
    'experience': 'work_experience',
    'work experience': 'work_experience',
    'professional experience': 'work_experience',
    'employment': 'work_experience',
    'employment history': 'work_experience',
    'work history': 'work_experience',
    'projects': 'projects',
    'personal projects': 'projects',
    'skills': 'skills',
    'technical skills': 'skills',
    'technologies': 'skills',
    'competencies': 'skills',
    'core competencies': 'skills',
    'leadership': 'leadership',
    'leadership experience': 'leadership',
    'volunteer': 'leadership',
    'achievements': 'achievements',
    'accomplishments': 'achievements',
    'awards': 'achievements',
    'honors': 'achievements',
    'certifications': 'achievements',
    'summary': 'summary',
    'professional summary': 'summary',
    'profile': 'summary',
    'objective': 'summary',
    'about': 'summary',
    'about me': 'summary',
}


def _is_section_header(line: str) -> Optional[str]:
    """Check if a line looks like a section header. Returns section key or None."""
    stripped = line.strip().rstrip(':').strip()
    lowered = stripped.lower()
    # Exact match
    if lowered in _SECTION_HEADERS:
        return _SECTION_HEADERS[lowered]
    # Header might be decorated (e.g., "== Education ==" or "--- SKILLS ---")
    cleaned = re.sub(r'^[\s\-=*#|]+|[\s\-=*#|]+$', '', lowered).strip()
    if cleaned in _SECTION_HEADERS:
        return _SECTION_HEADERS[cleaned]
    return None


def _heuristic_parse(raw_text: str) -> CandidateProfile:
    """Improved heuristic parser that uses section headers and keyword matching."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Try to identify name from the first non-empty line(s) that look like a name
    name = ''
    summary = ''
    for i, line in enumerate(lines[:5]):
        # Names are typically short, title-case, and don't contain section keywords
        if not name and len(line.split()) <= 5 and not _is_section_header(line):
            # Skip lines that look like addresses, emails, or phone numbers
            if not re.search(r'[@|•]|\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|http', line):
                name = line
                continue
        if not summary and name and len(line) > 20 and not _is_section_header(line):
            # Skip contact info lines
            if not re.search(r'[@|•]|\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|http', line):
                summary = line
                break

    # Section-based extraction
    sections: dict[str, list[str]] = {
        'education': [], 'work_experience': [], 'projects': [],
        'skills': [], 'leadership': [], 'achievements': [], 'summary_lines': [],
    }
    current_section: Optional[str] = None

    for line in lines:
        header = _is_section_header(line)
        if header:
            current_section = header if header != 'summary' else 'summary_lines'
            continue
        if current_section and current_section in sections:
            sections[current_section].append(line)

    # If section-based extraction found content, use it
    has_sections = any(v for v in sections.values())

    if has_sections:
        # Use section-based summary if available and better
        if sections['summary_lines'] and len(' '.join(sections['summary_lines'])) > len(summary):
            summary = ' '.join(sections['summary_lines'][:3])

        # Extract individual skills from skill lines (split on commas, pipes, bullets)
        raw_skills = []
        for skill_line in sections['skills']:
            parts = re.split(r'[,|•·;]', skill_line)
            raw_skills.extend(p.strip() for p in parts if p.strip() and len(p.strip()) < 50)
        if not raw_skills:
            raw_skills = sections['skills']

        profile = CandidateProfile(
            name=name,
            summary=summary,
            education=sections['education'],
            work_experience=sections['work_experience'],
            projects=sections['projects'],
            skills=raw_skills,
            leadership=sections['leadership'],
            achievements=sections['achievements'],
        )
    else:
        # Fall back to keyword matching
        def collect_keywords(keywords: list[str]) -> list[str]:
            return [line for line in lines if any(k in line.lower() for k in keywords)]

        # Extended keyword lists for better matching
        profile = CandidateProfile(
            name=name,
            summary=summary,
            education=collect_keywords([
                'university', 'college', 'bachelor', 'master', 'phd', 'degree',
                'diploma', 'school', 'institute', 'b.s.', 'b.a.', 'm.s.', 'm.a.',
                'mba', 'certification', 'certified',
            ]),
            work_experience=collect_keywords([
                'engineer', 'developer', 'manager', 'intern', 'analyst', 'architect',
                'consultant', 'designer', 'director', 'specialist', 'coordinator',
                'administrator', 'scientist', 'researcher', 'associate', 'senior',
                'junior', 'lead', 'head of', 'vp', 'cto', 'ceo',
            ]),
            projects=collect_keywords([
                'project', 'built', 'developed', 'launched', 'created', 'designed',
                'implemented', 'deployed', 'open source', 'hackathon', 'capstone',
            ]),
            skills=collect_keywords([
                'python', 'java', 'sql', 'aws', 'docker', 'kubernetes', 'react',
                'javascript', 'typescript', 'node', 'go', 'rust', 'c++', 'c#',
                'azure', 'gcp', 'linux', 'git', 'terraform', 'jenkins', 'ci/cd',
                'machine learning', 'deep learning', 'data science', 'agile',
                'scrum', 'html', 'css', 'vue', 'angular', 'django', 'flask',
                'spring', 'graphql', 'rest', 'api', 'microservice', 'kafka',
                'redis', 'mongodb', 'postgresql', 'mysql', 'elasticsearch',
            ]),
            leadership=collect_keywords([
                'lead', 'managed', 'mentored', 'owned', 'directed', 'supervised',
                'coordinated', 'organized', 'founded', 'co-founded', 'headed',
                'team of', 'spearheaded',
            ]),
            achievements=collect_keywords([
                'improved', 'reduced', 'increased', '%', 'award', 'recognized',
                'promoted', 'achieved', 'exceeded', 'patent', 'published',
                'revenue', 'savings', 'growth',
            ]),
        )

    # Look for target role / company
    lower = raw_text.lower()
    if 'target role:' in lower:
        marker = 'target role:'
        marker_idx = lower.find(marker)
        target_section = raw_text[marker_idx + len(marker):].strip()
        if target_section:
            profile.target_role = target_section.splitlines()[0].strip()

    if 'target company:' in lower:
        marker = 'target company:'
        marker_idx = lower.find(marker)
        target_section = raw_text[marker_idx + len(marker):].strip()
        if target_section:
            profile.target_company = target_section.splitlines()[0].strip()

    return profile
