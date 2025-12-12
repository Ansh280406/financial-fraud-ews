from pydantic import BaseModel

# Input model for the API
# This class MUST be named 'LoginAttempt' exactly
class LoginAttempt(BaseModel):
    user_id: str
    password: str
    ip_address: str
    device_fingerprint: str
    
# Output model for the API 
class RiskAssessment(BaseModel):
    final_risk_score: float
    security_action: str
    detector_scores: dict