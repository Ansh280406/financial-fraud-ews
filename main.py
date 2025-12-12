from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import pickle

# 🚨 FINAL FIX: Changed relative imports (from .models) to absolute imports (from models)
from models import LoginAttempt
from fusion_engine import FusionEngine
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck # Kept for structure, though logic is simplified below

# --- Configuration ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# 💡 SIMPLIFIED FIX: Hardcoded Simulated Detector Scores (to avoid file dependency)
SIMULATED_DETECTOR_SCORES = {
    "demo_user": {
        "A1_Behavior_DNA": 0.15,
        "A2_Geo_Velocity": 0.05,
        "A3_OTP_Misuse": 0.02
    },
    "demo_travel": {
        "A1_Behavior_DNA": 0.25,
        "A2_Geo_Velocity": 0.95,
        "A3_OTP_Misuse": 0.10
    },
    "demo_otp": {
        "A1_Behavior_DNA": 0.80,
        "A2_Geo_Velocity": 0.15,
        "A3_OTP_Misuse": 0.75
    },
    "demo_impersonation": {
        "A1_Behavior_DNA": 0.90,
        "A2_Geo_Velocity": 0.50,
        "A3_OTP_Misuse": 0.30
    }
}

# Load the Fusion Model
try:
    with open(os.path.join(PROJECT_DIR, 'fraud_model.pkl'), 'rb') as f:
        fusion_model = pickle.load(f)
except FileNotFoundError:
    print("Warning: 'fraud_model.pkl' not found. FusionEngine initialized without model.")
    fusion_model = None

# Initialize the Fusion Engine with the loaded model and the hardcoded scores
fusion_engine = FusionEngine(fusion_model=fusion_model, detector_scores=SIMULATED_DETECTOR_SCORES)

# --- FastAPI Setup ---
app = FastAPI(
    title="Financial Fraud EWS API",
    description="Early Warning System for Fraud Detection using ML Fusion Engine."
)

# --- CORS Configuration (The required FIX for frontend/backend communication) ---
origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---

@app.get("/", include_in_schema=False)
async def serve_index():
    """Serves the main dashboard HTML file."""
    index_path = os.path.join(PROJECT_DIR, 'index.html')
    if not os.path.exists(index_path):
        return HTMLResponse("<h1>Index file not found!</h1>", status_code=404)
    with open(index_path, 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/predict")
async def predict_fraud(login_attempt: LoginAttempt):
    """
    Accepts a LoginAttempt and returns the risk assessment from the Fusion Engine.
    """
    user_id = login_attempt.user_id
    
    # 1. Get detector scores for the user_id (simulated from hardcoded dictionary)
    if user_id not in fusion_engine.detector_scores:
        raise HTTPException(
            status_code=404, 
            detail="User ID not found in simulated data. Use one of: demo_user, demo_travel, demo_otp, demo_impersonation"
        )
        
    scores = fusion_engine.detector_scores[user_id]
    
    # 2. Run the Fusion Engine to get the final risk score and action
    result = fusion_engine.run_assessment(
        user_id=user_id,
        detector_scores=scores
    )
    
    # 3. Format the final response
    response_data = {
        "final_risk_score": result['final_risk_score'],
        "security_action": result['action'],
        "detector_scores": {
            "A1_Behavior_DNA": scores.get('A1_Behavior_DNA', 0.0),
            "A2_Geo_Velocity": scores.get('A2_Geo_Velocity', 0.0),
            "A3_OTP_Misuse": scores.get('A3_OTP_Misuse', 0.0)
        }
    }
    
    return response_data