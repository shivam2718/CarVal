"""
Valuation module - STUB.
Fair-value prediction (XGBoost) is Review 3 scope. The route exists so the UI and the
common vehicle JSON have a stable place for it; it never returns a made-up price.
"""

from fastapi import APIRouter, HTTPException

from app.core.store import inspections_db

router = APIRouter(prefix="/inspection/{inspection_id}/valuation", tags=["valuation"])

VALUATION_STUB = {
    "status": "pending",
    "predicted_fair_value": None,
    "currency": "INR",
    "message": "Car price valuation is not implemented in Review 2 (planned for Review 3).",
}


@router.get("")
def get_valuation(inspection_id: str):
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return {"inspection_id": inspection_id, **VALUATION_STUB}
