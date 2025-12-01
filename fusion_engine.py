# fusion_engine.py

# --- CONFIGURATION ---
# These are the "Weights" for your formula.
# w1 (Behavior) is 0.5 because impersonation is the hardest to catch.
WEIGHTS = {
    "w1_behavior": 0.5,
    "w2_geo_velocity": 0.3,
    "w3_otp_misuse": 0.2
}

# This table acts like a traffic light for security actions.
DECISION_MAPPING = [
    {"max_score": 0.3, "action": "Allow login", "level": "Safe"},
    {"max_score": 0.6, "action": "Silent logging + monitoring", "level": "Low Risk"},
    {"max_score": 0.8, "action": "Alerts user to verify activity", "level": "Suspicious"},
    {"max_score": 1.0, "action": "Block + force 2FA", "level": "High Risk"}
]

# --- LOGIC FUNCTIONS ---

def calculate_final_risk(a1: float, a2: float, a3: float) -> float:
    """
    Combines the three scores into one Final Risk Score.
    
    Includes a 'VETO RULE': 
    If any single detector screams danger (> 0.9), we ignore the average
    and force a high risk score immediately.
    """
    
    # 1. Calculate the Standard Weighted Average
    weighted_avg = (
        WEIGHTS["w1_behavior"] * a1 +
        WEIGHTS["w2_geo_velocity"] * a2 +
        WEIGHTS["w3_otp_misuse"] * a3
    )

    # 2. THE VETO RULE (Critical Security Update)
    # If Behavior OR Location OR OTP is extremely suspicious...
    if a1 >= 0.9 or a2 >= 0.9 or a3 >= 0.9:
        # ...we override the average and force a Block (0.95 or higher)
        return max(weighted_avg, 0.95)

    # Otherwise, return the normal weighted average
    return min(weighted_avg, 1.0)


def get_security_action(final_risk_score: float) -> dict:
    """
    Looks at the Final Risk Score and returns the correct Action from the table.
    """
    for rule in DECISION_MAPPING:
        if final_risk_score <= rule["max_score"]:
            return rule
            
    # Safety net: If something goes wrong, block it.
    return {"action": "Block + force 2FA", "level": "Critical Risk"}
