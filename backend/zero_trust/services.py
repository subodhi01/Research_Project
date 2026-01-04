import os
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ..database import SessionLocal
from ..models import User, ZeroTrustLoginEvent

DATA_PATH = os.path.join(os.path.dirname(__file__), "password_security_dataset.csv")


def _load_dataset() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    return df


def _build_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    if df.empty:
        return np.empty((0, 6))
    length = df["password_length"].astype(float)
    used_special = df["used_special_characters"].astype(str).str.lower().isin(["yes", "true", "1"]).astype(float)
    attempts = df["login_attempts"].astype(float)
    caps = df["was_capslock_on"].astype(str).str.lower().isin(["yes", "true", "1"]).astype(float)
    tabs = df["browser_tab_count"].astype(float)
    speed = df["typing_speed_wpm"].astype(float)
    x = np.stack([length.values, used_special.values, attempts.values, caps.values, tabs.values, speed.values], axis=1)
    return x


def train_zero_trust_model() -> Tuple[IsolationForest, np.ndarray]:
    df = _load_dataset()
    x = _build_feature_matrix(df)
    if x.shape[0] == 0:
        return IsolationForest(), np.array([])
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(x)
    scores = model.decision_function(x)
    return model, scores


def _build_session_features(payload: Dict[str, Any]) -> np.ndarray:
    length = float(payload.get("password_length", 0))
    used_special = str(payload.get("used_special_characters", "")).lower() in ["yes", "true", "1"]
    attempts = float(payload.get("login_attempts", 0))
    caps = str(payload.get("was_capslock_on", "")).lower() in ["yes", "true", "1"]
    tabs = float(payload.get("browser_tab_count", 0))
    speed = float(payload.get("typing_speed_wpm", 0))
    x = np.array([[length, float(used_special), attempts, float(caps), tabs, speed]], dtype=float)
    return x


def _get_heuristic_reasons(payload: Dict[str, Any]) -> List[str]:
    reasons = []
    password_length = payload.get("password_length", 0)
    typing_speed = payload.get("typing_speed_wpm", 60)
    login_attempts = payload.get("login_attempts", 1)
    browser_tabs = payload.get("browser_tab_count", 1)
    caps_lock = str(payload.get("was_capslock_on", "")).lower() in ["yes", "true", "1"]
    special_chars = str(payload.get("used_special_characters", "")).lower() in ["yes", "true", "1"]
    
    if password_length < 8:
        reasons.append("very_short_password")
    elif password_length < 10:
        reasons.append("short_password")
    
    if not special_chars:
        reasons.append("no_special_characters")
    
    if login_attempts >= 5:
        reasons.append("many_login_attempts")
    elif login_attempts >= 3:
        reasons.append("multiple_login_attempts")
    
    if typing_speed > 150:
        reasons.append("extremely_fast_typing")
    elif typing_speed > 120:
        reasons.append("unusually_fast_typing")
    elif typing_speed < 20:
        reasons.append("very_slow_typing")
    
    if caps_lock:
        reasons.append("capslock_on")
    
    if browser_tabs > 15:
        reasons.append("too_many_browser_tabs")
    elif browser_tabs > 10:
        reasons.append("many_browser_tabs")
    
    keyboard_lang = str(payload.get("keyboard_language", "")).upper()
    if keyboard_lang not in ["EN", "US", "GB", "AU", "CA"]:
        reasons.append("unusual_keyboard_language")
    
    return reasons


def score_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    model, train_scores = train_zero_trust_model()
    if train_scores.size == 0:
        return {"risk_score": 0.0, "risk_level": "unknown", "reasons": []}
    x = _build_session_features(payload)
    score = float(model.decision_function(x)[0])
    rank = float((train_scores < score).mean())
    risk_score = float(max(0.0, min(1.0, 1.0 - rank)))
    if risk_score >= 0.8:
        level = "high"
    elif risk_score >= 0.5:
        level = "medium"
    else:
        level = "low"
    reasons = _get_heuristic_reasons(payload)
    return {
        "risk_score": risk_score,
        "risk_level": level,
        "reasons": reasons,
    }


def process_login(username: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    base_result = score_session(payload)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            session.add(user)
            session.flush()
        event = ZeroTrustLoginEvent(
            user_id=user.id,
            username=username,
            risk_score=base_result["risk_score"],
            risk_level=base_result["risk_level"],
            reasons=base_result.get("reasons", []),
            payload=payload,
        )
        session.add(event)
        session.commit()
        base_result["user_id"] = user.id
        base_result["event_id"] = event.id
        return base_result
    finally:
        session.close()


def get_users_with_latest_risk() -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        users = session.query(User).all()
        results: List[Dict[str, Any]] = []
        for user in users:
            latest = (
                session.query(ZeroTrustLoginEvent)
                .filter(ZeroTrustLoginEvent.user_id == user.id)
                .order_by(ZeroTrustLoginEvent.created_at.desc())
                .first()
            )
            item: Dict[str, Any] = {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "department": user.department,
                "role": user.role,
            }
            if latest:
                item["last_risk_score"] = latest.risk_score
                item["last_risk_level"] = latest.risk_level
                item["last_login_at"] = latest.created_at.isoformat() if latest.created_at else None
            results.append(item)
        return results
    finally:
        session.close()


def get_recent_login_events(limit: int = 50) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        events = (
            session.query(ZeroTrustLoginEvent)
            .order_by(ZeroTrustLoginEvent.created_at.desc())
            .limit(limit)
            .all()
        )
        results: List[Dict[str, Any]] = []
        for e in events:
            results.append(
                {
                    "id": e.id,
                    "user_id": e.user_id,
                    "username": e.username,
                    "risk_score": e.risk_score,
                    "risk_level": e.risk_level,
                    "reasons": e.reasons,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
            )
        return results
    finally:
        session.close()


def get_zero_trust_stats(window_minutes: int = 1440) -> Dict[str, Any]:
    session = SessionLocal()
    try:
        now = datetime.utcnow()
        since = now - timedelta(minutes=window_minutes)
        q = (
            session.query(ZeroTrustLoginEvent)
            .filter(ZeroTrustLoginEvent.created_at >= since)
            .order_by(ZeroTrustLoginEvent.created_at.desc())
        )
        events = q.all()
        total = len(events)
        high = len([e for e in events if e.risk_level == "high"])
        medium = len([e for e in events if e.risk_level == "medium"])
        low = len([e for e in events if e.risk_level == "low"])
        return {
            "total_events": total,
            "high": high,
            "medium": medium,
            "low": low,
            "window_minutes": window_minutes,
        }
    finally:
        session.close()


def get_user_monitoring_data(username: str, limit: int = 100) -> Dict[str, Any]:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return {
                "username": username,
                "exists": False,
                "total_logins": 0,
                "events": [],
                "risk_trend": [],
                "avg_risk_score": 0.0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
            }
        
        events = (
            session.query(ZeroTrustLoginEvent)
            .filter(ZeroTrustLoginEvent.user_id == user.id)
            .order_by(ZeroTrustLoginEvent.created_at.desc())
            .limit(limit)
            .all()
        )
        
        total = session.query(ZeroTrustLoginEvent).filter(ZeroTrustLoginEvent.user_id == user.id).count()
        high_count = len([e for e in events if e.risk_level == "high"])
        medium_count = len([e for e in events if e.risk_level == "medium"])
        low_count = len([e for e in events if e.risk_level == "low"])
        
        risk_scores = [e.risk_score for e in events if e.risk_score is not None]
        avg_risk = float(np.mean(risk_scores)) if risk_scores else 0.0
        
        risk_trend = []
        for e in reversed(events[:30]):
            if e.created_at and e.risk_score is not None:
                risk_trend.append({
                    "timestamp": e.created_at.isoformat(),
                    "risk_score": e.risk_score,
                    "risk_level": e.risk_level,
                })
        
        event_list = []
        for e in events:
            event_list.append({
                "id": e.id,
                "risk_score": e.risk_score,
                "risk_level": e.risk_level,
                "reasons": e.reasons or [],
                "created_at": e.created_at.isoformat() if e.created_at else None,
            })
        
        return {
            "username": username,
            "exists": True,
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "department": user.department,
            "role": user.role,
            "total_logins": total,
            "events": event_list,
            "risk_trend": risk_trend,
            "avg_risk_score": avg_risk,
            "high_risk_count": high_count,
            "medium_risk_count": medium_count,
            "low_risk_count": low_count,
        }
    finally:
        session.close()