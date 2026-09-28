"""
CarVal Backend - FastAPI Orchestrator
Main entry point for the CarVal backend API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api import health, inspection

# Initialize FastAPI app
app = FastAPI(
    title="CarVal Backend",
    description="CarVal Vehicle Inspection Orchestrator - Vision & Document AI",
    version="0.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(inspection.router)


@app.get("/")
def read_root():
    """Root endpoint - API status"""
    return {
        "service": "CarVal Backend",
        "version": "0.1.0",
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
