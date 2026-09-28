"""
Health Check Endpoint
Member 3 - Backend Integration
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


@router.get("")
def health_check():
    """
    Health check endpoint
    GET /health
    
    Returns the status of the backend and connected services
    """
    return {
        "status": "healthy",
        "backend": "operational",
        "vision_service": "pending",  # To be populated by Member 1
        "document_ai_service": "pending",  # To be populated by Member 2
    }
