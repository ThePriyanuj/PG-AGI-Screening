"""
[Agent: Data_Architect] — Structural Ingestion Pipeline & RAG Service
Replaced ChromaDB with a simple JSON file-based store for Vercel deployment compatibility.
"""
import os
import re
import json
import math
from app.core.config import get_settings

settings = get_settings()

def _resolve_json_path() -> str:
    if os.getenv("VERCEL"):
        return "/tmp/pgagi_knowledge_base.json"
    
    db_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(db_dir, "pgagi_knowledge_base.json")

def _load_kb() -> list:
    path = _resolve_json_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def _save_kb(kb: list):
    path = _resolve_json_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kb, f)

def semantic_heading_chunker(text: str, source_book: str) -> list[dict]:
    chunks = []
    heading_patterns = [
        r'^#{1,3}\s+(.+)$',
        r'^Chapter\s+\d+[.:]\s*(.+)$',
        r'^\d+\.\d*\s+(.+)$',
        r'^[A-Z][A-Z\s]{5,}$',
    ]
    combined_pattern = '|'.join(f'({p})' for p in heading_patterns)
    
    lines = text.split('\n')
    current_chapter = "Introduction"
    current_chunk_lines = []
    chunk_id = 0
    
    for line in lines:
        is_heading = False
        for pattern in heading_patterns:
            match = re.match(pattern, line.strip(), re.MULTILINE)
            if match:
                if current_chunk_lines:
                    chunk_text = '\n'.join(current_chunk_lines).strip()
                    if len(chunk_text) > 50:
                        core_concept = _extract_core_concept(chunk_text)
                        chunks.append({
                            "id": f"{source_book}_{chunk_id}",
                            "text": chunk_text,
                            "metadata": {
                                "source_book": source_book,
                                "chapter_title": current_chapter,
                                "core_concept": core_concept,
                            }
                        })
                        chunk_id += 1
                current_chapter = match.group(1) or line.strip()
                current_chunk_lines = [line]
                is_heading = True
                break
        if not is_heading:
            current_chunk_lines.append(line)
        
        current_text = '\n'.join(current_chunk_lines)
        if len(current_text) > 1500:
            core_concept = _extract_core_concept(current_text)
            chunks.append({
                "id": f"{source_book}_{chunk_id}",
                "text": current_text.strip(),
                "metadata": {
                    "source_book": source_book,
                    "chapter_title": current_chapter,
                    "core_concept": core_concept,
                }
            })
            chunk_id += 1
            current_chunk_lines = []
            
    if current_chunk_lines:
        chunk_text = '\n'.join(current_chunk_lines).strip()
        if len(chunk_text) > 50:
            core_concept = _extract_core_concept(chunk_text)
            chunks.append({
                "id": f"{source_book}_{chunk_id}",
                "text": chunk_text,
                "metadata": {
                    "source_book": source_book,
                    "chapter_title": current_chapter,
                    "core_concept": core_concept,
                }
            })
    return chunks

def _extract_core_concept(text: str) -> str:
    ml_concepts = [
        "supervised learning", "unsupervised learning", "reinforcement learning",
        "neural network", "deep learning", "decision tree", "random forest",
        "support vector machine", "svm", "gradient descent", "backpropagation",
        "classification", "regression", "ensemble methods", "transformer",
        "attention mechanism", "natural language processing", "computer vision",
        "optimization", "loss function", "activation function"
    ]
    text_lower = text.lower()
    found_concepts = [c for c in ml_concepts if c in text_lower]
    if found_concepts:
        return ", ".join(found_concepts[:3])
    
    sentences = text.split('.')
    for s in sentences:
        s = s.strip()
        if len(s) > 20:
            return s[:100]
    return "General ML Concept"

def ingest_document(text: str, source_book: str):
    chunks = semantic_heading_chunker(text, source_book)
    if not chunks:
        return 0
        
    kb = _load_kb()
    
    # Remove existing chunks for this source book
    kb = [c for c in kb if c["metadata"]["source_book"] != source_book]
    
    kb.extend(chunks)
    _save_kb(kb)
    return len(chunks)

def _simple_text_embedding(text: str, dim: int = 64) -> list:
    vec = [0.0] * dim
    words = text.lower().split()
    for i, word in enumerate(words):
        idx = hash(word) % dim
        vec[idx] += 1.0 / (1 + i * 0.1)
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec

def retrieve_context(query: str, k: int = 3, skill_filter: list[str] = None) -> list[dict]:
    kb = _load_kb()
    if not kb:
        return []
        
    query_vec = _simple_text_embedding(query)
    
    scored_chunks = []
    for chunk in kb:
        # Boost score if skills match core concept
        skill_boost = 0.0
        if skill_filter:
            for skill in skill_filter[:5]:
                if skill.lower() in chunk["metadata"].get("core_concept", "").lower():
                    skill_boost += 0.2
        
        chunk_vec = _simple_text_embedding(chunk["text"])
        dot_product = sum(a * b for a, b in zip(query_vec, chunk_vec))
        
        scored_chunks.append({
            "text": chunk["text"],
            "metadata": chunk["metadata"],
            "score": dot_product + skill_boost
        })
        
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:k]

def get_knowledge_base_stats() -> dict:
    kb = _load_kb()
    return {
        "total_chunks": len(kb),
        "collection_name": "pgagi_knowledge_base_json",
        "status": "active" if len(kb) > 0 else "empty"
    }
