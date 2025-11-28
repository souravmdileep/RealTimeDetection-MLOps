from utils.model_loader import ModelManager
from fastapi import FastAPI, File, UploadFile
import numpy as np
import cv2
import time
import logging
from pathlib import Path

app = FastAPI()
model_manager = ModelManager()

# Logging setup 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

# Read current model version
def get_current_model():
    config_file = Path("config/current_model.txt")
    if config_file.exists():
        return config_file.read_text().strip()
    return "v1"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/switch_model")
def switch_model(version: str):
    if version not in ["v1", "v2"]:
        return {"error": "Invalid model version"}
    
    Path("config/current_model.txt").write_text(version)

    # Load selected model
    model_manager.load_model(version)
    
    logger.info(f"Switched to model: {version}")
    return {"message": f"Model switched to {version}"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    start = time.time()

    # Read image
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    current_version = get_current_model()

    # Load proper model
    model_manager.load_model(current_version)

    # Run detection
    detections = model_manager.predict(current_version, img)

    latency = (time.time() - start) * 1000

    logger.info(f"Model={current_version} | DetCount={len(detections)} | Latency={latency:.2f}ms")

    return {
        "model": current_version,
        "detections": detections,
        "latency_ms": latency
    }
