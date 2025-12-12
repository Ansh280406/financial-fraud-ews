from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import joblib
from datetime import datetime
from pydantic import BaseModel

# Absolute Imports
from models import LoginAttempt
from fusion_engine import FusionEngine
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck

# --- DATA MODELS ---
class OTPVerification(BaseModel):
    user_id: str
    otp_code: str

# --- DATABASE ---
USER_DB = {}
ACTIVITY_LOGS = []

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

# --- ENDPOINTS ---

@app.get("/", include_in_schema=False)
async def serve_login():
    path = os.path.join(PROJECT_DIR, 'bank_login.html')
    if not os.path.exists(path):
        path = os.path.join(PROJECT_DIR, 'index.html')
    if os.path.exists(path):
        with open(path, 'r') as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>Login page not found</h1>", status_code=404)

@app.get("/admin", include_in_schema=False)
async def serve_admin():
    path = os.path.join(PROJECT_DIR, 'admin_dashboard.html')
    if os.path.exists(path):
        with open(path, 'r') as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>Admin page not found</h1>", status_code=404)

@app.get("/admin/data")
async def get_admin_data():
    return {"logs": ACTIVITY_LOGS}

@app.post("/verify-otp")
async def verify_otp(data: OTPVerification):
    uid = data.user_id
    if uid not in USER_DB:
        raise HTTPException(status_code=404, detail="User not found")
    
    CORRECT_OTP = "1234"
    
    # 1. Check if ALREADY blocked
    if USER_DB[uid]["failed_otps"] >= 3:
         return {"status": "block", "message": "🚫 BLOCK: Max OTP attempts reached (Fraud Error)"}

    # 2. Verify Code
    if data.otp_code == CORRECT_OTP:
        USER_DB[uid]["failed_otps"] = 0 # Reset
        
        ACTIVITY_LOGS.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "user": uid, "location": "Unknown", "distance": "-", "risk": "0%",
            "action": "✅ OTP Verified", "status": "safe"
        })
        return {"status": "success", "message": "Login Successful"}
    else:
        USER_DB[uid]["failed_otps"] += 1
        count = USER_DB[uid]["failed_otps"]
        
        ACTIVITY_LOGS.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "user": uid, "location": "Unknown", "distance": "-", "risk": "High",
            "action": f"❌ Failed OTP Attempt ({count}/3)", "status": "warning"
        })

        if count >= 3:
            return {"status": "block", "message": "🚫 BLOCK: Max OTP attempts reached (Fraud Error)"}
        
        return {"status": "fail", "message": f"Incorrect OTP. Attempt {count}/3"}


@app.post("/predict")
async def predict_fraud(data: LoginAttempt):
    uid = data.user_id
    current_time = datetime.now()
    
    # NEW USER
    if uid not in USER_DB:
        USER_DB[uid] = {
            "last_lat": data.latitude, "last_lon": data.longitude,
            "last_login": current_time, "failed_otps": 0
        }
        ACTIVITY_LOGS.insert(0, {
            "time": current_time.strftime("%H:%M:%S"),
            "user": uid, "location": f"{data.latitude:.2f}, {data.longitude:.2f}",
            "distance": "0.0 km", "risk": "0%", "action": "✅ New Profile Created", "status": "safe"
        })
        # Even new users must do OTP now
        return {"final_risk_score": 0.0, "security_action": "✅ NEW DEVICE: OTP Required", "detector_scores": {}}

    # EXISTING USER
    history = USER_DB[uid]
    time_delta = current_time - history["last_login"]
    hours_diff = time_delta.total_seconds() / 3600.0

    score_behavior = behavior_engine.get_risk(data.typing_delay)
    score_geo = geo_engine.get_risk(data.latitude, data.longitude, history["last_lat"], history["last_lon"], hours_diff)
    score_otp = otp_engine.get_risk(history["failed_otps"])
    
    dist_km = geo_engine.calculate_haversine(history["last_lat"], history["last_lon"], data.latitude, data.longitude)

    scores = {"A1_Behavior_DNA": score_behavior, "A2_Geo_Velocity": score_geo, "A3_OTP_Misuse": score_otp}
    result = fusion_engine.run_assessment(scores)
    
    # Log Decision
    action_type = "safe"
    if "BLOCK" in result['action']: action_type = "danger"
    elif "FLAG" in result['action'] or "Email" in result['action']: action_type = "warning"

    ACTIVITY_LOGS.insert(0, {
        "time": current_time.strftime("%H:%M:%S"),
        "user": uid, "location": f"{data.latitude:.2f}, {data.longitude:.2f}",
        "distance": f"{dist_km:.1f} km", "risk": f"{result['final_risk_score']*100:.0f}%",
        "action": result['action'], "status": action_type
    })

    if "BLOCK" not in result['action']:
        USER_DB[uid]["last_lat"] = data.latitude
        USER_DB[uid]["last_lon"] = data.longitude
        USER_DB[uid]["last_login"] = current_time

    return {
        "final_risk_score": result['final_risk_score'],
        "security_action": result['action'],
        "detector_scores": scores
    }