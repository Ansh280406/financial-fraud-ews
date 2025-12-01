from pydantic import BaseModel
from typing import Dict, Optional

# --- INPUT DATA ---
class LoginRequest(BaseModel):
    user_id: str
    password: str  # <--- NEW FIELD
    ip_address: str
    device_fingerprint: str
    
    # Optional fields for demo triggers
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    otp_failures: Optional[int] = 0
    browser_type: Optional[str] = "Chrome"

# --- OUTPUT DATA ---
class RiskAssessmentResponse(BaseModel):
    final_risk_score: float
    security_action: str
    risk_level: str
    detector_scores: Dict[str, float]
    weights: Dict[str, float]
