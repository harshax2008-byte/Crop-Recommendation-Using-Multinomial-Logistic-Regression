"""
Crop Recommendation System - Data Loader Module
Author: College ML Project
Description: Handles dataset loading, fetching (if not locally present),
             and data cleaning / validation.
"""

import os
import urllib.request
import pandas as pd

# Path definitions
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "crop_recommendation.csv")

# Standard verified dataset source (Precision Agriculture / Kaggle Crop Recommendation Dataset)
DATASET_URL = (
    "https://raw.githubusercontent.com/Gladiator07/Harvestify/master/"
    "Data-processed/crop_recommendation.csv"
)

EXPECTED_FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
EXPECTED_COLUMNS = EXPECTED_FEATURES + ["label"]


def ensure_data_exists() -> str:
    """
    Checks if the dataset exists locally. If not, downloads it from the standard source.
    Returns the absolute path to the dataset CSV file.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        print(f"Dataset not found locally. Downloading from authentic repository:\n{DATASET_URL}")
        try:
            urllib.request.urlretrieve(DATASET_URL, DATA_FILE)
            print(f"Dataset downloaded successfully to: {DATA_FILE}")
        except Exception as e:
            raise RuntimeError(
                f"Failed to download dataset from {DATASET_URL}. "
                f"Please manually place 'crop_recommendation.csv' in {DATA_DIR}. Error: {e}"
            )
    else:
        print(f"Dataset found locally at: {DATA_FILE}")

    return DATA_FILE


def load_and_clean_data(file_path: str = None) -> pd.DataFrame:
    """
    Loads the CSV file into a pandas DataFrame and runs data cleaning checks:
      1. Verifies column names match expected features and target.
      2. Handles missing (null) values if present.
      3. Drops duplicate rows if any exist.
      4. Verifies data types of numerical columns.

    Returns:
        pd.DataFrame: Cleaned, validated dataframe.
    """
    if file_path is None:
        file_path = ensure_data_exists()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found at: {file_path}")

    # Step 1: Load CSV
    df = pd.read_csv(file_path)
    print(f"Initial raw dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")

    # Step 2: Validate columns
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    # Keep only the expected columns in standard order
    df = df[EXPECTED_COLUMNS].copy()

    # Step 3: Handle missing values (Data Cleaning)
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    if total_nulls > 0:
        print(f"Notice: Found {total_nulls} missing values. Cleaning missing rows...")
        df = df.dropna().reset_index(drop=True)
    else:
        print("Data Cleaning: Zero missing/null values detected.")

    # Step 4: Handle duplicate records
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        print(f"Notice: Found {dup_count} duplicate rows. Removing duplicates...")
        df = df.drop_duplicates().reset_index(drop=True)
    else:
        print("Data Cleaning: Zero duplicate rows detected.")

    # Step 5: Enforce numeric datatypes for features
    for col in EXPECTED_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop any rows where type conversion produced NaN
    df = df.dropna().reset_index(drop=True)

    # Standardize label strings (trim whitespace, lower case)
    df["label"] = df["label"].astype(str).str.strip().str.lower()

    unique_crops = df["label"].nunique()
    print(f"Data Cleaning Complete: {len(df)} valid records across {unique_crops} unique crops.")

    return df


if __name__ == "__main__":
    print("--- Running Data Loader Self-Check ---")
    data = load_and_clean_data()
    print("\nDataset Info:")
    print(data.info())
    print("\nFirst 5 Samples:")
    print(data.head())
    print("\nCrops present:")
    print(sorted(data["label"].unique()))
