"""
[Agent: AI_Specialist] — Adaptive Difficulty Gate
Implements the accuracy scoring function and difficulty progression:
  Simple -> Moderate -> Complex

Accuracy Score: S_acc(A,C) = w1 * CosineSimilarity(V_A, V_C) + w2 * |T_A ∩ T_C| / |T_C|

Where:
  V_A = embedding vector of candidate's answer
  V_C = embedding vector of expected context
  T_A = set of technical terms in the answer
  T_C = set of technical terms in the expected context
  w1, w2 = configurable weights (default 0.7, 0.3)
"""
import re
from app.core.config import get_settings

settings = get_settings()

# Technical terms dictionary for ML domain
ML_TECHNICAL_TERMS = {
    "supervised", "unsupervised", "reinforcement", "classification", "regression",
    "clustering", "neural", "network", "gradient", "descent", "backpropagation",
    "overfitting", "underfitting", "regularization", "cross-validation", "bias",
    "variance", "feature", "dimensionality", "reduction", "ensemble", "boosting",
    "bagging", "random", "forest", "decision", "tree", "svm", "kernel", "hyperplane",
    "loss", "function", "activation", "sigmoid", "relu", "softmax", "dropout",
    "batch", "normalization", "convolutional", "recurrent", "lstm", "transformer",
    "attention", "embedding", "tokenization", "precision", "recall", "f1",
    "accuracy", "auc", "roc", "confusion", "matrix", "epoch", "learning", "rate",
    "momentum", "optimizer", "adam", "sgd", "likelihood", "posterior", "prior",
    "bayesian", "markov", "probabilistic", "generative", "discriminative",
    "autoencoder", "gan", "vae", "latent", "manifold", "convergence",
    "stochastic", "deterministic", "hypothesis", "inductive", "deductive",
    "entropy", "information", "gain", "gini", "impurity", "pruning",
}


def extract_technical_terms(text: str) -> set:
    """Extract technical terms from text."""
    words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    return words.intersection(ML_TECHNICAL_TERMS)


def compute_term_overlap(answer_terms: set, context_terms: set) -> float:
    """Compute |T_A ∩ T_C| / |T_C| — the term overlap ratio."""
    if not context_terms:
        return 0.0
    intersection = answer_terms.intersection(context_terms)
    return len(intersection) / len(context_terms)


import math

def compute_cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec_a or not vec_b:
        return 0.0
        
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot_product / (norm_a * norm_b))


def simple_text_embedding(text: str, dim: int = 128) -> list:
    """
    Simple text embedding using character-level hashing.
    In production, this would use NVIDIA's embedding model.
    """
    vec = [0.0] * dim
    words = text.lower().split()
    for i, word in enumerate(words):
        idx = hash(word) % dim
        vec[idx] += 1.0 / (1 + i * 0.1)
    
    # Normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    
    return vec


def compute_accuracy_score(answer: str, expected_context: str) -> dict:
    """
    Compute the accuracy score using the formula:
    S_acc(A,C) = w1 * CosineSimilarity(V_A, V_C) + w2 * |T_A ∩ T_C| / |T_C|
    
    Returns detailed scoring breakdown.
    """
    # Extract technical terms
    answer_terms = extract_technical_terms(answer)
    context_terms = extract_technical_terms(expected_context)
    
    # Compute term overlap
    term_overlap = compute_term_overlap(answer_terms, context_terms)
    
    # Compute cosine similarity using simple embeddings
    vec_a = simple_text_embedding(answer)
    vec_c = simple_text_embedding(expected_context)
    cosine_sim = compute_cosine_similarity(vec_a, vec_c)
    
    # Weighted accuracy score
    accuracy = settings.W1_COSINE * cosine_sim + settings.W2_TERM * term_overlap
    
    return {
        "accuracy_score": round(accuracy, 4),
        "cosine_similarity": round(cosine_sim, 4),
        "term_overlap": round(term_overlap, 4),
        "answer_terms": list(answer_terms),
        "context_terms": list(context_terms),
        "matched_terms": list(answer_terms.intersection(context_terms)),
    }


def determine_difficulty(cumulative_accuracy: float, current_difficulty: str) -> str:
    """
    Adaptive Difficulty Gate: Determines next question difficulty.
    
    Rules:
    - If cumulative_accuracy >= COMPLEX_THRESHOLD (0.75): Complex
    - If cumulative_accuracy >= MODERATE_THRESHOLD (0.5): Moderate
    - Otherwise: Simple
    
    Difficulty can only increase or stay the same (no regression).
    """
    difficulty_order = {"simple": 0, "moderate": 1, "complex": 2}
    current_level = difficulty_order.get(current_difficulty, 0)
    
    if cumulative_accuracy >= settings.COMPLEX_THRESHOLD:
        new_level = 2
    elif cumulative_accuracy >= settings.MODERATE_THRESHOLD:
        new_level = 1
    else:
        new_level = 0
    
    # No regression: only move up or stay
    final_level = max(current_level, new_level)
    
    level_names = {0: "simple", 1: "moderate", 2: "complex"}
    return level_names[final_level]


def get_difficulty_prompt_modifier(difficulty: str) -> str:
    """Returns prompt instructions for each difficulty level."""
    modifiers = {
        "simple": (
            "Generate a SIMPLE/foundational question. "
            "Focus on definitions, basic concepts, and recall-type questions. "
            "The question should test fundamental understanding."
        ),
        "moderate": (
            "Generate a MODERATE/intermediate question. "
            "Focus on application, comparison between concepts, and 'why' questions. "
            "The candidate should demonstrate understanding beyond definitions."
        ),
        "complex": (
            "Generate a COMPLEX/advanced question. "
            "Focus on system design, trade-off analysis, novel problem-solving, "
            "and integration of multiple concepts. "
            "The candidate should demonstrate deep expertise."
        ),
    }
    return modifiers.get(difficulty, modifiers["simple"])
