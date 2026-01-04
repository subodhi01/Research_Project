from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    budget = Column(Float, default=0.0)


class CloudUsage(Base):
    __tablename__ = "cloud_usage"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True)
    account_id = Column(String, index=True) # Can be used for Department Name
    resource_id = Column(String, index=True)
    resource_type = Column(String, index=True)
    metric = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    value = Column(Float)
    cost = Column(Float)


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True)
    scope = Column(String, index=True)
    model_type = Column(String, index=True)
    mae = Column(Float)
    rmse = Column(Float)
    mape = Column(Float)
    horizon_hours = Column(Integer)
    input_points = Column(Integer)
    predictions = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True)
    account_id = Column(String, index=True) # Department
    resource_id = Column(String, index=True)
    current_type = Column(String)
    recommended_type = Column(String)
    action = Column(String, index=True)
    reason = Column(String)
    estimated_monthly_saving = Column(Float)
    status = Column(String, default="proposed", index=True) # proposed, deploying, deployed, rolled_back
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, index=True)
    applied = Column(Integer)
    realized_saving = Column(Float)
    notes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AnomalyThresholdConfig(Base):
    __tablename__ = "anomaly_threshold_configs"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String, index=True, nullable=True)
    metric = Column(String, index=True)
    method = Column(String)
    value = Column(Float)
    window_hours = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    department = Column(String, index=True)
    resource_id = Column(String, index=True)
    metric = Column(String, index=True)
    severity = Column(String, index=True)
    message = Column(String)
    payload = Column(JSON)
    delivered_via = Column(String)
    status = Column(String, index=True)


class AnomalyModelRun(Base):
    __tablename__ = "anomaly_model_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    window_hours = Column(Integer)
    z_score = Column(Float)
    tp = Column(Integer)
    fp = Column(Integer)
    fn = Column(Integer)
    tn = Column(Integer)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    accuracy = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class BudgetAlert(Base):
    __tablename__ = "budget_alerts"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    department = Column(String, index=True)
    provider = Column(String, index=True)
    severity = Column(String, index=True)
    message = Column(String)
    payload = Column(JSON)
    delivered_via = Column(String)
    status = Column(String, index=True)


class OptimizationModelRun(Base):
    __tablename__ = "optimization_model_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    window_minutes = Column(Integer)
    provider = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ReportSubscription(Base):
    __tablename__ = "report_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    role = Column(String, index=True)
    channel = Column(String, index=True)
    active = Column(Integer, index=True, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class UxFeedback(Base):
    __tablename__ = "ux_feedback"

    id = Column(Integer, primary_key=True, index=True)
    page = Column(String, index=True)
    component = Column(String, index=True)
    rating = Column(Integer)
    comment = Column(String)
    user_email = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class MetricUsage(Base):
    __tablename__ = "metric_usage"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(String, index=True)
    context = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    full_name = Column(String, index=True, nullable=True)
    email = Column(String, index=True, nullable=True)
    department = Column(String, index=True, nullable=True)
    role = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    login_events = relationship("ZeroTrustLoginEvent", back_populates="user")


class ZeroTrustLoginEvent(Base):
    __tablename__ = "zero_trust_login_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    username = Column(String, index=True)
    risk_score = Column(Float)
    risk_level = Column(String, index=True)
    reasons = Column(JSON)
    payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user = relationship("User", back_populates="login_events")
