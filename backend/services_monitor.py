import psutil
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from .models import CloudUsage, Recommendation, Department
from .database import SessionLocal

DEPARTMENTS = ["HR", "IT", "Dev", "Management"]
VM_PREFIX = "vps-slice-"

DEPARTMENT_ALLOCATIONS = {
    "Dev": 0.40,
    "IT": 0.30,
    "HR": 0.20,
    "Management": 0.10,
}

LAST_PERSISTED: Dict[str, datetime] = {}


def init_departments():
    session = SessionLocal()
    try:
        for dept in DEPARTMENTS:
            exists = session.query(Department).filter(Department.name == dept).first()
            if not exists:
                budget = 1000.0 if dept == "Dev" else 500.0
                session.add(Department(name=dept, budget=budget))
        session.commit()
    finally:
        session.close()


def persist_metrics(dept: str, cpu_percent: float, mem_percent: float, load_avg: float):
    now = datetime.utcnow()
    last = LAST_PERSISTED.get(dept)
    if last and (now - last).total_seconds() < 60:
        return
    session = SessionLocal()
    try:
        resource_id = f"{VM_PREFIX}{dept.lower()}-01"
        cpu_row = CloudUsage(
            provider="vps",
            account_id=dept,
            resource_id=resource_id,
            resource_type="vm",
            metric="cpu_pct",
            timestamp=now,
            value=cpu_percent,
            cost=0.0,
        )
        mem_row = CloudUsage(
            provider="vps",
            account_id=dept,
            resource_id=resource_id,
            resource_type="vm",
            metric="mem_pct",
            timestamp=now,
            value=mem_percent,
            cost=0.0,
        )
        load_row = CloudUsage(
            provider="vps",
            account_id=dept,
            resource_id=resource_id,
            resource_type="vm",
            metric="load_avg",
            timestamp=now,
            value=load_avg,
            cost=0.0,
        )
        session.add(cpu_row)
        session.add(mem_row)
        session.add(load_row)
        session.commit()
        LAST_PERSISTED[dept] = now
    finally:
        session.close()


def generate_realtime_monitor_data(dept: str) -> Dict:
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    mem_percent = mem.percent
    
    net_io = psutil.net_io_counters()
    disk_io = psutil.disk_io_counters()
    process_count = len(psutil.pids())
    
    try:
        load_avg = psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0.0
    except:
        load_avg = 0.0
    
    allocation = DEPARTMENT_ALLOCATIONS.get(dept, 0.25)
    
    dept_cpu = cpu_percent * allocation
    dept_mem = mem_percent * allocation
    dept_net_sent = (net_io.bytes_sent * allocation) if net_io else 0
    dept_net_recv = (net_io.bytes_recv * allocation) if net_io else 0
    dept_disk_read = (disk_io.read_bytes * allocation) if disk_io else 0
    dept_disk_write = (disk_io.write_bytes * allocation) if disk_io else 0
    dept_processes = int(process_count * allocation)
    
    dept_cpu = max(0, min(100, dept_cpu))
    dept_mem = max(0, min(100, dept_mem))
    
    status = "healthy"
    if dept_cpu > 80:
        status = "critical"
    elif dept_cpu > 60:
        status = "warning"

    persist_metrics(dept, dept_cpu, dept_mem, load_avg * allocation)

    return {
        "department": dept,
        "resource_id": f"{VM_PREFIX}{dept.lower()}-01",
        "cpu_usage": round(dept_cpu, 2),
        "memory_usage": round(dept_mem, 2),
        "network_sent_mb": round(dept_net_sent / (1024 * 1024), 2),
        "network_recv_mb": round(dept_net_recv / (1024 * 1024), 2),
        "disk_read_mb": round(dept_disk_read / (1024 * 1024), 2),
        "disk_write_mb": round(dept_disk_write / (1024 * 1024), 2),
        "process_count": dept_processes,
        "load_average": round(load_avg * allocation, 2),
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "system_cpu": round(cpu_percent, 2),
        "system_memory": round(mem_percent, 2),
        "system_processes": process_count,
        "system_load": round(load_avg, 2),
    }


def simulate_deployment(recommendation_id: int):
    session = SessionLocal()
    try:
        rec = session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not rec:
            return {"status": "error", "message": "Recommendation not found"}
        
        rec.status = "deploying"
        session.commit()

        import time
        time.sleep(1)
        
        cpu_after = psutil.cpu_percent(interval=0.5)
        mem_after = psutil.virtual_memory().percent
        
        if cpu_after > 90 or mem_after > 95:
            rec.status = "rolled_back"
            session.commit()
            return {
                "status": "rolled_back", 
                "message": "Performance degradation detected. Automated rollback triggered.",
                "metrics": {
                    "latency_ms": 450, 
                    "error_rate_percent": 5.2, 
                    "cpu_after": cpu_after,
                    "memory_after": mem_after,
                },
            }
        
        rec.status = "deployed"
        session.commit()
        return {
            "status": "success", 
            "message": "Optimization successfully deployed.",
             "metrics": {
                 "latency_ms": 45, 
                 "error_rate_percent": 0.1, 
                 "cpu_after": cpu_after,
                 "memory_after": mem_after,
             },
        }
    finally:
        session.close()


def get_department_recommendations(dept: str):
    session = SessionLocal()
    try:
        recs = session.query(Recommendation).filter(
            Recommendation.account_id == dept, 
            Recommendation.status == "proposed",
        ).all()
        
        if not recs:
            monitor = generate_realtime_monitor_data(dept)
            if monitor["cpu_usage"] < 20:
                rec = Recommendation(
                    provider="vps",
                    account_id=dept,
                    resource_id=monitor["resource_id"],
                    current_type="vps.large",
                    recommended_type="vps.medium",
                    action="Downsize",
                    reason="Under-utilization detected (<20% CPU)",
                    estimated_monthly_saving=45.0,
                    status="proposed",
                )
                session.add(rec)
                session.commit()
                recs = [rec]
            elif monitor["cpu_usage"] > 80:
                 rec = Recommendation(
                    provider="vps",
                    account_id=dept,
                    resource_id=monitor["resource_id"],
                    current_type="vps.medium",
                    recommended_type="vps.large",
                    action="Upsize",
                    reason="Over-utilization detected (>80% CPU)",
                    estimated_monthly_saving=-30.0,
                    status="proposed",
                )
                 session.add(rec)
                 session.commit()
                 recs = [rec]
                 
        return recs
    finally:
        session.close()
