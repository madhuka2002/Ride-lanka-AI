import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.recommend import router as recommend_router

app = FastAPI(
    title="Ride Lanka AI Service",
    description="Gemini-powered travel recommendation engine for Sri Lanka",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to backend URL in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(recommend_router, prefix="/api/ai", tags=["recommendations"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "Ride Lanka AI"}
