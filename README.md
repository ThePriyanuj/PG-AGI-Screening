# PG-AGI Technical Interviewer 🤖💼

An autonomous, agentic technical screening system designed to conduct deep-dive technical interviews. Built with a focus on **RAG (Retrieval-Augmented Generation)** and **NVIDIA NIM**, this system evaluates candidates based on their resumes and foundational knowledge from core ML textbooks.

![PG-AGI Banner](https://img.shields.io/badge/PG--AGI-Technical%20Screening-blueviolet?style=for-the-badge&logo=openai)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)
![NVIDIA](https://img.shields.io/badge/NVIDIA-NIM-76B900?style=for-the-badge&logo=nvidia)

## 🌟 Key Features

- **Adaptive Interview Pipeline**: Dynamic difficulty gating that adjusts based on candidate performance.
- **RAG-Powered Evaluation**: Contextualizes questions using a knowledge base built from industry-standard textbooks (e.g., Tom Mitchell's *Machine Learning*).
- **RAG Triad Observability**: Real-time metrics for Context Relevance, Answer Faithfulness, and Answer Relevance.
- **Glassmorphism UI**: A premium, modern interface with smooth animations and interactive chat.
- **Session Persistence**: Resume interviews exactly where you left off.
- **Comprehensive Dashboard**: Detailed post-interview summary with performance analytics and confidence scoring.

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **Engine**: Orchestrates the interview flow and state management.
- **Knowledge Base**: ChromaDB-powered vector store for semantic retrieval of technical concepts.
- **RAG Pipeline**: Integrates NVIDIA NIM API for high-performance inference and evaluation.
- **Resume Parser**: Extracts key skills and experience to tailor the interview.

### Frontend (Next.js/TypeScript)
- **Framework**: Next.js 15 with React 19.
- **Styling**: Tailwind CSS 4.0 for a sleek, responsive design.
- **Animations**: Framer Motion for premium transitions and micro-interactions.
- **State Management**: React Context/Hooks for real-time interview synchronization.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- NVIDIA NIM API Key

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configure environment variables in a `.env` file:
   ```env
   NVIDIA_API_KEY=your_api_key_here
   DATABASE_URL=sqlite+aiosqlite:///./pgagi.db
   ```
4. Ingest textbooks into the knowledge base:
   ```bash
   python scripts/ingest_textbooks.py --sample
   ```
5. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## 📊 RAG Triad Observability
The system employs the **RAG Triad** to ensure the quality of the AI's reasoning:
1. **Context Relevance**: Is the retrieved knowledge relevant to the question?
2. **Faithfulness**: Is the answer derived strictly from the retrieved context?
3. **Answer Relevance**: Does the answer directly address the candidate's query or the role requirements?

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.

---
Built with ❤️ by [ThePriyanuj](https://github.com/ThePriyanuj)
