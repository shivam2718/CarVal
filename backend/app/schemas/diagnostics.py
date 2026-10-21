"""
Request models for the OBD-II diagnostic photo feature.
Evidence itself is stored as plain dicts in inspections_db (same style as images/documents).
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ScannerStatus = Literal["unknown", "stored", "pending", "permanent", "current"]
ScanContext = Literal["unknown", "freeze_frame", "stored", "pending", "permanent", "current", "live"]


class ConfirmedCode(BaseModel):
    code: str = Field(..., description="DTC such as P0100 (the user has checked it against the photo)")
    scanner_status: ScannerStatus = "unknown"  # only set when the scanner screen says so


class ConfirmedReading(BaseModel):
    label: str
    value: str
    unit: Optional[str] = None
    context: ScanContext = "unknown"


class DiagnosticConfirmRequest(BaseModel):
    codes: List[ConfirmedCode] = Field(default_factory=list)
    readings: List[ConfirmedReading] = Field(default_factory=list)
    scan_context: ScanContext = "unknown"
    no_codes_visible: bool = False  # user states the screen shows no code (NOT the same as "healthy")
    notes: List[str] = Field(default_factory=list)