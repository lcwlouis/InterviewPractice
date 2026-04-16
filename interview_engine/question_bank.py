"""Deliberate question bank organised by interview type, seniority,
role family, competency, difficulty, and interviewer type.

The original design requires intentional question selection, not random
generation.  Every question is tagged with the competencies it tests.
"""

from models.schemas import CompetencyTag, InterviewPhase, InterviewType, InterviewerRole, Question


class QuestionBank:
    def __init__(self) -> None:
        self.questions: list[Question] = [
            # ── Warm-up / opening ──────────────────────────────────────
            Question(
                id='w1',
                text='Walk me through your background and what brings you here today.',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='any',
                role_family='general',
                competencies=[CompetencyTag.COMMUNICATION_CLARITY, CompetencyTag.MOTIVATION],
                difficulty=1,
                interviewer_type=InterviewerRole.HR,
                phase=InterviewPhase.WARMUP,
            ),
            Question(
                id='w2',
                text='What about this role or company excites you the most?',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='any',
                role_family='general',
                competencies=[CompetencyTag.MOTIVATION, CompetencyTag.BUSINESS_AWARENESS],
                difficulty=1,
                interviewer_type=InterviewerRole.HR,
                phase=InterviewPhase.WARMUP,
            ),
            # ── Behavioural — HR ───────────────────────────────────────
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
                id='b3',
                text='Tell me about a time you had to deliver difficult feedback to a peer.',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='mid',
                role_family='general',
                competencies=[CompetencyTag.COMMUNICATION_CLARITY, CompetencyTag.COLLABORATION],
                difficulty=2,
                interviewer_type=InterviewerRole.HR,
            ),
            Question(
                id='b4',
                text='Describe a situation where you had to adapt your approach after initial failure.',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='mid',
                role_family='general',
                competencies=[CompetencyTag.ADAPTABILITY, CompetencyTag.LEARNING_MINDSET],
                difficulty=3,
                interviewer_type=InterviewerRole.HR,
            ),
            Question(
                id='b5',
                text='Give an example of how you motivated a struggling team member.',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='senior',
                role_family='general',
                competencies=[CompetencyTag.LEADERSHIP, CompetencyTag.COLLABORATION],
                difficulty=3,
                interviewer_type=InterviewerRole.HR,
            ),
            Question(
                id='b6',
                text='Tell me about a time you championed an unpopular idea that ultimately succeeded.',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='senior',
                role_family='general',
                competencies=[CompetencyTag.OWNERSHIP, CompetencyTag.STAKEHOLDER_MANAGEMENT],
                difficulty=4,
                interviewer_type=InterviewerRole.SENIOR_LEADERSHIP,
            ),
            Question(
                id='b7',
                text='Describe your greatest professional achievement and why it matters.',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='any',
                role_family='general',
                competencies=[CompetencyTag.MOTIVATION, CompetencyTag.BUSINESS_AWARENESS],
                difficulty=2,
                interviewer_type=InterviewerRole.HR,
            ),
            Question(
                id='b8',
                text='How do you handle competing priorities when everything is urgent?',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='mid',
                role_family='general',
                competencies=[CompetencyTag.PROBLEM_SOLVING, CompetencyTag.STAKEHOLDER_MANAGEMENT],
                difficulty=3,
                interviewer_type=InterviewerRole.HR,
            ),
            # ── Technical ─────────────────────────────────────────────
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
                id='t2',
                text='Tell me about a difficult production incident and how you debugged it.',
                interview_type=InterviewType.TECHNICAL,
                seniority='mid',
                role_family='engineering',
                competencies=[CompetencyTag.PROBLEM_SOLVING, CompetencyTag.COMMUNICATION_CLARITY],
                difficulty=3,
                interviewer_type=InterviewerRole.TECHNICAL,
            ),
            Question(
                id='t3',
                text='How would you design a rate-limiter for a high-traffic API?',
                interview_type=InterviewType.TECHNICAL,
                seniority='mid',
                role_family='engineering',
                competencies=[CompetencyTag.TECHNICAL_DEPTH, CompetencyTag.PROBLEM_SOLVING],
                difficulty=3,
                interviewer_type=InterviewerRole.TECHNICAL,
            ),
            Question(
                id='t4',
                text='Explain a technical decision you made that you later regretted and what you learned.',
                interview_type=InterviewType.TECHNICAL,
                seniority='senior',
                role_family='engineering',
                competencies=[CompetencyTag.LEARNING_MINDSET, CompetencyTag.TECHNICAL_DEPTH],
                difficulty=4,
                interviewer_type=InterviewerRole.TECHNICAL,
            ),
            Question(
                id='t5',
                text='How do you approach testing strategy for a distributed system?',
                interview_type=InterviewType.TECHNICAL,
                seniority='senior',
                role_family='engineering',
                competencies=[CompetencyTag.TECHNICAL_DEPTH, CompetencyTag.PROBLEM_SOLVING],
                difficulty=4,
                interviewer_type=InterviewerRole.TECHNICAL,
            ),
            Question(
                id='t6',
                text='Tell me about a time you had to optimize performance in a critical path.',
                interview_type=InterviewType.TECHNICAL,
                seniority='mid',
                role_family='engineering',
                competencies=[CompetencyTag.TECHNICAL_DEPTH, CompetencyTag.PROBLEM_SOLVING],
                difficulty=3,
                interviewer_type=InterviewerRole.TECHNICAL,
            ),
            Question(
                id='t7',
                text='How would you migrate a monolith to microservices without downtime?',
                interview_type=InterviewType.TECHNICAL,
                seniority='senior',
                role_family='engineering',
                competencies=[CompetencyTag.TECHNICAL_DEPTH, CompetencyTag.STAKEHOLDER_MANAGEMENT],
                difficulty=5,
                interviewer_type=InterviewerRole.TECHNICAL,
            ),
            # ── Hybrid ────────────────────────────────────────────────
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
                id='h2',
                text='How do you decide when to take on tech debt versus pay it down?',
                interview_type=InterviewType.HYBRID,
                seniority='senior',
                role_family='engineering',
                competencies=[CompetencyTag.TECHNICAL_DEPTH, CompetencyTag.BUSINESS_AWARENESS],
                difficulty=4,
                interviewer_type=InterviewerRole.SENIOR_LEADERSHIP,
            ),
            Question(
                id='h3',
                text='Tell me about a time you had to influence without authority across teams.',
                interview_type=InterviewType.HYBRID,
                seniority='senior',
                role_family='general',
                competencies=[CompetencyTag.STAKEHOLDER_MANAGEMENT, CompetencyTag.LEADERSHIP],
                difficulty=4,
                interviewer_type=InterviewerRole.SENIOR_LEADERSHIP,
            ),
            Question(
                id='h4',
                text='How do you communicate complex technical topics to non-technical stakeholders?',
                interview_type=InterviewType.HYBRID,
                seniority='mid',
                role_family='general',
                competencies=[CompetencyTag.COMMUNICATION_CLARITY, CompetencyTag.STAKEHOLDER_MANAGEMENT],
                difficulty=3,
                interviewer_type=InterviewerRole.HR,
            ),
            Question(
                id='h5',
                text='Describe a time when you had to make a judgment call with incomplete data.',
                interview_type=InterviewType.HYBRID,
                seniority='senior',
                role_family='general',
                competencies=[CompetencyTag.OWNERSHIP, CompetencyTag.PROBLEM_SOLVING],
                difficulty=4,
                interviewer_type=InterviewerRole.SENIOR_LEADERSHIP,
            ),
            # ── Candidate questions phase ─────────────────────────────
            Question(
                id='cq1',
                text='Do you have any questions for us?',
                interview_type=InterviewType.BEHAVIOURAL,
                seniority='any',
                role_family='general',
                competencies=[CompetencyTag.BUSINESS_AWARENESS, CompetencyTag.MOTIVATION],
                difficulty=1,
                interviewer_type=InterviewerRole.HR,
                phase=InterviewPhase.CANDIDATE_QUESTIONS,
            ),
        ]

    def filter_questions(
        self,
        interview_type: InterviewType,
        max_difficulty: int = 5,
        phase: InterviewPhase | None = None,
    ) -> list[Question]:
        results = []
        for q in self.questions:
            type_match = q.interview_type in {interview_type, InterviewType.HYBRID}
            diff_match = q.difficulty <= max_difficulty
            phase_match = phase is None or q.phase == phase
            if type_match and diff_match and phase_match:
                results.append(q)
        return results

    def get_warmup_questions(self) -> list[Question]:
        return [q for q in self.questions if q.phase == InterviewPhase.WARMUP]

    def get_closing_question(self) -> Question | None:
        for q in self.questions:
            if q.phase == InterviewPhase.CANDIDATE_QUESTIONS:
                return q
        return None
