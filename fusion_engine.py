import numpy as np
import pickle

class FusionEngine:
    def __init__(self, fusion_model=None, detector_scores=None):
        """
        Initializes the Fusion Engine with the trained model and simulated detector scores.
        """
        self.model = fusion_model
        self.detector_scores = detector_scores if detector_scores is not None else {}
        self.RISK_THRESHOLD = 0.5  # Default threshold for blocking/flagging

    def _get_weighted_features(self, scores: dict) -> np.ndarray:
        """
        Converts detector scores into a feature vector for the ML model.
        Order of features must match the model training (A1, A2, A3).
        """
        try:
            features = np.array([
                scores['A1_Behavior_DNA'],
                scores['A2_Geo_Velocity'],
                scores['A3_OTP_Misuse']
            ]).reshape(1, -1)
            return features
        except KeyError as e:
            raise ValueError(f"Missing required detector score: {e}")

    def run_assessment(self, user_id: str, detector_scores: dict) -> dict:
        """
        Runs the full risk assessment pipeline.
        """
        
        # 1. Prepare features
        try:
            features = self._get_weighted_features(detector_scores)
        except ValueError as e:
            return {
                'final_risk_score': 0.0,
                'action': f"ERROR: {e}",
            }

        # 2. ML Model Prediction (If model is loaded)
        if self.model:
            # Predict probability of fraud (P(Fraud=1))
            try:
                risk_score = self.model.predict_proba(features)[:, 1][0]
            except Exception:
                # Fallback if model prediction fails
                risk_score = features.mean()
        else:
            # Fallback to simple averaging if model is missing
            risk_score = features.mean() 
            
        # 3. Decision Logic
        if risk_score > 0.85:
            action = "🚫 BLOCK ACCESS (High Risk)"
        elif risk_score > self.RISK_THRESHOLD:
            action = "⚠️ FLAG & CHALLENGE (Medium Risk)"
        else:
            action = "✅ ALLOW ACCESS (Low Risk)"
            
        return {
            'final_risk_score': float(risk_score),
            'action': action,
        }