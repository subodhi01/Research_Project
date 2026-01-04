import os

import numpy as np
import pandas as pd


def main() -> None:
    root = os.path.dirname(__file__)
    path = os.path.join(root, "password_security_dataset.csv")
    if not os.path.exists(path):
        return
    df = pd.read_csv(path)
    if df.empty:
        return
    if "risk_label" in df.columns:
        df = df.drop(columns=["risk_label"])
    length = df["password_length"].astype(float)
    used_special = df["used_special_characters"].astype(str).str.lower().isin(["yes", "true", "1"])
    attempts = df["login_attempts"].astype(float)
    caps = df["was_capslock_on"].astype(str).str.lower().isin(["yes", "true", "1"])
    speed = df["typing_speed_wpm"].astype(float)
    browser_tabs = df["browser_tab_count"].astype(float)
    
    score = np.zeros(len(df), dtype=float)
    score += np.where(length < 10, 2.0, 0.0)
    score += np.where(~used_special, 2.0, 0.0)
    score += np.where(attempts >= 5, 2.0, 0.0)
    score += np.where(caps, 1.0, 0.0)
    score += np.where(speed > 120, 1.0, 0.0)
    score += np.where(browser_tabs > 15, 0.5, 0.0)
    
    base_label = np.where(score >= 4.0, 1, 0)
    
    df["risk_label"] = base_label
    
    df.to_csv(path, index=False)


if __name__ == "__main__":
    main()


