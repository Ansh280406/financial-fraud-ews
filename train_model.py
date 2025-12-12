import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
import joblib

def train_models():
    print("🧠 Training Real-World AI Models...")
    rng = np.random.RandomState(42)

    # --- MODEL 1: BEHAVIOR AI (Keystroke Dynamics) ---
    # Detects: Bots (too fast) or Impersonators (too slow/erratic)
    # Feature: Average Keystroke Delay (seconds)
    
    # 1. Generate "Normal Human" Data (0.1s - 0.3s delay)
    X_human = 0.2 + 0.05 * rng.randn(1000, 1)
    X_human = np.clip(X_human, 0.1, 0.4)
    
    # 2. Generate "Bot" Data (0.0s - 0.02s delay)
    X_bot = rng.uniform(0.0, 0.02, size=(100, 1))
    
    # 3. Train Isolation Forest (Anomaly Detector)
    # -1 = Anomaly (Bot/Impersonator), 1 = Normal
    X_train_behavior = np.concatenate([X_human, X_bot])
    behavior_model = IsolationForest(contamination=0.1, random_state=42)
    behavior_model.fit(X_train_behavior)
    
    joblib.dump(behavior_model, "behavior_model.pkl")
    print("✅ 'behavior_model.pkl' (Isolation Forest) Saved!")


    # --- MODEL 2: FUSION ENGINE (Risk Aggregator) ---
    # Decides: Block vs Allow based on 3 scores
    # Features: [Behavior_Score, Geo_Score, OTP_Score]
    # Target: 1 (Fraud), 0 (Safe)
    
    # Generate Synthetic Training Data for Fusion
    # Columns: [Behavior_Risk, Geo_Risk, OTP_Risk]
    
    # Case A: Safe Users (Low scores across board)
    X_safe = rng.uniform(0, 0.3, size=(500, 3))
    y_safe = np.zeros(500)
    
    # Case B: Fraudsters (High scores in at least one area)
    X_fraud = rng.uniform(0.6, 1.0, size=(500, 3))
    y_fraud = np.ones(500)
    
    X_fusion = np.vstack([X_safe, X_fraud])
    y_fusion = np.hstack([y_safe, y_fraud])
    
    fusion_model = LogisticRegression()
    fusion_model.fit(X_fusion, y_fusion)
    
    joblib.dump(fusion_model, "fusion_model.pkl")
    print("✅ 'fusion_model.pkl' (Logistic Regression) Saved!")

if __name__ == "__main__":
    train_models()