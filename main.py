from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import pickle

# --- IMPORTS FIX ---
# We use absolute imports. Python will look for these files in the same folder.
from models import LoginAttempt
from fusion_engine import FusionEngine
# We import detectors to ensure the file exists, even if we don't use the logic directly here
import detectors 

# --- Configuration ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- SIMULATED DATA (Hardcoded to prevent JSON file errors) ---
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

# --- Load the Fusion Model ---
try:
    model_path = os.path.join(PROJECT_DIR, 'fraud_model.pkl')
    with open(model_path, 'rb') as f:
        fusion_model = pickle.load(f)
except FileNotFoundError:
    print(f"Warning: Model file not found at {model_path}. Running without model.")
    fusion_model = None

# Initialize Engine
fusion_engine = FusionEngine(fusion_model=fusion_model, detector_scores=SIMULATED_DETECTOR_SCORES)

# --- FastAPI Setup ---
app = FastAPI()

# --- CORS FIX (Critical for your HTML to work) ---
origins = ["*"]  # Allow all origins

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
    index_path = os.path.join(PROJECT_DIR, 'index.html')
    if not os.path.exists(index_path):
        return HTMLResponse("<h1>Index file not found!</h1>", status_code=404)
    with open(index_path, 'r') as f:
        return HTMLResponse(content=f.read())

@app.post("/predict")
async def predict_fraud(login_attempt: LoginAttempt):
    user_id = login_attempt.user_id
    
    # 1. Look up scores
    if user_id not in fusion_engine.detector_scores:
        raise HTTPException(status_code=404, detail="User ID not found in simulation.")
        
    scores = fusion_engine.detector_scores[user_id]
    
    # 2. Run Assessment
    result = fusion_engine.run_assessment(user_id=user_id, detector_scores=scores)
    
    # 3. Return Response
    return {
        "final_risk_score": result['final_risk_score'],
        "security_action": result['action'],
        "detector_scores": {
            "A1_Behavior_DNA": scores.get('A1_Behavior_DNA', 0.0),
            "A2_Geo_Velocity": scores.get('A2_Geo_Velocity', 0.0),
            "A3_OTP_Misuse": scores.get('A3_OTP_Misuse', 0.0)
        }
    }