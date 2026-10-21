"""
Document AI Service Client
Member 3 - Backend
Calls Member 2's Document AI Service and processes responses
"""

import httpx
from typing import List, Dict, Any
import os
import json
from pathlib import PurePath
import mimetypes


class DocumentAIError(Exception):
    """Document AI service is unreachable or returned an error (message is shown to the user)."""


class DocumentAIClient:
    """Client for interacting with Member 2's Document AI Service"""
    
    def __init__(self):
        self.document_ai_url = os.getenv("DOCUMENT_AI_SERVICE_URL", "http://localhost:8002")
        # Numeric OCR tries multiple image variants; allow those passes to finish.
        self.timeout = 90

    @staticmethod
    def _upload_file(document_path: str, file_bytes: bytes):
        """Keep the real extension and MIME type so the service can identify PDFs."""
        filename = PurePath(document_path or "document").name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return {"file": (filename, file_bytes, content_type)}

    async def extract_text(self, document_path: str, file_bytes: bytes, mode: str = "document") -> Dict[str, Any]:
        """Run OCR through Document AI and return its text for field verification."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.document_ai_url}/extract/text",
                    files=self._upload_file(document_path, file_bytes),
                    data={"mode": mode},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error extracting text with Document AI: {e}")
            return {"extracted": False, "raw_text": "", "error": str(e)}

    async def extract_odometer(self, document_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """Use Document AI's dedicated pretrained odometer OCR endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.document_ai_url}/extract/odometer",
                    files=self._upload_file(document_path, file_bytes),
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error extracting odometer reading with Document AI: {e}")
            return {
                "extracted": False,
                "raw_text": "",
                "reading_candidates": [],
                "ocr_confidence": 0.0,
                "error": str(e),
            }
    
    async def _extract(self, kind: str, document_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """POST to /extract/{kind}. Raises DocumentAIError with a readable reason instead of hiding failures."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.document_ai_url}/extract/{kind}",
                    files=self._upload_file(document_path, file_bytes),
                    timeout=self.timeout,
                )
        except httpx.HTTPError as e:
            raise DocumentAIError(f"Document AI unreachable at {self.document_ai_url}: {e}") from e
        if response.status_code != 200:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise DocumentAIError(f"Document AI returned {response.status_code}: {str(detail)[:300]}")
        return response.json()

    async def extract_rc_info(self, document_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """RC (Registration Certificate): registration number, owner, model, year, fuel, ..."""
        result = await self._extract("rc", document_path, file_bytes)
        return {
            "extracted": result.get("extracted", False),
            "fields": result.get("fields", {}),
            "field_confidence": result.get("field_confidence", {}),
            "confidence": result.get("confidence", 0.0),
            "ocr_confidence": result.get("ocr_confidence"),
            "source_document_id": result.get("source_document_id"),
        }

    async def extract_insurance_info(self, document_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """Insurance policy: policy number, validity dates, insurer, claims."""
        result = await self._extract("insurance", document_path, file_bytes)
        fields = result.get("fields", {})
        return {
            "extracted": any(fields.get(k) for k in ("policy_number", "valid_from", "valid_until", "insurer_name", "claims")),
            "policy_number": fields.get("policy_number"),
            "valid_from": fields.get("valid_from"),
            "valid_until": fields.get("valid_until"),
            "insurer_name": fields.get("insurer_name"),
            "insured_name": fields.get("insured_name"),
            "registration_number": fields.get("registration_number"),
            "idv": fields.get("idv"),
            "claims": fields.get("claims", []),
            "confidence": result.get("confidence", 0.0),
            "raw_text": result.get("raw_text", ""),
            "source_document_id": result.get("source_document_id"),
        }

    async def extract_service_info(self, document_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """Service bill: dates, mileage, work done, costs."""
        result = await self._extract("service", document_path, file_bytes)
        records = result.get("fields", {}).get("service_records", [])
        return {
            "extracted": len(records) > 0,
            "service_records": records,
            "confidence": result.get("confidence", 0.0),
            "source_document_id": result.get("source_document_id"),
        }

    async def health_check(self) -> bool:
        """Check if Document AI service is running"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.document_ai_url}/health",
                    timeout=5
                )
                return response.status_code == 200
        except Exception:
            return False
