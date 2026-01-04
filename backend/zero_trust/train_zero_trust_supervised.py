import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_curve, precision_recall_curve, auc, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight


def main() -> None:
    root = os.path.dirname(__file__)
    train_path = os.path.join(root, "password_security_train.csv")
    test_path = os.path.join(root, "password_security_test.csv")
    if not os.path.exists(train_path) or not os.path.exists(test_path):
        return
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    if train.empty or test.empty:
        return
    if "risk_label" not in train.columns or "risk_label" not in test.columns:
        return
    X_train = train.drop(columns=["risk_label", "used_special_characters", "keyboard_language", "was_capslock_on", "timezone"])
    y_train = train["risk_label"].astype(int)
    X_test = test.drop(columns=["risk_label", "used_special_characters", "keyboard_language", "was_capslock_on", "timezone"])
    y_test = test["risk_label"].astype(int)
    if y_train.nunique() < 2 or y_test.nunique() < 2:
        return
    X_train = X_train.astype(float).fillna(0.0)
    X_test = X_test.astype(float).fillna(0.0)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    class_weights = compute_class_weight('balanced', classes=np.array([0, 1]), y=y_train)
    class_weight_dict = {0: class_weights[0], 1: class_weights[1]}
    
    clf = SGDClassifier(loss="log_loss", penalty="l2", max_iter=1, learning_rate="optimal", random_state=42, warm_start=True, class_weight=class_weight_dict)
    epochs = 30
    train_acc = []
    test_acc = []
    train_loss = []
    test_loss = []
    train_f1 = []
    test_f1 = []
    for epoch in range(epochs):
        if epoch == 0:
            clf.partial_fit(X_train_scaled, y_train, classes=np.array([0, 1]))
        else:
            clf.partial_fit(X_train_scaled, y_train)
        y_train_pred = clf.predict(X_train_scaled)
        y_test_pred = clf.predict(X_test_scaled)
        y_train_prob = clf.predict_proba(X_train_scaled)
        y_test_prob = clf.predict_proba(X_test_scaled)
        train_acc.append(accuracy_score(y_train, y_train_pred))
        test_acc.append(accuracy_score(y_test, y_test_pred))
        train_loss.append(log_loss(y_train, y_train_prob, labels=[0, 1]))
        test_loss.append(log_loss(y_test, y_test_prob, labels=[0, 1]))
        train_f1.append(f1_score(y_train, y_train_pred, zero_division=0))
        test_f1.append(f1_score(y_test, y_test_pred, zero_division=0))
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(root)), "reports", "model_metrics")
    os.makedirs(reports_dir, exist_ok=True)
    epochs_axis = list(range(1, epochs + 1))
    plt.figure(figsize=(10, 4))
    plt.plot(epochs_axis, train_loss, marker="o", label="train")
    plt.plot(epochs_axis, test_loss, marker="o", label="test")
    plt.xlabel("Epoch")
    plt.ylabel("Log loss")
    plt.title("Zero trust training loss")
    plt.legend()
    plt.tight_layout()
    path_loss = os.path.join(reports_dir, "zero_trust_train_loss.png")
    plt.savefig(path_loss)
    plt.close()
    plt.figure(figsize=(10, 4))
    plt.plot(epochs_axis, train_acc, marker="o", label="train")
    plt.plot(epochs_axis, test_acc, marker="o", label="test")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Zero trust accuracy over epochs")
    plt.legend()
    plt.tight_layout()
    path_acc = os.path.join(reports_dir, "zero_trust_train_accuracy.png")
    plt.savefig(path_acc)
    plt.close()
    plt.figure(figsize=(10, 4))
    plt.plot(epochs_axis, train_f1, marker="o", label="train")
    plt.plot(epochs_axis, test_f1, marker="o", label="test")
    plt.xlabel("Epoch")
    plt.ylabel("F1")
    plt.title("Zero trust F1 over epochs")
    plt.legend()
    plt.tight_layout()
    path_f1 = os.path.join(reports_dir, "zero_trust_train_f1.png")
    plt.savefig(path_f1)
    plt.close()
    final_train_acc = accuracy_score(y_train, y_train_pred)
    final_test_acc = accuracy_score(y_test, y_test_pred)
    final_train_f1 = f1_score(y_train, y_train_pred, zero_division=0)
    final_test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
    
    print(f"Final Training Accuracy: {final_train_acc:.4f}")
    print(f"Final Test Accuracy: {final_test_acc:.4f}")
    print(f"Final Training F1: {final_train_f1:.4f}")
    print(f"Final Test F1: {final_test_f1:.4f}")
    
    y_test_prob = clf.predict_proba(X_test_scaled)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_test_prob)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(6, 6))
    plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("Zero trust ROC curve (supervised)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    path_roc = os.path.join(reports_dir, "zero_trust_supervised_roc.png")
    plt.savefig(path_roc)
    plt.close()
    pr_precision, pr_recall, _ = precision_recall_curve(y_test, y_test_prob)
    pr_auc = auc(pr_recall, pr_precision)
    plt.figure(figsize=(6, 6))
    plt.plot(pr_recall, pr_precision, label=f"AUC = {pr_auc:.3f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Zero trust precision–recall curve (supervised)")
    plt.legend(loc="lower left")
    plt.tight_layout()
    path_pr = os.path.join(reports_dir, "zero_trust_supervised_pr.png")
    plt.savefig(path_pr)
    plt.close()


if __name__ == "__main__":
    main()


