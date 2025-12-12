import numpy as np
import pickle

class FusionEngine:
    def __init__(self, fusion_model=None):
        self.model = fusion_model

    def run_assessment(self, detector_scores: dict) -> dict:
        """
        Aggregates scores and applies specific rules for Block vs Mail.
        """
        
        # Extract scores (default to 0.0 if missing)
        s1_behavior = detector_scores.get('A1_Behavior_DNA', 0.0)
        s2_geo = detector_scores.get('A2_Geo_Velocity', 0.0)
        s3_otp = detector_scores.get('A3_OTP_Misuse', 0.0)
        
        # --- RULE 1: CRITICAL BLOCKS (Travel & Bot) ---
        # If physically impossible travel OR brute force OTP -> IMMEDIATE BLOCK
        if s2_geo > 0.9:
            return {
                'final_risk_score': float(s2_geo),
                'action': "🚫 BLOCK: Impossible Travel Detected"
            }
        
        if s3_otp > 0.9:
            return {
                'final_risk_score': float(s3_otp),
                'action': "🚫 BLOCK: OTP Brute Force Detected"
            }

        # --- RULE 2: IMPERSONATION (Behavior) ---
        # If behavior is anomalous (Impersonation), but Geo/OTP are okay -> SEND MAIL
        # We check if Behavior is High (> 0.8)
        if s1_behavior > 0.8:
            return {
                'final_risk_score': float(s1_behavior),
                'action': "📧 ACTION: Impersonation Suspected - Email Sent"
            }

        # --- RULE 3: NORMAL AGGREGATION ---
        # If no specific rule triggered, calculate weighted risk
        # Weights: Behavior(20%), Geo(40%), OTP(40%)
        risk_score = (s1_behavior * 0.2) + (s2_geo * 0.4) + (s3_otp * 0.4)

        if risk_score > 0.85:
            action = "🚫 BLOCK ACCESS (High Aggregated Risk)"
        elif risk_score > 0.5:
            action = "⚠️ FLAG: Verify Identity"
        else:
            action = "✅ ALLOW ACCESS"
            
        return {
            'final_risk_score': float(risk_score),
            'action': action,
        }