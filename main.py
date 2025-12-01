from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import LoginRequest, RiskAssessmentResponse
from detectors import get_detector_scores
from fusion_engine import calculate_final_risk, get_security_action

app = FastAPI(title="AI-Driven Fraud Detection System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MOCK DATABASE OF USERS
VALID_USERS = {
    "demo_user": "password123",
    "demo_travel": "travel123",
    "demo_otp": "bot123",
    "demo_impersonation": "hacker123"
}

@app.post("/assess-login", response_model=RiskAssessmentResponse)
def assess_login_risk(login_data: LoginRequest):
    
    # 1. CREDENTIAL CHECK (Layer 0)
    stored_password = VALID_USERS.get(login_data.user_id)
    provided_password = getattr(login_data, 'password', None)

    if not stored_password or stored_password != provided_password:
        return RiskAssessmentResponse(
            final_risk_score=1.0,
            security_action="Block: Invalid Credentials",
            risk_level="Auth Failure",
            detector_scores={"A1_Behavior_DNA": 0.0, "A2_Geo_Velocity": 0.0, "A3_OTP_Misuse": 0.0},
            weights={"w1": 0.0, "w2": 0.0, "w3": 0.0}
        )

    # 2. DETERMINE SCENARIO FROM USER_ID
    scenario = "normal_login"
    if "travel" in login_data.user_id:
        scenario = "impossible_travel"
    elif "otp" in login_data.user_id:
        scenario = "otp_attack"
    elif "impersonation" in login_data.user_id:
        scenario = "impersonation"

    # 3. RUN RISK ENGINE
    a1, a2, a3 = get_detector_scores(scenario)
    final_risk = calculate_final_risk(a1, a2, a3)
    decision = get_security_action(final_risk)

    return RiskAssessmentResponse(
        final_risk_score=round(final_risk, 2),
        security_action=decision["action"],
        risk_level=decision["level"],
        detector_scores={
            "A1_Behavior_DNA": round(a1, 2),
            "A2_Geo_Velocity": round(a2, 2),
            "A3_OTP_Misuse": round(a3, 2)
        },
        weights={"w1": 0.5, "w2": 0.3, "w3": 0.2}
    )
