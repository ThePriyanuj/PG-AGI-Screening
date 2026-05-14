"""
PG-AGI Database Models (PostgreSQL via SQLAlchemy)
Session management and interaction logging with full data isolation.
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class InterviewSession(Base):
    """Represents a single interview session with a candidate."""
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_name = Column(String(255), nullable=False)
    job_role = Column(String(255), nullable=False)
    resume_text = Column(Text, nullable=True)
    extracted_skills = Column(JSON, default=list)
    current_difficulty = Column(String(20), default="simple")  # simple, moderate, complex
    current_question_index = Column(Integer, default=0)
    total_questions = Column(Integer, default=10)
    cumulative_accuracy = Column(Float, default=0.0)
    status = Column(String(20), default="active")  # active, completed, abandoned
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to interaction logs
    interactions = relationship("InteractionLog", back_populates="session", cascade="all, delete-orphan")


class InteractionLog(Base):
    """Logs every Q&A interaction within a session for observability."""
    __tablename__ = "interaction_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("interview_sessions.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    difficulty_level = Column(String(20), nullable=False)
    question_text = Column(Text, nullable=False)
    candidate_answer = Column(Text, nullable=True)
    expected_context = Column(Text, nullable=True)  # RAG-retrieved context
    source_citation = Column(JSON, nullable=True)  # {"source_book": ..., "chapter_title": ..., "core_concept": ...}

    # Scoring metrics
    accuracy_score = Column(Float, nullable=True)
    cosine_similarity = Column(Float, nullable=True)
    term_overlap = Column(Float, nullable=True)

    # RAG Triad observability
    context_relevance = Column(Float, nullable=True)
    answer_faithfulness = Column(Float, nullable=True)
    answer_relevance = Column(Float, nullable=True)

    is_correct = Column(Boolean, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="interactions")
