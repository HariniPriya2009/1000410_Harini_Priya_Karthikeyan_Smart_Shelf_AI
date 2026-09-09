"""
Step 3: Model Development.

Trains a YOLOv8 object detector on the prepared shelf dataset and reports
precision/recall. YOLOv8n (nano) is the recommended starting point — fast
to train on CPU/Colab, good enough to prove the pipeline works before you
try a bigger variant.

Usage:
    python src/train.py --data data.yaml --epochs 30 --batch 16 --model yolov8n.pt
"""

import argparse
from ultralytics import YOLO


def train(data_yaml: str, epochs: int, batch: int, model_name: str, img_size: int):
    model = YOLO(model_name)  # downloads pretrained weights on first run

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=img_size,
        project="runs",
        name="stocksense",
        patience=10,       # early stopping if no improvement
        exist_ok=True,
    )

    # Evaluate on the val/test split — precision, recall, mAP
    metrics = model.val()
    print("\n--- Evaluation ---")
    print(f"Precision: {metrics.box.mp:.3f}")
    print(f"Recall:    {metrics.box.mr:.3f}")
    print(f"mAP50:     {metrics.box.map50:.3f}")
    print(f"mAP50-95:  {metrics.box.map:.3f}")

    # Best weights are auto-saved; copy to a stable path for the app to load
    best_path = model.trainer.best
    print(f"\nBest weights saved at: {best_path}")
    print("Copy this file to models/best.pt for the Streamlit app to use it.")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLO model for StockSense Pro")
    parser.add_argument("--data", default="data.yaml")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--model", default="yolov8n.pt",
                         help="yolov8n.pt (fastest) / yolov8s.pt / yolov8m.pt (more accurate, slower)")
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    train(args.data, args.epochs, args.batch, args.model, args.imgsz)
