import threading
import time
import psutil
import os
from typing import Dict, Optional

_active_loads: Dict[str, Dict] = {} #active loads is used to store the active loads for the departments

def generate_cpu_load(duration: int, intensity: float, dept: str):
    """Generate CPU load for specified duration and intensity (0-1)"""
    end_time = time.time() + duration
    iterations = 0
    while time.time() < end_time:
        if intensity < 1.0:
            time.sleep(1.0 - intensity)
        for _ in range(int(500000 * intensity)):
            iterations += 1
            if iterations % 100000 == 0 and time.time() >= end_time:
                break

def generate_memory_load(size_mb: int, duration: int, dept: str):
    """Allocate memory for specified duration"""
    try:
        data = bytearray(size_mb * 1024 * 1024)
        time.sleep(duration)
        del data
    except MemoryError:
        pass

def start_department_load(dept: str, cpu_intensity: float = 0.5, memory_mb: int = 100, duration: int = 60):
    """
    Start load generation for a department.
    cpu_intensity: 0.0 to 1.0 (percentage of CPU to use)
    memory_mb: MB of memory to allocate
    duration: seconds to run
    """
    if dept in _active_loads:
        stop_department_load(dept)
    
    threads = []
    
    if cpu_intensity > 0:
        cpu_thread = threading.Thread(
            target=generate_cpu_load,
            args=(duration, cpu_intensity, dept),
            daemon=True
        )
        cpu_thread.start()
        threads.append(cpu_thread)
    
    if memory_mb > 0:
        mem_thread = threading.Thread(
            target=generate_memory_load,
            args=(memory_mb, duration, dept),
            daemon=True
        )
        mem_thread.start()
        threads.append(mem_thread)
    
    _active_loads[dept] = {
        "threads": threads,
        "cpu_intensity": cpu_intensity,
        "memory_mb": memory_mb,
        "duration": duration,
        "start_time": time.time()
    }
    
    return {
        "status": "started",
        "department": dept,
        "cpu_intensity": cpu_intensity,
        "memory_mb": memory_mb,
        "duration": duration,
        "message": f"Load generation started for {dept}"
    }

def stop_department_load(dept: str):
    """Stop load generation for a department"""
    if dept in _active_loads:
        load_info = _active_loads[dept]
        for thread in load_info["threads"]:
            if thread.is_alive():
                pass
        del _active_loads[dept]
        return {"status": "stopped", "department": dept, "message": f"Load generation stopped for {dept}"}
    return {"status": "not_found", "department": dept, "message": f"No active load found for {dept}"}

def get_active_loads():
    """Get list of departments with active load generation"""
    active = []
    to_remove = []
    
    current_time = time.time()
    for dept, load_info in _active_loads.items():
        elapsed = current_time - load_info["start_time"]
        if elapsed < load_info["duration"]:
            active.append({
                "department": dept,
                "cpu_intensity": load_info["cpu_intensity"],
                "memory_mb": load_info["memory_mb"],
                "elapsed": int(elapsed),
                "remaining": int(load_info["duration"] - elapsed)
            })
        else:
            to_remove.append(dept)
    
    for dept in to_remove:
        del _active_loads[dept]
    
    return active
