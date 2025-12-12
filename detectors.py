import math
import numpy as np
from datetime import datetime

# --- 1. GEO-VELOCITY DETECTOR ---
class GeoVelocityCheck:
    def __init__(self):
        self.MAX_SPEED_KMH = 800.0 

    def calculate_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371 
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_risk(self, current_location, last_location, time_diff_hours):
        if not last_location or not current_location: return 0.0
        
        distance = self.calculate_haversine(last_location[0], last_location[1], 
                                          current_location[0], current_location[1])
        
        if time_diff_hours <= 0: time_diff_hours = 0.001 
            
        speed = distance / time_diff_hours
        
        if speed > self.MAX_SPEED_KMH: return 1.0 # Impossible Travel
        return 0.0

# --- 2. BEHAVIOR DETECTOR ---
class BehaviorCheck:
    def get_risk(self, typing_delay_ms):
        """
        Input: Average typing delay in milliseconds.
        Logic: < 50ms (Bot/Script) OR > 3000ms (Anomaly) -> High Score
        """
        # Impersonation / Bot behavior
        if typing_delay_ms < 50: 
            return 1.0 # High Anomaly
        elif typing_delay_ms > 3000:
            return 0.9 # High Anomaly
        return 0.1 # Normal

# --- 3. OTP DETECTOR ---
class OTPCheck:
    def get_risk(self, failed_attempts):
        # 3 or more failures = Block
        if failed_attempts >= 3: return 1.0
        if failed_attempts == 2: return 0.5
        return 0.0