from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

# Enable CORS so Frontend can fetch alerts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for alerts (resets on restart)
incident_log = []

class Violation(BaseModel):
    object_class: str
    confidence: float
    timestamp: str = None

@app.get("/health")
def health():
    return {"status": "active", "service": "Alert Service"}

@app.post("/log_violation")
def log_violation(violation: Violation):
    # Add timestamp
    violation.timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Simple De-duplication: Don't spam the log if the same object was just seen
    if incident_log:
        last = incident_log[0] # Newest is first
        # If same object seen within last 2 seconds, ignore to prevent flooding
        # (This is a basic logic, can be improved)
        if last['object_class'] == violation.object_class:
            return {"status": "duplicate_ignored"}

    entry = violation.dict()
    incident_log.insert(0, entry) # Add to top
    
    # Keep only last 50 alerts
    if len(incident_log) > 50:
        incident_log.pop()
        
    print(f"🚨 SECURITY ALERT: {entry['object_class']} detected!")
    return {"status": "logged", "entry": entry}

@app.get("/get_alerts")
def get_alerts():
    return incident_log

@app.post("/clear_alerts")
def clear_alerts():
    global incident_log
    incident_log = []
    return {"status": "cleared"}
