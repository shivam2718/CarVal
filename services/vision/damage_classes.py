"""
CarVal damage classes - single source of truth for class order.
Member 1 - Vision/Damage Detection

The index of each class is its YOLO class id. Do not reorder: trained
weights depend on it. Add new classes only at the end.
"""

CLASSES = ["dent", "scratch", "crack", "glass", "lamp", "tire"]

CLASS_TO_ID = {name: i for i, name in enumerate(CLASSES)}
