from fastapi import FastAPI
from backend.config import settings

app = FastAPI(
    title="CloudRAG API",
    description="Production-style document intelligence and RAG API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        }

@app.get("/live")
def liveness_check():
    return {
        "status": "alive"
        }

@app.get("/ready")
def readiness_check():
    return {
        "status": "ready"
        }