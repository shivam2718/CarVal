# CarVal Vision: damage detection evaluation

- **Split:** `test` (374 images, 785 damage boxes)
- **Dataset:** /Users/shipsy/Documents/BTP/datasets/CarDD_yolo/data.yaml
- **Image size:** 640  |  **Device:** mps  |  **Date:** 2026-10-11
- **Metrics:** Precision and recall are at each model's best-F1 confidence threshold. mAP@50 is the mean average precision at IoU 0.5; mAP@50-95 averages IoU 0.5 to 0.95.

## Overall

| Model | Params | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|---|---|
| baseline | 3.1M | 0.762 | 0.642 | **0.710** | 0.549 |
| finetune | 11.1M | 0.747 | 0.679 | **0.718** | 0.569 |

## Per class

| Class | Boxes | baseline P | baseline R | baseline mAP@50 | finetune P | finetune R | finetune mAP@50 |
|---|---|---|---|---|---|---|---|
| dent | 236 | 0.717 | 0.525 | 0.600 | 0.682 | 0.534 | 0.592 |
| scratch | 307 | 0.629 | 0.528 | 0.592 | 0.614 | 0.564 | 0.556 |
| crack | 70 | 0.551 | 0.271 | 0.340 | 0.534 | 0.429 | 0.436 |
| glass | 71 | 0.908 | 0.958 | 0.980 | 0.903 | 0.972 | 0.986 |
| lamp | 69 | 0.804 | 0.696 | 0.835 | 0.829 | 0.702 | 0.837 |
| tire | 32 | 0.963 | 0.875 | 0.912 | 0.919 | 0.875 | 0.901 |

## Speed

| Model | Preprocess | Inference | Postprocess |
|---|---|---|---|
| baseline | 0.17 ms | 2.77 ms | 8.17 ms |
| finetune | 0.17 ms | 5.05 ms | 17.43 ms |
