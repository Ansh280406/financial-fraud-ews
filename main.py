from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from models import LoginRequest, OTPRequest, AuthResponse
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engines
geo_engine = GeoVelocityCheck()
ai_engine = BehaviorCheck()
otp_engine = OTPCheck()

# MOCK DB (Stores User History + Credentials)
DB = {
    "user": {
        "password": "password123",
        "last_lat": 28.7041, "last_lon": 77.1025, # New Delhi
        "last_login": datetime.now() - timedelta(hours=24),
        "otp_secret": "1234"
    }
}

@app.post("/login", response_model=AuthResponse)
def login(data: LoginRequest):
    print(f"Login Attempt: {data.user_id} | Lat: {data.latitude} | TypeSpeed: {data.avg_keystroke_delay}s")

    # 1. Verify Credentials
    user = DB.get(data.user_id)
    if not user or user["password"] != data.password:
        return {"status": "BLOCKED", "message": "Invalid Credentials", "risk_score": 0.0}

    # 2. Run AI & Geo Checks
    geo_risk = geo_engine.get_risk(data.latitude, data.longitude, user)
    ai_risk = ai_engine.get_risk(data.avg_keystroke_delay)
    
    total_risk = (geo_risk + ai_risk) / 2
    
    # 3. Update History (if safe-ish)
    if geo_risk == 0:
        user['last_lat'] = data.latitude
        user['last_lon'] = data.longitude
        user['last_login'] = datetime.now()

    # 4. Decision
    if geo_risk == 1.0:
        return {"status": "BLOCKED", "message": "Impossible Travel Detected", "risk_score": 1.0}
    
    if ai_risk == 1.0:
        # AI thinks it's a bot/imposter, but we give a chance via OTP
        return {"status": "MFA_REQUIRED", "message": "Unusual Typing Detected", "risk_score": 1.0}

    return {"status": "MFA_REQUIRED", "message": "Login Validated. Enter OTP.", "risk_score": 0.0}

@app.post("/verify-otp", response_model=AuthResponse)
def verify_otp(data: OTPRequest):
    # 1. Check Bot Flooding
    if otp_engine.check_flood(data.user_id):
        return {"status": "BLOCKED", "message": "Too many OTP attempts (Bot detected)", "risk_score": 1.0}

    # 2. Verify Code
    if data.otp_code == "1234": # Hardcoded for demo
        otp_engine.reset(data.user_id)
        return {"status": "SUCCESS", "message": "Access Granted", "risk_score": 0.0}
    
    return {"status": "FAILED", "message": "Invalid OTP", "risk_score": 0.5}