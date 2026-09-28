"""
Document AI Service Client
Member 3 - Backend
Calls Member 2's Document AI Service and processes responses
"""

import httpx
from typing import List, Dict, Any
import os


class DocumentAIClient:
    """Client for interacting with Member 2's Document AI Service"""
    
    def __init__(self):
        self.document_ai_url = os.getenv("DOCUMENT_AI_SERVICE_URL", "http://localhost:8002")
    
    async def extract_rc_info(self, document_path: str) -> Dict[str, Any]:
        """
        Extract information from RC (Registration Certificate)
        
        Args:
            document_path: Path to RC document
            
        Returns:
            Extracted RC information (registration number, owner, model, year, etc.)
        """
        # TODO: Implement actual HTTP call to Member 2's Document AI Service
        # Expected response format:
        # {
        #   "extracted": true,
        #   "fields": {
        #     "registration_number": "DL-01-AB-1234",
        #     "owner": "John Doe",
        #     "model": "Maruti Swift",
        #     "manufacturing_year": 2015,
        #     "registration_year": 2015
        #   },
        #   "confidence": 0.92
        # }
        
        return {
            "extracted": False,
            "fields": {},
            "confidence": None
        }
    
    async def extract_insurance_info(self, document_path: str) -> Dict[str, Any]:
        """
        Extract information from Insurance document
        
        Args:
            document_path: Path to insurance document
            
        Returns:
            Extracted insurance information (policy number, valid dates, claims)
        """
        # TODO: Implement call to Member 2's Document AI Service
        
        return {
            "extracted": False,
            "policy_number": None,
            "valid_from": None,
            "valid_until": None,
            "claims": [],
            "confidence": None
        }
    
    async def extract_service_history(self, document_paths: List[str]) -> Dict[str, Any]:
        """
        Extract information from Service Bills
        
        Args:
            document_paths: List of paths to service bill documents
            
        Returns:
            Extracted service history (dates, mileage, work done, costs)
        """
        # TODO: Implement call to Member 2's Document AI Service
        
        return {
            "service_records": [],
            "confidence": None
        }
