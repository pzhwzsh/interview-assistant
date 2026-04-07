from sqlalchemy.orm import Session, joinedload
from typing import Dict, List
from app.models.database import User, AnswerRecord, Question
from app.models.schemas import UserHistory
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MemoryManagerAgent:
    def __init__(self, db_session: Session):
        self.db = db_session

    def record_answer(self, user_id: str, question_id: str,
                      answer: str, score: float,
                      time_spent: int, evaluation_details: Dict):
        """记录用户答题并更新用户统计数据"""
        try:
            answer_record = AnswerRecord(
                user_id=user_id,
                question_id=question_id,
                answer_content=answer,
                score=score,
                time_spent=time_spent,
                evaluation_details=evaluation_details
            )
            self.db.add(answer_record)

            # 查找或创建用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(id=user_id, username=f"user_{user_id[:8]}", email=f"{user_id}@temp.com", hashed_password="")
                self.db.add(user)
                self.db.flush()

            # 初始化统计字段
            if user.total_questions is None:
                user.total_questions = 0
            if user.average_score is None:
                user.average_score = 0.0

            # 更新平均分和总题数
            user.total_questions += 1
            total_score = (user.average_score * (user.total_questions - 1)) + score
            user.average_score = total_score / user.total_questions

            self.db.commit()
            logger.info(f"Recorded answer for user {user_id}, new avg score: {user.average_score:.2f}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record answer: {e}")
            raise e

    def get_user_history(self, user_id: str, limit: int = 20) -> UserHistory:
        """获取用户历史答题记录，使用 joinedload 优化查询"""
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return UserHistory(
                user_id=user_id,
                total_questions=0,
                average_score=0.0,
                difficulty_distribution={},
                recent_answers=[],
                weak_areas=[],
                strong_areas=[]
            )

        recent_records = (
            self.db.query(AnswerRecord)
            .options(joinedload(AnswerRecord.question))
            .filter(AnswerRecord.user_id == user_id)
            .order_by(AnswerRecord.submitted_at.desc())
            .limit(limit)
            .all()
        )

        # 简单的强弱项分析逻辑
        topic_scores = defaultdict(list)
        difficulty_dist = defaultdict(int)

        recent_answers = []
        for r in recent_records:
            # 统计难度分布
            if r.question:
                difficulty_dist[r.question.difficulty] += 1

            recent_answers.append({
                "id": r.id,
                "question_id": r.question_id,
                "question_content": r.question.content if r.question else "题目已删除",
                "difficulty": r.question.difficulty if r.question else "unknown",
                "answer_content": r.answer_content[:100] + "..." if len(r.answer_content) > 100 else r.answer_content,
                "score": r.score,
                "feedback": r.feedback,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                "time_spent": r.time_spent,
                "evaluation_details": r.evaluation_details or {}
            })

        # 计算强弱项（基于最近5次低分和高分题目）
        sorted_answers = sorted(recent_answers, key=lambda x: x['score'])
        weak_areas = [a['question_content'] for a in sorted_answers[:3] if a['score'] < 60]
        strong_areas = [a['question_content'] for a in sorted_answers[-3:] if a['score'] >= 85]

        return UserHistory(
            user_id=user_id,
            total_questions=user.total_questions or 0,
            average_score=user.average_score or 0.0,
            difficulty_distribution=dict(difficulty_dist),
            recent_answers=recent_answers,
            weak_areas=weak_areas,
            strong_areas=strong_areas
        )
