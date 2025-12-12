from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import random
from datetime import datetime

# Absolute Imports
from models import LoginAttempt, OTPVerification
from fusion_engine import FusionEngine
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck

# --- DATABASES ---
USER_DB = {}        # Stores Profile History
ACTIVITY_LOGS = []  # Stores Admin Logs
OTP_CACHE = {}      # Stores the temporary OTP for each email { "email": "1234" }

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
    if not os.path.exists(path): path = os.path.join(PROJECT_DIR, 'index.html')
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
    uid = data.email
    
    # 1. Check if blocked
    if uid in USER_DB and USER_DB[uid]["failed_otps"] >= 3:
         return {"status": "block", "message": "🚫 BLOCK: Account Locked (Fraud Error)"}

    # 2. Retrieve the Real Generated OTP
    real_otp = OTP_CACHE.get(uid)
    
    if not real_otp:
        return {"status": "fail", "message": "Session Expired. Login again."}

    # 3. Verify
    if data.otp_code == real_otp:
        if uid in USER_DB: USER_DB[uid]["failed_otps"] = 0 # Reset
        
        # Log Success
        ACTIVITY_LOGS.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "user": uid, "location": "-", "otp": "Verified", "risk": "0%",
            "action": "✅ Login Successful", "status": "safe"
        })
        return {"status": "success", "message": "Login Successful"}
    else:
        # Increment Failures
        if uid in USER_DB: USER_DB[uid]["failed_otps"] += 1
        count = USER_DB[uid]["failed_otps"] if uid in USER_DB else 1
        
        ACTIVITY_LOGS.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "user": uid, "location": "-", "otp": "Failed", "risk": "High",
            "action": f"❌ Wrong OTP ({count}/3)", "status": "warning"
        })

        if count >= 3:
            return {"status": "block", "message": "🚫 BLOCK: Max OTP attempts reached"}
        
        return {"status": "fail", "message": f"Incorrect OTP. Attempt {count}/3"}


@app.post("/predict")
async def predict_fraud(data: LoginAttempt):
    uid = data.email
    current_time = datetime.now()
    
    # --- GENERATE RANDOM OTP ---
    generated_otp = str(random.randint(1000, 9999)) # 4 Digit Random
    OTP_CACHE[uid] = generated_otp  # Save it
    
    # 1. NEW USER REGISTRATION
    if uid not in USER_DB:
        USER_DB[uid] = {
            "last_lat": data.latitude, "last_lon": data.longitude,
            "last_login": current_time, "failed_otps": 0
        }
        
        # Log New Profile + OTP
        ACTIVITY_LOGS.insert(0, {
            "time": current_time.strftime("%H:%M:%S"),
            "user": uid, 
            "location": f"{data.latitude:.2f}, {data.longitude:.2f}",
            "otp": generated_otp,  # SHOW OTP IN ADMIN
            "risk": "0%", 
            "action": "✅ New Profile - OTP Sent", 
            "status": "safe"
        })
        return {"final_risk_score": 0.0, "security_action": "✅ OTP Sent to Email", "detector_scores": {}}

    # 2. EXISTING USER CHECKS
    history = USER_DB[uid]
    time_delta = current_time - history["last_login"]
    hours_diff = time_delta.total_seconds() / 3600.0

    score_behavior = behavior_engine.get_risk(data.typing_delay)
    score_geo = geo_engine.get_risk(data.latitude, data.longitude, history["last_lat"], history["last_lon"], hours_diff)
    score_otp = otp_engine.get_risk(history["failed_otps"])
    
    scores = {"A1_Behavior_DNA": score_behavior, "A2_Geo_Velocity": score_geo, "A3_OTP_Misuse": score_otp}
    result = fusion_engine.run_assessment(scores)
    
    # Log Decision + OTP
    action_type = "safe"
    if "BLOCK" in result['action']: action_type = "danger"
    elif "FLAG" in result['action'] or "Email" in result['action']: action_type = "warning"
    
    # If Blocked, DO NOT send OTP (or invalidate it)
    otp_display = generated_otp
    if "BLOCK" in result['action']: 
        OTP_CACHE.pop(uid, None)
        otp_display = "BLOCKED"

    ACTIVITY_LOGS.insert(0, {
        "time": current_time.strftime("%H:%M:%S"),
        "user": uid, 
        "location": f"{data.latitude:.2f}, {data.longitude:.2f}",
        "otp": otp_display, # SHOW OTP IN ADMIN
        "risk": f"{result['final_risk_score']*100:.0f}%",
        "action": result['action'], 
        "status": action_type
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