"""
Automated tests for the OBD-II diagnostic photo feature (no running server needed).

Run from the backend folder:
    python -m pytest test_obd_diagnostics.py -v

Tests that need real OCR are skipped automatically if Tesseract (or a usable font) is missing.
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from app.main import app
from app.services import diagnostic_ocr
from app.services.diagnostic_ocr import DiagnosticOCRError
from app.services.dtc_catalog import lookup_code, match_titles

client = TestClient(app)


# ---------------------------------------------------------------- helpers
def _font():
    for name in ("consola.ttf", "arial.ttf", "DejaVuSansMono.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(name, 34)
        except OSError:
            continue
    return None


def _tesseract_works() -> bool:
    try:
        diagnostic_ocr.pytesseract.image_to_string(Image.new("L", (20, 20)))
        return True
    except Exception:
        return False


needs_ocr = pytest.mark.skipif(_font() is None or not _tesseract_works(), reason="Tesseract or a usable font is missing")


def scanner_image(lines, dark=True, fmt="JPEG") -> bytes:
    bg, fg = ((15, 25, 40), (230, 230, 230)) if dark else ((235, 235, 235), (20, 20, 20))
    img = Image.new("RGB", (1000, 520), bg)
    draw, y = ImageDraw.Draw(img), 20
    for line in lines:
        draw.text((30, y), line, fill=fg, font=_font())
        y += 52
    buf = io.BytesIO()
    img.save(buf, fmt)
    return buf.getvalue()


def new_inspection() -> str:
    return client.post("/inspection").json()["inspection_id"]


def upload(iid, data=None, name="scan.jpg", mime="image/jpeg"):
    data = data or scanner_image(["P0100"])
    return client.post(f"/inspection/{iid}/obd/photos", files=[("files", (name, data, mime))])


def fake_ocr(codes=(), suggestions=(), readings=(), context="unknown"):
    def _fake(_bytes):
        return {
            "ocr_text": "fake text", "ocr_pass": "normal",
            "proposed_codes": [{"code": c, "ocr_confidence": 0.9, "ocr_uncertain": False} for c in codes],
            "uncertain_codes": list(suggestions), "proposed_readings": list(readings),
            "scan_context": context, "status_keywords_seen": [],
        }
    return _fake


# ---------------------------------------------------------------- engine_assessment basics
def test_no_scan_means_unknown_not_healthy():
    iid = new_inspection()
    ea = client.get(f"/inspection/{iid}").json()["engine_assessment"]
    assert ea["status"] == "not_provided"
    assert ea["risk_flags"] == []
    assert "UNKNOWN" in ea["limitations"][0]


def test_scanner_photo_never_enters_vision_images():
    iid = new_inspection()
    assert upload(iid).status_code == 200
    full = client.get(f"/inspection/{iid}").json()
    assert full["input_files"]["images"] == []
    assert "contents" not in full["engine_assessment"]["diagnostic_evidence"][0]


# ---------------------------------------------------------------- upload validation
def test_upload_rejects_bad_files_and_unknown_inspection():
    iid = new_inspection()
    assert upload(iid, b"hello", "notes.txt", "text/plain").status_code == 400
    assert upload(iid, b"not really an image", "fake.jpg").status_code == 400
    assert upload("INS-DOESNOTEXIST").status_code == 404
    assert client.get("/inspection/NOPE/obd").status_code == 404


# ---------------------------------------------------------------- catalogue / title matching (no OCR needed)
def test_catalogue_lookup_and_title_matching():
    assert lookup_code("p0303")["description"] == "Cylinder 3 Misfire Detected"
    assert lookup_code("P9999") is None
    hit = match_titles("MP69033\n| Cylinder 3 Misfire\n| Detected\n| MOTOPOWER")
    assert [h["suggested_code"] for h in hit] == ["P0303"]          # only the best match, not P0301/P0302
    assert match_titles("Hello world\nVehicle Speed 40\nMenu") == []


# ---------------------------------------------------------------- OCR parsing (OCR itself faked)
def test_lookalike_misread_is_suggested_not_applied(monkeypatch):
    monkeypatch.setattr(diagnostic_ocr, "_prepare", lambda b: Image.new("L", (10, 10)))
    monkeypatch.setattr(diagnostic_ocr, "_ocr_pass",
                        lambda img, psm: ("Codes\nPO100", [("Codes", 90.0), ("PO100", 70.0)]))
    result = diagnostic_ocr.extract_diagnostic_text(b"x")
    assert result["proposed_codes"] == []                              # never rewritten silently
    assert result["uncertain_codes"][0]["suggested_code"] == "P0100"


def test_reading_parser_handles_dropped_underscore_and_ignores_menu_lines():
    readings = diagnostic_ocr._parse_readings(
        "FUELSYS1 OL\nLOAD PCT (%) 55.7\nECT (°F) 159\nRPM 780\nSELECT OPTION 3\nVIEW FREEZE 12", "freeze_frame")
    labels = {r["label"]: r["value"] for r in readings}
    assert labels == {"FUELSYS1": "OL", "LOAD_PCT": "55.7", "ECT": "159", "RPM": "780"}


# ---------------------------------------------------------------- real OCR on generated screens
@needs_ocr
def test_real_ocr_reads_dark_freeze_frame_screen():
    iid = new_inspection()
    data = scanner_image(["View Freeze Frame", "P0100", "FUELSYS1  OL", "LOAD_PCT (%)  55.7", "ECT (°F)  159"])
    eid = upload(iid, data).json()["evidence"][0]["evidence_id"]
    ev = client.post(f"/inspection/{iid}/obd/extract/{eid}").json()["evidence"]
    assert ev["ocr_status"] == "needs_user_confirmation"
    assert "P0100" in [c["code"] for c in ev["extracted_codes"]]
    assert ev["scan_context"] == "freeze_frame"
    assert "LOAD_PCT" in [r["label"] for r in ev["extracted_readings"]]
    assert all(c["user_confirmed"] is False for c in ev["extracted_codes"])    # proposals only


@needs_ocr
def test_real_ocr_reads_light_screen_with_two_codes():
    iid = new_inspection()
    eid = upload(iid, scanner_image(["Stored Codes", "P0301", "P0420"], dark=False), "s.png", "image/png").json()["evidence"][0]["evidence_id"]
    ev = client.post(f"/inspection/{iid}/obd/extract/{eid}").json()["evidence"]
    assert {"P0301", "P0420"} <= {c["code"] for c in ev["extracted_codes"]}


# ---------------------------------------------------------------- full workflow (OCR faked, so it runs anywhere)
def test_full_flow_create_upload_extract_confirm_get(monkeypatch):
    monkeypatch.setattr("app.api.obd.extract_diagnostic_text", fake_ocr(codes=["P0303"]))
    iid = new_inspection()
    eid = upload(iid).json()["evidence"][0]["evidence_id"]

    # before confirmation: flagged as unverified, no code finding yet
    client.post(f"/inspection/{iid}/obd/extract/{eid}")
    ea = client.get(f"/inspection/{iid}").json()["engine_assessment"]
    assert ea["status"] == "awaiting_confirmation"
    assert [f["flag"] for f in ea["risk_flags"]] == ["diagnostic_evidence_unverified"]

    body = {"codes": [{"code": "p0303", "scanner_status": "stored"}], "readings": [], "scan_context": "unknown",
            "no_codes_visible": False, "notes": ["page 1/2"]}
    r = client.post(f"/inspection/{iid}/obd/confirm/{eid}", json=body)
    assert r.status_code == 200
    code = r.json()["evidence"]["extracted_codes"][0]
    assert (code["code"], code["entry_source"], code["user_confirmed"]) == ("P0303", "ocr_confirmed", True)

    full = client.get(f"/inspection/{iid}").json()
    ea = full["engine_assessment"]
    assert ea["status"] == "confirmed" and ea["risk_level"] == "undetermined"
    flag = ea["risk_flags"][0]
    assert (flag["flag"], flag["code"]) == ("diagnostic_code_present", "P0303")
    assert flag["description"] == "Cylinder 3 Misfire Detected" and flag["possible_causes"]
    assert eid in flag["evidence"]                                   # traceable to the source photo
    assert full["pipeline_status"]["diagnostics_confirmed"] is True

    # confirmed evidence cannot be re-extracted
    assert client.post(f"/inspection/{iid}/obd/extract/{eid}").status_code == 409


def test_confirm_validation_and_no_code_screen(monkeypatch):
    monkeypatch.setattr("app.api.obd.extract_diagnostic_text", fake_ocr())
    iid = new_inspection()
    eid = upload(iid).json()["evidence"][0]["evidence_id"]
    url = f"/inspection/{iid}/obd/confirm/{eid}"

    assert client.post(url, json={"codes": [{"code": "P9999"}]}).status_code == 422     # invalid DTC shape
    assert client.post(url, json={"codes": []}).status_code == 422                      # nothing confirmed
    assert client.post(url, json={"codes": [{"code": "P0100", "scanner_status": "bogus"}]}).status_code == 422

    assert client.post(url, json={"codes": [], "no_codes_visible": True}).status_code == 200
    ea = client.get(f"/inspection/{iid}").json()["engine_assessment"]
    assert ea["status"] == "confirmed"
    assert ea["risk_flags"] == []                                    # no code seen is NOT "healthy"
    assert any("not a clean scan" in l for l in ea["limitations"])


def test_ocr_failure_is_recoverable_with_manual_entry(monkeypatch):
    def boom(_bytes):
        raise DiagnosticOCRError("Tesseract OCR is not installed")
    monkeypatch.setattr("app.api.obd.extract_diagnostic_text", boom)
    iid = new_inspection()
    eid = upload(iid).json()["evidence"][0]["evidence_id"]

    r = client.post(f"/inspection/{iid}/obd/extract/{eid}").json()
    assert r["evidence"]["ocr_status"] == "ocr_failed" and r["manual_entry_required"] is True

    ok = client.post(f"/inspection/{iid}/obd/confirm/{eid}",
                     json={"codes": [{"code": "P0420"}], "scan_context": "unknown"})
    assert ok.status_code == 200
    assert ok.json()["evidence"]["extracted_codes"][0]["entry_source"] == "user_added"