"""
Test script for the Vision Service
Member 1 - Vision/Damage Detection

Standalone checks with ✓/✗ output. Run from services/vision/:
    python test_vision.py
Also works with pytest:  pytest test_vision.py

Needs no running server (uses FastAPI's TestClient) and no trained weights: checks that depend on
trained weights or on the CarDD dataset are reported as skipped when those are missing.
"""

import io
import json
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import config  # noqa: E402
import main  # noqa: E402
from damage_classes import CLASSES, CLASS_TO_ID  # noqa: E402
from detector import DamageDetector, draw_annotations, severity_from_area  # noqa: E402

SCHEMA = json.loads((HERE.parent.parent / "schemas" / "vehicle_schema_v1.json").read_text())
SCHEMA_DAMAGE_KEYS = set(SCHEMA["vision"]["damage_detection"]["image_results"][0]["damages"][0])
SCHEMA_BBOX_KEYS = set(SCHEMA["vision"]["damage_detection"]["image_results"][0]["damages"][0]["bbox"])
SCHEMA_ODOMETER_KEYS = set(SCHEMA["vision"]["odometer"])
SAMPLE_JSON = HERE.parent.parent / "sample_data" / "mock_responses" / "vision_response.json"
CARDD_TEST_IMAGE = Path.home() / "Documents/BTP/datasets/CarDD_yolo/images/test/000012.jpg"  # flat tyre


try:  # under pytest, skips are real skips
    from _pytest.outcomes import Skipped as Skip
except ImportError:
    class Skip(Exception):
        pass


def jpeg_bytes(size=(320, 240), color=(120, 120, 120)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


def client() -> TestClient:
    return TestClient(main.app)


def check_response_shape(body: dict):
    assert set(body) == {"model", "image_results", "odometer"}, f"unexpected keys {set(body)}"
    assert set(body["odometer"]) == SCHEMA_ODOMETER_KEYS
    for result in body["image_results"]:
        assert set(result) == {"image_id", "damages"}
        for d in result["damages"]:
            assert set(d) == SCHEMA_DAMAGE_KEYS, f"damage keys {set(d)} != schema {SCHEMA_DAMAGE_KEYS}"
            assert set(d["bbox"]) == SCHEMA_BBOX_KEYS
            assert d["type"] in CLASSES
            assert 0.0 <= d["confidence"] <= 1.0
            assert d["evidence"] == [result["image_id"]]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_class_order():
    assert CLASSES == ["dent", "scratch", "crack", "glass", "lamp", "tire"]
    assert [CLASS_TO_ID[c] for c in CLASSES] == list(range(6))


def test_severity_rule():
    assert severity_from_area(0.005) == "low"
    assert severity_from_area(0.05) == "medium"
    assert severity_from_area(0.30) == "high"


def test_health():
    with client() as c:
        body = c.get("/health").json()
    assert body["status"] in ("healthy", "degraded")
    assert body["model_mode"] in ("trained", "fallback", "unavailable")
    assert body["classes"] == CLASSES


def test_analyze_upload_matches_contract():
    with client() as c:
        r = c.post("/analyze/upload", files=[("files", ("IMG-TEST0001.jpg", jpeg_bytes(), "image/jpeg"))])
    assert r.status_code == 200, r.text
    body = r.json()
    check_response_shape(body)
    assert body["image_results"][0]["image_id"] == "IMG-TEST0001"


def test_annotated_image_is_returned():
    with client() as c:
        c.post("/analyze/upload", files=[("files", ("IMG-TEST0002.jpg", jpeg_bytes(), "image/jpeg"))])
        r = c.get("/annotated/IMG-TEST0002")
        missing = c.get("/annotated/IMG-NOPE")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert Image.open(io.BytesIO(r.content)).size == (320, 240)
    assert missing.status_code == 404


def test_analyze_by_file_path_json_contract():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "IMG-001.jpg"
        path.write_bytes(jpeg_bytes())
        with client() as c:
            by_path = c.post("/analyze", json={"image_paths": [str(path)]})
            by_pair = c.post("/analyze", json={"image_paths": [{"image_id": "IMG-009", "path": str(path)}]})
    assert by_path.status_code == 200 and by_path.json()["image_results"][0]["image_id"] == "IMG-001"
    assert by_pair.status_code == 200 and by_pair.json()["image_results"][0]["image_id"] == "IMG-009"
    check_response_shape(by_path.json())


def test_analyze_by_bare_id_uses_image_dir():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "IMG-001.png").write_bytes(b"")
        Image.new("RGB", (64, 64)).save(Path(tmp) / "IMG-001.png")
        old = main.settings.image_dir
        main.settings.image_dir = Path(tmp)
        try:
            with client() as c:
                ok = c.post("/analyze", json={"image_paths": ["IMG-001"]})
                missing = c.post("/analyze", json={"image_paths": ["IMG-404"]})
        finally:
            main.settings.image_dir = old
    assert ok.status_code == 200 and ok.json()["image_results"][0]["image_id"] == "IMG-001"
    assert missing.status_code == 404


def test_bad_requests_are_rejected():
    with client() as c:
        wrong_type = c.post("/analyze/upload", files=[("files", ("notes.txt", b"hello", "text/plain"))])
        fake_jpg = c.post("/analyze/upload", files=[("files", ("x.jpg", b"not an image", "image/jpeg"))])
        empty = c.post("/analyze", json={"image_paths": []})
        too_big = c.post("/analyze/upload", files=[("files", ("big.jpg", b"0" * (11 * 1024 * 1024), "image/jpeg"))])
    assert wrong_type.status_code == 400
    assert fake_jpg.status_code == 400
    assert empty.status_code == 422
    assert too_big.status_code == 400


def test_single_image_alias():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "car.jpg"
        path.write_bytes(jpeg_bytes())
        with client() as c:
            r = c.post("/vision/analyze", json={"image_path": str(path), "image_id": "IMG-001"})
    assert r.status_code == 200, r.text
    assert set(r.json()) == {"image_id", "model", "damages"} and r.json()["image_id"] == "IMG-001"


def test_fallback_when_weights_missing():
    old = config.DEFAULT_WEIGHTS
    config.DEFAULT_WEIGHTS = Path("/nonexistent/best.pt")
    try:
        s = config.Settings(model_path=Path("/nonexistent/other.pt"))
        det = DamageDetector(s)
        det.load()
        damages = det.detect(Image.new("RGB", (100, 100)), "IMG-001")
    finally:
        config.DEFAULT_WEIGHTS = old
    assert det.mode in ("fallback", "unavailable")
    assert damages == []
    assert "fallback" in det.model_name


def test_boxes_are_drawn():
    img = Image.new("RGB", (200, 100), (0, 0, 0))
    damage = {"type": "dent", "confidence": 0.9, "bbox": {"x1": 20, "y1": 20, "x2": 120, "y2": 80}}
    out = Image.open(io.BytesIO(draw_annotations(img, [damage]))).convert("RGB")
    assert sum(out.getpixel((70, 50))) < 60   # inside the box: unchanged
    assert sum(out.getpixel((20, 50))) > 200  # on the box edge: coloured


def test_sample_json_matches_schema():
    if not SAMPLE_JSON.exists():
        raise Skip("sample_data/mock_responses/vision_response.json not generated yet")
    check_response_shape(json.loads(SAMPLE_JSON.read_text()))


def test_demo_page_served():
    with client() as c:
        r = c.get("/demo")
    assert r.status_code == 200 and "CarVal Vision Demo" in r.text


def test_real_model_finds_flat_tyre():
    if not CARDD_TEST_IMAGE.exists():
        raise Skip("CarDD test image not on this machine")
    with client() as c:
        if main.detector.mode != "trained":
            raise Skip("no trained weights in weights/best.pt")
        body = c.post("/analyze", json={"image_paths": [str(CARDD_TEST_IMAGE)]}).json()
    check_response_shape(body)
    img = Image.open(CARDD_TEST_IMAGE)
    types = [d["type"] for d in body["image_results"][0]["damages"]]
    assert "tire" in types, f"expected a tire detection, got {types}"
    for d in body["image_results"][0]["damages"]:
        b = d["bbox"]
        assert 0 <= b["x1"] < b["x2"] <= img.width and 0 <= b["y1"] < b["y2"] <= img.height


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all() -> bool:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    passed = failed = skipped = 0
    print("=" * 60)
    print("VISION SERVICE TESTS")
    print("=" * 60)
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
            passed += 1
        except Skip as why:
            print(f"- {name}  (skipped: {why})")
            skipped += 1
        except Exception as exc:
            print(f"✗ {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print("-" * 60)
    print(f"{passed} passed, {failed} failed, {skipped} skipped")
    print("✓ ALL TESTS PASSED" if not failed else "✗ SOME TESTS FAILED")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
