from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict
import os
import json
import logging
from app.models.schemas import AnswerSubmission, EvaluationResult, DifficultyLevel
from app.utils.metrics import monitor_performance, metrics

logger = logging.getLogger(__name__)


class AnswerEvaluatorAgent:
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")

        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is missing!")

        self.llm = ChatOpenAI(
            model="deepseek-chat",
            temperature=0.3,
            max_tokens=800,
            openai_api_key=api_key,
            openai_api_base=api_base
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """你是严格但公正的技术面试官。

评分标准：
- 90-100: 优秀，全面深入，有独到见解
- 75-89: 良好，覆盖主要知识点，逻辑清晰
- 60-74: 及格，基本正确但缺乏深度
- 40-59: 需要改进，存在明显漏洞
- 0-39: 不合格，完全偏离主题或错误

请根据题目难度级别客观评价。"""),
            ("human", """题目：{question}

候选人答案：
{answer}

难度级别：{difficulty}
作答时间：{time_spent}秒
自信程度：{confidence}/10

请以严格的 JSON 格式返回评估结果（不要包含 markdown 标记）：
{{
  "score": 85,
  "feedback": "总体评价...",
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggested_improvements": ["建议1", "建议2"],
  "next_difficulty_recommendation": "advanced"
}}""")
        ])

    def evaluate_answer(self, answer_submission: AnswerSubmission,
                        question_text: str, difficulty: str = "intermediate") -> EvaluationResult:
        chain = self.prompt_template | self.llm

        try:
            response = chain.invoke({
                "question": question_text,
                "answer": answer_submission.answer,
                "difficulty": difficulty,
                "time_spent": answer_submission.time_spent_seconds,
                "confidence": answer_submission.self_confidence
            })

            eval_data = self._parse_evaluation(response.content)

            return EvaluationResult(
                score=eval_data['score'],
                feedback=eval_data['feedback'],
                strengths=eval_data.get('strengths', []),
                weaknesses=eval_data.get('weaknesses', []),
                suggested_improvements=eval_data.get('suggested_improvements', []),
                next_difficulty_recommendation=self._parse_difficulty(
                    eval_data.get('next_difficulty_recommendation', 'intermediate')
                )
            )
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            # 降级方案：返回一个基础的评估结果
            return EvaluationResult(
                score=60.0,
                feedback="系统评估出现异常，已转为人工复核模式。",
                strengths=["完成了作答"],
                weaknesses=["系统无法自动解析"],
                suggested_improvements=["请检查网络连接或稍后重试"],
                next_difficulty_recommendation=DifficultyLevel.INTERMEDIATE
            )

    def _parse_evaluation(self, content: str) -> Dict:
        import json
        try:
            if "json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except (json.JSONDecodeError, IndexError, AttributeError):
            return {
                "score": 70,
                "feedback": content[:200],
                "strengths": ["完成了作答"],
                "weaknesses": ["需要更详细"],
                "suggested_improvements": ["增加案例"],
                "next_difficulty_recommendation": "intermediate"
            }

    def _parse_difficulty(self, diff_str: str) -> DifficultyLevel:
        difficulty_map = {
            "beginner": DifficultyLevel.BEGINNER,
            "intermediate": DifficultyLevel.INTERMEDIATE,
            "advanced": DifficultyLevel.ADVANCED,
            "expert": DifficultyLevel.EXPERT
            }
        return difficulty_map.get(diff_str.lower(), DifficultyLevel.INTERMEDIATE)