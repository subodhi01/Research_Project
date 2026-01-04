from typing import Dict, List
import os
import json
from urllib import request as urlrequest

from .forecasting_budget.services import compare_forecast_to_budget, multi_cloud_cost_trends
from .services_monitor import generate_realtime_monitor_data, DEPARTMENTS
from .models import Recommendation, ReportSubscription
from .database import SessionLocal


def classify_cost_impact(saving: float) -> str:
    v = abs(saving)
    if v < 50:
        return "low"
    if v < 200:
        return "moderate"
    return "high"


def compute_global_insights(default_budget: float = 3000.0) -> Dict:
    monitor = [generate_realtime_monitor_data(d) for d in DEPARTMENTS]
    critical = [m for m in monitor if m["status"] == "critical"]
    warning = [m for m in monitor if m["status"] == "warning"]

    forecast_summary = compare_forecast_to_budget(monthly_budget=default_budget, forecast_days=30)

    session = SessionLocal()
    try:
        recs = session.query(Recommendation).all()
    finally:
        session.close()

    total_positive = sum(r.estimated_monthly_saving for r in recs if r.estimated_monthly_saving and r.estimated_monthly_saving > 0)
    total_negative = sum(r.estimated_monthly_saving for r in recs if r.estimated_monthly_saving and r.estimated_monthly_saving < 0)

    impact_level = classify_cost_impact(total_positive)

    summary_text = []
    if forecast_summary["status"] == "over_budget_risk":
        summary_text.append("Projected spend is above budget; consider immediate rightsizing and budget review.")
    elif forecast_summary["status"] == "under_budget":
        summary_text.append("Projected spend is below budget; there may be room to consolidate or invest in efficiency.")
    else:
        summary_text.append("Spend is tracking close to budget; monitor high-variance workloads.")

    if critical:
        summary_text.append(f"{len(critical)} departments are in critical CPU state; deploy urgent optimization.")
    elif warning:
        summary_text.append(f"{len(warning)} departments show elevated load; plan scaling or throttling.")

    if total_positive > 0:
        summary_text.append(f"Current recommendations can unlock about ${round(total_positive, 2)} per month in savings.")

    return {
        "monitor": monitor,
        "forecast": forecast_summary,
        "recommendations": {
            "count": len(recs),
            "total_positive_saving": total_positive,
            "total_negative_saving": total_negative,
            "impact_level": impact_level,
        },
        "nlg": " ".join(summary_text),
    }


def compute_role_insights(role: str, default_budget: float = 3000.0) -> Dict:
    role = role.lower()
    global_insights = compute_global_insights(default_budget=default_budget)

    if role in ["finance", "fin", "cfo"]:
        forecast = global_insights["forecast"]
        recs = global_insights["recommendations"]
        text = f"Budget status is {forecast['status'].replace('_', ' ')} with projected total ${round(forecast['projected_total'], 2)} against budget ${round(forecast['budget'], 2)}. "
        if recs["total_positive_saving"] > 0:
            text += f"Approved optimizations could save about ${round(recs['total_positive_saving'], 2)} per month. "
        text += "Focus on high-impact rightsizing and reserved-capacity planning."
        return {"role": "finance", "insight": text, "data": {"forecast": forecast, "recommendations": recs}}

    if role in ["it", "ops", "sre"]:
        critical = [m for m in global_insights["monitor"] if m["status"] == "critical"]
        warning = [m for m in global_insights["monitor"] if m["status"] == "warning"]
        text = ""
        if critical:
            names = ", ".join(m["department"] for m in critical)
            text += f"Critical load detected in {names}. Prioritize stabilization and evaluate scaling options. "
        elif warning:
            names = ", ".join(m["department"] for m in warning)
            text += f"Elevated load observed in {names}. Monitor saturation and consider proactive scaling. "
        else:
            text += "All departments are within healthy bounds; maintain monitoring cadence. "
        return {"role": "it", "insight": text, "data": {"monitor": global_insights["monitor"]}}

    if role in ["dev", "developer", "engineering"]:
        dev_stats = next((m for m in global_insights["monitor"] if m["department"] == "Dev"), None)
        text = ""
        if dev_stats and dev_stats["status"] != "healthy":
            text += f"Dev workloads are {dev_stats['status']}; review CI/CD jobs, test environments, and non-production clusters. "
        else:
            text += "Dev workloads are stable; experiment with spot-like strategies or schedule-based scaling. "
        return {"role": "dev", "insight": text, "data": {"dev": dev_stats}}

    if role in ["management", "exec", "ceo"]:
        forecast = global_insights["forecast"]
        recs = global_insights["recommendations"]
        text = f"Cloud spend is currently {forecast['status'].replace('_', ' ')} relative to budget, with potential savings of ${round(recs['total_positive_saving'], 2)} per month. "
        text += "The platform is aligned with FinOps best practices and supports continuous optimization across teams."
        return {"role": "management", "insight": text, "data": {"forecast": forecast, "recommendations": recs}}

    return {"role": role, "insight": global_insights["nlg"], "data": global_insights}


def compute_trend_story(default_budget: float = 3000.0) -> Dict:
    global_insights = compute_global_insights(default_budget=default_budget)
    trends = multi_cloud_cost_trends(days=60)
    vps = trends.get("vps", [])
    aws = trends.get("aws", [])
    story_parts: List[str] = []
    story_parts.append(global_insights["nlg"])
    if vps:
        first = vps[0]["value"]
        last = vps[-1]["value"]
        if last > first * 1.1:
            story_parts.append("VPS spend is trending upward over the last 60 days.")
        elif last < first * 0.9:
            story_parts.append("VPS spend is trending downward over the last 60 days.")
    if aws:
        first = aws[0]["value"]
        last = aws[-1]["value"]
        if last > first * 1.1:
            story_parts.append("AWS services show a noticeable increase in daily cost.")
        elif last < first * 0.9:
            story_parts.append("AWS services are trending slightly down in daily cost.")
    resource_insights: List[Dict] = []
    for m in global_insights["monitor"]:
        if m["status"] == "critical":
            resource_insights.append(
                {
                    "title": m["department"],
                    "text": "Department {} is in critical state with CPU {:.1f}% and memory {:.1f}%.".format(
                        m["department"], m["cpu_usage"], m["memory_usage"]
                    ),
                }
            )
    return {
        "story": " ".join(story_parts),
        "resource_insights": resource_insights,
        "forecast": global_insights["forecast"],
    }


def list_report_subscriptions() -> List[Dict]:
    session = SessionLocal()
    try:
        subs = session.query(ReportSubscription).all()
    finally:
        session.close()
    out: List[Dict] = []
    for s in subs:
        out.append(
            {
                "id": s.id,
                "email": s.email,
                "role": s.role,
                "channel": s.channel,
                "active": bool(s.active),
            }
        )
    return out


def create_report_subscription(email: str, role: str, channel: str) -> Dict:
    session = SessionLocal()
    try:
        sub = ReportSubscription(email=email, role=role.lower(), channel=channel, active=1)
        session.add(sub)
        session.commit()
        return {"id": sub.id, "email": sub.email, "role": sub.role, "channel": sub.channel, "active": True}
    finally:
        session.close()


def send_role_reports(default_budget: float = 3000.0) -> Dict:
    webhook_url = os.getenv("REPORT_WEBHOOK_URL") or os.getenv("ALERT_WEBHOOK_URL")
    subs = list_report_subscriptions()
    roles = sorted(set(s["role"] for s in subs if s["active"]))
    role_insights: Dict[str, Dict] = {}
    for r in roles:
        role_insights[r] = compute_role_insights(role=r, default_budget=default_budget)
    delivered = 0
    if webhook_url:
        for s in subs:
            if not s["active"]:
                continue
            info = role_insights.get(s["role"])
            if not info:
                continue
            payload = {
                "email": s["email"],
                "role": s["role"],
                "channel": s["channel"],
                "insight": info["insight"],
            }
            data = json.dumps(payload).encode("utf-8")
            req = urlrequest.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
            try:
                urlrequest.urlopen(req, timeout=5)
                delivered += 1
            except Exception:
                continue
    return {"subscriptions": len(subs), "roles": roles, "delivered": delivered}
