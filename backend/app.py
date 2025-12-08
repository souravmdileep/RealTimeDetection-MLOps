from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from backend.utils.model_loader import ModelManager
import numpy as np
import cv2
import time
import logging
from pathlib import Path
import requests 

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config" / "current_model.txt"

model_manager = ModelManager()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

# --- STATE FOR MOVEMENT TRACKING ---
last_person_box = None
MOVEMENT_THRESHOLD = 50 # Pixels of difference to trigger alert

# --- SECURITY CONFIG ---
BANNED_ITEMS = ["cell phone", "laptop", "mouse", "keyboard", "remote", "tv"]
ALERT_SERVICE_URL = "http://alert-service:8001/log_violation"

def get_current_model():
    if CONFIG_PATH.exists():
        return CONFIG_PATH.read_text().strip()
    return "v2"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/switch_model")
def switch_model(version: str):
    if version not in ["v1", "v2"]:
        return {"error": "Invalid model version"}
    CONFIG_PATH.write_text(version)
    model_manager.load_model(version)
    # Reset movement tracking on switch
    global last_person_box
    last_person_box = None
    return {"message": f"Model switched to {version}"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    global last_person_box
    start = time.time()

    # 1. Process Image
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    current_version = get_current_model()
    model_manager.load_model(current_version)
    detections = model_manager.predict(current_version, img)

    latency = (time.time() - start) * 1000

    # --- 2. LOGIC FOR V1 (MOVEMENT DETECTION) ---
    if current_version == "v1":
        person_found = False
        for det in detections:
            if det["class"] == "person":
                person_found = True
                box = det["box"] # [x, y, w, h]
                
                # Calculate center point
                center_x = box[0] + (box[2] / 2)
                center_y = box[1] + (box[3] / 2)

                if last_person_box:
                    # Calculate movement distance
                    prev_x, prev_y = last_person_box
                    dist = np.sqrt((center_x - prev_x)**2 + (center_y - prev_y)**2)
                    
                    if dist > MOVEMENT_THRESHOLD:
                        # TRIGGER YELLOW ALERT
                        try:
                            payload = {"object_class": "SUSPICIOUS MOVEMENT", "confidence": dist}
                            requests.post(ALERT_SERVICE_URL, json=payload, timeout=0.1)
                        except: pass
                
                # Update history
                last_person_box = (center_x, center_y)
                break
        
        # If person is missing (Left the frame)
        if not person_found and last_person_box:
             try:
                payload = {"object_class": "STUDENT LEFT FRAME", "confidence": 1.0}
                requests.post(ALERT_SERVICE_URL, json=payload, timeout=0.1)
             except: pass


    # --- 3. LOGIC FOR V2 (CONTRABAND DETECTION) ---
    elif current_version == "v2":
        for det in detections:
            if det["class"] in BANNED_ITEMS and det["score"] > 0.5:
                try:
                    payload = {"object_class": det["class"], "confidence": det["score"]}
                    requests.post(ALERT_SERVICE_URL, json=payload, timeout=0.1)
                except: pass

    return {
        "model": current_version,
        "detections": detections,
        "latency_ms": latency
    }
