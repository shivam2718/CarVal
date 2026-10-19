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
    
    async def extract_rc_info(self, document_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract information from RC (Registration Certificate)
        
        Args:
            document_path: Path to RC document
            file_bytes: File content as bytes
            
        Returns:
            Extracted RC information (registration number, owner, model, year, etc.)
        """
        try:
            async with httpx.AsyncClient() as client:
                files = self._upload_file(document_path, file_bytes)
                response = await client.post(
                    f"{self.document_ai_url}/extract/rc",
                    files=files,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "extracted": result.get("extracted", False),
                        "fields": result.get("fields", {}),
                        "field_confidence": result.get("field_confidence", {}),
                        "confidence": result.get("confidence", 0.0),
                        "source_document_id": result.get("source_document_id")
                    }
        except Exception as e:
            print(f"Error calling Document AI service: {e}")
        
        return {
            "extracted": False,
            "fields": {},
            "field_confidence": {},
            "confidence": 0.0,
            "source_document_id": None
        }
    
    async def extract_insurance_info(self, document_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract information from Insurance document
        
        Args:
            document_path: Path to insurance document
            file_bytes: File content as bytes
            
        Returns:
            Extracted insurance information (policy number, valid dates, claims)
        """
        try:
            async with httpx.AsyncClient() as client:
                files = self._upload_file(document_path, file_bytes)
                response = await client.post(
                    f"{self.document_ai_url}/extract/insurance",
                    files=files,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[DEBUG] Full Document AI insurance response: {json.dumps(result, indent=2)}")
                    fields = result.get("fields", {})
                    return {
                        "extracted": result.get("extracted", False),
                        "policy_number": fields.get("policy_number"),
                        "valid_from": fields.get("valid_from"),
                        "valid_until": fields.get("valid_until"),
                        "claims": fields.get("claims", []),
                        "confidence": result.get("confidence", 0.0),
                        "raw_text": result.get("raw_text", ""),
                        "source_document_id": result.get("source_document_id")
                    }
        except Exception as e:
            print(f"Error calling Document AI service: {e}")
        
        return {
            "extracted": False,
            "policy_number": None,
            "valid_from": None,
            "valid_until": None,
            "claims": [],
            "confidence": 0.0,
            "raw_text": "",
            "source_document_id": None
        }
    
    async def extract_service_history(self, document_paths: List[str], file_bytes_list: List[bytes]) -> Dict[str, Any]:
        """
        Extract information from Service Bills
        
        Args:
            document_paths: List of paths to service bill documents
            file_bytes_list: List of file contents as bytes
            
        Returns:
            Extracted service history (dates, mileage, work done, costs)
        """
        service_records = []
        
        try:
            async with httpx.AsyncClient() as client:
                for idx, file_bytes in enumerate(file_bytes_list):
                    source_name = document_paths[idx] if idx < len(document_paths) else f"service_bill_{idx}.jpg"
                    files = self._upload_file(source_name, file_bytes)
                    response = await client.post(
                        f"{self.document_ai_url}/extract/service",
                        files=files,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        fields = result.get("fields", {})
                        if "service_records" in fields:
                            service_records.extend(fields["service_records"])
        except Exception as e:
            print(f"Error calling Document AI service: {e}")
        
        return {
            "service_records": service_records,
            "confidence": 0.75,
            "extracted": len(service_records) > 0
        }
    
    async def extract_service_info(self, document_path: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract information from Service Bill
        
        Args:
            document_path: Path to service bill document
            file_bytes: File content as bytes
            
        Returns:
            Extracted service information (dates, mileage, work done, costs)
        """
        try:
            async with httpx.AsyncClient() as client:
                files = self._upload_file(document_path, file_bytes)
                response = await client.post(
                    f"{self.document_ai_url}/extract/service",
                    files=files,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    fields = result.get("fields", {})
                    return {
                        "extracted": result.get("extracted", False),
                        "service_records": fields.get("service_records", []),
                        "confidence": result.get("confidence", 0.0),
                        "source_document_id": result.get("source_document_id")
                    }
        except Exception as e:
            print(f"Error calling Document AI service: {e}")
        
        return {
            "extracted": False,
            "service_records": [],
            "confidence": 0.0,
            "source_document_id": None
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
