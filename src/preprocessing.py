"""
Crop Recommendation System - Preprocessing & Pipeline Module
Author: College ML Project
Description: Handles feature/target separation, train-test splitting,
             and scikit-learn Pipeline construction combining feature
             scaling (StandardScaler) with Multinomial Logistic Regression.
"""

from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

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


def build_pipeline(random_state: int = 42, max_iter: int = 1000) -> Pipeline:
    """
    Builds a robust, production-safe scikit-learn Pipeline.

    Architecture:
      Step 1: StandardScaler
              Z-score normalization: z = (x - mean) / std.
              Crucial for Logistic Regression because features like Rainfall (0-300mm)
              and pH (3-10) have vastly different scales. Without scaling, larger
              magnitude features disproportionately dominate the gradient optimization.

      Step 2: LogisticRegression(multi_class='multinomial', solver='lbfgs')
              Configured specifically for MULTINOMIAL multiclass classification.
              Applies the Softmax function directly across all 22 crop classes,
              producing valid, well-calibrated class probabilities that sum to 1.
    """
    # In modern scikit-learn (>=1.8), solver='lbfgs' inherently optimizes multinomial loss.
    # We maintain backward compatibility for older scikit-learn versions where multi_class was an explicit argument.
    import inspect
    clf_kwargs = {
        "solver": "lbfgs",
        "max_iter": max_iter,
        "random_state": random_state
    }
    if "multi_class" in inspect.signature(LogisticRegression.__init__).parameters:
        clf_kwargs["multi_class"] = "multinomial"

    pipeline = Pipeline([
        (
            "scaler",
            StandardScaler()
        ),
        (
            "classifier",
            LogisticRegression(**clf_kwargs)
        )
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
