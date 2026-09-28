# Vision Service

**Owner**: Member 1 - Vision/Damage Detection

## Overview
Car image analysis module for damage detection using YOLOv8.

## Review 2 Objectives
- [ ] Prepare damage-detection dataset
- [ ] Set up YOLOv8 baseline
- [ ] Fine-tune for six damage classes: dent, scratch, crack, glass, lamp, tire
- [ ] Generate damage detection outputs (class, confidence, bounding box)
- [ ] Evaluate using precision, recall, mAP@50
- [ ] Create vision inference API: `POST /vision/analyze`
- [ ] Provide sample JSON output for frontend integration

## Expected Review 2 Demo
Upload a car image → detected damage is displayed with bounding boxes, class, and confidence.

## API Contract

### POST /vision/analyze
Analyze a car image for damage.

**Request:**
```json
{
  "image_path": "path/to/image.jpg"
}
```

**Response:**
```json
{
  "image_id": "IMG-001",
  "model": "YOLOv8-damage-detection-v1",
  "damages": [
    {
      "damage_id": "DMG-001",
      "type": "dent",
      "confidence": 0.95,
      "bbox": {
        "x1": 100,
        "y1": 100,
        "x2": 200,
        "y2": 200
      },
      "severity": "medium",
      "affected_part": "door"
    }
  ]
}
```

## Damage Classes
1. **dent** - Surface indentation
2. **scratch** - Surface damage/scratches
3. **crack** - Broken glass/structural cracks
4. **glass** - Damaged windows or glass
5. **lamp** - Damaged lights/lamps
6. **tire** - Damaged tires/wheels

## Later Extensions (Review 3+)
- Odometer detection and reading
- Severity classification refinement
- Multi-angle analysis
- Damage progression tracking

## Integration Notes
- FastAPI backend will call this service at `VISION_SERVICE_URL`
- Results are stored in the common Vehicle JSON structure
- Maintain traceability: damage should reference source image ID
