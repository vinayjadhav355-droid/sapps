# ============================================================
#  MODULE 1: data_loader.py
#  Responsibility: Load and validate the CSV dataset
#  This module reads the student data CSV file, checks for
#  missing values, and prepares it for model training.
# ============================================================

import pandas as pd
import os
import logging

# Set up logging so we can track what happens during data loading
logger = logging.getLogger(__name__)


# ── Column definitions ──────────────────────────────────────
# These are the expected columns in the CSV file
REQUIRED_COLUMNS = [
    "Student_Name", "Attendance",
    "Assignment_Maths", "Assignment_English", "Assignment_Science",
    "Assignment_Kannada", "Assignment_Hindi",
    "Internal_Maths", "Internal_English", "Internal_Science",
    "Internal_Kannada", "Internal_Hindi",
    "Exam_Maths", "Exam_English", "Exam_Science",
    "Exam_Kannada", "Exam_Hindi",
    "Performance"
]

# Columns used as input features for the model (exclude name + label)
FEATURE_COLUMNS = [
    "Attendance",
    "Assignment_Maths", "Assignment_English", "Assignment_Science",
    "Assignment_Kannada", "Assignment_Hindi",
    "Internal_Maths", "Internal_English", "Internal_Science",
    "Internal_Kannada", "Internal_Hindi",
    "Exam_Maths", "Exam_English", "Exam_Science",
    "Exam_Kannada", "Exam_Hindi"
]

TARGET_COLUMN = "Performance"


def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load the student CSV file and perform basic validation.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Cleaned dataframe ready for training.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing.
    """

    # ── Step 1: Check if file exists ────────────────────────
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"\n[ERROR] CSV file not found at: {filepath}"
            f"\nPlease make sure 'students.csv' exists inside the 'data/' folder."
        )

    # ── Step 2: Read the CSV ────────────────────────────────
    logger.info(f"Loading dataset from: {filepath}")
    df = pd.read_csv(filepath)

    # ── Step 3: Strip whitespace from column names ──────────
    df.columns = df.columns.str.strip()

    # ── Step 4: Strip whitespace from string values ─────────
    df["Student_Name"] = df["Student_Name"].str.strip()
    df[TARGET_COLUMN]  = df[TARGET_COLUMN].str.strip()

    # ── Step 5: Check all required columns exist ────────────
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"\n[ERROR] Missing columns in CSV: {missing_cols}"
            f"\nExpected columns: {REQUIRED_COLUMNS}"
        )

    # ── Step 6: Handle missing values ───────────────────────
    missing_count = df[FEATURE_COLUMNS].isnull().sum().sum()
    if missing_count > 0:
        logger.warning(
            f"Found {missing_count} missing value(s) in feature columns. "
            "Filling with column median values."
        )
        # Fill numeric missing values with median of each column
        df[FEATURE_COLUMNS] = df[FEATURE_COLUMNS].fillna(
            df[FEATURE_COLUMNS].median()
        )

    # Drop rows where Performance (target) is missing
    before = len(df)
    df = df.dropna(subset=[TARGET_COLUMN])
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} row(s) with missing 'Performance' label.")

    # ── Step 7: Validate Performance labels ─────────────────
    valid_labels = {"Good", "Average", "Bad", "Fail"}
    invalid = df[~df[TARGET_COLUMN].isin(valid_labels)][TARGET_COLUMN].unique()
    if len(invalid) > 0:
        raise ValueError(
            f"\n[ERROR] Invalid Performance labels found: {list(invalid)}"
            f"\nAllowed values: {list(valid_labels)}"
        )

    logger.info(f"Dataset loaded successfully. Total students: {len(df)}")
    return df


def get_student_record(df: pd.DataFrame, student_name: str) -> pd.Series | None:
    """
    Search for a student by name (case-insensitive) in the dataframe.

    Args:
        df (pd.DataFrame): The full student dataset.
        student_name (str): Name entered by the teacher.

    Returns:
        pd.Series | None: The student's row, or None if not found.
    """

    # Normalize both the search query and dataframe names to lowercase
    search_name = student_name.strip().lower()
    match = df[df["Student_Name"].str.lower() == search_name]

    if match.empty:
        return None

    # Return the first matching row (in case of duplicates)
    return match.iloc[0]


def get_feature_row(student_row: pd.Series) -> pd.DataFrame:
    """
    Extract only the feature columns from a student row for prediction.

    Args:
        student_row (pd.Series): A single student's full row.

    Returns:
        pd.DataFrame: Single-row dataframe with only feature columns.
    """
    return student_row[FEATURE_COLUMNS].to_frame().T.reset_index(drop=True)


def get_csv_hash(filepath: str) -> str:
    """
    Compute an MD5 hash of the CSV file contents.
    Used to detect if the CSV has changed since last training.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        str: MD5 hex digest of the file.
    """
    import hashlib
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()
