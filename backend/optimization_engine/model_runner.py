#!/usr/bin/env python3
import time
import sys
import os
import importlib.util

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

spec = importlib.util.spec_from_file_location(
    "train_optimization_model",
    os.path.join(backend_dir, "optimization_engine", "train_optimization_model.py")
)
train_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(train_module)
train_model = train_module.main

def run_continuously():
    print("Starting continuous model training...")
    print(f"Training interval: 3600 seconds (1 hour)")
    
    while True:
        try:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting model training cycle...")
            train_model()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Training cycle completed. Waiting 3600 seconds...")
            time.sleep(3600)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal. Stopping...")
            break
        except Exception as e:
            print(f"\nError in training cycle: {e}")
            print("Waiting 60 seconds before retry...")
            time.sleep(60)

if __name__ == "__main__":
    run_continuously()

