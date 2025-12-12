import math
import numpy as np
import os
import joblib
from datetime import datetime

# --- 1. GEO-VELOCITY (Physics Engine) ---
class GeoVelocityCheck:
    def __init__(self):
        self.MAX_SPEED_KMH = 800.0 # Speed of a commercial jet

    def calculate_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371 # Earth Radius km
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_risk(self, curr_lat, curr_lon, last_lat, last_lon, hours_diff):
        # First time login is safe
        if last_lat is None or last_lon is None: return 0.0
            
        dist = self.calculate_haversine(last_lat, last_lon, curr_lat, curr_lon)
        
        if hours_diff <= 0: hours_diff = 0.001
        speed = dist / hours_diff
        
        # If speed > 800km/h, it's physically impossible
        if speed > self.MAX_SPEED_KMH: return 1.0
        return 0.0

# --- 2. BEHAVIOR AI (Isolation Forest) ---
class BehaviorCheck:
    def __init__(self):
        self.model = None
        # Try to load the trained model
        try:
            path = os.path.join(os.path.dirname(__file__), "behavior_model.pkl")
            if os.path.exists(path):
                self.model = joblib.load(path)
        except:
            print("⚠️ Behavior Model not found. Using Logic Fallback.")

    def get_risk(self, typing_delay_ms):
        # Convert ms to seconds
        delay_sec = typing_delay_ms / 1000.0
        
        if self.model:
            # Predict: -1 = Anomaly, 1 = Normal
            pred = self.model.predict([[delay_sec]])[0]
            if pred == -1: return 1.0 # Anomaly detected
            return 0.0
        else:
            # Fallback Logic
            if typing_delay_ms < 50: return 1.0 # Bot
            if typing_delay_ms > 1000: return 0.8 # Sluggish
            return 0.1

# --- 3. OTP CHECK ---
class OTPCheck:
    def get_risk(self, failed_attempts):
        if failed_attempts >= 3: return 1.0 # Brute Force
        if failed_attempts == 2: return 0.5
        return 0.0