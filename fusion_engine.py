import numpy as np
import pickle

class FusionEngine:
    def __init__(self, fusion_model=None):
        self.model = fusion_model
        # This threshold determines when we switch from "Challenge" to "Block"
        # in the absence of a Veto trigger.
        self.RISK_THRESHOLD = 0.5 

    def run_assessment(self, detector_scores: dict) -> dict:
        """
        Aggregates scores using ML or Fallback Logic and applies Veto Rules.
        """
        
        # --- 1. PREPARE DATA ---
        # Extract scores safely
        s1 = detector_scores.get('A1_Behavior_DNA', 0.0)
        s2 = detector_scores.get('A2_Geo_Velocity', 0.0)
        s3 = detector_scores.get('A3_OTP_Misuse', 0.0)
        
        features = np.array([[s1, s2, s3]])

        # --- 2. VETO RULE (The "Best Logic" Requirement) ---
        # If any single detector is absolutely certain of fraud (> 0.9),
        # we block immediately. No average can save it.
        if max([s1, s2, s3]) >= 0.9:
            return {
                'final_risk_score': float(max([s1, s2, s3])),
                'action': "🚫 BLOCK ACCESS (Veto Triggered)"
            }

        # --- 3. FUSION LOGIC (ML or Weighted Average) ---
        risk_score = 0.0
        
        if self.model:
            try:
                # Use the loaded Machine Learning model
                # The model learned how to weigh these 3 factors during training
                risk_score = self.model.predict_proba(features)[:, 1][0]
            except Exception as e:
                print(f"Model prediction failed: {e}. Using fallback.")
                # Fallback: Weighted Average
                # (Behavior: 20%, Geo: 40%, OTP: 40%)
                risk_score = (s1 * 0.2) + (s2 * 0.4) + (s3 * 0.4)
        else:
            # Fallback if no model exists
            risk_score = (s1 * 0.2) + (s2 * 0.4) + (s3 * 0.4)

        # --- 4. FINAL DECISION ---
        if risk_score > 0.80:
            action = "🚫 BLOCK ACCESS (High Risk)"
        elif risk_score > 0.40:
            action = "⚠️ FLAG & CHALLENGE (Suspicious)"
        else:
            action = "✅ ALLOW ACCESS (Safe)"
            
        return {
            'final_risk_score': float(risk_score),
            'action': action,
        }