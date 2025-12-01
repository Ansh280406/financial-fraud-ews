# detectors.py
import random

# For the MVP (Prototype), we simulate the AI scores.
# This allows you to demonstrate different attack scenarios to judges.

def get_detector_scores(scenario: str):
    """
    Returns (A1, A2, A3) based on the test scenario.
    Ranges are 0.0 (Safe) to 1.0 (High Risk).
    """
    
    # CASE 1: Normal User (Everything looks safe)
    if scenario == "normal_login":
        # A1 (Behavior): Low - Matches user history
        a1 = random.uniform(0.1, 0.2)
        # A2 (Geo): Low - Same city as yesterday
        a2 = random.uniform(0.0, 0.1)
        # A3 (OTP): Low - 1 request, 1 success
        a3 = random.uniform(0.0, 0.1)

    # CASE 2: Impossible Travel (The "Jumper" Attack)
    elif scenario == "impossible_travel":
        # A1: Low - Device is correct
        a1 = random.uniform(0.1, 0.2)
        # A2: HIGH - IP is in Russia, 1 hour after login in India
        a2 = random.uniform(0.9, 1.0) 
        # A3: Low - OTP is correct
        a3 = random.uniform(0.1, 0.2)

    # CASE 3: Bot Attack / OTP Brute Force
    elif scenario == "otp_attack":
        # A1: Medium - Bot behavior
        a1 = random.uniform(0.4, 0.6)
        # A2: Low - IP is okay
        a2 = random.uniform(0.1, 0.2)
        # A3: HIGH - 10 failed OTP requests
        a3 = random.uniform(0.85, 0.95)

    # CASE 4: Account Takeover (Subtle Impersonation)
    elif scenario == "impersonation":
        # A1: HIGH - Wrong typing speed, new browser
        a1 = random.uniform(0.8, 0.9) 
        # A2: Medium - Different city but possible
        a2 = random.uniform(0.4, 0.5)
        # A3: Low
        a3 = random.uniform(0.1, 0.2)

    else:
        # Default: Random values if scenario is unknown
        a1 = random.uniform(0.0, 0.5)
        a2 = random.uniform(0.0, 0.5)
        a3 = random.uniform(0.0, 0.5)

    return a1, a2, a3
