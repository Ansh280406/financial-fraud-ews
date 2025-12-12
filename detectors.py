# detectors.py
import math
from datetime import datetime

# --- 1. GEO-VELOCITY DETECTOR ---
class GeoVelocityCheck:
    def __init__(self):
        self.MAX_VELOCITY_KMH = 800.0 

    def calculate_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2)**2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_score(self, current_data, history):
        """
        Returns a risk score (0.0 to 1.0) based on speed.
        """
        if not history or 'last_lat' not in history:
            return 0.0  # First time login is safe

        # Calculate Distance
        dist = self.calculate_haversine(
            history['last_lat'], history['last_lon'],
            current_data.latitude, current_data.longitude
        )

        # Calculate Time Diff (Hours)
        last_time = history.get('last_login_time', datetime.now())
        time_diff = (datetime.now() - last_time).total_seconds() / 3600.0

        if time_diff <= 0: return 0.5 # Suspicious instant travel

        velocity = dist / time_diff

        # Logic: If speed > 800km/h -> High Risk (1.0)
        if velocity > self.MAX_VELOCITY_KMH:
            return 1.0
        elif velocity > 200:
            return 0.5
        return 0.0

# --- 2. OTP FRAUD DETECTOR ---
class OTPFraudCheck:
    def __init__(self):
        self.MAX_FAILURES = 3

    def get_score(self, current_data, history):
        """
        Returns risk based on failed attempts count.
        """
        failures = history.get('failed_otp_count', 0)
        
        if failures >= self.MAX_FAILURES:
            return 1.0 # Account Locked logic
        elif failures == 1:
            return 0.3
        elif failures == 2:
            return 0.7
        return 0.0

# --- 3. BEHAVIORAL DETECTOR ---
class BehavioralCheck:
    def __init__(self):
        self.HIGH_RISK_MERCHANTS = ["CryptoExchange", "BettingSite"]

    def get_score(self, current_data, history):
        """
        Returns risk based on Spending and Merchant.
        """
        # 1. Merchant Check
        if current_data.merchant in self.HIGH_RISK_MERCHANTS:
            return 1.0

        # 2. Amount Deviation (Z-Score approximation)
        avg = history.get('avg_spend', 500.0) # Default avg
        
        if current_data.amount > (avg * 5):
            return 1.0 # Huge spike
        elif current_data.amount > (avg * 2):
            return 0.5 # Moderate spike
            
        return 0.1 # Safe
