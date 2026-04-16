from models.schemas import InterviewType


RUBRIC_WEIGHTS = {
    InterviewType.BEHAVIOURAL: {
        'structure': 0.2,
        'specificity': 0.2,
        'ownership': 0.15,
        'reflection': 0.15,
        'business_impact': 0.1,
        'communication': 0.2,
    },
    InterviewType.TECHNICAL: {
        'structure': 0.15,
        'specificity': 0.15,
        'ownership': 0.1,
        'reflection': 0.1,
        'technical_depth': 0.3,
        'problem_solving': 0.2,
    },
    InterviewType.HYBRID: {
        'structure': 0.15,
        'specificity': 0.15,
        'ownership': 0.15,
        'reflection': 0.1,
        'technical_depth': 0.2,
        'business_impact': 0.1,
        'communication': 0.15,
    },
}
