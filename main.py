from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

# Import your modules
from models import LoginRequest, RiskAssessmentResponse
from detectors import GeoVelocityCheck, OTPFraudCheck, BehavioralCheck
from fusion_engine import calculate_final_risk, get_security_action, WEIGHTS

app = FastAPI()

# 1. CORS (So your HTML works with the Cloud Server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Initialize Detectors
geo_detector = GeoVelocityCheck()
otp_detector = OTPFraudCheck()
behavior_detector = BehavioralCheck()

# 3. MOCK DATABASE
# We use 'timedelta' here to ensure the last login was definitely in the past.
# This prevents the "0 seconds elapsed" issue when the server restarts.
MOCK_DB = {
    "demo_user": {
        "last_lat": 28.7041, "last_lon": 77.1025, # New Delhi
        "last_login_time": datetime.now() - timedelta(hours=24), # Logged in yesterday
        "avg_spend": 500.0,
        "failed_otp_count": 0
    },
    "demo_travel": {
        "last_lat": 40.7128, "last_lon": -74.0060, # New York
        "last_login_time": datetime.now() - timedelta(hours=2), # Logged in 2 Hours ago
        "avg_spend": 200.0,
        "failed_otp_count": 0
    },
    "demo_otp": {
        "last_lat": 28.7041, "last_lon": 77.1025,
        "last_login_time": datetime.now() - timedelta(hours=1),
        "avg_spend": 500.0,
        "failed_otp_count": 5 # ALREADY HAS 5 FAILURES
    }
}

@app.post("/predict", response_model=RiskAssessmentResponse)
def predict_risk(data: LoginRequest):
    print(f"Analyzing Request for: {data.user_id}")

    # A. Fetch History (or create default)
    user_history = MOCK_DB.get(data.user_id, {
        "last_lat": 0.0, "last_lon": 0.0,
        "avg_spend": 100.0,
        "failed_otp_count": 0,
        "last_login_time": datetime.now() - timedelta(hours=24)
    })

    # B. Run Detectors (REAL LOGIC)
    score_a1 = behavior_detector.get_score(data, user_history)
    score_a2 = geo_detector.get_score(data, user_history)
    score_a3 = otp_detector.get_score(data, user_history)

    # C. Fusion Engine (Calculate Final Score)
    final_score = calculate_final_risk(score_a1, score_a2, score_a3)
    decision = get_security_action(final_score)

    # D. Prepare Response
    response = {
        "final_risk_score": round(final_score, 2),
        "security_action": decision["action"],
        "risk_level": decision["level"],
        "detector_scores": {
            "A1_Behavior_DNA": round(score_a1, 2),
            "A2_Geo_Velocity": round(score_a2, 2),
            "A3_OTP_Misuse": round(score_a3, 2)
        },
        "weights": WEIGHTS
    }

    return response

# Health Check
@app.get("/")
def home():
    return {"status": "Active", "system": "Real-Time Logic Enabled"}
