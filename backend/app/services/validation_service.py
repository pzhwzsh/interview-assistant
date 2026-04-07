from app.models.schemas import AnswerSubmission, ValidationResult
import re


class ValidationService:
    MIN_ANSWER_LENGTH = 20
    SOFT_MIN_LENGTH = 50
    MAX_ANSWER_LENGTH = 5000
    SOFT_MAX_LENGTH = 3000
    MIN_TIME_SECONDS = 10
    SUSPICIOUSLY_FAST_SECONDS = 60

    @classmethod
    def validate_answer(cls, submission: AnswerSubmission) -> ValidationResult:
        errors = []
        warnings = []
        suggestions = []

        answer = submission.answer.strip()

        if len(answer) < cls.MIN_ANSWER_LENGTH:
            errors.append(f"答案过短，至少需要{cls.MIN_ANSWER_LENGTH}个字符")

        injection_keywords = ["ignore previous", "system prompt", "new instruction"]
        if any(keyword in answer.lower() for keyword in injection_keywords):
            warnings.append("检测到可能的指令注入内容，请专注于回答技术问题")

        if len(answer) < cls.MIN_ANSWER_LENGTH:
            errors.append(f"答案过短，至少需要{cls.MIN_ANSWER_LENGTH}个字符")

        if len(answer) < cls.SOFT_MIN_LENGTH:
            warnings.append("答案较短，建议提供更详细的解释")

        if len(answer) > cls.MAX_ANSWER_LENGTH:
            errors.append(f"答案过长，超过{cls.MAX_ANSWER_LENGTH}字符限制")

        if len(answer) > cls.SOFT_MAX_LENGTH:
            warnings.append("答案较长，建议精简")

        if submission.time_spent_seconds < cls.MIN_TIME_SECONDS:
            errors.append("作答时间过短")

        if submission.time_spent_seconds < cls.SUSPICIOUSLY_FAST_SECONDS:
            warnings.append("作答速度很快，确保充分思考")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
