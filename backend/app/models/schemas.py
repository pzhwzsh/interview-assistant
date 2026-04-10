from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"


class ProjectType(str, Enum):
    WEB_BACKEND = "web_backend"
    MOBILE_APP = "mobile_app"
    DATA_PIPELINE = "data_pipeline"
    MICROSERVICES = "microservices"
    DISTRIBUTED_SYSTEM = "distributed_system"
    AI_ML = "ai_ml"


class AnswerType(str, Enum):
    TEXT = "text"
    CODE = "code"


class QuestionRequest(BaseModel):
    language: ProgrammingLanguage
    project_type: ProjectType
    difficulty: DifficultyLevel
    user_id: str
    topic_focus: Optional[str] = None


class QuestionResponse(BaseModel):
    question_id: str
    question: str
    difficulty: DifficultyLevel
    hints: List[str] = []
    expected_topics: List[str] = []
    estimated_time_minutes: int = 15


class AnswerSubmission(BaseModel):
    question_id: str
    user_id: str
    answer: str
    time_spent_seconds: int
    self_confidence: Optional[int] = Field(ge=1, le=10, default=5)
    answer_type: Optional[AnswerType] = AnswerType.TEXT


class EvaluationResult(BaseModel):
    score: float = Field(ge=0, le=100)
    feedback: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    suggested_improvements: List[str] = []
    next_difficulty_recommendation: DifficultyLevel


class UserHistory(BaseModel):
    user_id: str
    total_questions: int
    average_score: float
    difficulty_distribution: Dict[str, int]
    recent_answers: List[Dict]
    weak_areas: List[str]
    strong_areas: List[str]


class ValidationResult(BaseModel):
    is_valid: bool
    warnings: List[str] = []
    errors: List[str] = []
    suggestions: List[str] = []
