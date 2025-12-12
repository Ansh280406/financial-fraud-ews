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

# --- LOAD ML MODEL ---
fusion_model = None
try:
    model_path = os.path.join(PROJECT_DIR, 'fraud_model.pkl')
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            fusion_model = pickle.load(f)
except Exception:
    print("Warning: Model not found. Fusion Engine will use logic fallback.")

# --- INITIALIZE ENGINES ---
# We instantiate the detector classes so we can use their logic
geo_engine = GeoVelocityCheck()
behavior_engine = BehaviorCheck()
otp_engine = OTPCheck()
fusion_engine = FusionEngine(fusion_model=fusion_model)

# --- MOCK DATABASE (SCENARIOS) ---
# Instead of hardcoded scores, we define "Contexts" (Raw Data)
# This simulates what we would fetch from a database for that user.
SCENARIO_CONTEXTS = {
    "demo_user": {
        "prev_loc": (40.7128, -74.0060), # New York
        "curr_loc": (40.7306, -73.9352), # New York (Queens) - Close
        "time_diff": 2.0,                # 2 hours later
        "typing_delay": 120,             # 120ms (Normal human)
        "failed_otps": 0                 # No failures
    },
    "demo_travel": {
        "prev_loc": (40.7128, -74.0060), # New York
        "curr_loc": (35.6762, 139.6503), # Tokyo - VERY Far
        "time_diff": 1.0,                # 1 hour later (Impossible!)
        "typing_delay": 110,             # Normal typing
        "failed_otps": 0
    },
    "demo_otp": {
        "prev_loc": (40.7128, -74.0060),
        "curr_loc": (40.7128, -74.0060), # Same location
        "time_diff": 24.0,
        "typing_delay": 100,
        "failed_otps": 3                 # 3 Failures (Bot attack!)
    },
    "demo_impersonation": {
        "prev_loc": (40.7128, -74.0060),
        "curr_loc": (34.0522, -118.2437), # Los Angeles
        "time_diff": 5.0,                 # 5 hours (Borderline possible by fast jet)
        "typing_delay": 10,               # 10ms (Super fast script/bot)
        "failed_otps": 1
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
    
    # 1. Fetch User Context (Simulating DB Lookup)
    if user_id not in SCENARIO_CONTEXTS:
        raise HTTPException(status_code=404, detail="User Scenario Not Found")
        
    ctx = SCENARIO_CONTEXTS[user_id]
    
    # 2. RUN DETECTORS (Real Calculation)
    # A1: Behavior Check
    score_behavior = behavior_engine.get_risk(ctx['typing_delay'])
    
    # A2: Geo-Velocity Check
    score_geo = geo_engine.get_risk(
        ctx['curr_loc'], 
        ctx['prev_loc'], 
        ctx['time_diff']
    )
    
    # A3: OTP Check
    score_otp = otp_engine.get_risk(ctx['failed_otps'])
    
    detector_results = {
        "A1_Behavior_DNA": score_behavior,
        "A2_Geo_Velocity": score_geo,
        "A3_OTP_Misuse": score_otp
    }
    
    # 3. RUN FUSION ENGINE
    final_result = fusion_engine.run_assessment(detector_results)
    
    return {
        "final_risk_score": final_result['final_risk_score'],
        "security_action": final_result['action'],
        "detector_scores": detector_results
    }