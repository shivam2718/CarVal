"""Local DTC catalogue lookup. Unknown codes return None (never guessed)."""

import difflib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "dtc_catalog.json"


@lru_cache(maxsize=1)
def _load() -> dict:
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {k.upper(): v for k, v in data.items() if not k.startswith("_")}


def lookup_code(code: str) -> Optional[dict]:
    return _load().get((code or "").strip().upper())


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def match_titles(text: str, threshold: float = 0.9) -> List[Dict[str, str]]:
    """
    Scanners usually print the code AND its title (e.g. "Cylinder 3 Misfire Detected").
    Small/blurry photos often lose the code but keep the title, so match OCR lines against catalogue titles.
    Returned as SUGGESTIONS only: the user must still confirm.
    """
    raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
    windows = []  # (original text, normalised) for 1-3 consecutive lines
    for size in (1, 2, 3):
        for i in range(len(raw_lines) - size + 1):
            chunk = " ".join(raw_lines[i:i + size])
            windows.append((chunk, _norm(chunk)))

    scored = []
    for code, info in _load().items():
        title = _norm(info["description"])
        best_ratio, best_text = 0.0, ""
        for original, norm in windows:
            if not norm:
                continue
            ratio = difflib.SequenceMatcher(None, norm, title).ratio()
            if ratio > best_ratio:
                best_ratio, best_text = ratio, original
        if best_ratio >= threshold:
            scored.append((best_ratio, code, best_text, info["description"]))

    scored.sort(reverse=True)
    if not scored:
        return []
    top = scored[0][0]
    return [
        {
            "raw_text": raw,
            "suggested_code": code,
            "reason": f"Screen text matches the title of {code} ({title})",
        }
        for ratio, code, raw, title in scored
        if top - ratio <= 0.01  # keep only the best match(es); near-identical titles (P0301 vs P0303) are not both offered
    ]