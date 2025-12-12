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

# --- DATABASE & LOGS ---
# USER_DB: Stores the *Current State* (for logic)
USER_DB = {}

# ACTIVITY_LOGS: Stores the *History* (for Admin Dashboard)
ACTIVITY_LOGS = []

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

# --- ENDPOINTS ---

@app.get("/", include_in_schema=False)
async def serve_login():
    path = os.path.join(PROJECT_DIR, 'bank_login.html')
    if os.path.exists(path):
        with open(path, 'r') as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>Login page not found</h1>", status_code=404)

@app.get("/admin", include_in_schema=False)
async def serve_admin():
    # New Admin Page
    path = os.path.join(PROJECT_DIR, 'admin_dashboard.html')
    if os.path.exists(path):
        with open(path, 'r') as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>Admin page not found</h1>", status_code=404)

@app.get("/admin/data")
async def get_admin_data():
    # API for the Dashboard to fetch logs
    return {"logs": ACTIVITY_LOGS}

@app.post("/predict")
async def predict_fraud(data: LoginAttempt):
    uid = data.user_id
    current_time = datetime.now()
    
    # 1. NEW USER REGISTRATION
    if uid not in USER_DB:
        USER_DB[uid] = {
            "last_lat": data.latitude, "last_lon": data.longitude,
            "last_login": current_time, "failed_otps": 0
        }
        # Log the Event
        log_entry = {
            "time": current_time.strftime("%H:%M:%S"),
            "user": uid,
            "location": f"{data.latitude:.2f}, {data.longitude:.2f}",
            "distance": "0 km",
            "risk": "0%",
            "action": "✅ New Profile Created",
            "status": "safe"
        }
        ACTIVITY_LOGS.insert(0, log_entry) # Add to top of list
        
        return {
            "final_risk_score": 0.0, "security_action": "✅ NEW DEVICE DETECTED: Profile Created",
            "detector_scores": {}
        }

    # 2. EXISTING USER CHECKS
    history = USER_DB[uid]
    time_delta = current_time - history["last_login"]
    hours_diff = time_delta.total_seconds() / 3600.0

    # Run Detectors
    score_behavior = behavior_engine.get_risk(data.typing_delay)
    score_geo = geo_engine.get_risk(data.latitude, data.longitude, history["last_lat"], history["last_lon"], hours_diff)
    score_otp = otp_engine.get_risk(history["failed_otps"])
    
    # Calculate Distance Moved (for Admin Display)
    dist_km = geo_engine.calculate_haversine(history["last_lat"], history["last_lon"], data.latitude, data.longitude)

    scores = {"A1_Behavior_DNA": score_behavior, "A2_Geo_Velocity": score_geo, "A3_OTP_Misuse": score_otp}
    result = fusion_engine.run_assessment(scores)
    
    # 3. LOG THE EVENT
    action_type = "safe"
    if "BLOCK" in result['action']: action_type = "danger"
    elif "FLAG" in result['action'] or "Email" in result['action']: action_type = "warning"

    log_entry = {
        "time": current_time.strftime("%H:%M:%S"),
        "user": uid,
        "location": f"{data.latitude:.2f}, {data.longitude:.2f}",
        "distance": f"{dist_km:.1f} km",
        "risk": f"{result['final_risk_score']*100:.0f}%",
        "action": result['action'],
        "status": action_type
    }
    ACTIVITY_LOGS.insert(0, log_entry)

    # 4. UPDATE HISTORY (If not blocked)
    if "BLOCK" not in result['action']:
        USER_DB[uid]["last_lat"] = data.latitude
        USER_DB[uid]["last_lon"] = data.longitude
        USER_DB[uid]["last_login"] = current_time
        USER_DB[uid]["failed_otps"] = 0
    else:
        if "OTP" in result['action']: USER_DB[uid]["failed_otps"] += 1

    return {
        "final_risk_score": result['final_risk_score'],
        "security_action": result['action'],
        "detector_scores": scores
    }