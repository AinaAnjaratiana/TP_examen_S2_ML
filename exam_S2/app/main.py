from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.assistant import router as assistant_router
from app.api.observabilite import router as observabilite_router
from app.api.tickets import router as tickets_router
from app.api.utilisateurs import router as utilisateurs_router

app = FastAPI(
    title="mAIntenance & Assistance",
    description="Assistant intelligent de support informatique — analyse, RAG, agent avec outils, sécurité et observabilité.",
    version="1.0.0",
)

app.include_router(assistant_router)
app.include_router(tickets_router)
app.include_router(utilisateurs_router)
app.include_router(observabilite_router)

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
