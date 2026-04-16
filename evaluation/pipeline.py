import json
import re
from statistics import mean

from evaluation.rubrics import RUBRIC_WEIGHTS
from models.schemas import (
    AnswerAnalysis,
    CoachingFeedback,
    GapAnalysis,
    InterviewType,
    QuestionEvaluation,
    RubricScore,
    SessionReport,
)


class EvaluationPipeline:
    def decompose_answer(self, question_id: str, answer_text: str) -> AnswerAnalysis:
        snippets = [s.strip() for s in re.split(r'[.!?]', answer_text) if s.strip()]

        def pick(*keywords: str) -> str:
            for snippet in snippets:
                lowered = snippet.lower()
                if any(k in lowered for k in keywords):
                    return snippet
            return ''

        analysis = AnswerAnalysis(
            question_id=question_id,
            claimed_context=pick('when', 'at', 'in my role', 'team'),
            goal_or_task=pick('goal', 'task', 'needed to', 'objective'),
            actions_taken=pick('i built', 'i implemented', 'i led', 'i changed', 'i created'),
            technical_details=pick('architecture', 'system', 'api', 'database', 'latency', 'debug'),
            result_outcome=pick('result', 'impact', 'improved', 'reduced', 'increased', '%'),
            learning_reflection=pick('learned', 'next time', 'would', 'reflection'),
            emotional_interpersonal_signals=pick('team', 'stakeholder', 'mentor', 'conflict'),
            transcript_evidence=snippets[:4],
        )
        if not analysis.claimed_context:
            analysis.missing_evidence.append('No concrete situation/context stated.')
        if not analysis.actions_taken:
            analysis.missing_evidence.append('No clear actions taken by candidate.')
        if not analysis.result_outcome:
            analysis.missing_evidence.append('No measurable result or outcome presented.')
        if not analysis.learning_reflection:
            analysis.missing_evidence.append('No explicit learning/reflection provided.')
        return analysis

    def score_rubric(self, analysis: AnswerAnalysis, interview_type: InterviewType) -> RubricScore:
        weights = RUBRIC_WEIGHTS[interview_type]

        def binary_score(value: str) -> float:
            return 9.0 if value else 3.0

        category_scores = {
            'structure': 8.0 if analysis.claimed_context and analysis.actions_taken and analysis.result_outcome else 4.0,
            'specificity': 8.0 if len(' '.join(analysis.transcript_evidence)) > 80 else 4.5,
            'ownership': binary_score(analysis.actions_taken),
            'reflection': binary_score(analysis.learning_reflection),
            'business_impact': binary_score(analysis.result_outcome),
            'technical_depth': binary_score(analysis.technical_details),
            'problem_solving': binary_score(analysis.actions_taken),
            'communication': 7.5 if len(analysis.transcript_evidence) >= 2 else 4.0,
        }

        weighted_total = 0.0
        reasoning = {}
        for category, weight in weights.items():
            score = category_scores.get(category, 0.0)
            weighted_total += score * weight
            reasoning[category] = f'Score={score:.1f}; evidence={analysis.transcript_evidence[:2]}'

        return RubricScore(category_scores=category_scores, weighted_total=round(weighted_total, 2), reasoning=reasoning)

    def analyze_gaps(self, analysis: AnswerAnalysis) -> GapAnalysis:
        text = ' '.join(analysis.transcript_evidence).lower()
        has_metric = bool(re.search(r'\b\d+%?\b', text))
        has_result_statement = bool(analysis.result_outcome)
        return GapAnalysis(
            weak_ownership=not bool(analysis.actions_taken),
            vague_results=not has_result_statement or not has_metric,
            no_metrics=not has_metric,
            insufficient_technical_depth=not bool(analysis.technical_details),
            poor_structure=not bool(analysis.claimed_context and analysis.actions_taken and analysis.result_outcome),
            weak_reflection=not bool(analysis.learning_reflection),
            ignored_business_impact='business' not in text and not bool(analysis.result_outcome),
            did_not_answer_question=not bool(analysis.actions_taken or analysis.result_outcome),
            notes=list(analysis.missing_evidence),
        )

    def synthesize_rewrite_outline(self, gap: GapAnalysis) -> str:
        improvements = []
        if gap.poor_structure:
            improvements.append('Use STAR: Situation, Task, Actions, Result, Learning.')
        if gap.no_metrics:
            improvements.append('Add measurable outcomes (%, time, dollars, reliability).')
        if gap.insufficient_technical_depth:
            improvements.append('Include system components and tradeoff decisions.')
        if gap.weak_reflection:
            improvements.append('Close with reflection and what you would improve.')
        return ' '.join(improvements) or 'Keep concise structure and explicit action-outcome links.'

    def build_coaching_feedback(self, analysis: AnswerAnalysis, gap: GapAnalysis, rewrite_outline: str) -> CoachingFeedback:
        missing = []
        if gap.no_metrics:
            missing.append('Quantitative impact metrics')
        if gap.insufficient_technical_depth:
            missing.append('Technical implementation detail')
        if gap.weak_reflection:
            missing.append('Reflection / learning')

        return CoachingFeedback(
            what_worked=['Included concrete transcript evidence.'] if analysis.transcript_evidence else [],
            what_was_weak=list(analysis.missing_evidence),
            what_was_missing=missing,
            likely_interviewer_inference=[
                'Interviewer may infer limited ownership.' if gap.weak_ownership else 'Interviewer sees signs of ownership.',
                'Interviewer may question impact scale.' if gap.no_metrics else 'Interviewer can gauge impact scale.',
            ],
            immediate_improvements=[
                'Lead with concise context and specific responsibility.',
                'Emphasize concrete actions and tradeoffs.',
                'Close with measurable result and learning.',
            ],
            stronger_answer_outline=rewrite_outline,
            retry_prompt='Retry in 90 seconds using STAR and at least one metric.',
        )

    def evaluate_answer(self, question_id: str, answer_text: str, interview_type: InterviewType) -> QuestionEvaluation:
        analysis = self.decompose_answer(question_id, answer_text)
        rubric = self.score_rubric(analysis, interview_type)
        gaps = self.analyze_gaps(analysis)
        rewrite = self.synthesize_rewrite_outline(gaps)
        coaching = self.build_coaching_feedback(analysis, gaps, rewrite)
        return QuestionEvaluation(
            question_id=question_id,
            answer_analysis=analysis,
            rubric_score=rubric,
            gap_analysis=gaps,
            coaching_feedback=coaching,
        )

    def to_structured_json(self, evaluation: QuestionEvaluation) -> str:
        return json.dumps(evaluation.model_dump(mode='json'), indent=2)

    def to_human_critique(self, evaluation: QuestionEvaluation) -> str:
        data = evaluation.model_dump(mode='json')
        return (
            f"Question {data['question_id']} critique:\n"
            f"- Weighted score: {data['rubric_score']['weighted_total']}\n"
            f"- Evidence used: {data['answer_analysis']['transcript_evidence']}\n"
            f"- What worked: {', '.join(data['coaching_feedback']['what_worked']) or 'None'}\n"
            f"- What was weak: {', '.join(data['coaching_feedback']['what_was_weak']) or 'None'}\n"
            f"- What was missing: {', '.join(data['coaching_feedback']['what_was_missing']) or 'None'}\n"
            f"- Immediate improvements: {', '.join(data['coaching_feedback']['immediate_improvements'])}\n"
            f"- Better outline: {data['coaching_feedback']['stronger_answer_outline']}"
        )

    def build_session_report(self, evaluations: list[QuestionEvaluation], competency_map: dict, interviewer_feedback: dict) -> SessionReport:
        if not evaluations:
            return SessionReport(
                overall_summary='No answers were evaluated.',
                interview_score_by_category={},
                interviewer_feedback=interviewer_feedback,
                question_breakdown={},
                competency_coverage_map=competency_map,
            )

        best = max(evaluations, key=lambda e: e.rubric_score.weighted_total)
        worst = min(evaluations, key=lambda e: e.rubric_score.weighted_total)
        categories = evaluations[0].rubric_score.category_scores.keys()

        score_by_category = {
            category: round(mean(e.rubric_score.category_scores.get(category, 0) for e in evaluations), 2)
            for category in categories
        }

        return SessionReport(
            overall_summary='Candidate showed progress with opportunities to improve specificity and evidence.',
            interview_score_by_category=score_by_category,
            interviewer_feedback=interviewer_feedback,
            question_breakdown={e.question_id: e for e in evaluations},
            competency_coverage_map=competency_map,
            best_answer_question_id=best.question_id,
            weakest_answer_question_id=worst.question_id,
            missed_opportunities=['Add more metrics', 'Tie decisions to business impact'],
            stronger_rewrites={e.question_id: e.coaching_feedback.stronger_answer_outline or '' for e in evaluations},
            communication_observations=['Some answers were concise; others needed tighter structure.'],
            body_language_observations=['Body language requires multimodal provider integration.'],
            confidence_presence_observations=['Confidence improved when discussing direct ownership.'],
            suggested_drills=['90-second STAR drill', 'Tradeoff explanation drill', 'Metric anchoring drill'],
            top_3_actions=['Quantify impact', 'Improve answer structure', 'Add reflection consistently'],
        )
