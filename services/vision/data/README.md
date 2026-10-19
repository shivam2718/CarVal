# Vision dataset

Datasets are **not committed**. Everything lives under `services/vision/datasets/` (gitignored):

```
datasets/
├── raw/
│   ├── roboflow/        # unzipped Roboflow export
│   └── cardd/           # unzipped CarDD release
└── carval_damage/       # built by prepare_dataset.py: images/, labels/, data.yaml, dataset_summary.json
```

All commands below are run from `services/vision/` with the venv active (`source .venv/bin/activate`).

## Option A: Roboflow Universe (available now)

1. Create a free account at https://universe.roboflow.com.
2. Search for **"car damage"**. Pick a dataset whose class list (shown on its page) covers as many of
   dent / scratch / crack / glass / lamp / tire as possible, and that is licensed CC BY 4.0.
   Candidates: `ratchakrit/cardd-efev9-qkikx` (a CarDD upload) and `ratchakrit/car-damage-merged-qefuo`.
   Check the class list on the page yourself before downloading.
3. Open the dataset → **Dataset** tab → pick a version → **Download Dataset**.
4. Format **YOLOv8** → **Show download code** → **Terminal** tab. Copy the `curl` URL; it looks like
   `https://universe.roboflow.com/ds/XXXXXXXX?key=YYYYYYYY`. Treat the `key` like a password and don't commit it.
5. Download and unzip:
   ```bash
   mkdir -p datasets/raw/roboflow
   curl -L "<URL from step 4>" -o datasets/raw/roboflow.zip
   unzip -q datasets/raw/roboflow.zip -d datasets/raw/roboflow && rm datasets/raw/roboflow.zip
   ```
6. Check how its classes map:
   ```bash
   python data/prepare_dataset.py inspect --source roboflow --src datasets/raw/roboflow
   ```
   For each class listed as `(unmapped)`, add a line to `data/class_map.yaml` that maps it to one of the
   six CarVal classes, or to `null` to drop it. Run `inspect` again until nothing is unmapped.
7. Build:
   ```bash
   python data/prepare_dataset.py build --source roboflow --src datasets/raw/roboflow
   ```
   If the export already has train/valid/test, those splits are kept. Otherwise the images are re-split
   70/20/10 (seed 42). Use `--resplit` to force a re-split and `--split 0.8 0.1 0.1` to change the ratios.

## Option B: CarDD (request access)

CarDD (Wang et al., 2023, *IEEE T-ITS*): about 4,000 high-resolution images and over 9,000 instances.
Its six classes are dent, scratch, crack, glass shatter, lamp broken and tire flat, which map one-to-one
onto ours.

1. Go to https://cardd-ustc.github.io and download the **Licensing Form** (`CarDD_license.pdf`).
2. Fill it in (name, institution, academic/non-commercial use) and sign it. If the form needs a
   supervisor or faculty signature, get one.
3. Email it to the CarDD authors. The site gives no address, so use the corresponding-author email from
   the paper, https://arxiv.org/abs/2211.00945. They reply with a download link.
4. Download the COCO version and unzip it into `datasets/raw/cardd/`. The script finds
   `annotations/instances_*.json` and the image folders by itself, so the exact layout doesn't matter.
5. Inspect and build:
   ```bash
   python data/prepare_dataset.py inspect --source cardd --src datasets/raw/cardd
   python data/prepare_dataset.py build   --source cardd --src datasets/raw/cardd --overwrite
   ```
   CarDD's official train/val/test splits are kept.

## Output

- `datasets/carval_damage/data.yaml`: the file passed to training and evaluation (classes 0-5 in the order
  given in `damage_classes.py`).
- `datasets/carval_damage/dataset_summary.json`: images and instances per split and class, plus dropped and
  unmapped source classes. Use it for the dataset slide in the review.

Useful flags: `--symlink` (link images instead of copying them, to save disk space), `--drop-empty` (skip
images with no damage boxes; they are kept as background images by default), `--out <dir>`.
