"""
[Agent: AI_Specialist] — RAG Triad Observability Module
Implements the three pillars of RAG observability:
1. Context Relevance: How relevant is the retrieved context to the question?
2. Answer Faithfulness: Is the AI's evaluation faithful to the retrieved context?
3. Answer Relevance: How relevant is the candidate's answer to the question asked?
"""
from openai import OpenAI
from app.core.config import get_settings
import json

settings = get_settings()

client = OpenAI(
    base_url=settings.NVIDIA_BASE_URL,
    api_key=settings.NVIDIA_API_KEY or "dummy_key_to_prevent_startup_crash",
)


def evaluate_rag_triad(
    question: str,
    candidate_answer: str,
    retrieved_context: str,
    ai_feedback: str = "",
) -> dict:
    """
    Evaluate the RAG Triad metrics for a single Q&A interaction.
    
    Returns: {
        "context_relevance": float (0-1),
        "answer_faithfulness": float (0-1),
        "answer_relevance": float (0-1),
        "triad_score": float (0-1, average of all three)
    }
    """
    try:
        prompt = f"""You are an evaluation expert. Score the following RAG interaction on three metrics.
Each score must be between 0.0 and 1.0.

QUESTION: {question}

RETRIEVED CONTEXT (from textbook): {retrieved_context[:2000]}

CANDIDATE'S ANSWER: {candidate_answer}

AI EVALUATION FEEDBACK: {ai_feedback[:1000]}

Score these three metrics:
1. context_relevance: How relevant is the RETRIEVED CONTEXT to the QUESTION? (1.0 = perfectly relevant)
2. answer_faithfulness: Is the AI EVALUATION FEEDBACK grounded in the RETRIEVED CONTEXT? (1.0 = fully grounded)
3. answer_relevance: How relevant is the CANDIDATE'S ANSWER to the QUESTION? (1.0 = perfectly relevant)

Return ONLY a JSON object with these three keys and float values. No explanation."""

        response = client.chat.completions.create(
            model=settings.NVIDIA_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a precise evaluation system. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=256,
        )

        content = response.choices[0].message.content.strip()
        # Clean up potential markdown
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        scores = json.loads(content.strip())
        
        # Ensure all values are floats between 0 and 1
        for key in ["context_relevance", "answer_faithfulness", "answer_relevance"]:
            if key in scores:
                scores[key] = max(0.0, min(1.0, float(scores[key])))
            else:
                scores[key] = 0.5
        
        scores["triad_score"] = round(
            (scores["context_relevance"] + scores["answer_faithfulness"] + scores["answer_relevance"]) / 3, 4
        )
        
        return scores

    except Exception as e:
        print(f"RAG Triad evaluation failed: {e}")
        return {
            "context_relevance": 0.5,
            "answer_faithfulness": 0.5,
            "answer_relevance": 0.5,
            "triad_score": 0.5,
        }
