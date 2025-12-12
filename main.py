from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# Absolute Imports
from models import LoginAttempt, OTPVerification
from fusion_engine import FusionEngine
from detectors import GeoVelocityCheck, BehaviorCheck, OTPCheck

# --- CONFIGURATION ---
# These are loaded from Render's Environment Variables
MAIL_USERNAME = os.getenv("MAIL_USERNAME") # Your gmail address
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD") # Your 16-char App Password

# --- DATABASES ---
USER_DB = {}
ACTIVITY_LOGS = []
OTP_CACHE = {}

# --- INITIALIZE ENGINES ---
geo_engine = GeoVelocityCheck()
behavior_engine = BehaviorCheck()
otp_engine = OTPCheck()
fusion_engine = FusionEngine()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- EMAIL SENDER FUNCTION ---
def send_real_email(to_email, otp_code):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("⚠️ Email credentials missing in environment variables!")
        return False
    
    subject = "Global Bank - Login Verification Code"
    body = f"""
    Security Alert: Login Attempt Detected.
    
    Your Verification Code is: {otp_code}
    
    If this was not you, your account may be compromised.
    """
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = MAIL_USERNAME
    msg['To'] = to_email

    try:
        # Connect to Gmail SMTP Server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, to_email, msg.as_string())
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# --- ENDPOINTS ---

@app.get("/", include_in_schema=False)
async def serve_login():
    path = os.path.join(PROJECT_DIR, 'bank_login.html')
    if not os.path.exists(path): path = os.path.join(PROJECT_DIR, 'index.html')
    if os.path.exists(path):
        with open(path, 'r') as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>Login page not found</h1>", status_code=404)

@app.get("/admin", include_in_schema=False)
async def serve_admin():
    path = os.path.join(PROJECT_DIR, 'admin_dashboard.html')
    if os.path.exists(path):
        with open(path, 'r') as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>Admin page not found</h1>", status_code=404)

@app.get("/admin/data")
async def get_admin_data():
    return {"logs": ACTIVITY_LOGS}

@app.post("/verify-otp")
async def verify_otp(data: OTPVerification):
    uid = data.email
    
    if uid in USER_DB and USER_DB[uid]["failed_otps"] >= 3:
         return {"status": "block", "message": "🚫 BLOCK: Account Locked"}

    real_otp = OTP_CACHE.get(uid)
    
    if not real_otp:
        return {"status": "fail", "message": "Session Expired"}

    if data.otp_code == real_otp:
        if uid in USER_DB: USER_DB[uid]["failed_otps"] = 0
        ACTIVITY_LOGS.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "user": uid, "location": "-", "otp": "Verified", "risk": "0%",
            "action": "✅ Login Successful", "status": "safe"
        })
        return {"status": "success", "message": "Login Successful"}
    else:
        if uid in USER_DB: USER_DB[uid]["failed_otps"] += 1
        count = USER_DB[uid]["failed_otps"] if uid in USER_DB else 1
        
        ACTIVITY_LOGS.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "user": uid, "location": "-", "otp": "Failed", "risk": "High",
            "action": f"❌ Wrong OTP ({count}/3)", "status": "warning"
        })

        if count >= 3:
            return {"status": "block", "message": "🚫 BLOCK: Max OTP attempts reached"}
        return {"status": "fail", "message": f"Incorrect OTP. Attempt {count}/3"}

@app.post("/predict")
async def predict_fraud(data: LoginAttempt):
    uid = data.email
    current_time = datetime.now()
    
    # 1. Generate OTP
    generated_otp = str(random.randint(1000, 9999))
    OTP_CACHE[uid] = generated_otp
    
    # 2. Determine Action Logic (Fusion Engine)
    # (Initialize history if new user)
    if uid not in USER_DB:
        USER_DB[uid] = { "last_lat": data.latitude, "last_lon": data.longitude, "last_login": current_time, "failed_otps": 0 }
        fusion_result = {"final_risk_score": 0.0, "action": "✅ New Profile"}
        scores = {}
    else:
        # Existing User Logic
        history = USER_DB[uid]
        time_delta = current_time - history["last_login"]
        hours_diff = time_delta.total_seconds() / 3600.0
        
        score_b = behavior_engine.get_risk(data.typing_delay)
        score_g = geo_engine.get_risk(data.latitude, data.longitude, history["last_lat"], history["last_lon"], hours_diff)
        score_o = otp_engine.get_risk(history["failed_otps"])
        scores = {"A1_Behavior_DNA": score_b, "A2_Geo_Velocity": score_g, "A3_OTP_Misuse": score_o}
        fusion_result = fusion_engine.run_assessment(scores)

    # 3. Handle Actions
    action_text = fusion_result['action']
    status_color = "safe"
    
    if "BLOCK" in action_text:
        status_color = "danger"
        # DO NOT SEND EMAIL IF BLOCKED
        ACTIVITY_LOGS.insert(0, {
            "time": current_time.strftime("%H:%M:%S"),
            "user": uid, "location": "Blocked", "otp": "BLOCKED", "risk": "100%", "action": action_text, "status": "danger"
        })
    else:
        # SAFE or WARNING -> SEND EMAIL
        if "Email" in action_text: status_color = "warning"
        
        # --- SEND THE ACTUAL EMAIL ---
        email_sent = send_real_email(uid, generated_otp)
        log_otp_status = "📧 Emailed" if email_sent else "❌ Mail Failed"
        
        ACTIVITY_LOGS.insert(0, {
            "time": current_time.strftime("%H:%M:%S"),
            "user": uid, "location": f"{data.latitude:.2f}, {data.longitude:.2f}",
            "otp": f"{generated_otp} ({log_otp_status})", # Logs show if sent
            "risk": f"{fusion_result.get('final_risk_score', 0)*100:.0f}%",
            "action": action_text, 
            "status": status_color
        })

    # Update History if Safe
    if "BLOCK" not in action_text:
        USER_DB[uid]["last_lat"] = data.latitude
        USER_DB[uid]["last_lon"] = data.longitude
        USER_DB[uid]["last_login"] = current_time

    return {
        "final_risk_score": fusion_result.get('final_risk_score', 0.0),
        "security_action": action_text,
        "detector_scores": scores
    }