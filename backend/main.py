from fastapi import FastAPI, HTTPException

from backend.config import settings
from backend.health import get_health_status, is_ready

app = FastAPI(
    title="CloudRAG API",
    description="Production-style document intelligence and RAG API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "service": settings.app_name,
        "environment": settings.environment,
        **get_health_status(),
    }

@app.get("/live")
def liveness_check():
    return {
        "status": "alive"
        }

@app.get("/ready")
def readiness_check():
    if not is_ready():
        raise HTTPException(
            status_code=503,
            detail="Database is not ready",
        )
    return {
        "status": "ready"
        }