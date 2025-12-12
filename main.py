from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import pickle

# Absolute Imports
from models import LoginAttempt
from fusion_engine import FusionEngine
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck

# --- CONFIGURATION ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- INITIALIZE ENGINES ---
geo_engine = GeoVelocityCheck()
behavior_engine = BehaviorCheck()
otp_engine = OTPCheck()
fusion_engine = FusionEngine() # No model needed for rule-based logic

# --- MOCK SCENARIOS (Tuned for your request) ---
SCENARIO_CONTEXTS = {
    # CASE 1: Normal User -> Allow
    "demo_user": {
        "prev_loc": (40.7128, -74.0060), "curr_loc": (40.7128, -74.0060), # Same place
        "time_diff": 1.0, 
        "typing_delay": 150, # Normal speed
        "failed_otps": 0
    },
    # CASE 2: Impossible Travel -> Block
    "demo_travel": {
        "prev_loc": (40.7128, -74.0060), "curr_loc": (51.5074, -0.1278), # NY to London
        "time_diff": 2.0, # 2 hours (Impossible!)
        "typing_delay": 150,
        "failed_otps": 0
    },
    # CASE 3: OTP Script -> Block
    "demo_otp": {
        "prev_loc": (40.7128, -74.0060), "curr_loc": (40.7128, -74.0060),
        "time_diff": 1.0,
        "typing_delay": 150,
        "failed_otps": 5 # 5 Failures (Attack)
    },
    # CASE 4: Impersonation -> Send Mail
    "demo_impersonation": {
        "prev_loc": (40.7128, -74.0060), "curr_loc": (40.7128, -74.0060),
        "time_diff": 1.0,
        "typing_delay": 10, # 10ms (Inhuman speed/Bot script impersonation)
        "failed_otps": 0
    }
}

# --- FASTAPI APP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def serve_index():
    index_path = os.path.join(PROJECT_DIR, 'index.html')
    if not os.path.exists(index_path):
        return HTMLResponse("<h1>Index file not found!</h1>", status_code=404)
    with open(index_path, 'r') as f:
        return HTMLResponse(content=f.read())

@app.post("/predict")
async def predict_fraud(login_attempt: LoginAttempt):
    user_id = login_attempt.user_id
    
    if user_id not in SCENARIO_CONTEXTS:
        raise HTTPException(status_code=404, detail="User Scenario Not Found")
        
    ctx = SCENARIO_CONTEXTS[user_id]
    
    # Run Detectors
    score_behavior = behavior_engine.get_risk(ctx['typing_delay'])
    score_geo = geo_engine.get_risk(ctx['curr_loc'], ctx['prev_loc'], ctx['time_diff'])
    score_otp = otp_engine.get_risk(ctx['failed_otps'])
    
    detector_results = {
        "A1_Behavior_DNA": score_behavior,
        "A2_Geo_Velocity": score_geo,
        "A3_OTP_Misuse": score_otp
    }
    
    # Run Fusion Logic
    final_result = fusion_engine.run_assessment(detector_results)
    
    return {
        "final_risk_score": final_result['final_risk_score'],
        "security_action": final_result['action'],
        "detector_scores": detector_results
    }