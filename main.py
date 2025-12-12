from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import joblib
from datetime import datetime

from models import LoginAttempt
from fusion_engine import FusionEngine
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck

# --- STATE MANAGEMENT (In-Memory DB) ---
# In a real app, this would be Redis/PostgreSQL.
# We pre-populate 'demo_user' at New York to test Impossible Travel.
USER_DB = {
    "demo_user": {
        "last_lat": 40.7128, 
        "last_lon": -74.0060, # New York
        "last_login": datetime.now(),
        "failed_otps": 0
    }
}

# --- INITIALIZE ENGINES ---
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
    
    # 1. Retrieve User History
    history = USER_DB.get(uid, {})
    last_lat = history.get("last_lat")
    last_lon = history.get("last_lon")
    last_time = history.get("last_login")
    
    # 2. Calculate Time Diff
    if last_time:
        hours_diff = (datetime.now() - last_time).total_seconds() / 3600.0
    else:
        hours_diff = 1.0 # First login defaults to 1 hour
        
    # 3. RUN REAL DETECTORS
    # Behavior: Checks typing delay against AI Model
    score_behavior = behavior_engine.get_risk(data.typing_delay)
    
    # Geo: Calculates Haversine speed
    score_geo = geo_engine.get_risk(data.latitude, data.longitude, last_lat, last_lon, hours_diff)
    
    # OTP: Checks failed attempts (mocked to 0 for login endpoint)
    score_otp = otp_engine.get_risk(history.get("failed_otps", 0))

    # 4. RUN FUSION
    scores = {
        "A1_Behavior_DNA": score_behavior,
        "A2_Geo_Velocity": score_geo,
        "A3_OTP_Misuse": score_otp
    }
    result = fusion_engine.run_assessment(scores)
    
    # 5. UPDATE STATE (If allowed)
    if "BLOCK" not in result['action']:
        USER_DB[uid] = {
            "last_lat": data.latitude,
            "last_lon": data.longitude,
            "last_login": datetime.now(),
            "failed_otps": 0
        }
    
    return {
        "final_risk_score": result['final_risk_score'],
        "security_action": result['action'],
        "detector_scores": scores
    }