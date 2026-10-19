# Vision Service

**Owner**: Member 1 - Vision/Damage Detection

YOLOv8 damage detection for car images. For each image it returns the damage class, confidence and
bounding box. Port **8001**.

Classes (fixed order, class ids 0-5): `dent`, `scratch`, `crack`, `glass`, `lamp`, `tire`.

## Review 2 status

- [x] Dataset prepared (CarDD, converted to YOLO format with train/val/test splits)
- [x] YOLOv8 baseline (yolov8n)
- [x] Fine-tuned for the six damage classes (yolov8s, class-balanced sampling)
- [x] Damage output: class, confidence, bounding box
- [x] Evaluation: precision, recall, mAP@50 overall and per class ([reports/metrics.md](reports/metrics.md))
- [x] Inference API: `POST /analyze` (contract in [docs/API_CONTRACT.md](../../docs/API_CONTRACT.md))
- [x] Sample JSON for integration: [sample_data/mock_responses/vision_response.json](../../sample_data/mock_responses/vision_response.json)
- [ ] Odometer reading (the field is returned with `detected: false`; planned for Review 3)

Demo: upload a car image at `http://localhost:8001/demo` and the detected damage is shown with bounding
boxes, class and confidence.

## Results (test split, 374 images, 785 boxes)

| Model | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|---|
| Baseline (yolov8n, no balancing) | 0.762 | 0.642 | 0.710 | 0.549 |
| Fine-tuned (yolov8s, repeat-factor sampling) | 0.747 | 0.679 | 0.718 | 0.569 |

Per-class mAP@50 (fine-tuned): glass 0.986, tire 0.901, lamp 0.837, dent 0.592, scratch 0.556, crack 0.436.
The full table is in [reports/metrics.md](reports/metrics.md) and `reports/metrics.json`.

## Setup

Python 3.11 recommended.

```bash
cd services/vision
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the service

```bash
cd services/vision
source .venv/bin/activate
python main.py          # http://localhost:8001
```

- Swagger UI: `http://localhost:8001/docs`
- Demo page: `http://localhost:8001/demo`
- Health: `curl http://localhost:8001/health`

The service loads `weights/best.pt` (or the file in `VISION_MODEL_PATH`). If no trained weights exist it
still starts and answers every request, but reports no damages and says so in `/health`
(`model_mode: "fallback"`), because the pretrained COCO model has no damage classes. It does not reload on
code changes: stop it and start it again after editing.

### Configuration

Environment variables, or a `services/vision/.env` file (gitignored). All are optional.

| Variable | Default | Meaning |
|---|---|---|
| `VISION_MODEL_PATH` | `weights/best.pt` | Trained weights |
| `VISION_CONFIDENCE_THRESHOLD` | `0.25` | Minimum confidence of a reported damage |
| `VISION_IOU_THRESHOLD` | `0.5` | Overlap threshold for removing duplicate boxes |
| `VISION_DEVICE` | `auto` | `auto` picks CUDA, then Apple MPS, then CPU. Or `mps`, `cpu`, `0` |
| `VISION_IMAGE_DIR` | unset | Folder where bare image IDs such as `IMG-001` are looked up |
| `VISION_HOST` / `VISION_PORT` | `127.0.0.1` / `8001` | Bind address |

## API

### GET /health
Model status: `model_mode` is `trained`, `fallback` or `unavailable`.

### POST /analyze
The endpoint from the API contract. The backend calls this.

Request:
```json
{ "image_paths": ["IMG-001", "IMG-002"] }
```
Each entry can be a file path, a bare image ID (resolved inside `VISION_IMAGE_DIR` as `IMG-001.jpg`,
`.jpeg` or `.png`), or `{"image_id": "IMG-001", "path": "/data/uploads/a.jpg"}`. An optional
`"confidence"` (0 to 1) overrides the default threshold.

Response (see the full example in `sample_data/mock_responses/vision_response.json`):
```json
{
  "model": "YOLOv8-damage-detection-v1",
  "image_results": [
    {
      "image_id": "IMG-001",
      "damages": [
        {
          "damage_id": "DMG-001",
          "type": "tire",
          "confidence": 0.9618,
          "bbox": { "x1": 29, "y1": 220, "x2": 362, "y2": 554 },
          "severity": "high",
          "affected_part": null,
          "evidence": ["IMG-001"]
        }
      ]
    }
  ],
  "odometer": { "detected": false, "value_km": null, "confidence": null, "image_id": null, "evidence": [] }
}
```

- `bbox` is in pixels of the original image (top-left `x1,y1`, bottom-right `x2,y2`). Images are rotated
  according to their EXIF orientation first, so boxes line up with what a browser displays.
- `severity` (`low`, `medium`, `high`) is a rule based on how much of the image the box covers. It is not
  a trained model.
- `affected_part` is always `null` for now (no part detector).
- `damage_id` values are unique within one response. `evidence` holds the source `image_id`.
- Errors: `404` if an image cannot be found, `400` for a file that is not a valid jpg/png, `422` for a
  malformed request.

### POST /analyze/upload
Same response for images sent as multipart form data (field `files`, jpg/jpeg/png, max 10 MB each). If a
file is named like `IMG-1A2B3C4D.jpg` that stem is used as the `image_id`, otherwise one is generated.

### GET /annotated/{image_id}
JPEG of that image with boxes, class and confidence drawn on. Available for the most recent 50 analysed
images.

### POST /vision/analyze
Single-image form: `{"image_path": "...", "image_id": "IMG-001"}` returns
`{"image_id", "model", "damages"}`.

## Mapping to the Vehicle JSON

The response uses the field names of [schemas/vehicle_schema_v1.json](../../schemas/vehicle_schema_v1.json)
without any additions:

| Response | Vehicle JSON |
|---|---|
| `model` | `vision.damage_detection.model` |
| `image_results` | `vision.damage_detection.image_results` |
| `odometer` | `vision.odometer` |

Set `pipeline_status.vision_completed` to `true` once this is stored.

### What the backend needs to do

1. `POST /inspection/{id}/images` currently stores only metadata and discards the file contents. Images
   need to be saved to disk, named by their ID (for example `uploads/IMG-1A2B3C4D.jpg`).
2. `VisionServiceClient.analyze_images` in `backend/app/services/vision_client.py` needs to call
   `POST {VISION_SERVICE_URL}/analyze` with those paths (or set `VISION_IMAGE_DIR` on the vision service
   and send the bare IDs).
3. To show the boxes, the frontend can draw them from `bbox` on the image it already has, or display
   `GET {VISION_SERVICE_URL}/annotated/{image_id}`.

## Dataset

Datasets are not committed. See [data/README.md](data/README.md) for download steps (CarDD, or a Roboflow
Universe export) and conversion.

```bash
# Inspect how a downloaded dataset's classes map to the six CarVal classes
python data/prepare_dataset.py inspect --source cardd --src <path to CarDD_COCO>

# Convert to YOLO format (keeps CarDD's train/val/test splits)
python data/prepare_dataset.py build --source cardd --src <path to CarDD_COCO> --out <output dir>
```

Class mapping lives in [data/class_map.yaml](data/class_map.yaml). The CarDD training set is imbalanced
(scratch 2560 boxes, tire 225), which training handles with repeat-factor sampling.

## Training

```bash
# Baseline: yolov8n, default settings, no class balancing
python training/train.py --preset baseline --data <dataset>/data.yaml

# Fine-tune: longer schedule, cosine LR, repeat-factor sampling for rare classes
python training/train.py --preset finetune --data <dataset>/data.yaml

# yolov8s on a GPU (as used for the reported results)
python training/train.py --preset finetune --model yolov8s.pt --data <dataset>/data.yaml --device 0 --batch 32
```

The fine-tune preset copies its best checkpoint to `weights/best.pt`, which the API loads. Runs are written
to `runs/` (gitignored).

On a MacBook with Apple silicon the default device is `mps`; yolov8n takes about 8 minutes per epoch.
[training/CarVal_Vision_Colab.ipynb](training/CarVal_Vision_Colab.ipynb) runs the same pipeline on a Colab
GPU, reading the dataset and code from Google Drive.

## Evaluation

```bash
python evaluation/evaluate.py --data <dataset>/data.yaml \
    --weights weights/baseline_best.pt:baseline \
    --weights weights/finetune_best.pt:finetune
```

Writes `reports/metrics.json` and `reports/metrics.md` with precision, recall, mAP@50 and mAP@50-95,
overall and per class, on the test split. Precision and recall are taken at each model's best-F1
confidence threshold.

## Tests

```bash
python test_vision.py       # standalone, prints ✓/✗
pytest test_vision.py       # also works with pytest
```

No running server or trained weights are required. The test against a real image is skipped when the
weights or dataset are missing.

To regenerate the sample JSON from the trained model:

```bash
python generate_sample.py <image1.jpg> <image2.jpg>
```

## Files

```
services/vision/
├── main.py                 FastAPI app (port 8001)
├── detector.py             model loading, inference, severity rule, box drawing
├── config.py               settings from environment variables
├── damage_classes.py       class names and ids (single source of truth)
├── demo.html               upload page served at /demo
├── data/                   dataset conversion and class mapping
├── training/               train.py and the Colab notebook
├── evaluation/             evaluate.py
├── reports/                metrics.json / metrics.md
├── weights/                trained weights (gitignored)
├── test_vision.py
└── generate_sample.py
```

## Later extensions (Review 3+)
- Odometer detection and reading
- Severity classification refinement
- Part detection to fill `affected_part`
- Multi-angle analysis
- Damage progression tracking
