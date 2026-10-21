"""
Builds the `engine_assessment` block of the combined Vehicle JSON from stored diagnostic evidence.

Rules (from the OBD feature guide):
- Only USER-CONFIRMED codes create findings.
- A code means "a condition was detected", not "this part is faulty".
- No scan / no code / OCR failure = UNKNOWN evidence, never "healthy".
- No health score or valuation change is computed from OCR alone.
"""

from typing import Any, Dict, List

from app.services.dtc_catalog import lookup_code

SECRET_KEYS = {"contents"}


def public_evidence(ev: Dict[str, Any]) -> Dict[str, Any]:
    """Evidence without the raw image bytes."""
    return {k: v for k, v in ev.items() if k not in SECRET_KEYS}


def build_engine_assessment(inspection: Dict[str, Any]) -> Dict[str, Any]:
    evidence: List[Dict[str, Any]] = inspection.get("diagnostics", [])
    confirmed = [e for e in evidence if e.get("ocr_status") == "confirmed"]
    unconfirmed = [e for e in evidence if e.get("ocr_status") != "confirmed"]

    flags: List[Dict[str, Any]] = []
    actions: List[str] = []

    for ev in confirmed:
        refs = [ev["evidence_id"], ev["source_image_id"]]
        for c in ev.get("extracted_codes", []):
            info = lookup_code(c["code"])
            flags.append({
                "flag": "diagnostic_code_present",
                "code": c["code"],
                "description": c.get("description"),
                "in_catalogue": c.get("in_catalogue", info is not None),
                "possible_causes": (info or {}).get("possible_causes", []),
                "scanner_status": c.get("scanner_status", "unknown"),
                "scan_context": ev.get("scan_context", "unknown"),
                "note": "A code shows a detected condition; it does not prove which part is faulty.",
                "evidence": refs,
            })
            for check in (info or {}).get("follow_up_checks", []):
                if check not in actions:
                    actions.append(check)

    for ev in unconfirmed:
        flags.append({
            "flag": "diagnostic_evidence_unverified",
            "note": "Scanner photo uploaded but codes are not confirmed by the user yet.",
            "evidence": [ev["evidence_id"], ev["source_image_id"]],
        })

    if not evidence:
        status = "not_provided"
    elif not confirmed:
        status = "awaiting_confirmation"
    elif unconfirmed:
        status = "partially_confirmed"
    else:
        status = "confirmed"

    limitations: List[str] = []
    if status == "not_provided":
        limitations.append("No diagnostic scan was provided. Engine/electronic-system condition is UNKNOWN, not healthy.")
    else:
        limitations.append("A scanner photo may show stored or freeze-frame data rather than a current fault.")
        limitations.append("No visible code in a photo is not a clean scan: the screen may show only one page or mode.")
    if any(c.get("extracted_codes") for c in confirmed):
        actions.append("Have a qualified mechanic confirm each code with a full diagnostic scan before buying.")
        actions.append("Do not clear codes during the inspection: clearing erases evidence.")

    return {
        "status": status,
        "diagnostic_evidence": [public_evidence(e) for e in evidence],
        "risk_level": "undetermined",
        "risk_flags": flags,
        "recommended_actions": actions,
        "limitations": limitations,
    }