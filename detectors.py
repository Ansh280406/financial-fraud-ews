import math
import joblib
import numpy as np
import os
from datetime import datetime

# --- 1. GEO-VELOCITY DETECTOR ---
class GeoVelocityCheck:
    def __init__(self):
        # Threshold: 800 km/h (approx plane speed)
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
        # Safety check: If no history, it's the first login (Safe)
        if not history or 'last_lat' not in history:
            return 0.0  

        # 1. Calculate Distance
        dist = self.calculate_haversine(
            history['last_lat'], history['last_lon'],
            current_data.latitude, current_data.longitude
        )

        # 2. Calculate Time Diff (Hours)
        last_time = history.get('last_login_time', datetime.now())
        time_diff = (datetime.now() - last_time).total_seconds() / 3600.0

        # Handle suspicious "instant" travel (divide by zero protection)
        if time_diff <= 0: 
            return 0.5 

        velocity = dist / time_diff

        # 3. Logic: If speed > 800km/h -> High Risk (1.0)
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

# --- 3. BEHAVIORAL DETECTOR (AI POWERED) ---
class BehavioralCheck:
    def __init__(self):
        self.model_path = "fraud_model.pkl"
        self.model = None
        self.HIGH_RISK_MERCHANTS = ["CryptoExchange", "BettingSite"]
        
        # Load the AI Model if it exists
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("✅ AI Model loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading AI model: {e}")
        else:
            print("⚠️ Warning: AI Model ('fraud_model.pkl') not found. Using fallback logic.")

    def get_score(self, current_data, history):
        """
        Returns risk based on Machine Learning prediction.
        """
        amount = current_data.amount
        
        # --- Check 1: Blacklisted Merchants ---
        if current_data.merchant in self.HIGH_RISK_MERCHANTS:
            return 1.0

        # --- Check 2: Machine Learning Analysis ---
        if self.model is not None:
            # Prepare data: The model expects a 2D array [[amount]]
            features = np.array([[amount]])
            
            # Predict: 1 = Normal, -1 = Anomaly
            prediction = self.model.predict(features)[0]
            
            if prediction == -1:
                return 1.0  # AI flagged this as an anomaly (High Risk)
            else:
                return 0.0  # AI says this fits normal patterns
        
        # --- Fallback: Manual Rules (If model is missing) ---
        else:
            avg = history.get('avg_spend', 500.0)
            if amount > (avg * 5): return 1.0
            if amount > (avg * 2): return 0.5
            return 0.0