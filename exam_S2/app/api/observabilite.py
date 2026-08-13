from fastapi import APIRouter

from app.core.observabilite import obtenir_traces

router = APIRouter(prefix="/api/observabilite", tags=["Observabilité"])


@router.get("/traces")
def lire_traces(limite: int = 50):
    return obtenir_traces(limite=limite)
