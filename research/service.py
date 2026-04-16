from dataclasses import dataclass


@dataclass
class ResearchResult:
    subject: str
    likely_background: str
    function_department: str
    speaking_style_clues: str
    company_role_context: str
    confidence: float
    citations: list[str]


class ResearchService:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def search(self, subject: str) -> list[dict]:
        if not self.enabled:
            return []
        return []

    def extract(self, findings: list[dict]) -> dict:
        if not findings:
            return {}
        return {
            'likely_background': str(findings)[:120],
            'function_department': 'Unknown',
            'speaking_style_clues': 'Insufficient data',
            'company_role_context': 'Insufficient data',
        }

    def summarize(self, subject: str, extracted: dict, findings: list[dict]) -> ResearchResult:
        confidence = min(1.0, len(findings) / 5)
        if confidence < 0.4:
            return ResearchResult(
                subject=subject,
                likely_background='Fallback to archetypal behavior',
                function_department='Unknown',
                speaking_style_clues='Not enough public data; use role archetype.',
                company_role_context='Not enough public data; use user-provided context.',
                confidence=confidence,
                citations=[f.get('url', '') for f in findings],
            )
        return ResearchResult(
            subject=subject,
            likely_background=extracted.get('likely_background', ''),
            function_department=extracted.get('function_department', ''),
            speaking_style_clues=extracted.get('speaking_style_clues', ''),
            company_role_context=extracted.get('company_role_context', ''),
            confidence=confidence,
            citations=[f.get('url', '') for f in findings],
        )

    def research_subject(self, subject: str) -> ResearchResult:
        findings = self.search(subject)
        extracted = self.extract(findings)
        return self.summarize(subject, extracted, findings)
