"""
Crop Recommendation System - Preprocessing & Pipeline Module
Author: College ML Project
Description: Handles feature/target separation, train-test splitting,
             and scikit-learn Pipeline construction combining feature
             scaling (StandardScaler) with Random Forest + Logistic Regression ensemble.
"""

from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET_COLUMN = "label"


def separate_features_and_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separates the input features (X) from the target class labels (y).
    """
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y


def split_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Splits the dataset into training (80%) and testing (20%) sets.
    Uses 'stratify=y' to guarantee that every crop class is evenly represented
    in both training and testing partitions, preventing class imbalance.
    """
    X, y = separate_features_and_target(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )

    print(f"Data Split Complete:")
    print(f"  Training samples: {len(X_train)} ({(1-test_size)*100:.0f}%)")
    print(f"  Testing samples:  {len(X_test)} ({test_size*100:.0f}%)")
    print(f"  Total classes:    {y.nunique()}")

    return X_train, X_test, y_train, y_test


def build_pipeline(random_state: int = 42, max_iter: int = 2000) -> Pipeline:
    """
    Builds a robust, production-safe scikit-learn Pipeline.

    Architecture:
      Step 1: StandardScaler
              Z-score normalization: z = (x - mean) / std.

      Step 2: VotingClassifier (Soft Voting Ensemble)
              - RandomForestClassifier: 300 trees, robust feature-based model
              - Multinomial LogisticRegression: lbfgs solver, Softmax probabilities
              - GradientBoostingClassifier: boosted ensemble for edge cases
              Soft voting averages the class probabilities, producing confident
              and well-calibrated predictions across all 22+ crop classes.
    """
    # Build sub-classifiers for ensemble
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1
    )

    lr = LogisticRegression(
        solver="lbfgs",
        max_iter=max_iter,
        C=10.0,
        class_weight="balanced",
        random_state=random_state
    )

    gb = GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8,
        random_state=random_state
    )

    # Voting ensemble with soft probability averaging
    ensemble = VotingClassifier(
        estimators=[
            ("rf", rf),
            ("lr", lr),
            ("gb", gb),
        ],
        voting="soft",
        weights=[3, 1, 2]  # Weight RF highest, then GB, then LR
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", ensemble)
    ])
    return pipeline


if __name__ == "__main__":
    from data_loader import load_and_clean_data

    print("--- Running Preprocessing Pipeline Test ---")
    data = load_and_clean_data()
    X_tr, X_te, y_tr, y_te = split_data(data)
    pipe = build_pipeline()
    print("\nPipeline Architecture:")
    print(pipe)
