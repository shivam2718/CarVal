"""
Vision Service Client (Member 3 -> Member 1)
Sends uploaded car images to the Vision Service (port 8001) and returns its response unchanged.
File names are set to the backend image ID (IMG-XXXX.jpg) so damage evidence points at the right image.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


class VisionServiceError(Exception):
    """Raised when the Vision Service is down or returns an error."""


class VisionServiceClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("VISION_SERVICE_URL", "http://localhost:8001").rstrip("/")
        self.timeout = float(os.getenv("VISION_TIMEOUT_S", "120"))

    async def health(self) -> str:
        """'operational' | 'degraded' | 'error' (used by GET /health)."""
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                r = await client.get(f"{self.base_url}/health")
            if r.status_code != 200:
                return "error"
            return "operational" if r.json().get("status") == "healthy" else "degraded"
        except Exception:
            return "error"

    async def analyze_images(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        files = []
        for img in images:
            ext = Path(img["filename"] or "").suffix.lower() or ".jpg"
            files.append(
                ("files", (f"{img['file_id']}{ext}", img["contents"], img.get("content_type") or "image/jpeg"))
            )
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(f"{self.base_url}/analyze/upload", files=files)
        except httpx.HTTPError as e:
            raise VisionServiceError(f"Vision Service unreachable at {self.base_url}: {e}") from e

        if r.status_code != 200:
            raise VisionServiceError(f"Vision Service returned {r.status_code}: {r.text[:300]}")
        return r.json()

    async def annotated(self, image_id: str) -> Optional[bytes]:
        """JPEG with boxes drawn by the Vision Service (None if not cached there)."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(f"{self.base_url}/annotated/{image_id}")
            return r.content if r.status_code == 200 else None
        except httpx.HTTPError:
            return None