import math
import joblib
import numpy as np
import os
from datetime import datetime

# 1. GEO-VELOCITY (Impossible Travel)
class GeoVelocityCheck:
    def __init__(self):
        self.MAX_SPEED_KMH = 800.0 

    def calculate_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371 # Earth Radius km
        d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def get_risk(self, current_lat, current_lon, history):
        if not history or history['last_lat'] == 0: return 0.0
        
        dist = self.calculate_haversine(history['last_lat'], history['last_lon'], current_lat, current_lon)
        hours_diff = (datetime.now() - history['last_login']).total_seconds() / 3600.0
        
        if hours_diff <= 0: hours_diff = 0.001 # Prevent div by zero
        speed = dist / hours_diff
        
        if speed > self.MAX_SPEED_KMH: return 1.0 # Impossible Travel
        return 0.0

# 2. BEHAVIOR AI (Keystroke Dynamics)
class BehaviorCheck:
    def __init__(self):
        self.model = None
        if os.path.exists("fraud_model.pkl"):
            self.model = joblib.load("fraud_model.pkl")

    def get_risk(self, keystroke_delay):
        if not self.model: return 0.0
        # AI Prediction (-1 is Anomaly)
        pred = self.model.predict([[keystroke_delay]])[0]
        return 1.0 if pred == -1 else 0.0

# 3. OTP BOT CHECK (Rate Limiting)
class OTPCheck:
    def __init__(self):
        self.attempts = {} # In-memory store (Use Redis in prod)

    def check_flood(self, user_id):
        # Allow max 3 attempts
        count = self.attempts.get(user_id, 0)
        if count >= 3: return True # Blocked
        self.attempts[user_id] = count + 1
        return False
        
    def reset(self, user_id):
        self.attempts[user_id] = 0