import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analysis, health
from core.config import settings

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Multi-Agent Data Analyst",
    description="Upload a CSV and let a crew of LLM agents analyze it.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analysis.router)
