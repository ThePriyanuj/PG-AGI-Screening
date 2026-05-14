"""
[Agent: Backend_Engineer] — FastAPI API Endpoints
Implements the three core endpoints with session-based persistence:
- POST /upload-resume — Parse and extract skills from resume
- POST /start-interview — Initialize a new interview session
- POST /submit-answer — Submit answer and get next question
- GET /session/{id}/summary — Get interview summary
- GET /knowledge-base/stats — Get KB statistics
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import json

from app.db.database import get_db
from app.db.models import InterviewSession, InteractionLog
from app.services.resume_parser import extract_text_from_pdf, extract_skills_with_ai
from app.services.interview_engine import (
    generate_question,
    evaluate_answer,
    generate_session_summary,
)
from app.services.difficulty_gate import determine_difficulty
from app.services.rag_pipeline import get_knowledge_base_stats, ingest_document

router = APIRouter(prefix="/api", tags=["Interview"])


# ========================
# Request/Response Models
# ========================

class StartInterviewRequest(BaseModel):
    candidate_name: str
    job_role: str
    resume_text: Optional[str] = None
    skills: Optional[list] = None
    total_questions: int = 10


class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: str


class IngestTextRequest(BaseModel):
    text: str
    source_book: str


# ========================
# Endpoints
# ========================

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse a resume PDF. Extracts text and uses AI
    to identify skills, technologies, and domain exposure.
    """
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")
    
    try:
        content = await file.read()
        
        if file.filename.lower().endswith('.pdf'):
            resume_text = extract_text_from_pdf(content)
        else:
            resume_text = content.decode('utf-8', errors='ignore')
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file.")
        
        # AI-powered skill extraction
        extracted_data = extract_skills_with_ai(resume_text)
        
        return {
            "status": "success",
            "resume_text": resume_text[:3000],
            "extracted": extracted_data,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {str(e)}")


@router.post("/start-interview")
async def start_interview(
    request: StartInterviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize a new interview session.
    Creates a session in PostgreSQL and generates the first question.
    """
    session_id = str(uuid.uuid4())
    
    # Merge provided skills with any resume-extracted skills
    skills = request.skills or []
    
    # Create session record
    session = InterviewSession(
        id=session_id,
        candidate_name=request.candidate_name,
        job_role=request.job_role,
        resume_text=request.resume_text,
        extracted_skills=skills,
        current_difficulty="simple",
        total_questions=request.total_questions,
        status="active",
    )
    
    db.add(session)
    await db.commit()
    
    # Generate first question
    session_data = {
        "extracted_skills": skills,
        "job_role": request.job_role,
        "current_difficulty": "simple",
    }
    
    question_data = generate_question(session_data, question_number=1)
    
    # Log the interaction
    interaction = InteractionLog(
        id=str(uuid.uuid4()),
        session_id=session_id,
        question_number=1,
        difficulty_level=question_data["difficulty"],
        question_text=question_data["question"],
        expected_context=question_data.get("context_used", ""),
        source_citation=question_data.get("source_citation"),
    )
    
    db.add(interaction)
    await db.commit()
    
    return {
        "status": "success",
        "session_id": session_id,
        "question_number": 1,
        "total_questions": request.total_questions,
        "question": question_data["question"],
        "difficulty": question_data["difficulty"],
        "source_citation": question_data.get("source_citation"),
    }


@router.post("/submit-answer")
async def submit_answer(
    request: SubmitAnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an answer to the current question.
    Evaluates the answer, updates difficulty, and generates the next question.
    """
    # Fetch the session
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == request.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    if session.status != "active":
        raise HTTPException(status_code=400, detail="This interview session has already ended.")
    
    current_q = session.current_question_index + 1
    
    # Fetch the current unanswered interaction
    result = await db.execute(
        select(InteractionLog)
        .where(InteractionLog.session_id == request.session_id)
        .where(InteractionLog.candidate_answer == None)
        .order_by(InteractionLog.question_number.desc())
    )
    current_interaction = result.scalar_one_or_none()
    
    if not current_interaction:
        raise HTTPException(status_code=400, detail="No pending question found.")
    
    # Evaluate the answer
    evaluation = evaluate_answer(
        question=current_interaction.question_text,
        answer=request.answer,
        expected_context=current_interaction.expected_context or "",
        difficulty=current_interaction.difficulty_level,
        source_citation=current_interaction.source_citation or {},
    )
    
    # Update the interaction log
    current_interaction.candidate_answer = request.answer
    current_interaction.accuracy_score = evaluation["accuracy_score"]
    current_interaction.cosine_similarity = evaluation["scoring_details"]["cosine_similarity"]
    current_interaction.term_overlap = evaluation["scoring_details"]["term_overlap"]
    current_interaction.is_correct = evaluation["is_correct"]
    current_interaction.ai_feedback = evaluation["feedback"]
    current_interaction.context_relevance = evaluation["rag_triad"].get("context_relevance")
    current_interaction.answer_faithfulness = evaluation["rag_triad"].get("answer_faithfulness")
    current_interaction.answer_relevance = evaluation["rag_triad"].get("answer_relevance")
    
    # Update cumulative accuracy
    all_interactions_result = await db.execute(
        select(InteractionLog)
        .where(InteractionLog.session_id == request.session_id)
        .where(InteractionLog.accuracy_score != None)
    )
    all_scored = all_interactions_result.scalars().all()
    
    total_accuracy = sum(i.accuracy_score for i in all_scored if i.accuracy_score) + evaluation["accuracy_score"]
    count = len(all_scored) + 1
    cumulative_accuracy = total_accuracy / count
    
    # Determine new difficulty
    new_difficulty = determine_difficulty(cumulative_accuracy, session.current_difficulty)
    
    # Update session
    session.current_question_index = current_q
    session.cumulative_accuracy = cumulative_accuracy
    session.current_difficulty = new_difficulty
    
    response_data = {
        "status": "answer_evaluated",
        "question_number": current_q,
        "evaluation": {
            "is_correct": evaluation["is_correct"],
            "accuracy_score": evaluation["accuracy_score"],
            "feedback": evaluation["feedback"],
            "source_citation": evaluation["source_citation"],
        },
        "difficulty_update": {
            "previous": current_interaction.difficulty_level,
            "current": new_difficulty,
            "cumulative_accuracy": round(cumulative_accuracy, 4),
        },
        "rag_triad": evaluation["rag_triad"],
    }
    
    # Check if interview is complete
    if current_q >= session.total_questions:
        session.status = "completed"
        await db.commit()
        
        # Generate summary
        interactions_result = await db.execute(
            select(InteractionLog)
            .where(InteractionLog.session_id == request.session_id)
            .order_by(InteractionLog.question_number)
        )
        all_interactions = interactions_result.scalars().all()
        
        interaction_dicts = []
        for i in all_interactions:
            interaction_dicts.append({
                "question": i.question_text,
                "answer": i.candidate_answer,
                "is_correct": i.is_correct,
                "accuracy_score": i.accuracy_score,
                "difficulty": i.difficulty_level,
                "source_citation": i.source_citation,
                "rag_triad": {
                    "context_relevance": i.context_relevance,
                    "answer_faithfulness": i.answer_faithfulness,
                    "answer_relevance": i.answer_relevance,
                },
            })
        
        session_dict = {
            "candidate_name": session.candidate_name,
            "job_role": session.job_role,
            "current_difficulty": session.current_difficulty,
        }
        
        summary = generate_session_summary(session_dict, interaction_dicts)
        
        response_data["status"] = "interview_completed"
        response_data["summary"] = summary
    else:
        # Generate next question
        session_data = {
            "extracted_skills": session.extracted_skills or [],
            "job_role": session.job_role,
            "current_difficulty": new_difficulty,
        }
        
        # Get previous Q&A for context
        prev_result = await db.execute(
            select(InteractionLog)
            .where(InteractionLog.session_id == request.session_id)
            .order_by(InteractionLog.question_number)
        )
        prev_interactions = prev_result.scalars().all()
        previous_qa = [
            {"question": i.question_text, "answer": i.candidate_answer}
            for i in prev_interactions
        ]
        
        next_question = generate_question(
            session_data,
            question_number=current_q + 1,
            previous_qa=previous_qa,
        )
        
        # Log new interaction
        new_interaction = InteractionLog(
            id=str(uuid.uuid4()),
            session_id=request.session_id,
            question_number=current_q + 1,
            difficulty_level=next_question["difficulty"],
            question_text=next_question["question"],
            expected_context=next_question.get("context_used", ""),
            source_citation=next_question.get("source_citation"),
        )
        db.add(new_interaction)
        
        response_data["next_question"] = {
            "question_number": current_q + 1,
            "question": next_question["question"],
            "difficulty": next_question["difficulty"],
            "source_citation": next_question.get("source_citation"),
        }
    
    await db.commit()
    return response_data


@router.get("/session/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the summary of a completed interview session."""
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    interactions_result = await db.execute(
        select(InteractionLog)
        .where(InteractionLog.session_id == session_id)
        .order_by(InteractionLog.question_number)
    )
    all_interactions = interactions_result.scalars().all()
    
    interaction_dicts = []
    for i in all_interactions:
        interaction_dicts.append({
            "question_number": i.question_number,
            "question": i.question_text,
            "answer": i.candidate_answer,
            "is_correct": i.is_correct,
            "accuracy_score": i.accuracy_score,
            "difficulty": i.difficulty_level,
            "feedback": i.ai_feedback,
            "source_citation": i.source_citation,
            "rag_triad": {
                "context_relevance": i.context_relevance,
                "answer_faithfulness": i.answer_faithfulness,
                "answer_relevance": i.answer_relevance,
            },
        })
    
    session_dict = {
        "candidate_name": session.candidate_name,
        "job_role": session.job_role,
        "current_difficulty": session.current_difficulty,
    }
    
    summary = generate_session_summary(session_dict, interaction_dicts)
    summary["interactions"] = interaction_dicts
    
    return summary


@router.get("/knowledge-base/stats")
async def knowledge_base_stats():
    """Get statistics about the current knowledge base."""
    return get_knowledge_base_stats()


@router.post("/knowledge-base/ingest")
async def ingest_text(request: IngestTextRequest):
    """Ingest text content into the knowledge base."""
    try:
        count = ingest_document(request.text, request.source_book)
        return {
            "status": "success",
            "chunks_ingested": count,
            "source_book": request.source_book,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
