import math
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
        if not history or history.get('last_lat') == 0: return 0.0
        
        # Simple date parsing fallback
        try:
            last_login_dt = datetime.fromisoformat(history['last_login'])
        except:
            return 0.0

        dist = self.calculate_haversine(history['last_lat'], history['last_lon'], current_lat, current_lon)
        hours_diff = (datetime.now() - last_login_dt).total_seconds() / 3600.0
        
        if hours_diff <= 0: hours_diff = 0.001 
        speed = dist / hours_diff
        
        if speed > self.MAX_SPEED_KMH: return 1.0 
        return 0.0

# 2. BEHAVIOR AI (Keystroke Dynamics)
class BehaviorCheck:
    def __init__(self):
        self.model = None

    def get_risk(self, keystroke_delay):
        return 0.0

# 3. OTP BOT CHECK (Rate Limiting)
class OTPCheck:
    def __init__(self):
        self.attempts = {} 

    def check_flood(self, user_id):
        count = self.attempts.get(user_id, 0)
        if count >= 3: return True 
        self.attempts[user_id] = count + 1
        return False
        
    def reset(self, user_id):
        self.attempts[user_id] = 0