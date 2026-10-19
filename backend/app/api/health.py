"""
Health Check Endpoint (Member 3)
GET /health -> backend + live status of Vision and Document AI services.
"""

import os

import httpx
from fastapi import APIRouter

from app.services.vision_client import VisionServiceClient

router = APIRouter(prefix="/health", tags=["health"])

vision_client = VisionServiceClient()


async def _document_ai_status() -> str:
    url = os.getenv("DOCUMENT_AI_SERVICE_URL", "http://localhost:8002").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            r = await client.get(f"{url}/health")
        return "operational" if r.status_code == 200 else "error"
    except Exception:
        return "error"


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "backend": "operational",
        "vision_service": await vision_client.health(),
        "document_ai_service": await _document_ai_status(),
    }