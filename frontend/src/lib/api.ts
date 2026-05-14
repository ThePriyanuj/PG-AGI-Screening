/**
 * PG-AGI Frontend API Client
 * Handles all communication with the FastAPI backend.
 */

function normalizeApiBaseUrl(rawUrl?: string): string {
  const baseUrl = (rawUrl || "http://localhost:8000/api").replace(/\/+$/, "");
  return baseUrl.endsWith("/api") ? baseUrl : `${baseUrl}/api`;
}

const DEFAULT_API_BASE =
  process.env.NODE_ENV === "production"
    ? "https://backend-beta-ashen-34.vercel.app/api"
    : "http://localhost:8000/api";

const API_BASE = normalizeApiBaseUrl(process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE);

export interface ResumeUploadResponse {
  status: string;
  resume_text: string;
  extracted: {
    candidate_name: string;
    skills: string[];
    technologies: string[];
    domain_exposure: string[];
    experience_level: string;
  };
}

export interface StartInterviewResponse {
  status: string;
  session_id: string;
  question_number: number;
  total_questions: number;
  question: string;
  difficulty: string;
  source_citation: {
    source_book: string;
    chapter_title: string;
    core_concept: string;
  };
}

export interface SubmitAnswerResponse {
  status: string;
  question_number: number;
  evaluation: {
    is_correct: boolean;
    accuracy_score: number;
    feedback: string;
    source_citation: {
      source_book: string;
      chapter_title: string;
      core_concept: string;
    };
  };
  difficulty_update: {
    previous: string;
    current: string;
    cumulative_accuracy: number;
  };
  rag_triad: {
    context_relevance: number;
    answer_faithfulness: number;
    answer_relevance: number;
    triad_score: number;
  };
  next_question?: {
    question_number: number;
    question: string;
    difficulty: string;
    source_citation: {
      source_book: string;
      chapter_title: string;
      core_concept: string;
    };
  };
  summary?: SessionSummary;
}

export interface SessionSummary {
  candidate_name: string;
  job_role: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  average_accuracy: number;
  final_difficulty: string;
  difficulty_distribution: {
    simple: number;
    moderate: number;
    complex: number;
  };
  rag_triad_averages: {
    context_relevance: number;
    answer_faithfulness: number;
    answer_relevance: number;
  };
  sources_cited: Array<{
    source_book: string;
    chapter_title: string;
    core_concept: string;
  }>;
  recommendation: string;
  interactions?: Array<{
    question_number: number;
    question: string;
    answer: string;
    is_correct: boolean;
    accuracy_score: number;
    difficulty: string;
    feedback: string;
    source_citation: {
      source_book: string;
      chapter_title: string;
      core_concept: string;
    };
    rag_triad: {
      context_relevance: number;
      answer_faithfulness: number;
      answer_relevance: number;
    };
  }>;
}

export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload-resume`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || "Resume upload failed");
  }

  return res.json();
}

export async function startInterview(data: {
  candidate_name: string;
  job_role: string;
  resume_text?: string;
  skills?: string[];
  total_questions?: number;
}): Promise<StartInterviewResponse> {
  const res = await fetch(`${API_BASE}/start-interview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to start" }));
    throw new Error(error.detail || "Failed to start interview");
  }

  return res.json();
}

export async function submitAnswer(data: {
  session_id: string;
  answer: string;
}): Promise<SubmitAnswerResponse> {
  const res = await fetch(`${API_BASE}/submit-answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Submission failed" }));
    throw new Error(error.detail || "Failed to submit answer");
  }

  return res.json();
}

export async function getSessionSummary(sessionId: string): Promise<SessionSummary> {
  const res = await fetch(`${API_BASE}/session/${sessionId}/summary`);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Not found" }));
    throw new Error(error.detail || "Failed to get summary");
  }

  return res.json();
}
