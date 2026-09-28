"""
Vehicle Data Schemas (Pydantic Models)
Mirrors CarVal vehicle_schema_v1.json for type safety
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class BoundingBox(BaseModel):
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None


class Damage(BaseModel):
    damage_id: Optional[str] = None
    type: Optional[str] = None
    confidence: Optional[float] = None
    bbox: BoundingBox = BoundingBox()
    severity: Optional[str] = None
    affected_part: Optional[str] = None
    evidence: List[str] = []


class ImageResult(BaseModel):
    image_id: Optional[str] = None
    damages: List[Damage] = []


class DamageDetection(BaseModel):
    model: Optional[str] = None
    image_results: List[ImageResult] = []


class OdometerReading(BaseModel):
    detected: bool = False
    value_km: Optional[float] = None
    confidence: Optional[float] = None
    image_id: Optional[str] = None
    evidence: List[str] = []


class VisionData(BaseModel):
    damage_detection: DamageDetection = DamageDetection()
    odometer: OdometerReading = OdometerReading()


class ServiceRecord(BaseModel):
    service_id: Optional[str] = None
    date: Optional[str] = None
    mileage_km: Optional[float] = None
    service_center: Optional[str] = None
    work_done: List[str] = []
    parts_replaced: List[str] = []
    cost: Optional[float] = None
    currency: str = "INR"
    source_document_ids: List[str] = []


class DocumentData(BaseModel):
    rc: Dict[str, Any] = {}
    insurance: Dict[str, Any] = {}
    service_history: List[ServiceRecord] = []


class InspectionResult(BaseModel):
    schema_version: str = "1.0"
    vehicle_id: str
    vehicle: Dict[str, Any] = {}
    input_files: Dict[str, Any] = {}
    vision: VisionData = VisionData()
    documents: DocumentData = DocumentData()
    vehicle_history: Dict[str, Any] = {}
    pipeline_status: Dict[str, bool] = {}
