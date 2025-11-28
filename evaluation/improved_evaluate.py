import os
import time
import json
import requests

TEST_DIR = "test_images"
API_URL = "http://localhost:8000/predict"

def evaluate_improved():
    results = {
        "model_version": "v2",
        "total_images": 0,
        "total_detections": 0,
        "avg_confidence": 0,
        "avg_latency_ms": 0,
        "class_counts": {}
    }

    confidences = []
    latencies = []
    class_counts = {}

    for filename in os.listdir(TEST_DIR):
        if not filename.lower().endswith((".jpg", ".png", ".jpeg")):
            continue

        filepath = os.path.join(TEST_DIR, filename)
        files = {"file": open(filepath, "rb")}

        start = time.time()
        response = requests.post(API_URL, files=files).json()
        end = time.time()

        detections = response["detections"]
        latency = response["latency_ms"]

        # Aggregate metrics
        results["total_images"] += 1
        results["total_detections"] += len(detections)
        latencies.append(latency)

        for det in detections:
            conf = det["score"]
            cls = det["class"]

            confidences.append(conf)
            class_counts[cls] = class_counts.get(cls, 0) + 1

    # Compute averages
    results["avg_confidence"] = sum(confidences) / len(confidences) if confidences else 0
    results["avg_latency_ms"] = sum(latencies) / len(latencies) if latencies else 0
    results["class_counts"] = class_counts

    # Save to file
    with open("improved_metrics.json", "w") as f:
        json.dump(results, f, indent=4)

    print("Improved evaluation complete. Metrics saved to improved_metrics.json.")

if __name__ == "__main__":
    evaluate_improved()
