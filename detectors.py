import math
import numpy as np
import os
import joblib
from datetime import datetime

# --- 1. GEO-VELOCITY (Physics Engine) ---
class GeoVelocityCheck:
    def __init__(self):
        self.MAX_SPEED_KMH = 800.0 # Speed of a plane

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
        if last_lat is None or last_lon is None:
            return 0.0 # First login is always safe
            
        dist = self.calculate_haversine(last_lat, last_lon, curr_lat, curr_lon)
        
        if hours_diff <= 0: hours_diff = 0.001
        speed = dist / hours_diff
        
        # If speed > 800km/h, it's physically impossible
        if speed > self.MAX_SPEED_KMH:
            return 1.0
        return 0.0

# --- 2. BEHAVIOR AI (Isolation Forest) ---
class BehaviorCheck:
    def __init__(self):
        self.model = None
        try:
            # Load the Isolation Forest trained in train_model.py
            self.model = joblib.load("behavior_model.pkl")
        except:
            print("⚠️ Behavior Model not found. Using fallback logic.")

    def get_risk(self, typing_delay_ms):
        # Convert ms to seconds (Model was trained on seconds)
        delay_sec = typing_delay_ms / 1000.0
        
        if self.model:
            # Predict: 1 = Normal, -1 = Anomaly
            # We reshape because sklearn expects 2D array
            pred = self.model.predict([[delay_sec]])[0]
            if pred == -1:
                return 1.0 # High Risk (Bot or Impersonator)
            return 0.0 # Normal
        else:
            # Fallback logic if model missing
            if typing_delay_ms < 50: return 1.0 # Bot
            if typing_delay_ms > 1000: return 0.5 # Sluggish
            return 0.0

# --- 3. OTP CHECK ---
class OTPCheck:
    def get_risk(self, failed_attempts):
        if failed_attempts >= 3: return 1.0
        if failed_attempts == 2: return 0.5
        return 0.0