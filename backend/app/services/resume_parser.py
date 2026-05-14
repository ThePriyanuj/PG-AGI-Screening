"""
[Agent: Data_Architect] — Resume Processing Service
Extracts text, skills, and domain exposure from PDF/text resumes
using the NVIDIA NIM Qwen model for intelligent extraction.
"""
import PyPDF2
import io
import json
from openai import OpenAI
from app.core.config import get_settings

settings = get_settings()

client = OpenAI(
    base_url=settings.NVIDIA_BASE_URL,
    api_key=settings.NVIDIA_API_KEY or "dummy_key_to_prevent_startup_crash",
)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Parse a PDF file and extract all text content."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def extract_skills_with_ai(resume_text: str) -> dict:
    """
    Uses Qwen model to intelligently extract structured information from resume.
    Returns: {
        "candidate_name": str,
        "skills": list[str],
        "technologies": list[str],
        "domain_exposure": list[str],
        "experience_level": str
    }
    """
    try:
        response = client.chat.completions.create(
            model=settings.NVIDIA_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": """You are a resume analysis expert. Extract structured information from the resume.
Return a JSON object with these exact keys:
- "candidate_name": the person's full name
- "skills": list of technical and soft skills
- "technologies": list of specific technologies, tools, frameworks
- "domain_exposure": list of industry domains they have experience in
- "experience_level": one of "entry", "mid", "senior", "expert"

Return ONLY valid JSON, no markdown formatting, no explanation."""
                },
                {
                    "role": "user",
                    "content": f"Extract structured information from this resume:\n\n{resume_text[:4000]}"
                }
            ],
            temperature=0.3,
            top_p=0.8,
            max_tokens=1024,
        )

        content = response.choices[0].message.content.strip()
        # Clean up potential markdown formatting
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        if content.endswith("```"):
            content = content[:-3]

        return json.loads(content.strip())
    except Exception as e:
        print(f"AI skill extraction failed: {e}")
        # Fallback: basic keyword extraction
        return {
            "candidate_name": "Unknown Candidate",
            "skills": _basic_skill_extraction(resume_text),
            "technologies": [],
            "domain_exposure": [],
            "experience_level": "mid"
        }


def _basic_skill_extraction(text: str) -> list:
    """Fallback keyword-based skill extraction."""
    common_skills = [
        "python", "java", "javascript", "react", "node.js", "sql", "machine learning",
        "deep learning", "tensorflow", "pytorch", "scikit-learn", "nlp", "computer vision",
        "data analysis", "statistics", "algorithms", "data structures", "git", "docker",
        "kubernetes", "aws", "azure", "gcp", "rest api", "microservices", "agile",
        "neural networks", "reinforcement learning", "supervised learning", "unsupervised learning"
    ]
    text_lower = text.lower()
    return [skill for skill in common_skills if skill in text_lower]
