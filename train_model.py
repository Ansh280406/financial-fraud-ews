import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

# --- REAL LIFE IMPERSONATION DATA ---
# Feature: "Average Keystroke Delay" (seconds)
# Humans: Usually 0.1s to 0.3s per key.
# Bots: Near 0.0s (Instant paste).
# Impersonators/Elderly/Distracted: > 0.5s (Searching for keys).

rng = np.random.RandomState(42)

# 1. Generate "Normal Human" Data (1000 samples)
# Normal distribution around 0.15s (150ms) with some variance
X_humans = 0.15 + 0.05 * rng.randn(1000, 1)
# Clip to realistic bounds (0.05s to 0.4s)
X_humans = np.clip(X_humans, 0.05, 0.4)

# 2. Generate "Anomalies" (Bots & Impersonators)
# Bots: Super fast (0.001s)
X_bots = rng.uniform(low=0.0, high=0.02, size=(50, 1))
# Slow Typers: Very slow (0.6s to 1.0s)
X_slow = rng.uniform(low=0.6, high=1.0, size=(50, 1))

# Combine
X_train = np.concatenate([X_humans, X_bots, X_slow])

# 3. Train Model
clf = IsolationForest(contamination=0.1, random_state=42)
clf.fit(X_train)

# 4. Save
joblib.dump(clf, "fraud_model.pkl")
print("✅ Keystroke Dynamics Model Trained & Saved!")
print("   - Learns that Humans type ~150ms per key.")
print("   - Will flag Bots (instant) or Impersonators (hesitant).")