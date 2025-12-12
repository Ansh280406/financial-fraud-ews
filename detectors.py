import math
import numpy as np
from datetime import datetime, timedelta

# --- 1. GEO-VELOCITY DETECTOR (The Physics Logic) ---
class GeoVelocityCheck:
    def __init__(self):
        self.MAX_SPEED_KMH = 800.0  # Speed of a commercial airliner

    def calculate_haversine(self, lat1, lon1, lat2, lon2):
        """Calculates the great-circle distance between two points on Earth."""
        R = 6371  # Earth radius in km
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_risk(self, current_location: tuple, last_location: tuple, time_diff_hours: float) -> float:
        """
        Calculates risk based on speed of travel between two logins.
        """
        if not last_location or not current_location:
            return 0.0
            
        distance = self.calculate_haversine(last_location[0], last_location[1], 
                                          current_location[0], current_location[1])
        
        if time_diff_hours <= 0:
            time_diff_hours = 0.001 # Avoid division by zero
            
        speed = distance / time_diff_hours
        
        # LOGIC: If speed > max_speed, it's physically impossible -> Risk 1.0
        # Otherwise, scale risk relative to speed (optional)
        if speed > self.MAX_SPEED_KMH:
            return 1.0
        return 0.0

# --- 2. BEHAVIOR DETECTOR (The Pattern Logic) ---
class BehaviorCheck:
    def get_risk(self, typing_delay_ms: float) -> float:
        """
        Simple logic: Bots type instantly (0ms) or too consistently.
        Humans vary.
        """
        # LOGIC: If typing is inhumanly fast (< 50ms), it's a bot/script.
        if typing_delay_ms < 50:
            return 1.0 # High likelihood of Bot
        # LOGIC: If typing is extremely slow (> 3000ms), might be older user or remote proxy lag
        elif typing_delay_ms > 3000:
            return 0.2
        return 0.1 # Normal behavior

# --- 3. OTP DETECTOR (The Frequency Logic) ---
class OTPCheck:
    def get_risk(self, failed_attempts: int) -> float:
        """
        Calculates risk based on number of recent failed OTP entries.
        """
        # LOGIC: 3+ failures = Brute Force Attack
        if failed_attempts >= 3:
            return 1.0 # Veto-level risk
        elif failed_attempts == 2:
            return 0.6 # High suspicion
        elif failed_attempts == 1:
            return 0.1 # Normal typo
        return 0.0