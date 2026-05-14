"""
PG-AGI Backend — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints import router
from app.db.database import init_db
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("PG-AGI Backend Starting...")
    await init_db()
    print("Database initialized")
    yield
    print("PG-AGI Backend Shutting Down...")


app = FastAPI(
    title="PG-AGI Technical Screening API",
    description="Autonomous role-based technical interview system with RAG.",
    version="1.0.0",
    lifespan=lifespan,
)

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://frontend-7ptttcvxx-priyanuj-das-projects.vercel.app",
    "https://frontend-beta-ashen-34.vercel.app",
]

CORS_ALLOW_ORIGIN_REGEX = r"https://frontend-.*\.vercel\.app"
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_origin_regex=CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

app.include_router(router)


@app.get("/")
async def root():
    return {"service": "PG-AGI", "version": "1.0.0", "status": "operational", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
