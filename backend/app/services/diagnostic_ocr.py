"""
Diagnostic Photo OCR (OBD-II scanner screen reader)

Reads a PHOTO of an existing scanner screen. CarVal never connects to the car.
Everything returned here is a PROPOSAL: the user must confirm it before it is used.

Runs inside the backend (Pillow + pytesseract are already in requirements.txt).
The Tesseract program itself must be installed:
  Windows: install Tesseract, then either add it to PATH or set TESSERACT_CMD
           (e.g. C:\\Program Files\\Tesseract-OCR\\tesseract.exe)
"""

import os
import re
from io import BytesIO
from typing import Any, Dict, List, Tuple

import pytesseract
from PIL import Image, ImageOps
from pytesseract import Output

from app.services.dtc_catalog import match_titles


class DiagnosticOCRError(Exception):
    """Recoverable OCR failure (Tesseract missing, unreadable image, timeout)."""


# --- Tesseract location (Windows-friendly) -----------------------------------------------
def _configure_tesseract() -> None:
    cmd = os.getenv("TESSERACT_CMD")
    if not cmd and os.name == "nt":
        default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default):
            cmd = default
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd


_configure_tesseract()

# --- Patterns -----------------------------------------------------------------------------
# Standard DTC shape: system letter + digit 0-3 + three hex characters (P0100, U0100, ...)
DTC_STRICT = re.compile(r"(?<![A-Z0-9])([PBCU][0-3][0-9A-F]{3})(?![A-Z0-9])")
_LOOKALIKE_TOKEN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9]{5}(?![A-Za-z0-9])")
_LOOKALIKE_MAP = str.maketrans({"O": "0", "Q": "0", "I": "1", "L": "1"})

# Label = one word, or two words (Tesseract often drops the underscore: "LOAD PCT" instead of "LOAD_PCT")
_LABEL = r"([A-Z][A-Z0-9_]{1,15}(?: [A-Z0-9_]{1,8})?)"
_READING_WITH_UNIT = re.compile(r"^\s*" + _LABEL + r"\s*\(([^)]{1,6})\)\s+(-?\d+(?:\.\d+)?|[A-Z]{1,4}\d?)\s*$")
_READING_PLAIN = re.compile(r"^\s*" + _LABEL + r"\s+(-?\d+(?:\.\d+)?|[A-Z]{1,4}\d?)\s*$")
_KNOWN_LABELS = {
    "RPM", "ECT", "IAT", "MAP", "MAF", "VSS", "SPEED", "TP", "LOAD_PCT", "FUELSYS1", "FUELSYS2",
    "SHRTFT1", "SHRTFT2", "LONGFT1", "LONGFT2", "FUEL_PRES", "SPARKADV", "O2B1S1", "O2B1S2",
}
_STATUS_WORDS = ("FREEZE FRAME", "PENDING", "PERMANENT", "STORED", "CURRENT", "HISTORY", "CLEARED")

MIN_WIDTH = 1400       # upscale small photos so small scanner fonts become readable
MAX_SIDE = 2600        # shrink huge photos to keep OCR fast
OCR_TIMEOUT_S = 30


def _prepare(image_bytes: bytes) -> Image.Image:
    try:
        img = Image.open(BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)  # phone photos are often stored rotated
        img = img.convert("L")
    except Exception as e:
        raise DiagnosticOCRError(f"Cannot open image: {e}") from e

    longest = max(img.size)
    if longest > MAX_SIDE:
        scale = MAX_SIDE / longest
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    elif img.width < MIN_WIDTH:
        scale = min(3.0, MIN_WIDTH / img.width)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    return ImageOps.autocontrast(img)


def _ocr_pass(img: Image.Image, psm: int) -> Tuple[str, List[Tuple[str, float]]]:
    """One Tesseract run -> (text rebuilt line by line, [(word, confidence 0-100)])."""
    try:
        data = pytesseract.image_to_data(
            img, config=f"--oem 3 --psm {psm}", output_type=Output.DICT, timeout=OCR_TIMEOUT_S
        )
    except pytesseract.TesseractNotFoundError as e:
        raise DiagnosticOCRError(
            "Tesseract OCR is not installed or not found. Install it (or set TESSERACT_CMD) "
            "- you can still enter the codes manually."
        ) from e
    except pytesseract.TesseractError as e:  # must come BEFORE RuntimeError (it is a subclass of it)
        detail = str(e)
        if "traineddata" in detail or "TESSDATA_PREFIX" in detail:
            raise DiagnosticOCRError(
                "Tesseract is installed but its English language data (eng.traineddata) is missing or unreadable. "
                "Put eng.traineddata in the tessdata folder or set TESSDATA_PREFIX - "
                "you can still enter the codes manually."
            ) from e
        raise DiagnosticOCRError(f"OCR failed: {detail}") from e
    except RuntimeError as e:  # pytesseract raises a plain RuntimeError on timeout
        raise DiagnosticOCRError(f"OCR timed out: {e}") from e

    lines: Dict[Tuple[int, int, int], List[Tuple[int, str]]] = {}
    words: List[Tuple[str, float]] = []
    for i in range(len(data["text"])):
        token = (data["text"][i] or "").strip()
        if not token:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1.0
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append((data["left"][i], token))
        if conf >= 0:
            words.append((token, conf))
    text = "\n".join(" ".join(t for _, t in sorted(parts)) for _, parts in sorted(lines.items()))
    return text, words


def _strict_codes(words: List[Tuple[str, float]]) -> Dict[str, float]:
    found: Dict[str, float] = {}
    for token, conf in words:
        for code in DTC_STRICT.findall(token.upper()):
            found[code] = max(found.get(code, 0.0), conf)
    return found


def _parse_readings(text: str, context: str) -> List[Dict[str, Any]]:
    readings: List[Dict[str, Any]] = []
    seen = set()
    for line in text.splitlines():
        m = _READING_WITH_UNIT.match(line)
        raw_label = unit = value = None
        if m:
            raw_label, unit, value = m.group(1), m.group(2).strip(), m.group(3)
        else:
            m = _READING_PLAIN.match(line)
            if m:
                raw_label, value = m.group(1), m.group(2)
        if not raw_label:
            continue
        label = raw_label
        if " " in raw_label:
            joined = raw_label.replace(" ", "_")
            if joined not in _KNOWN_LABELS:
                continue  # two-word line that is not a known reading label (e.g. a menu title)
            label = joined  # OCR dropped the underscore; the user still sees/edits it
        elif m and not unit and label not in _KNOWN_LABELS:
            continue      # "LABEL value" without a unit is only trusted for known labels
        if label in seen or DTC_STRICT.fullmatch(label):
            continue
        seen.add(label)
        readings.append({"label": label, "value": value, "unit": unit, "context": context, "user_confirmed": False})
    return readings


def extract_diagnostic_text(image_bytes: bytes) -> Dict[str, Any]:
    """Photo bytes -> OCR text + proposed codes/readings. Raises DiagnosticOCRError if OCR can't run."""
    base = _prepare(image_bytes)
    variants = [("normal", base), ("inverted", ImageOps.invert(base))]  # scanners often show light-on-dark

    results = []  # (name, text, words)
    for name, img in variants:
        text, words = _ocr_pass(img, 6)
        results.append((name, text, words))
    if not any(_strict_codes(w) for _, _, w in results):
        for name, img in variants:  # second chance with sparse-text mode
            text, words = _ocr_pass(img, 11)
            results.append((f"{name}-sparse", text, words))

    # best pass for the displayed text = most confidently read words
    best_name, best_text, best_words = max(results, key=lambda r: sum(1 for _, c in r[2] if c >= 60))

    # strict candidates: union over all passes (best confidence kept)
    merged: Dict[str, float] = {}
    for _, _, words in results:
        for code, conf in _strict_codes(words).items():
            merged[code] = max(merged.get(code, 0.0), conf)

    proposed_codes = [
        {"code": code, "ocr_confidence": round(conf / 100.0, 3), "ocr_uncertain": False}
        for code, conf in sorted(merged.items())
    ]

    # look-alike misreads (e.g. 'PO100'): offered as a SUGGESTION, never applied silently
    uncertain: List[Dict[str, Any]] = []
    seen_raw = set()
    for token in _LOOKALIKE_TOKEN.findall(best_text):
        up = token.upper()
        if up in seen_raw or DTC_STRICT.fullmatch(up) or not re.match(r"^[PBCU]", up):
            continue
        if sum(ch.isdigit() for ch in up) < 2:
            continue
        fixed = up.translate(_LOOKALIKE_MAP)
        if fixed != up and DTC_STRICT.fullmatch(fixed) and fixed not in merged:
            seen_raw.add(up)
            uncertain.append({"raw_text": token, "suggested_code": fixed})
        # Title match: lets a photo with an unreadable code but readable title still produce a suggestion
    already = {u["suggested_code"] for u in uncertain} | set(merged)
    for hit in match_titles(best_text):
        if hit["suggested_code"] not in already:
            uncertain.append(hit)

    upper = best_text.upper()
    upper = best_text.upper()
    context = "freeze_frame" if "FREEZE FRAME" in upper else "unknown"
    return {
        "ocr_text": best_text,
        "ocr_pass": best_name,
        "proposed_codes": proposed_codes,
        "uncertain_codes": uncertain,
        "proposed_readings": _parse_readings(best_text, context),
        "scan_context": context,
        "status_keywords_seen": [w for w in _STATUS_WORDS if w in upper],
    }