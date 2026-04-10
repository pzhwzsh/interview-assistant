from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean, Table
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/interview_assistant")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


user_favorites = Table(
    'user_favorites',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('question_id', String, ForeignKey('questions.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_questions = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    preferences = Column(JSON, default={})

    answer_records = relationship("AnswerRecord", back_populates="user")
    favorite_questions = relationship("Question", secondary=user_favorites, backref="favorited_by")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    language = Column(String, nullable=False)
    project_type = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    entropy_hash = Column(String, unique=True, index=True)
    question_metadata = Column("metadata", JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    interview_mode = Column(String, default="standard")


class AnswerRecord(Base):
    __tablename__ = "answer_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    answer_content = Column(Text, nullable=False)
    score = Column(Float)
    feedback = Column(Text)
    time_spent = Column(Integer)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    evaluation_details = Column(JSON, default={})
    answer_type = Column(String, default="text")
    is_correct = Column(Boolean, default=False)

    user = relationship("User", back_populates="answer_records")
    question = relationship("Question")


def init_db():
    Base.metadata.create_all(bind=engine)
