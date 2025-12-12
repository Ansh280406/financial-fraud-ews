from pydantic import BaseModel

class LoginAttempt(BaseModel):
    email: str
    password: str
    latitude: float
    longitude: float
    typing_delay: float
    device_fingerprint: str

class OTPVerification(BaseModel):
    email: str
    otp_code: str

class RiskAssessment(BaseModel):
    final_risk_score: float
    security_action: str
    detector_scores: dict