from typing import List
from app.models.schemas import DifficultyLevel


class DifficultyAdjusterAgent:
    DIFFICULTY_LEVELS = [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED,
        DifficultyLevel.EXPERT
    ]

    @classmethod
    def adjust_difficulty(cls, current_difficulty: DifficultyLevel,
                          recent_scores: List[float],
                          target_accuracy: float = 75.0) -> DifficultyLevel:
        if not recent_scores:
            return current_difficulty

        avg_score = sum(recent_scores) / len(recent_scores)
        current_index = cls.DIFFICULTY_LEVELS.index(current_difficulty)

        if avg_score >= target_accuracy + 10 and current_index < len(cls.DIFFICULTY_LEVELS) - 1:
            return cls.DIFFICULTY_LEVELS[current_index + 1]
        elif avg_score < target_accuracy - 15 and current_index > 0:
            return cls.DIFFICULTY_LEVELS[current_index - 1]

        return current_difficulty
