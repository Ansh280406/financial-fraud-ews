from pydantic import BaseModel
from typing import Optional

# STEP 1: LOGIN REQUEST
class LoginRequest(BaseModel):
    user_id: str
    password: str
    latitude: float
    longitude: float
    avg_keystroke_delay: float  # <--- New AI Feature

# STEP 2: OTP REQUEST
class OTPRequest(BaseModel):
    user_id: str
    otp_code: str

# RESPONSE
class AuthResponse(BaseModel):
    status: str       # "SUCCESS", "MFA_REQUIRED", "BLOCKED"
    message: str
    risk_score: float