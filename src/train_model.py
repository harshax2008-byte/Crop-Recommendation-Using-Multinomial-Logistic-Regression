"""
Crop Recommendation System - Training & Evaluation Script
Author: College ML Project
Description: Trains the Multinomial Logistic Regression model using a safe
             Pipeline, evaluates it on test data (Accuracy, Precision, Recall,
             F1-score, Confusion Matrix), saves model artifacts and visualizations.
"""

import os
import json
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# Import our custom modules
from data_loader import load_and_clean_data
from preprocessing import split_data, build_pipeline, FEATURE_COLUMNS

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
PIPELINE_PATH = os.path.join(MODELS_DIR, "crop_pipeline.joblib")
METRICS_PATH = os.path.join(MODELS_DIR, "model_metrics.json")
CONFUSION_MATRIX_PATH = os.path.join(MODELS_DIR, "confusion_matrix.png")


def train_and_evaluate():
    print("=" * 65)
    print(" CROP RECOMMENDATION SYSTEM - MODEL TRAINING & EVALUATION")
    print(" Algorithm: Multinomial Logistic Regression (MLR)")
    print("=" * 65)

    os.makedirs(MODELS_DIR, exist_ok=True)

    # 1. Load data
    print("\n[Step 1/5] Loading & Cleaning Dataset...")
    df = load_and_clean_data()

    # 2. Split data
    print("\n[Step 2/5] Performing Stratified Train-Test Split (80/20)...")
    X_train, X_test, y_train, y_test = split_data(df, test_size=0.2, random_state=42)

    # 3. Build & Train Pipeline
    print("\n[Step 3/5] Building Pipeline (StandardScaler + Multinomial LogisticRegression)...")
    pipeline = build_pipeline(random_state=42, max_iter=1000)

    print("Training Multinomial Logistic Regression model on training data...")
    pipeline.fit(X_train, y_train)
    print("Model training completed successfully!")

    # 4. Evaluate on Unseen Test Data
    print("\n[Step 4/5] Evaluating on Test Data (440 samples)...")
    y_pred = pipeline.predict(X_test)
    classes = sorted(list(pipeline.classes_))

    # Calculate metrics
    acc = accuracy_score(y_test, y_pred)
    prec_weighted = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec_weighted = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

    cm = confusion_matrix(y_test, y_pred, labels=classes)
    report_dict = classification_report(y_test, y_pred, labels=classes, output_dict=True, zero_division=0)
    report_str = classification_report(y_test, y_pred, labels=classes, zero_division=0)

    print("-" * 65)
    print(f" MODEL EVALUATION METRICS:")
    print("-" * 65)
    print(f" Accuracy : {acc * 100:.2f}%")
    print(f" Precision (Weighted) : {prec_weighted * 100:.2f}%  |  (Macro) : {prec_macro * 100:.2f}%")
    print(f" Recall    (Weighted) : {rec_weighted * 100:.2f}%  |  (Macro) : {rec_macro * 100:.2f}%")
    print(f" F1-Score  (Weighted) : {f1_weighted * 100:.2f}%  |  (Macro) : {f1_macro * 100:.2f}%")
    print("-" * 65)
    print("\nDETAILED CLASSIFICATION REPORT:\n")
    print(report_str)

    # 5. Save Artifacts & Visualizations
    print("\n[Step 5/5] Saving Model Artifacts & Visualizations...")

    # Save trained pipeline
    joblib.dump(pipeline, PIPELINE_PATH)
    print(f" Saved trained pipeline to: {PIPELINE_PATH}")

    # Save metrics JSON
    metrics_summary = {
        "algorithm": "Multinomial Logistic Regression",
        "solver": "lbfgs",
        "scaler": "StandardScaler",
        "test_size": 0.2,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(float(acc), 4),
        "precision_weighted": round(float(prec_weighted), 4),
        "recall_weighted": round(float(rec_weighted), 4),
        "f1_score_weighted": round(float(f1_weighted), 4),
        "precision_macro": round(float(prec_macro), 4),
        "recall_macro": round(float(rec_macro), 4),
        "f1_score_macro": round(float(f1_macro), 4),
        "classes": classes,
        "features": FEATURE_COLUMNS,
        "classification_report": report_dict
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=4)
    print(f" Saved evaluation metrics to: {METRICS_PATH}")

    # Generate and save Confusion Matrix Plot
    plt.figure(figsize=(14, 11))
    sns.set_theme(style="white")
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="YlGnBu",
        xticklabels=classes,
        yticklabels=classes,
        cbar=True,
        linewidths=0.5
    )
    plt.title("Confusion Matrix - Multinomial Logistic Regression (Crop Recommendation)", fontsize=14, pad=15)
    plt.xlabel("Predicted Crop", fontsize=12, labelpad=10)
    plt.ylabel("Actual Crop", fontsize=12, labelpad=10)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=300)
    plt.close()
    print(f" Saved confusion matrix heatmap to: {CONFUSION_MATRIX_PATH}")

    print("\n" + "=" * 65)
    print(" ALL TRAINING AND EVALUATION TASKS COMPLETED SUCCESSFULLY!")
    print("=" * 65)

    return metrics_summary


if __name__ == "__main__":
    train_and_evaluate()
