from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import pickle

# --- ABSOLUTE IMPORTS ---
from models import LoginAttempt
from fusion_engine import FusionEngine
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck 

# --- CONFIGURATION ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- SIMULATED DATA ---
SIMULATED_DETECTOR_SCORES = {
    "demo_user": {"A1_Behavior_DNA": 0.15, "A2_Geo_Velocity": 0.05, "A3_OTP_Misuse": 0.02},
    "demo_travel": {"A1_Behavior_DNA": 0.25, "A2_Geo_Velocity": 0.95, "A3_OTP_Misuse": 0.10},
    "demo_otp": {"A1_Behavior_DNA": 0.80, "A2_Geo_Velocity": 0.15, "A3_OTP_Misuse": 0.75},
    "demo_impersonation": {"A1_Behavior_DNA": 0.90, "A2_Geo_Velocity": 0.50, "A3_OTP_Misuse": 0.30}
}

# --- LOAD MODEL ---
fusion_model = None
try:
    model_path = os.path.join(PROJECT_DIR, 'fraud_model.pkl')
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            fusion_model = pickle.load(f)
except Exception as e:
    print(f"Warning: Could not load model: {e}")

# --- INIT ENGINE ---
fusion_engine = FusionEngine(fusion_model=fusion_model, detector_scores=SIMULATED_DETECTOR_SCORES)

# --- FASTAPI APP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---
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
    if user_id not in fusion_engine.detector_scores:
        raise HTTPException(status_code=404, detail="User ID not found in simulation.")
        
    scores = fusion_engine.detector_scores[user_id]
    result = fusion_engine.run_assessment(user_id=user_id, detector_scores=scores)
    
    return {
        "final_risk_score": result['final_risk_score'],
        "security_action": result['action'],
        "detector_scores": {
            "A1_Behavior_DNA": scores.get('A1_Behavior_DNA', 0.0),
            "A2_Geo_Velocity": scores.get('A2_Geo_Velocity', 0.0),
            "A3_OTP_Misuse": scores.get('A3_OTP_Misuse', 0.0)
        }
    }