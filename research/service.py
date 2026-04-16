"""Web research service — Tavily-powered search with extract → summarize pipeline.

Implements Suggestion 2: real web research integration.
Uses Tavily (AI-optimised search API) when SEARCH_API_KEY is set.
Falls back gracefully to archetypal behavior when unavailable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    subject: str
    likely_background: str
    function_department: str
    speaking_style_clues: str
    company_role_context: str
    confidence: float
    citations: list[str]


def _get_tavily():  # noqa: ANN202
    """Lazy-import tavily so the app works even if the package is missing."""
    try:
        from tavily import TavilyClient
        return TavilyClient
    except ImportError:
        return None


class ResearchService:
    def __init__(self, enabled: bool = False, api_key: str = '') -> None:
        self.enabled = enabled
        self.api_key = api_key

    def search(self, subject: str) -> list[dict]:
        if not self.enabled:
            return []
        TavilyClient = _get_tavily()
        if TavilyClient is None or not self.api_key:
            logger.info('Tavily not available — returning empty search results.')
            return []
        try:
            client = TavilyClient(api_key=self.api_key)
            response = client.search(
                query=f'{subject} professional background LinkedIn',
                search_depth='basic',
                max_results=5,
            )
            results = response.get('results', [])
            return [
                {
                    'title': r.get('title', ''),
                    'url': r.get('url', ''),
                    'content': r.get('content', ''),
                }
                for r in results
            ]
        except Exception:
            logger.exception('Tavily search failed for subject: %s', subject)
            return []

    def extract(self, findings: list[dict]) -> dict:
        if not findings:
            return {}
        combined_content = ' '.join(f.get('content', '') for f in findings)
        return {
            'likely_background': combined_content[:300],
            'function_department': 'Unknown',
            'speaking_style_clues': 'Derived from web search data.',
            'company_role_context': combined_content[300:600] if len(combined_content) > 300 else 'Insufficient data',
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
