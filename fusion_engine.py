import numpy as np
import joblib

class FusionEngine:
    def __init__(self):
        self.model = None
        try:
            self.model = joblib.load("fusion_model.pkl")
        except:
            print("⚠️ Fusion Model not found. Using Rule-Based Fallback.")

    def run_assessment(self, detector_scores: dict) -> dict:
        # 1. Extract Features
        s1 = detector_scores.get('A1_Behavior_DNA', 0.0)
        s2 = detector_scores.get('A2_Geo_Velocity', 0.0)
        s3 = detector_scores.get('A3_OTP_Misuse', 0.0)
        
        # 2. VETO RULE (Immediate Block)
        # If Impossible Travel (1.0) or Bot (1.0) -> BLOCK
        if s2 >= 0.9:
            return {'final_risk_score': 1.0, 'action': "🚫 BLOCK: Impossible Travel"}
        if s3 >= 0.9:
            return {'final_risk_score': 1.0, 'action': "🚫 BLOCK: Brute Force Attack"}

        # 3. AI FUSION
        if self.model:
            # Predict probability of fraud
            risk_score = self.model.predict_proba([[s1, s2, s3]])[:, 1][0]
        else:
            # Fallback Weighted Average
            risk_score = (s1 * 0.3) + (s2 * 0.4) + (s3 * 0.3)

        # 4. DECISION
        if risk_score > 0.8:
            action = "🚫 BLOCK ACCESS"
        elif risk_score > 0.5:
            action = "⚠️ FLAG & CHALLENGE"
        elif s1 == 1.0: # Specific catch for Behavioral Anomaly
             action = "📧 ACTION: Verify Identity (Email Sent)"
        else:
            action = "✅ ALLOW ACCESS"
            
        return {
            'final_risk_score': float(risk_score),
            'action': action,
        }