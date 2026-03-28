#!/usr/bin/env python3
# ============================================================
#  main.py  —  Entry Point
#  Student Performance Prediction System
#
#  HOW TO RUN:
#      python main.py
#
#  FLOW:
#    1. Load latest CSV data
#    2. Check if model needs retraining (CSV hash comparison)
#    3. Train or reload the model
#    4. Enter interactive loop:
#         a. Teacher enters student name
#         b. System searches CSV
#         c. If found → predict + display full report
#         d. If not found → show helpful error
#         e. Repeat until teacher exits
# ============================================================

import os
import sys
import logging

# ── Set up logging ───────────────────────────────────────────
# Logs go to both console (WARNING+) and a log file (DEBUG+)
LOG_DIR  = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  [%(levelname)-8s]  %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "app.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout)   # console — only WARNING+
    ]
)
# Suppress DEBUG/INFO from console; let the UI handle display
logging.getLogger().handlers[1].setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ── Ensure project root is on the Python path ────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── Import project modules ───────────────────────────────────
try:
    from modules.data_loader   import load_csv, get_student_record, get_csv_hash
    from modules.model_trainer import train_model
    from modules.predictor     import predict_student
    from modules import interface as ui
except ImportError as e:
    print(f"\n[FATAL] Could not import required module: {e}")
    print("Make sure you are running this script from the project root folder.")
    sys.exit(1)


# ── Path to CSV dataset ──────────────────────────────────────
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "students.csv")


# ─────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────

def main():
    """Main application loop."""

    # ── Show banner ──────────────────────────────────────────
    ui.show_banner()

    # ── Step 1: Load CSV dataset ─────────────────────────────
    ui.show_status("Loading student dataset...", "info")
    try:
        df = load_csv(CSV_PATH)
    except FileNotFoundError as e:
        ui.show_status(str(e), "error")
        sys.exit(1)
    except ValueError as e:
        ui.show_status(str(e), "error")
        sys.exit(1)

    # ── Step 2: Get CSV hash for smart caching ───────────────
    csv_hash = get_csv_hash(CSV_PATH)
    logger.info(f"CSV hash: {csv_hash}")

    # ── Step 3: Train or reload model ───────────────────────
    ui.show_status("Checking if model retraining is required...", "info")
    try:
        clf, le, accuracy = train_model(df, csv_hash)
    except Exception as e:
        ui.show_status(f"Model training failed: {e}", "error")
        logger.exception("Model training error")
        sys.exit(1)

    # ── Step 4: Display training summary ─────────────────────
    ui.show_training_summary(accuracy, len(df))

    # ── Step 5: Interactive prediction loop ──────────────────
    while True:
        name = ui.prompt_student_name()

        # Exit conditions
        if name.lower() in ("exit", "quit", "q", ""):
            ui.show_goodbye()
            break

        # ── Search for student in CSV ────────────────────────
        student_row = get_student_record(df, name)

        if student_row is None:
            # Student not in dataset
            ui.show_not_found(name)
        else:
            # ── Predict + display report ─────────────────────
            try:
                result = predict_student(student_row, clf, le)
                ui.display_report(result)
            except Exception as e:
                ui.show_status(f"Prediction error: {e}", "error")
                logger.exception(f"Prediction failed for student: {name}")

        # ── Ask to continue ──────────────────────────────────
        if not ui.ask_continue():
            ui.show_goodbye()
            break


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        ui.show_goodbye()
        sys.exit(0)
