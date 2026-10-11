"""
Generate sample_data/mock_responses/vision_response.json from real model output
Member 1 - Vision/Damage Detection

Runs the real service code (weights/best.pt) on a few images and saves the /analyze response, for
Member 3's integration and the frontend. Image IDs are IMG-001, IMG-002, ... as in docs/API_CONTRACT.md.

Usage (from services/vision/):
  python generate_sample.py IMAGE [IMAGE ...] [--out PATH]
  python generate_sample.py ~/Documents/BTP/datasets/CarDD_yolo/images/test/000012.jpg ~/Documents/BTP/datasets/CarDD_yolo/images/test/000023.jpg
"""

import argparse
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import main

DEFAULT_OUT = main.VISION_DIR.parent.parent / "sample_data" / "mock_responses" / "vision_response.json"


def build_sample(images):
    with TestClient(main.app) as client:  # runs lifespan -> loads weights
        if main.detector.mode != "trained":
            sys.exit("No trained weights found (weights/best.pt). A sample from fallback mode would be empty.")
        files = [("files", (f"IMG-{i:03d}{Path(p).suffix.lower()}", open(p, "rb"), "image/jpeg"))
                 for i, p in enumerate(images, start=1)]
        res = client.post("/analyze/upload", files=files)
        res.raise_for_status()
        return res.json()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    sample = build_sample([p.expanduser() for p in args.images])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(sample, indent=2) + "\n")
    n = sum(len(r["damages"]) for r in sample["image_results"])
    print(f"✓ Wrote {args.out}  ({len(sample['image_results'])} images, {n} damages)")
