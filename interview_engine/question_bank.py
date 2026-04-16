from models.schemas import CompetencyTag, InterviewType, InterviewerRole, Question


class QuestionBank:
    def __init__(self) -> None:
        self.questions = [
            Question(
                id='b1',
                text='Tell me about a time you resolved a conflict on your team.',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='mid',
                role_family='general',
                competencies=[CompetencyTag.CONFLICT_RESOLUTION, CompetencyTag.COLLABORATION],
                difficulty=2,
                interviewer_type=InterviewerRole.HR,
            ),
            Question(
                id='b2',
                text='Describe a time you took ownership in an ambiguous situation.',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='senior',
                role_family='general',
                competencies=[CompetencyTag.OWNERSHIP, CompetencyTag.ADAPTABILITY],
                difficulty=3,
                interviewer_type=InterviewerRole.SENIOR_LEADERSHIP,
            ),
            Question(
                id='t1',
                text='Walk me through a system you designed and key tradeoffs.',
                interview_type=InterviewType.TECHNICAL,
                seniority='senior',
                role_family='engineering',
                competencies=[CompetencyTag.TECHNICAL_DEPTH, CompetencyTag.PROBLEM_SOLVING],
                difficulty=4,
                interviewer_type=InterviewerRole.TECHNICAL,
            ),
            Question(
                id='h1',
                text='How do you balance speed versus reliability under stakeholder pressure?',
                interview_type=InterviewType.HYBRID,
                seniority='senior',
                role_family='engineering',
                competencies=[CompetencyTag.BUSINESS_AWARENESS, CompetencyTag.STAKEHOLDER_MANAGEMENT],
                difficulty=4,
                interviewer_type=InterviewerRole.SENIOR_LEADERSHIP,
            ),
            Question(
                id='t2',
                text='Tell me about a difficult production incident and how you debugged it.',
                interview_type=InterviewType.TECHNICAL,
                seniority='mid',
                role_family='engineering',
                competencies=[CompetencyTag.PROBLEM_SOLVING, CompetencyTag.COMMUNICATION_CLARITY],
                difficulty=3,
                interviewer_type=InterviewerRole.TECHNICAL,
            ),
        ]

    def filter_questions(self, interview_type: InterviewType, max_difficulty: int = 5) -> list[Question]:
        return [
            q
            for q in self.questions
            if q.interview_type in {interview_type, InterviewType.HYBRID} and q.difficulty <= max_difficulty
        ]
