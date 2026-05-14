# PG-AGI Technical Interviewer: Comprehensive Project Documentation

## 1. Project Overview

**PG-AGI Technical Interviewer** is an autonomous, agentic technical screening system designed to conduct interactive, role-based interviews. It leverages Retrieval-Augmented Generation (RAG) and high-performance AI models to evaluate candidates dynamically based on their resumes, target job roles, and ongoing performance. 

Unlike static question banks, PG-AGI tailors every question to the candidate's specific background, assesses answers in real-time using mathematical term-overlap and semantic similarity, and dynamically adjusts the difficulty level of the interview to find the limits of the candidate's knowledge.

---

## 2. System Architecture

The application is built using a modern decoupled architecture, split between a highly interactive React/Next.js frontend and a robust Python/FastAPI backend.

### The Agentic Workflow
The system operates as a coordinated team of AI agents:
1. **Frontend Experience Agent**: Manages the UI/UX, capturing user input via glassmorphism-styled forms and dynamic chat interfaces.
2. **Data Architect Agent (Backend)**: Parses resumes using PyPDF2, coordinates structural RAG ingestion, and handles database persistence.
3. **AI Specialist Agent (Backend)**: Uses NVIDIA NIM APIs (specifically the Qwen coder models) to generate targeted technical questions, evaluate answers, and compute RAG Triad metrics.

---

## 3. Core Features & Capabilities

### A. AI-Powered Resume Processing
When a candidate uploads a PDF or text resume, the backend uses PyPDF2 to extract raw text. It then prompts the NVIDIA LLM to intelligently extract structured data, including:
- Candidate Name
- Key Skills & Technologies
- Domain Exposure
- Estimated Experience Level

### B. Adaptive Difficulty Gate
The interview does not follow a linear path. It utilizes a **Difficulty Gate** that adapts based on candidate accuracy.
* **Accuracy Scoring Formula**: `S_acc(A,C) = w1 * CosineSimilarity(V_A, V_C) + w2 * (|T_A ∩ T_C| / |T_C|)`
  * Combines dense vector semantic similarity with sparse technical term overlap to fairly judge a candidate's answer against the "textbook" expected context.
* **Progression**: The interview strictly progresses from `Simple` -> `Moderate` -> `Complex`. If a candidate consistently scores above thresholds (e.g., > 0.75 accuracy), the system escalates the difficulty. The system never regresses to a lower difficulty, preventing candidates from artificially manipulating the difficulty.

### C. Knowledge Base & RAG Pipeline
To ensure the AI doesn't hallucinate technical concepts, it grounds its questions in an ingested knowledge base (simulating an engineering textbook or internal company documentation).
* **Semantic Heading Chunker**: Documents are chunked contextually based on markdown headings or chapter titles, ensuring concepts aren't split arbitrarily.
* **Vercel-Optimized JSON Vector Store**: To bypass Vercel's strict 250MB serverless limit, the heavy `chromadb` dependency was replaced with a bespoke, pure-Python in-memory vector database. It uses a character-level hashing text embedding to compute similarities and stores chunks locally in Vercel's `/tmp` directory.

### D. RAG Triad Observability
Every single interaction is logged and evaluated for AI trustworthiness using the **RAG Triad**:
1. **Context Relevance**: Is the retrieved information actually relevant to the candidate's skills?
2. **Answer Faithfulness**: Is the AI's grading based purely on the provided context (avoiding hallucinated grading)?
3. **Answer Relevance**: Did the candidate actually answer the question asked?

### E. Session Persistence & Summary Generation
Interviews are persisted in a SQLite database (mapped via SQLAlchemy). Once the session concludes, the system generates a comprehensive summary dashboard, including:
- Final hiring recommendation (e.g., STRONG HIRE, NO HIRE).
- Cumulative accuracy and difficulty distribution.
- RAG Triad averages for auditability.

---

## 4. Technology Stack

### Frontend (Client-Side)
* **Framework**: Next.js 14 (App Router)
* **Language**: TypeScript
* **Styling**: Vanilla CSS (Tailwind excluded per project requirements) with a rich, modern Glassmorphism and Aurora aesthetic.
* **Icons**: `lucide-react`
* **Deployment**: Vercel

### Backend (Server-Side)
* **Framework**: FastAPI (Python 3.12)
* **Database ORM**: SQLAlchemy with `aiosqlite` for asynchronous SQLite access.
* **AI Provider**: NVIDIA NIM API (Model: `qwen/qwen3-coder-480b-a35b-instruct`)
* **Vector Store**: Custom Pure-Python JSON Vector Store (Optimized for Serverless)
* **Deployment**: Vercel Serverless Functions

---

## 5. Project Directory Structure

```text
ML_Project_Demo/
├── frontend/                     # Next.js Application
│   ├── src/
│   │   ├── app/                  # Next.js App Router (page.tsx, globals.css)
│   │   ├── components/           # Reusable UI (SetupPhase, InterviewPhase, Summary)
│   │   └── types/                # TypeScript Interfaces
│   ├── public/                   # Static Assets
│   └── package.json              # Frontend Dependencies
│
└── backend/                      # FastAPI Application
    ├── app/
    │   ├── api/                  # API Routers (endpoints.py)
    │   ├── core/                 # App config & environment variables
    │   ├── db/                   # SQLAlchemy Models & SQLite Engine
    │   └── services/             # Core Business Logic
    │       ├── difficulty_gate.py  # Adaptive scoring logic
    │       ├── interview_engine.py # Core LLM prompting pipeline
    │       ├── observability.py    # RAG triad evaluation
    │       ├── rag_pipeline.py     # JSON-based Vector Store
    │       └── resume_parser.py    # AI parsing & PDF extraction
    ├── main.py                   # FastAPI Entry Point
    ├── requirements.txt          # Python Dependencies
    └── vercel.json               # Serverless Routing Config
```

---

## 6. How the System Handles Edge Cases

* **Serverless Bundle Limits**: AI/ML libraries (`numpy`, `scikit-learn`, `chromadb`) were stripped from the backend to ensure the bundle stays well under Vercel's 250MB limit, preventing cold-start timeouts.
* **CORS Management**: CORS headers are explicitly managed dynamically by FastAPI's `CORSMiddleware` using regex to match any Vercel deployment branch, ensuring seamless frontend-to-backend communication.
* **Missing API Keys**: If `NVIDIA_API_KEY` is not provided in the environment, the backend gracefully injects a dummy key during import so the server doesn't crash, allowing it to boot up and serve health endpoints safely.

---

## 7. Deployment Guide

### Deploying the Backend
1. Navigate to the `backend/` directory.
2. Run `npx vercel --prod`.
3. In the Vercel Dashboard, go to your new backend project's **Settings > Environment Variables**.
4. Add your `NVIDIA_API_KEY`.
5. Note the deployment URL (e.g., `https://backend-beta.vercel.app`).

### Deploying the Frontend
1. Navigate to the `frontend/` directory.
2. Run `npx vercel --prod`.
3. In the Vercel Dashboard, go to your new frontend project's **Settings > Environment Variables**.
4. Set `NEXT_PUBLIC_API_URL` to point to your backend API route (e.g., `https://backend-beta.vercel.app/api`).
5. Redeploy the frontend to ensure the environment variables are baked into the build.
