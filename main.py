from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import joblib
from datetime import datetime

# Absolute Imports
from models import LoginAttempt
from fusion_engine import FusionEngine
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck

# --- STATE MANAGEMENT ---
# We seed the database with "History" so calculations work.
# All demo users "live" in New York.
USER_DB = {
    "demo_user": {
        "last_lat": 40.7128, "last_lon": -74.0060, # NY
        "last_login": datetime.now(), 
        "failed_otps": 0
    },
    "demo_travel": {
        "last_lat": 40.7128, "last_lon": -74.0060, # NY
        "last_login": datetime.now(), 
        "failed_otps": 0
    },
    "demo_otp": {
        "last_lat": 40.7128, "last_lon": -74.0060, # NY
        "last_login": datetime.now(), 
        "failed_otps": 5 # HISTORY OF FAILURES
    },
    "demo_impersonation": {
        "last_lat": 40.7128, "last_lon": -74.0060, # NY
        "last_login": datetime.now(), 
        "failed_otps": 0
    }
}

# --- INITIALIZE ---
geo_engine = GeoVelocityCheck()
behavior_engine = BehaviorCheck()
otp_engine = OTPCheck()
fusion_engine = FusionEngine()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", include_in_schema=False)
async def serve_index():
    path = os.path.join(PROJECT_DIR, 'index.html')
    if os.path.exists(path):
        with open(path, 'r') as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>Frontend not found</h1>", status_code=404)

@app.post("/predict")
async def predict_fraud(data: LoginAttempt):
    uid = data.user_id
    
    # 1. Get History (default to NY if unknown)
    history = USER_DB.get(uid, {
        "last_lat": 40.7128, "last_lon": -74.0060, 
        "last_login": datetime.now(), "failed_otps": 0
    })
    
    # 2. Simulate time passage (2 hours) for calculation validity
    hours_diff = 2.0 

    # 3. RUN REAL LOGIC
    # Behavior: Checks typing delay against AI Model
    score_behavior = behavior_engine.get_risk(data.typing_delay)
    
    # Geo: Calculates Haversine distance/speed
    score_geo = geo_engine.get_risk(data.latitude, data.longitude, 
                                    history["last_lat"], history["last_lon"], hours_diff)
    
    # OTP: Checks failed attempts history
    score_otp = otp_engine.get_risk(history["failed_otps"])

    scores = {
        "A1_Behavior_DNA": score_behavior,
        "A2_Geo_Velocity": score_geo,
        "A3_OTP_Misuse": score_otp
    }
    
    # 4. Fusion Decision
    result = fusion_engine.run_assessment(scores)
    
    return {
        "final_risk_score": result['final_risk_score'],
        "security_action": result['action'],
        "detector_scores": scores
    }