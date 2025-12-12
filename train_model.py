import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
import joblib
import os

def train_models():
    print("🧠 Training Real-World AI Models...")
    rng = np.random.RandomState(42)

    # ==========================================
    # MODEL 1: BEHAVIOR AI (Keystroke Dynamics)
    # ==========================================
    print("1️⃣  Training Behavior Model (Isolation Forest)...")
    
    # 1. Generate "Normal Human" Data
    # Humans type with a delay between 0.1s (100ms) and 0.4s (400ms)
    # We generate 1000 samples centered around 0.2s
    X_human = 0.2 + 0.05 * rng.randn(1000, 1)
    X_human = np.clip(X_human, 0.1, 0.4)
    
    # 2. Generate "Bot/Script" Data (Anomalies)
    # Bots type instantly: 0.0s to 0.02s (0-20ms)
    X_bot = rng.uniform(0.0, 0.02, size=(100, 1))
    
    # 3. Train Isolation Forest
    # This model learns the "Human" pattern and flags anything else as -1 (Anomaly)
    X_train_behavior = np.concatenate([X_human, X_bot])
    behavior_model = IsolationForest(contamination=0.1, random_state=42)
    behavior_model.fit(X_train_behavior)
    
    joblib.dump(behavior_model, "behavior_model.pkl")
    print("   ✅ Saved 'behavior_model.pkl'")


    # ==========================================
    # MODEL 2: FUSION ENGINE (Risk Aggregator)
    # ==========================================
    print("2️⃣  Training Fusion Model (Logistic Regression)...")
    
    # We need to teach the model how to weigh the 3 detector scores:
    # [Behavior_Score, Geo_Score, OTP_Score]
    
    # 1. Generate "Safe" User Data (Low scores across the board)
    # 500 samples where scores are between 0.0 and 0.3
    X_safe = rng.uniform(0, 0.3, size=(500, 3))
    y_safe = np.zeros(500) # Label 0 = Safe
    
    # 2. Generate "Fraud" User Data (High scores)
    # 500 samples where scores are high (0.6 to 1.0)
    X_fraud = rng.uniform(0.6, 1.0, size=(500, 3))
    y_fraud = np.ones(500) # Label 1 = Fraud
    
    # 3. Train Logistic Regression
    # This learns that High Scores = Fraud
    X_fusion = np.vstack([X_safe, X_fraud])
    y_fusion = np.hstack([y_safe, y_fraud])
    
    fusion_model = LogisticRegression()
    fusion_model.fit(X_fusion, y_fusion)
    
    joblib.dump(fusion_model, "fusion_model.pkl")
    print("   ✅ Saved 'fusion_model.pkl'")
    
    print("\n🎉 All models trained successfully!")

if __name__ == "__main__":
    train_models()