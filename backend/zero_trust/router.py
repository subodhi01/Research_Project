from fastapi import APIRouter, Query
from pydantic import BaseModel

from .services import score_session, process_login, get_users_with_latest_risk, get_recent_login_events, get_zero_trust_stats, get_user_monitoring_data


router = APIRouter(prefix="/api/zero-trust", tags=["zero-trust"])


class ZeroTrustSessionPayload(BaseModel):
    password_length: int
    used_special_characters: str
    keyboard_language: str
    login_attempts: int
    was_capslock_on: str
    browser_tab_count: int
    challenge_sequence: str = ""
    timezone: str
    typing_speed_wpm: float


class ZeroTrustLoginPayload(ZeroTrustSessionPayload):
    username: str


@router.post("/score-session")
async def score_zero_trust_session(payload: ZeroTrustSessionPayload):
    return score_session(payload.dict())


@router.post("/login")
async def zero_trust_login(payload: ZeroTrustLoginPayload):
    data = payload.dict()
    username = data.pop("username")
    return process_login(username, data)


@router.get("/users")
async def zero_trust_users():
    return {"items": get_users_with_latest_risk()}


@router.get("/login-events/recent")
async def zero_trust_recent_events(limit: int = Query(50, gt=0, le=500)):
    return {"items": get_recent_login_events(limit=limit)}


@router.get("/stats")
async def zero_trust_stats(window_minutes: int = Query(1440, gt=0, le=10080)):
    return get_zero_trust_stats(window_minutes=window_minutes)


@router.get("/users/{username}/monitoring")
async def zero_trust_user_monitoring(username: str):
    return get_user_monitoring_data(username)