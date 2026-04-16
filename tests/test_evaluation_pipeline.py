import unittest

from evaluation.pipeline import EvaluationPipeline
from models.schemas import InterviewType


class EvaluationPipelineTests(unittest.TestCase):
    def test_pipeline_outputs_json_then_human_critique(self):
        pipeline = EvaluationPipeline()
        answer = (
            'In my last role our checkout service timed out during peak traffic. '
            'My goal was latency below 300ms. '
            'I redesigned caching and optimized 3 queries. '
            'This reduced p95 latency by 42% and incident pages by half. '
            'I learned to set SLOs with stakeholders earlier.'
        )

        evaluation = pipeline.evaluate_answer('q1', answer, InterviewType.TECHNICAL)
        structured = pipeline.to_structured_json(evaluation)
        critique = pipeline.to_human_critique(evaluation)

        self.assertIn('rubric_score', structured)
        self.assertIn('transcript_evidence', structured)
        self.assertIn('Weighted score', critique)
        self.assertIn('Evidence used', critique)

    def test_gap_analysis_detects_missing_metrics(self):
        pipeline = EvaluationPipeline()
        answer = 'I worked with my team and improved things but cannot share specific outcomes.'
        evaluation = pipeline.evaluate_answer('q2', answer, InterviewType.BEHAVIOURAL)

        self.assertTrue(evaluation.gap_analysis.no_metrics)
        self.assertTrue(evaluation.gap_analysis.vague_results)


if __name__ == '__main__':
    unittest.main()
