# ============================================================
#  MODULE 2: model_trainer.py
#  Responsibility: Train, save, and reload the ML model
#  Uses Random Forest Classifier from scikit-learn.
#  Implements smart caching: only retrains when CSV changes.
# ============================================================

import os
import pickle
import json
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

from modules.data_loader import FEATURE_COLUMNS, TARGET_COLUMN

logger = logging.getLogger(__name__)


# ── File paths for saved model artefacts ────────────────────
MODEL_DIR        = os.path.join(os.path.dirname(__file__), "..", "model")
MODEL_PATH       = os.path.join(MODEL_DIR, "model.pkl")
ENCODER_PATH     = os.path.join(MODEL_DIR, "label_encoder.pkl")
META_PATH        = os.path.join(MODEL_DIR, "model_meta.json")  # stores csv hash + accuracy


def _save_artefacts(clf: RandomForestClassifier,
                    le: LabelEncoder,
                    csv_hash: str,
                    accuracy: float,
                    report: str) -> None:
    """
    Save the trained model, label encoder, and metadata to disk.

    Args:
        clf: Trained Random Forest model.
        le: Fitted LabelEncoder for the target column.
        csv_hash: MD5 hash of the CSV file at training time.
        accuracy: Model accuracy on the test split.
        report: Full classification report string.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)

    with open(MODEL_PATH,   "wb") as f: pickle.dump(clf, f)
    with open(ENCODER_PATH, "wb") as f: pickle.dump(le,  f)

    meta = {
        "csv_hash":       csv_hash,
        "accuracy":       round(accuracy, 4),
        "feature_columns": FEATURE_COLUMNS,
        "classes":        list(le.classes_),
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Model saved to {MODEL_PATH}")


def _load_artefacts():
    """
    Load saved model and encoder from disk.

    Returns:
        tuple: (RandomForestClassifier, LabelEncoder, dict of metadata)
               Returns (None, None, None) if files don't exist.
    """
    if not all(os.path.exists(p) for p in [MODEL_PATH, ENCODER_PATH, META_PATH]):
        return None, None, None

    with open(MODEL_PATH,   "rb") as f: clf = pickle.load(f)
    with open(ENCODER_PATH, "rb") as f: le  = pickle.load(f)
    with open(META_PATH,    "r")  as f: meta = json.load(f)

    return clf, le, meta


def train_model(df: pd.DataFrame,
                csv_hash: str,
                force_retrain: bool = False):
    """
    Train (or reload) the Random Forest model.

    Smart caching logic:
    - If a saved model exists AND the CSV hash hasn't changed → reload it.
    - If CSV has changed (new data added) OR no model exists → retrain.

    Args:
        df (pd.DataFrame): Full student dataset.
        csv_hash (str): MD5 hash of the current CSV.
        force_retrain (bool): If True, always retrain regardless of cache.

    Returns:
        tuple: (trained_clf, label_encoder, accuracy_float)
    """

    # ── Check cache ──────────────────────────────────────────
    if not force_retrain:
        clf, le, meta = _load_artefacts()
        if clf is not None and meta is not None:
            if meta.get("csv_hash") == csv_hash:
                acc = meta.get("accuracy", 0.0)
                logger.info(
                    f"CSV unchanged. Reloading cached model "
                    f"(accuracy: {acc*100:.2f}%)."
                )
                return clf, le, acc
            else:
                logger.info("CSV has changed. Retraining model on updated data...")

    # ── Prepare features and target ──────────────────────────
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    # Encode string labels → integers (Required by sklearn)
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # ── Train/test split (80% train, 20% test) ───────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded   # ensures balanced split across all categories
    )

    # ── Train Random Forest ──────────────────────────────────
    logger.info("Training Random Forest Classifier...")
    clf = RandomForestClassifier(
        n_estimators=200,     # 200 decision trees for stability
        max_depth=10,         # prevent overfitting
        min_samples_split=2,
        random_state=42,
        n_jobs=-1             # use all CPU cores
    )
    clf.fit(X_train, y_train)

    # ── Evaluate ─────────────────────────────────────────────
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report   = classification_report(
        y_test, y_pred,
        target_names=le.classes_,
        zero_division=0
    )

    logger.info(f"Training complete. Test Accuracy: {accuracy * 100:.2f}%")
    logger.debug(f"\nClassification Report:\n{report}")

    # ── Save to disk ─────────────────────────────────────────
    _save_artefacts(clf, le, csv_hash, accuracy, report)

    return clf, le, accuracy
