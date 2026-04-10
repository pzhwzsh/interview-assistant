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
from app.agents.mock_interview_agent import mock_interview_agent
from app.services.validation_service import ValidationService
from app.utils.prompt_entropy import entropy_engine
from app.utils.metrics import metrics
from pydantic import BaseModel
from typing import Optional
import uuid
import logging
import subprocess
import tempfile
import os
import signal

logger = logging.getLogger("interview-assistant")


router = APIRouter()

question_agent = QuestionGeneratorAgent()
evaluator_agent = AnswerEvaluatorAgent()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CodeExecutionRequest(BaseModel):
    code: str
    language: str

class MockInterviewStartRequest(BaseModel):
    mode: str
    language: str = "通用"
    experience_level: str = "中级"
    target_role: str = "软件工程师"
    user_id: str


class MockInterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str
    user_id: str


@router.post("/api/mock-interview/start")
async def start_mock_interview(request: MockInterviewStartRequest):
    session_id = str(uuid.uuid4())

    context = {
        "language": request.language,
        "experience_level": request.experience_level,
        "target_role": request.target_role
    }

    first_question = mock_interview_agent.initialize_conversation(
        session_id, request.mode, context
    )

    return {
        "session_id": session_id,
        "mode": request.mode,
        "first_question": first_question
    }


@router.post("/api/mock-interview/answer")
async def submit_mock_answer(request: MockInterviewAnswerRequest):
    try:
        result = await mock_interview_agent.process_answer_stream(
            request.session_id,
            request.answer
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/mock-interview/end/{session_id}")
async def end_mock_interview(session_id: str):
    try:
        summary = mock_interview_agent.end_conversation(session_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/mock-interview/state/{session_id}")
async def get_interview_state(session_id: str):
    try:
        state = mock_interview_agent.get_conversation_state(session_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/favorite/{question_id}")
async def toggle_favorite(question_id: str, user_id: str, db: Session = Depends(get_db)):
    from app.models.database import User

    user = db.query(User).filter(User.id == user_id).first()
    question = db.query(Question).filter(Question.id == question_id).first()

    if not user or not question:
        raise HTTPException(status_code=404, detail="用户或题目不存在")

    if question in user.favorite_questions:
        user.favorite_questions.remove(question)
        db.commit()
        return {"message": "已取消收藏", "favorited": False}
    else:
        user.favorite_questions.append(question)
        db.commit()
        return {"message": "收藏成功", "favorited": True}


@router.get("/api/user-favorites/{user_id}")
async def get_user_favorites(user_id: str, db: Session = Depends(get_db)):
    from app.models.database import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    favorites = []
    for q in user.favorite_questions:
        favorites.append({
            "id": q.id,
            "content": q.content[:200],
            "difficulty": q.difficulty,
            "language": q.language,
            "project_type": q.project_type
        })

    return {"favorites": favorites, "total": len(favorites)}


@router.get("/api/wrong-questions/{user_id}")
async def get_wrong_questions(user_id: str, db: Session = Depends(get_db)):
    from app.models.database import AnswerRecord

    wrong_answers = db.query(AnswerRecord).filter(
        AnswerRecord.user_id == user_id,
        AnswerRecord.score < 60
    ).order_by(AnswerRecord.submitted_at.desc()).limit(20).all()

    wrong_questions = []
    for record in wrong_answers:
        wrong_questions.append({
            "id": record.id,
            "question_id": record.question_id,
            "question_content": record.question.content if record.question else "未知",
            "your_answer": record.answer_content[:200],
            "score": record.score,
            "feedback": record.feedback,
            "submitted_at": record.submitted_at.isoformat(),
            "difficulty": record.question.difficulty if record.question else "unknown"
        })

    return {"wrong_questions": wrong_questions, "total": len(wrong_questions)}


@router.get("/api/search-questions")
async def search_questions(query: str, user_id: str, limit: int = 10):
    from app.services.vector_store import vector_store

    similar = vector_store.search_similar_questions(query, n_results=limit)

    return {
        "query": query,
        "results": similar,
        "total": len(similar)
    }


@router.post("/api/generate-question", response_model=QuestionResponse)
async def generate_question(request: QuestionRequest, db: Session = Depends(get_db)):
    import time
    start_time = time.time()
    logger.info(f"Starting question generation for user {request.user_id}")

    try:
        llm_start = time.time()
        question = question_agent.generate_question(request)
        llm_time = time.time() - llm_start
        logger.info(f"[PERFORMANCE] LLM generation took {llm_time:.2f}s")

        entropy_hash = entropy_engine.generate_entropy_seed(
            request.language.value,
            request.project_type.value,
            request.difficulty.value,
            request.user_id
        )

        db_start = time.time()
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
        db_time = time.time() - db_start
        logger.info(f"[PERFORMANCE] Database insert took {db_time:.2f}s")

        vector_start = time.time()
        from app.services.vector_store import vector_store
        vector_store.add_question(
            question_id=question.question_id,
            content=question.question,
            metadata={
                "language": request.language.value,
                "difficulty": request.difficulty.value,
                "project_type": request.project_type.value
            }
        )
        vector_time = time.time() - vector_start
        logger.info(f"[PERFORMANCE] Vector store operation took {vector_time:.2f}s")

        total_time = time.time() - start_time
        logger.info(
            f"[PERFORMANCE] Total: {total_time:.2f}s | LLM:{llm_time:.2f}s | DB:{db_time:.2f}s | Vector:{vector_time:.2f}s")

        return question
    except Exception as e:
        db.rollback()
        logger.error(f"Question generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成题目失败: {str(e)}")


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

    for name, value in metrics.counters.items():
        lines.append(f"# HELP {name} Total count")
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")

    for name, value in metrics.gauges.items():
        lines.append(f"# HELP {name} Current value")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")

    for name, stats in summary.items():
        lines.append(f"# HELP {name} Duration statistics")
        lines.append(f"# TYPE {name} summary")
        lines.append(f'{name}_count {stats["count"]}')
        lines.append(f'{name}_sum {stats["avg"] * stats["count"]}')

    return "\n".join(lines)
# 在文件末尾（第 321 行之后）添加这个接口
@router.post("/api/run-code")
async def run_code(request: CodeExecutionRequest):
    """安全地执行用户代码"""
    code = request.code
    language = request.language.lower()

    # 安全检查：限制代码长度
    if len(code) > 10000:
        raise HTTPException(status_code=400, detail="代码过长，请控制在10000字符以内")

    # 定义支持的语言和执行命令
    supported_languages = {
        'python': {'command': 'python', 'extension': '.py', 'timeout': 5},
        'javascript': {'command': 'node', 'extension': '.js', 'timeout': 5},
        'typescript': {'command': 'ts-node', 'extension': '.ts', 'timeout': 5},
    }

    if language not in supported_languages:
        return {
            "output": f"⚠️ {language} 语言暂不支持在线运行\n\n支持的語言: Python, JavaScript, TypeScript\n\n请在本地环境中测试代码",
            "error": None
        }

    lang_config = supported_languages[language]

    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=lang_config['extension'],
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            tmp_file.write(code)
            tmp_path = tmp_file.name

        try:
            # 执行代码
            process = subprocess.run(
                [lang_config['command'], tmp_path],
                capture_output=True,
                text=True,
                timeout=lang_config['timeout'],
                cwd=os.path.dirname(tmp_path)
            )

            output = process.stdout
            error = process.stderr

            # 如果既有输出又有错误，合并显示
            result_output = ""
            if output:
                result_output += output
            if error:
                if result_output:
                    result_output += "\n--- 错误信息 ---\n"
                result_output += error

            if not result_output:
                result_output = "代码执行完成，无输出"

            return {
                "output": result_output[:5000],  # 限制输出长度
                "error": None,
                "exit_code": process.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "error": "⏱️ 代码执行超时（超过5秒），可能存在无限循环",
                "exit_code": -1
            }
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Code execution error: {str(e)}")
        return {
            "output": "",
            "error": f"❌ 代码执行失败: {str(e)}",
            "exit_code": -1
        }

