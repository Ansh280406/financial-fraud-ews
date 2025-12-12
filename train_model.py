# train_model.py
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

# 1. GENERATE SYNTHETIC DATA
# Imagine "Normal" behavior is spending between $20 and $100.
# We generate 1000 data points representing normal users.
rng = np.random.RandomState(42)
X_normal = rng.uniform(low=20, high=100, size=(1000, 1))

# We also add a few "Outliers" (Fraud) to make the model robust
# Fraudsters spend big: $1000 to $5000
X_outliers = rng.uniform(low=1000, high=5000, size=(50, 1))

# Combine them into one dataset
X_train = np.concatenate([X_normal, X_outliers])

# 2. TRAIN THE MODEL (Isolation Forest)
# contamination=0.05 means "we expect about 5% of data to be weird"
clf = IsolationForest(max_samples=100, random_state=42, contamination=0.05)
clf.fit(X_train)

# 3. SAVE THE TRAINED MODEL
# We save this "Brain" to a file so our API can use it later.
joblib.dump(clf, "fraud_model.pkl")

print("✅ Model trained and saved as 'fraud_model.pkl'")
print("   - Normal patterns learned: Spending $20-$100")
print("   - Anomaly detection ready.")