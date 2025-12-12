from pydantic import BaseModel

class LoginAttempt(BaseModel):
    user_id: str
    password: str
    ip_address: str
    device_fingerprint: str

class RiskAssessment(BaseModel):
    final_risk_score: float
    security_action: str
    detector_scores: dict