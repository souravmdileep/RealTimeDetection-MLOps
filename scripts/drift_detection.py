import os
import json
import requests
import time
from collections import Counter

# Configuration
TEST_DIR = "evaluation/test_images"
# TEST_DIR = "evaluation/bad_data"
# Note: In Docker, this might change, but for now use localhost
PREDICT_URL = "http://localhost:8000/predict" 
REFERENCE_FILE = "scripts/baseline_reference.json"

def load_baseline():
    if not os.path.exists(REFERENCE_FILE):
        print(f"Error: Reference file {REFERENCE_FILE} not found.")
        return None
    with open(REFERENCE_FILE) as f:
        return json.load(f)

def run_inference(image_path):
    try:
        with open(image_path, "rb") as f:
            start = time.time()
            r = requests.post(PREDICT_URL, files={"file": (image_path, f, "image/jpeg")})
            if r.status_code != 200:
                return None
            return r.json()
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def detect_drift():
    print("--- Starting Drift Detection Check ---")
    baseline = load_baseline()
    if not baseline: return

    all_conf = []
    all_classes = []
    all_det_counts = []

    # Get images (limit to 20 for speed during check)
    images = [f for f in os.listdir(TEST_DIR) if f.lower().endswith((".jpg", ".png", ".jpeg"))][:20]
    
    if not images:
        print("No images found for drift check.")
        return

    print(f"Checking {len(images)} sample images against baseline...")

    for img in images:
        path = os.path.join(TEST_DIR, img)
        result = run_inference(path)
        
        if not result: continue

        detections = result.get("detections", [])
        all_det_counts.append(len(detections))

        for d in detections:
            all_conf.append(d["score"])
            all_classes.append(d["class"])

    if not all_conf:
        print("No detections made. Potential severe drift or broken model.")
        return

    # Compute Current Metrics
    avg_conf = sum(all_conf) / len(all_conf)
    avg_det = sum(all_det_counts) / len(all_det_counts)

    class_counts = Counter(all_classes)
    total_detected = sum(class_counts.values())
    class_dist = {cls: count / total_detected for cls, count in class_counts.items()}

    print(f"Current Avg Confidence: {avg_conf:.2f} (Baseline: {baseline['avg_confidence']})")
    print(f"Current Avg Detections: {avg_det:.2f} (Baseline: {baseline['avg_detections']})")

    # --- Check Rules ---
    drift_reasons = []

    # 1. Confidence Drop
    if avg_conf < (baseline["avg_confidence"] - baseline["min_confidence_drop"]):
        drift_reasons.append(f"Confidence drop detected ({avg_conf:.2f} < {baseline['avg_confidence']})")

    # 2. Unexpected Classes
    unexpected = [cls for cls in class_counts if cls not in baseline["expected_classes"]]
    if unexpected:
        drift_reasons.append(f"Unexpected classes found: {unexpected}")

    # 3. Detection Count Shift
    if abs(avg_det - baseline["avg_detections"]) > 1.5:
        drift_reasons.append(f"Detection count shifted significantly ({avg_det:.2f} vs {baseline['avg_detections']})")

    # Final Decision
    if drift_reasons:
        print("\n DRIFT DETECTED! ")
        for reason in drift_reasons:
            print(f" - {reason}")
        # In a real pipeline, we would return exit(1) to fail the build
    else:
        print("\nSystem Healthy. No drift detected.")

if __name__ == "__main__":
    detect_drift()