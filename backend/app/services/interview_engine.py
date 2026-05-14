"""
[Agent: AI_Specialist] — Interview Engine
Core AI service that orchestrates:
- Dynamic Query Generation (resume skills × job roles × RAG context)
- Question generation with adaptive difficulty
- Answer evaluation with source citations
- Session management and scoring
"""
from openai import OpenAI
from app.core.config import get_settings
from app.services.rag_pipeline import retrieve_context
from app.services.difficulty_gate import (
    compute_accuracy_score,
    determine_difficulty,
    get_difficulty_prompt_modifier,
)
from app.services.observability import evaluate_rag_triad
import json

settings = get_settings()

client = OpenAI(
    base_url=settings.NVIDIA_BASE_URL,
    api_key=settings.NVIDIA_API_KEY or "dummy_key_to_prevent_startup_crash",
)


def build_dynamic_query(skills: list, job_role: str, difficulty: str) -> str:
    """
    Dynamic Query Generator: Intersects resume skills with job roles
    to create targeted retrieval queries.
    """
    skill_str = ", ".join(skills[:5]) if skills else "general programming"
    return f"{job_role} interview question about {skill_str} at {difficulty} level"


def generate_question(
    session_data: dict,
    question_number: int,
    previous_qa: list = None,
) -> dict:
    """
    Generate an adaptive interview question using RAG.
    
    Returns: {
        "question": str,
        "difficulty": str,
        "context_used": str,
        "source_citation": dict,
        "rag_query": str,
    }
    """
    skills = session_data.get("extracted_skills", [])
    job_role = session_data.get("job_role", "Machine Learning Engineer")
    difficulty = session_data.get("current_difficulty", "simple")
    
    # Build dynamic query intersecting skills and role
    rag_query = build_dynamic_query(skills, job_role, difficulty)
    
    # Retrieve relevant context from knowledge base
    contexts = retrieve_context(rag_query, k=3, skill_filter=skills)
    
    context_text = ""
    source_citation = {"source_book": "N/A", "chapter_title": "N/A", "core_concept": "N/A"}
    
    if contexts:
        context_text = "\n\n".join([c["text"] for c in contexts])
        # Use the most relevant chunk's metadata as the citation
        source_citation = contexts[0].get("metadata", source_citation)
    
    # Build the prompt with difficulty modifier
    difficulty_instruction = get_difficulty_prompt_modifier(difficulty)
    
    # Build conversation history for context
    history_text = ""
    if previous_qa:
        history_text = "\n\nPrevious Q&A in this interview:\n"
        for qa in previous_qa[-3:]:  # Last 3 questions for context
            history_text += f"Q: {qa.get('question', '')[:200]}\n"
            history_text += f"A: {qa.get('answer', '')[:200]}\n\n"
    
    system_prompt = f"""You are an expert technical interviewer for the role of {job_role}.
You are conducting a structured technical interview.

{difficulty_instruction}

This is question #{question_number} of the interview.

IMPORTANT RULES:
1. Ask exactly ONE clear, focused question
2. The question MUST be based on the provided knowledge base context
3. Do NOT repeat any previously asked questions
4. The question should naturally test knowledge related to the candidate's skills: {', '.join(skills[:5])}
5. Do NOT include the answer or hints in your question
6. Keep the question concise (2-3 sentences max)

KNOWLEDGE BASE CONTEXT:
{context_text[:3000] if context_text else "No specific context available. Ask a general ML question appropriate for the role."}
{history_text}"""

    try:
        response = client.chat.completions.create(
            model=settings.NVIDIA_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a {difficulty} level technical interview question for a {job_role} candidate."}
            ],
            temperature=0.7,
            top_p=0.8,
            max_tokens=512,
        )
        
        question_text = response.choices[0].message.content.strip()
        
        # Clean: remove thinking tags if present (Qwen sometimes includes these)
        if "<think>" in question_text:
            # Remove everything between <think> and </think>
            import re
            question_text = re.sub(r'<think>.*?</think>', '', question_text, flags=re.DOTALL).strip()
        
        return {
            "question": question_text,
            "difficulty": difficulty,
            "context_used": context_text[:1000],
            "source_citation": source_citation,
            "rag_query": rag_query,
        }
    
    except Exception as e:
        print(f"Question generation failed: {e}")
        return {
            "question": f"[{difficulty.upper()}] Tell me about your experience with {skills[0] if skills else 'machine learning'} and how it applies to the {job_role} role.",
            "difficulty": difficulty,
            "context_used": "",
            "source_citation": source_citation,
            "rag_query": rag_query,
        }


def evaluate_answer(
    question: str,
    answer: str,
    expected_context: str,
    difficulty: str,
    source_citation: dict,
) -> dict:
    """
    Evaluate a candidate's answer against the expected context.
    
    Returns: {
        "is_correct": bool,
        "accuracy_score": float,
        "feedback": str,
        "scoring_details": dict,
        "rag_triad": dict,
        "source_citation": dict,
    }
    """
    # Compute accuracy score using the formal function
    scoring = compute_accuracy_score(answer, expected_context)
    
    # Get AI-generated feedback
    try:
        eval_prompt = f"""You are evaluating a candidate's answer in a technical interview.

QUESTION: {question}
CANDIDATE'S ANSWER: {answer}
REFERENCE CONTEXT (from textbook): {expected_context[:2000]}

Evaluate the answer based on:
1. Technical accuracy (does it align with the reference context?)
2. Completeness (did they cover the key points?)
3. Clarity of explanation

Provide:
1. A brief assessment (2-3 sentences)
2. Whether the answer is correct (true/false)
3. Key points they missed (if any)

Return as JSON: {{"feedback": "...", "is_correct": true/false, "missed_points": ["...", "..."]}}"""

        response = client.chat.completions.create(
            model=settings.NVIDIA_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a fair and precise technical evaluator. Return only valid JSON."},
                {"role": "user", "content": eval_prompt}
            ],
            temperature=0.3,
            max_tokens=512,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean: remove thinking tags
        if "<think>" in content:
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        # Clean markdown
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            if "```" in content:
                content = content.split("```")[0]
        
        eval_result = json.loads(content.strip())
        feedback = eval_result.get("feedback", "Answer evaluated.")
        is_correct = eval_result.get("is_correct", scoring["accuracy_score"] > 0.5)
        
    except Exception as e:
        print(f"AI evaluation failed: {e}")
        feedback = "Answer received and scored based on term matching."
        is_correct = scoring["accuracy_score"] > 0.5
    
    # Evaluate RAG Triad (async in production, sync here for simplicity)
    rag_triad = evaluate_rag_triad(
        question=question,
        candidate_answer=answer,
        retrieved_context=expected_context,
        ai_feedback=feedback,
    )
    
    return {
        "is_correct": is_correct,
        "accuracy_score": scoring["accuracy_score"],
        "feedback": feedback,
        "scoring_details": scoring,
        "rag_triad": rag_triad,
        "source_citation": source_citation,
    }


def generate_session_summary(session_data: dict, interactions: list) -> dict:
    """Generate a comprehensive session summary with all metrics."""
    total_questions = len(interactions)
    correct_answers = sum(1 for i in interactions if i.get("is_correct"))
    
    avg_accuracy = (
        sum(i.get("accuracy_score", 0) for i in interactions) / total_questions
        if total_questions > 0 else 0
    )
    
    avg_triad = {
        "context_relevance": 0,
        "answer_faithfulness": 0,
        "answer_relevance": 0,
    }
    
    for interaction in interactions:
        triad = interaction.get("rag_triad", {})
        for key in avg_triad:
            avg_triad[key] += triad.get(key, 0)
    
    if total_questions > 0:
        for key in avg_triad:
            avg_triad[key] = round(avg_triad[key] / total_questions, 4)
    
    # Difficulty distribution
    difficulty_dist = {"simple": 0, "moderate": 0, "complex": 0}
    for interaction in interactions:
        level = interaction.get("difficulty", "simple")
        difficulty_dist[level] = difficulty_dist.get(level, 0) + 1
    
    # Source citations used
    sources_used = []
    for interaction in interactions:
        citation = interaction.get("source_citation", {})
        if citation and citation.get("source_book") != "N/A":
            sources_used.append(citation)
    
    return {
        "candidate_name": session_data.get("candidate_name", "Unknown"),
        "job_role": session_data.get("job_role", "Unknown"),
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "score_percentage": round((correct_answers / total_questions * 100) if total_questions > 0 else 0, 1),
        "average_accuracy": round(avg_accuracy, 4),
        "final_difficulty": session_data.get("current_difficulty", "simple"),
        "difficulty_distribution": difficulty_dist,
        "rag_triad_averages": avg_triad,
        "sources_cited": sources_used,
        "recommendation": _generate_recommendation(correct_answers, total_questions, avg_accuracy),
    }


def _generate_recommendation(correct: int, total: int, accuracy: float) -> str:
    """Generate a hiring recommendation based on performance."""
    if total == 0:
        return "Insufficient data for recommendation."
    
    ratio = correct / total
    
    if ratio >= 0.8 and accuracy >= 0.7:
        return "STRONG HIRE — Candidate demonstrated excellent technical depth and accuracy."
    elif ratio >= 0.6 and accuracy >= 0.5:
        return "HIRE — Candidate shows solid fundamentals with room for growth."
    elif ratio >= 0.4:
        return "MAYBE — Candidate has foundational knowledge but needs further assessment."
    else:
        return "NO HIRE — Candidate did not demonstrate sufficient technical proficiency."
