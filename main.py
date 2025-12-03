from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

# 1. Allow Frontend to Connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Define the Data Model (Must match your JavaScript!)
class LoginData(BaseModel):
    user_id: str
    password: str
    ip_address: str
    device_fingerprint: str

# 3. The Prediction Endpoint
@app.post("/predict")
def predict_risk(data: LoginData):
    print(f"Analyzing login for: {data.user_id}")

    # --- SIMULATION LOGIC ---
    # We fake the scores based on which button you clicked (user_id)
    
    risk_score = 0.1  # Default safe
    action = "ALLOW"
    detectors = {
        "A1_Behavior_DNA": "LOW",
        "A2_Geo_Velocity": "LOW", 
        "A3_OTP_Misuse": "LOW"
    }

    if data.user_id == "demo_travel":
        risk_score = 0.95
        action = "BLOCK"
        detectors["A2_Geo_Velocity"] = "CRITICAL (3000km/h)"
        detectors["A1_Behavior_DNA"] = "MEDIUM"
        
    elif data.user_id == "demo_otp":
        risk_score = 0.85
        action = "MFA_CHALLENGE"
        detectors["A3_OTP_Misuse"] = "HIGH (Rapid Attempts)"

    elif data.user_id == "demo_impersonation":
        risk_score = 0.75
        action = "VERIFY_IDENTITY"
        detectors["A1_Behavior_DNA"] = "HIGH (Keystroke Mismatch)"

    # Return the exact JSON format your HTML expects
    return {
        "final_risk_score": risk_score,
        "security_action": action,
        "detector_scores": detectors
    }

# 4. Health Check
@app.get("/")
def home():
    return {"message": "Fraud Detection Server is Running"}
