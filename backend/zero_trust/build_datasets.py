import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def main() -> None:
    root = os.path.dirname(__file__)
    path = os.path.join(root, "password_security_dataset.csv")
    if not os.path.exists(path):
        return
    df = pd.read_csv(path)
    if df.empty:
        return
    if "risk_label" not in df.columns:
        return
    df = df.copy()
    df["uses_special_char"] = df["used_special_characters"].astype(str).str.lower().isin(["yes", "true", "1"]).astype(int)
    df["capslock_on_flag"] = df["was_capslock_on"].astype(str).str.lower().isin(["yes", "true", "1"]).astype(int)
    df["short_password_flag"] = (df["password_length"].astype(float) < 10).astype(int)
    df["many_login_attempts_flag"] = (df["login_attempts"].astype(float) >= 5).astype(int)
    df["fast_typing_flag"] = (df["typing_speed_wpm"].astype(float) > 120).astype(int)
    tz = df["timezone"].astype(str).str.replace("UTC", "", regex=False)
    tz = tz.replace("", "+0")
    df["timezone_offset_hours"] = tz.astype(str).str.replace("+", "", regex=False).astype(float)
    df["risk_score_heuristic"] = (
        2.0 * df["short_password_flag"]
        + 2.0 * (1 - df["uses_special_char"])
        + 2.0 * df["many_login_attempts_flag"]
        + 1.0 * df["capslock_on_flag"]
        + 1.0 * df["fast_typing_flag"]
    )
    features_path = os.path.join(root, "password_security_dataset_features.csv")
    df.to_csv(features_path, index=False)
    X = df.drop(columns=["user_id", "session_ip", "challenge_sequence"])
    y = df["risk_label"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )
    train = X_train.copy()
    train["risk_label"] = y_train.values
    test = X_test.copy()
    test["risk_label"] = y_test.values
    train_path = os.path.join(root, "password_security_train.csv")
    test_path = os.path.join(root, "password_security_test.csv")
    train.to_csv(train_path, index=False)
    test.to_csv(test_path, index=False)


if __name__ == "__main__":
    main()


