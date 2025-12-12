import numpy as np
import joblib
import os

class FusionEngine:
    def __init__(self, fusion_model=None):
        self.model = fusion_model
        # Try load model if not passed
        if self.model is None:
            try:
                path = os.path.join(os.path.dirname(__file__), "fusion_model.pkl")
                if os.path.exists(path):
                    self.model = joblib.load(path)
            except:
                pass

    def run_assessment(self, detector_scores: dict) -> dict:
        # 1. Extract Features
        s1 = detector_scores.get('A1_Behavior_DNA', 0.0)
        s2 = detector_scores.get('A2_Geo_Velocity', 0.0)
        s3 = detector_scores.get('A3_OTP_Misuse', 0.0)
        
        # --- VETO RULE 1: IMMEDIATE BLOCK ---
        # Impossible Travel OR Brute Force OTP -> BLOCK
        if s2 >= 0.9:
            return {'final_risk_score': 1.0, 'action': "🚫 BLOCK: Impossible Travel Detected"}
        if s3 >= 0.9:
            return {'final_risk_score': 1.0, 'action': "🚫 BLOCK: OTP Brute Force Detected"}

        # --- VETO RULE 2: VERIFY IDENTITY ---
        # Impersonation (Behavior) -> SEND MAIL
        if s1 >= 0.8:
            return {'final_risk_score': float(s1), 'action': "📧 ACTION: Impersonation Suspected - Email Sent"}

        # --- AI FUSION (Aggregation) ---
        if self.model:
            try:
                risk_score = self.model.predict_proba([[s1, s2, s3]])[:, 1][0]
            except:
                risk_score = (s1 * 0.2) + (s2 * 0.4) + (s3 * 0.4)
        else:
            risk_score = (s1 * 0.2) + (s2 * 0.4) + (s3 * 0.4)

        # --- FINAL THRESHOLDS ---
        if risk_score > 0.85:
            action = "🚫 BLOCK ACCESS"
        elif risk_score > 0.5:
            action = "⚠️ FLAG & CHALLENGE"
        else:
            action = "✅ ALLOW ACCESS"
            
        return {
            'final_risk_score': float(risk_score),
            'action': action,
        }