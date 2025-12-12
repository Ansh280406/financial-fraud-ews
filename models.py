# models.py
from pydantic import BaseModel
from typing import Dict, Optional

# --- INPUT DATA ---
class LoginRequest(BaseModel):
    user_id: str
    password: str
    ip_address: str
    device_fingerprint: str
    
    # Optional fields for the specific detectors
    latitude: float = 0.0
    longitude: float = 0.0
    amount: float = 0.0       # Added for Behavioral Check
    merchant: str = "Unknown" # Added for Behavioral Check
    otp_input: str = ""       # For OTP validation

# --- OUTPUT DATA ---
class RiskAssessmentResponse(BaseModel):
    final_risk_score: float
    security_action: str
    risk_level: str
    detector_scores: Dict[str, float]
    weights: Dict[str, float]
