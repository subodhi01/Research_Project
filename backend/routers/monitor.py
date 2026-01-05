from fastapi import APIRouter, Query, HTTPException
from typing import List
from ..services_monitor import (
    init_departments, 
    generate_realtime_monitor_data, 
    get_department_recommendations, 
    simulate_deployment,
    DEPARTMENTS
)
from ..services_loadgen import start_department_load, stop_department_load, get_active_loads

router = APIRouter(prefix="/api/monitor", tags=["monitor"])

@router.on_event("startup")
async def startup_event():
    init_departments()

@router.get("/departments")
async def get_departments():
    return DEPARTMENTS

@router.get("/realtime/{dept}")
async def get_realtime_stats(dept: str):
    if dept not in DEPARTMENTS:
        raise HTTPException(status_code=404, detail="Department not found")
    return generate_realtime_monitor_data(dept)

@router.get("/recommendations/{dept}")
async def get_recommendations(dept: str):
    if dept not in DEPARTMENTS:
        raise HTTPException(status_code=404, detail="Department not found")
    return get_department_recommendations(dept)

@router.post("/deploy/{recommendation_id}")
async def deploy_recommendation(recommendation_id: int):
    return simulate_deployment(recommendation_id)

@router.post("/load/start/{dept}")
async def start_load(
    dept: str,
    cpu_intensity: float = Query(0.5, ge=0.0, le=1.0, description="CPU load intensity (0.0-1.0)"),
    memory_mb: int = Query(100, ge=0, le=2048, description="Memory to allocate in MB"),
    duration: int = Query(60, ge=1, le=3600, description="Duration in seconds")
):
    if dept not in DEPARTMENTS:
        raise HTTPException(status_code=404, detail="Department not found")
    return start_department_load(dept, cpu_intensity, memory_mb, duration)

@router.post("/load/stop/{dept}")
async def stop_load(dept: str):
    if dept not in DEPARTMENTS:
        raise HTTPException(status_code=404, detail="Department not found")
    return stop_department_load(dept)

@router.get("/load/active")
async def list_active_loads():
    return {"active_departments": get_active_loads()}
