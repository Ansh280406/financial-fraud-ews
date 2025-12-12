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

# --- STATE MANAGEMENT (UPDATED FOR VELLORE, INDIA) ---
# We align the history with your current location so you don't get blocked by Geo-Check
# unless you specifically use the 'demo_travel' account.

VELLORE_LAT = 12.9165
VELLORE_LON = 79.1325
NY_LAT = 40.7128
NY_LON = -74.0060

USER_DB = {
    # 1. Normal User (History is Vellore -> You are in Vellore -> SAFE)
    "demo_user": {
        "last_lat": VELLORE_LAT, "last_lon": VELLORE_LON, 
        "last_login": datetime.now(), "failed_otps": 0
    },
    
    # 2. Impossible Travel (History is NY -> You are in Vellore -> BLOCK)
    "demo_travel": {
        "last_lat": NY_LAT, "last_lon": NY_LON, 
        "last_login": datetime.now(), "failed_otps": 0
    },
    
    # 3. OTP Attacker (History is Vellore -> Location Safe -> BLOCK due to OTPs)
    "demo_otp": {
        "last_lat": VELLORE_LAT, "last_lon": VELLORE_LON, 
        "last_login": datetime.now(), "failed_otps": 5 
    },
    
    # 4. Impersonator (History is Vellore -> Location Safe -> MAIL due to Typing)
    "demo_impersonation": {
        "last_lat": VELLORE_LAT, "last_lon": VELLORE_LON, 
        "last_login": datetime.now(), "failed_otps": 0
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
    path = os.path.join(PROJECT_DIR, 'bank_login.html') # Serving your new login page
    if os.path.exists(path):
        with open(path, 'r') as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>Login page not found</h1>", status_code=404)

@app.post("/predict")
async def predict_fraud(data: LoginAttempt):
    uid = data.user_id
    
    # 1. Retrieve User History (Default to Vellore if unknown, so new users don't get blocked)
    history = USER_DB.get(uid, {
        "last_lat": VELLORE_LAT, "last_lon": VELLORE_LON, 
        "last_login": datetime.now(), "failed_otps": 0
    })
    
    # 2. Assume 2 hours have passed for all simulations
    hours_diff = 2.0 

    # 3. RUN REAL LOGIC
    # Behavior: AI Model checks typing delay
    score_behavior = behavior_engine.get_risk(data.typing_delay)
    
    # Geo: Haversine Formula calculates speed
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