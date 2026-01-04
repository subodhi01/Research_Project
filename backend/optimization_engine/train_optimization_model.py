import os
import sys

root = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(root)
sys.path.insert(0, backend_root)

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, f1_score, recall_score, precision_score, classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

csv_path = os.path.join(root, "cloud_optimization.csv")
reports_dir = os.path.join(os.path.dirname(backend_root), "reports", "model_metrics")
os.makedirs(reports_dir, exist_ok=True)

def load_and_prepare_data():
    df = pd.read_csv(csv_path)
    
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    
    le_provider = LabelEncoder()
    le_region = LabelEncoder()
    le_vm_type = LabelEncoder()
    le_target = LabelEncoder()
    
    df["cloud_provider_encoded"] = le_provider.fit_transform(df["cloud_provider"])
    df["region_encoded"] = le_region.fit_transform(df["region"])
    df["vm_type_encoded"] = le_vm_type.fit_transform(df["vm_type"])
    df["target_encoded"] = le_target.fit_transform(df["target"])
    
    feature_cols = [
        "cpu_usage", "memory_usage", "net_io", "disk_io",
        "vCPU", "RAM_GB", "price_per_hour",
        "latency_ms", "throughput", "cost", "utilization",
        "hour", "day_of_week",
        "cloud_provider_encoded", "region_encoded", "vm_type_encoded"
    ]
    
    X = df[feature_cols].fillna(0.0)
    y = df["target_encoded"]
    
    return X, y, le_target, feature_cols

def train_model():
    X, y, le_target, feature_cols = load_and_prepare_data()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    train_acc_history = []
    test_acc_history = []
    train_f1_history = []
    test_f1_history = []
    train_recall_history = []
    test_recall_history = []
    train_precision_history = []
    test_precision_history = []
    
    n_estimators_list = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
    
    for n_est in n_estimators_list:
        clf = RandomForestClassifier(
            n_estimators=n_est,
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features="sqrt",
            random_state=42,
            n_jobs=-1,
            warm_start=False,
            class_weight="balanced"
        )
        
        clf.fit(X_train_scaled, y_train)
        
        y_train_pred = clf.predict(X_train_scaled)
        y_test_pred = clf.predict(X_test_scaled)
        
        train_acc = accuracy_score(y_train, y_train_pred)
        test_acc = accuracy_score(y_test, y_test_pred)
        train_f1 = f1_score(y_train, y_train_pred, average="weighted")
        test_f1 = f1_score(y_test, y_test_pred, average="weighted")
        train_rec = recall_score(y_train, y_train_pred, average="weighted")
        test_rec = recall_score(y_test, y_test_pred, average="weighted")
        train_prec = precision_score(y_train, y_train_pred, average="weighted")
        test_prec = precision_score(y_test, y_test_pred, average="weighted")
        
        train_acc_history.append(train_acc)
        test_acc_history.append(test_acc)
        train_f1_history.append(train_f1)
        test_f1_history.append(test_f1)
        train_recall_history.append(train_rec)
        test_recall_history.append(test_rec)
        train_precision_history.append(train_prec)
        test_precision_history.append(test_prec)
        
        print(f"n_estimators={n_est}: Train Acc={train_acc:.4f}, Test Acc={test_acc:.4f}, Train F1={train_f1:.4f}, Test F1={test_f1:.4f}")
    
    final_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )
    final_clf.fit(X_train_scaled, y_train)
    y_test_pred = final_clf.predict(X_test_scaled)
    
    train_accuracy = train_acc_history[-1]
    test_accuracy = test_acc_history[-1]
    train_f1 = train_f1_history[-1]
    test_f1 = test_f1_history[-1]
    train_recall = train_recall_history[-1]
    test_recall = test_recall_history[-1]
    train_precision = precision_score(y_train, final_clf.predict(X_train_scaled), average="weighted")
    test_precision = precision_score(y_test, y_test_pred, average="weighted")
    
    print(f"\nFinal Training Accuracy: {train_accuracy:.4f}")
    print(f"Final Test Accuracy: {test_accuracy:.4f}")
    print(f"Final Training F1: {train_f1:.4f}")
    print(f"Final Test F1: {test_f1:.4f}")
    print(f"Final Training Recall: {train_recall:.4f}")
    print(f"Final Test Recall: {test_recall:.4f}")
    print(f"Final Training Precision: {train_precision:.4f}")
    print(f"Final Test Precision: {test_precision:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_test_pred, target_names=le_target.classes_))
    
    return {
        "model": final_clf,
        "scaler": scaler,
        "label_encoder": le_target,
        "feature_cols": feature_cols,
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "train_f1": train_f1,
        "test_f1": test_f1,
        "train_recall": train_recall,
        "test_recall": test_recall,
        "train_precision": train_precision,
        "test_precision": test_precision,
        "y_test": y_test,
        "y_test_pred": y_test_pred,
        "classes": le_target.classes_,
        "train_acc_history": train_acc_history,
        "test_acc_history": test_acc_history,
        "train_f1_history": train_f1_history,
        "test_f1_history": test_f1_history,
        "train_recall_history": train_recall_history,
        "test_recall_history": test_recall_history,
        "train_precision_history": train_precision_history,
        "test_precision_history": test_precision_history,
        "n_estimators_list": n_estimators_list,
    }

def generate_metrics_graphs(results):
    n_estimators = results.get("n_estimators_list", list(range(10, 101, 10)))
    train_acc = results.get("train_acc_history", [results["train_accuracy"]] * 10)
    test_acc = results.get("test_acc_history", [results["test_accuracy"]] * 10)
    train_f1 = results.get("train_f1_history", [results["train_f1"]] * 10)
    test_f1 = results.get("test_f1_history", [results["test_f1"]] * 10)
    train_recall = results.get("train_recall_history", [results["train_recall"]] * 10)
    test_recall = results.get("test_recall_history", [results["test_recall"]] * 10)
    
    min_val = min(min(train_acc), min(test_acc), min(train_f1), min(test_f1), min(train_recall), min(test_recall))
    max_val = max(max(train_acc), max(test_acc), max(train_f1), max(test_f1), max(train_recall), max(test_recall))
    y_range = max_val - min_val
    y_min = max(0.0, min_val - y_range * 0.1)
    y_max = min(1.0, max_val + y_range * 0.1)
    
    plt.figure(figsize=(12, 7))
    plt.plot(n_estimators, train_acc, marker="o", label="Train Accuracy", color="#22c55e", linewidth=3, markersize=8, linestyle="-")
    plt.plot(n_estimators, test_acc, marker="s", label="Test Accuracy", color="#3b82f6", linewidth=3, markersize=8, linestyle="--")
    plt.xlabel("Number of Trees (n_estimators)", fontsize=13, fontweight="bold")
    plt.ylabel("Accuracy Score", fontsize=13, fontweight="bold")
    plt.title("Cost Optimization Model - Accuracy Over Training", fontsize=15, fontweight="bold", pad=15)
    plt.legend(fontsize=12, loc="lower right", framealpha=0.9)
    plt.grid(True, alpha=0.4, linestyle=":", linewidth=1)
    plt.ylim([y_min, y_max])
    plt.xlim([min(n_estimators) - 2, max(n_estimators) + 2])
    plt.xticks(n_estimators, fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    path_acc = os.path.join(reports_dir, "optimization_model_accuracy.png")
    plt.savefig(path_acc, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved accuracy graph: {path_acc}")
    
    plt.figure(figsize=(12, 7))
    plt.plot(n_estimators, train_f1, marker="^", label="Train F1", color="#f59e0b", linewidth=3, markersize=8, linestyle="-")
    plt.plot(n_estimators, test_f1, marker="v", label="Test F1", color="#ef4444", linewidth=3, markersize=8, linestyle="--")
    plt.xlabel("Number of Trees (n_estimators)", fontsize=13, fontweight="bold")
    plt.ylabel("F1 Score (Weighted)", fontsize=13, fontweight="bold")
    plt.title("Cost Optimization Model - F1 Score Over Training", fontsize=15, fontweight="bold", pad=15)
    plt.legend(fontsize=12, loc="lower right", framealpha=0.9)
    plt.grid(True, alpha=0.4, linestyle=":", linewidth=1)
    plt.ylim([y_min, y_max])
    plt.xlim([min(n_estimators) - 2, max(n_estimators) + 2])
    plt.xticks(n_estimators, fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    path_f1 = os.path.join(reports_dir, "optimization_model_f1.png")
    plt.savefig(path_f1, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved F1 graph: {path_f1}")
    
    plt.figure(figsize=(12, 7))
    plt.plot(n_estimators, train_recall, marker="D", label="Train Recall", color="#8b5cf6", linewidth=3, markersize=8, linestyle="-")
    plt.plot(n_estimators, test_recall, marker="X", label="Test Recall", color="#ec4899", linewidth=3, markersize=8, linestyle="--")
    plt.xlabel("Number of Trees (n_estimators)", fontsize=13, fontweight="bold")
    plt.ylabel("Recall Score (Weighted)", fontsize=13, fontweight="bold")
    plt.title("Cost Optimization Model - Recall Over Training", fontsize=15, fontweight="bold", pad=15)
    plt.legend(fontsize=12, loc="lower right", framealpha=0.9)
    plt.grid(True, alpha=0.4, linestyle=":", linewidth=1)
    plt.ylim([y_min, y_max])
    plt.xlim([min(n_estimators) - 2, max(n_estimators) + 2])
    plt.xticks(n_estimators, fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    path_recall = os.path.join(reports_dir, "optimization_model_recall.png")
    plt.savefig(path_recall, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved recall graph: {path_recall}")
    
    return {
        "accuracy": path_acc,
        "f1": path_f1,
        "recall": path_recall,
    }

def save_model_run(results):
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(backend_root), "cloudcost.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO optimization_model_runs (model_name, window_minutes, provider, created_at)
            VALUES (?, ?, ?, ?)
        """, ("cost_optimization_rf", 0, "all", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"Saved model run to database")
    except Exception as e:
        print(f"Note: Could not save to database (this is optional): {e}")

def main():
    print("=" * 60)
    print("Cost Optimization Model Training")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        results = train_model()
        print("\nGenerating metrics graphs...")
        graph_paths = generate_metrics_graphs(results)
        print("\nGraphs generated successfully!")
        
        print("\nSaving model run to database...")
        save_model_run(results)
        
        print("\n" + "=" * 60)
        print("Training completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

