from pydantic import BaseModel
from typing import Optional

class LoginAttempt(BaseModel):
    user_id: str
    password: str
    latitude: float  # Real GPS Lat
    longitude: float # Real GPS Lon
    typing_delay: float # Real Avg Delay (ms)
    device_fingerprint: str
    
class RiskAssessment(BaseModel):
    final_risk_score: float
    security_action: str
    detector_scores: dict