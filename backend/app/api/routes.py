from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, init_db
from app.models.schemas import (
    QuestionRequest, QuestionResponse,
    AnswerSubmission, EvaluationResult,
    UserHistory
)
from app.models.database import Question
from app.agents.question_generator_agent import QuestionGeneratorAgent
from app.agents.answer_evaluator_agent import AnswerEvaluatorAgent
from app.agents.memory_manager_agent import MemoryManagerAgent
from app.agents.difficulty_adjuster_agent import DifficultyAdjusterAgent
from app.services.validation_service import ValidationService
from app.utils.prompt_entropy import entropy_engine
from app.utils.metrics import metrics

router = APIRouter()

question_agent = QuestionGeneratorAgent()
evaluator_agent = AnswerEvaluatorAgent()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/api/generate-question", response_model=QuestionResponse)
async def generate_question(request: QuestionRequest, db: Session = Depends(get_db)):
    try:
        question = question_agent.generate_question(request)

        entropy_hash = entropy_engine.generate_entropy_seed(
            request.language.value,
            request.project_type.value,
            request.difficulty.value,
            request.user_id
        )

        db_question = Question(
            id=question.question_id,
            content=question.question,
            language=request.language.value,
            project_type=request.project_type.value,
            difficulty=request.difficulty.value,
            entropy_hash=entropy_hash,
            question_metadata={
                "hints": question.hints,
                "expected_topics": question.expected_topics,
                "estimated_time_minutes": question.estimated_time_minutes
            }
        )
        db.add(db_question)
        db.commit()

        return question
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/submit-answer", response_model=EvaluationResult)
async def submit_answer(submission: AnswerSubmission, db: Session = Depends(get_db)):
    validation = ValidationService.validate_answer(submission)

    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"validation_errors": validation.errors}
        )

    question = db.query(Question).filter(Question.id == submission.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    memory_agent = MemoryManagerAgent(db)

    # Deleted:evaluation = evaluator_agent.evaluate_answer(submission, question.content)
    evaluation = evaluator_agent.evaluate_answer(
        submission,
        question.content,
        question.difficulty
    )
    memory_agent.record_answer(
        user_id=submission.user_id,
        question_id=submission.question_id,
        answer=submission.answer,
        score=evaluation.score,
        time_spent=submission.time_spent_seconds,
        evaluation_details=evaluation.dict()
    )

    history = memory_agent.get_user_history(submission.user_id)
    recent_scores = [r['score'] for r in history.recent_answers[-5:]] if history.recent_answers else []
    adjusted_difficulty = DifficultyAdjusterAgent.adjust_difficulty(
        evaluation.next_difficulty_recommendation,
        recent_scores
    )
    evaluation.next_difficulty_recommendation = adjusted_difficulty

    entropy_engine.clear_old_hashes()

    return evaluation


@router.get("/api/user-history/{user_id}", response_model=UserHistory)
async def get_user_history(user_id: str, db: Session = Depends(get_db)):
    memory_agent = MemoryManagerAgent(db)
    return memory_agent.get_user_history(user_id)

@router.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus 格式的指标"""
    summary = metrics.get_summary()

    lines = []

    # Counters
    for name, value in metrics.counters.items():
        lines.append(f"# HELP {name} Total count")
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")

    # Gauges
    for name, value in metrics.gauges.items():
        lines.append(f"# HELP {name} Current value")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")

    # Histograms
    for name, stats in summary.items():
        lines.append(f"# HELP {name} Duration statistics")
        lines.append(f"# TYPE {name} summary")
        lines.append(f'{name}_count {stats["count"]}')
        lines.append(f'{name}_sum {stats["avg"] * stats["count"]}')

    return "\n".join(lines)
