import os
import json
import requests
import time
from collections import Counter

# Configuration
TEST_DIR = "evaluation/test_images"
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
            r = requests.post(PREDICT_URL, files={"file": (image_path, f, "image/jpeg")})
            
            # --- DEBUGGING CHANGE START ---
            if r.status_code != 200:
                print(f"FAILED: {image_path} | Status: {r.status_code} | Reason: {r.text}")
                return None
            # --- DEBUGGING CHANGE END ---
            
            return r.json()
    except Exception as e:
        print(f"Connection failed for {image_path}: {e}")
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
        print(f"No images found in {TEST_DIR}.")
        return

    print(f"Checking {len(images)} sample images against baseline...")

    for img in images:
        path = os.path.join(TEST_DIR, img)
        result = run_inference(path)
        
        if not result: continue

        detections = result.get("detections", [])
        
        # --- DEBUGGING CHANGE: Print if empty ---
        if not detections:
            print(f"WARNING: Image {img} returned 0 detections.")
        # ----------------------------------------

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
    else:
        print("\nSystem Healthy. No drift detected.")

if __name__ == "__main__":
    detect_drift()