# ============================================================
#  app.py  —  Flask Web Server
#  Student Performance Prediction System
#
#  LOCAL:   python app.py  →  http://localhost:5000
#  RENDER:  Set DATABASE_URL env var → PostgreSQL mode
# ============================================================

import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, render_template, request, jsonify
from modules.data_loader   import load_csv, get_student_record, get_csv_hash, FEATURE_COLUMNS, TARGET_COLUMN
from modules.model_trainer import train_model
from modules.predictor     import predict_student, SUBJECT_MAP
import db

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app      = Flask(__name__)
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "students.csv")
SUBJECTS = ["Maths", "English", "Science", "Kannada", "Hindi"]

# ── Init DB on Render, seed from CSV on first deploy ────────
if db.USE_DB:
    logger.info("PostgreSQL mode — initialising...")
    db.init_db()
    db.seed_db_from_csv(CSV_PATH)
else:
    logger.info("Local CSV mode.")

# ── Load data + train model ──────────────────────────────────
def _load_df():
    raw = db.load_all(CSV_PATH)
    raw = raw.dropna(subset=[TARGET_COLUMN])
    raw[FEATURE_COLUMNS] = raw[FEATURE_COLUMNS].fillna(raw[FEATURE_COLUMNS].median())
    return raw

logger.info("Loading dataset and preparing model...")
df       = _load_df()
csv_hash = get_csv_hash(CSV_PATH)
clf, le, accuracy = train_model(df, csv_hash)
logger.info(f"Model ready. Students: {len(df)}  Accuracy: {accuracy*100:.2f}%")


def _reload_model():
    global df, csv_hash, clf, le, accuracy
    df       = _load_df()
    csv_hash = get_csv_hash(CSV_PATH)
    clf, le, accuracy = train_model(df, csv_hash, force_retrain=True)


def _compute_performance(marks):
    avgs = []
    for s in SUBJECTS:
        a, i, e = marks[s]
        avgs.append(((a/25)*100 + (i/50)*100 + e) / 3)
    overall = sum(avgs) / len(avgs)
    if   overall >= 80: perf = "Good"
    elif overall >= 65: perf = "Average"
    elif overall >= 50: perf = "Bad"
    else:               perf = "Fail"
    return overall, perf


def _validate_marks(data):
    marks = {}
    for s in SUBJECTS:
        try:
            a = float(data.get(f"assign_{s}", 0))
            i = float(data.get(f"internal_{s}", 0))
            e = float(data.get(f"exam_{s}", 0))
        except (TypeError, ValueError):
            return None, (jsonify({"status": "error", "message": f"Invalid marks for {s}."}), 400)
        if not (0 <= a <= 25):
            return None, (jsonify({"status": "error", "message": f"{s} Assignment must be 0-25."}), 400)
        if not (0 <= i <= 50):
            return None, (jsonify({"status": "error", "message": f"{s} Internal must be 0-50."}), 400)
        if not (0 <= e <= 100):
            return None, (jsonify({"status": "error", "message": f"{s} Exam must be 0-100."}), 400)
        marks[s] = (a, i, e)
    return marks, None


# ── Routes ───────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/students")
def students():
    return jsonify(sorted(df["Student_Name"].tolist()))


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"status": "error", "message": "Please enter a student name."}), 400
    row = get_student_record(df, name)
    if row is None:
        return jsonify({"status": "not_found",
                        "message": f'No student named "{name}" found in the database.',
                        "hint": "Check the spelling or browse the student list below."}), 404
    result = predict_student(row, clf, le)
    return jsonify({
        "status":       "ok",
        "name":         result["name"],
        "category":     result["category"],
        "confidence":   result["confidence"],
        "overall_avg":  result["overall_avg"],
        "overall_pct":  result["overall_pct"],
        "attendance":   result["attendance"],
        "subject_scores": {
            subj: {"assignment": sc["assignment"], "internal": sc["internal"],
                   "exam": sc["exam"], "total": sc["total"],
                   "percent": sc["percent"], "grade": sc["grade"]}
            for subj, sc in result["subject_scores"].items()
        },
        "weak_subjects":  result["weak_subjects"],
        "overview":       result["suggestion_data"]["overview"],
        "headline":       result["suggestion_data"]["headline"],
        "action_plan":    result["suggestion_data"]["action_plan"],
        "parent_note":    result["suggestion_data"]["parent_note"],
        "subject_tips":   result["subject_tips"],
    })


@app.route("/stats")
def stats():
    counts = df["Performance"].value_counts().to_dict()
    return jsonify({
        "total":    len(df),
        "accuracy": round(accuracy * 100, 2),
        "distribution": {
            "Good":    counts.get("Good",    0),
            "Average": counts.get("Average", 0),
            "Bad":     counts.get("Bad",     0),
            "Fail":    counts.get("Fail",    0),
        }
    })


@app.route("/add_student", methods=["POST"])
def add_student():
    data       = request.get_json(force=True)
    name       = str(data.get("name", "")).strip()
    roll       = str(data.get("roll", "")).strip()
    attendance = data.get("attendance")

    if not name:
        return jsonify({"status": "error", "message": "Student name is required."}), 400
    try:
        attendance = float(attendance)
        if not (0 <= attendance <= 100):
            raise ValueError("Attendance must be 0-100.")
    except (TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    marks, err = _validate_marks(data)
    if err: return err

    if roll and db.roll_exists(roll, CSV_PATH):
        return jsonify({"status": "error",
                        "message": f"Roll Number '{roll}' is already taken."}), 400

    overall, perf = _compute_performance(marks)
    row_dict = {"Student_Name": name, "Roll_Number": roll, "Attendance": attendance}
    for s in SUBJECTS:
        a, i, e = marks[s]
        row_dict[f"Assignment_{s}"] = a
        row_dict[f"Internal_{s}"]   = i
        row_dict[f"Exam_{s}"]       = e
    row_dict["Performance"] = perf

    db.insert_student(row_dict, CSV_PATH)
    _reload_model()
    return jsonify({"status": "ok", "message": f"Student '{name}' added successfully.",
                    "performance": perf, "overall": round(overall, 1), "total": len(df)})


@app.route("/all_students")
def all_students():
    return jsonify(db.get_all_records(CSV_PATH))


@app.route("/edit_student", methods=["POST"])
def edit_student():
    data          = request.get_json(force=True)
    original_name = str(data.get("original_name", "")).strip()
    original_roll = str(data.get("original_roll", "")).strip()
    name          = str(data.get("name", "")).strip()
    roll          = str(data.get("roll", "")).strip()
    attendance    = data.get("attendance")

    if not name:
        return jsonify({"status": "error", "message": "Student name is required."}), 400
    try:
        attendance = float(attendance)
        if not (0 <= attendance <= 100):
            raise ValueError("Attendance must be 0-100.")
    except (TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    marks, err = _validate_marks(data)
    if err: return err

    if roll and roll != original_roll and db.roll_exists(roll, CSV_PATH, exclude_roll=original_roll):
        return jsonify({"status": "error",
                        "message": f"Roll Number '{roll}' is already taken."}), 400

    overall, perf = _compute_performance(marks)
    row_dict = {"Student_Name": name, "Roll_Number": roll, "Attendance": attendance}
    for s in SUBJECTS:
        a, i, e = marks[s]
        row_dict[f"Assignment_{s}"] = a
        row_dict[f"Internal_{s}"]   = i
        row_dict[f"Exam_{s}"]       = e
    row_dict["Performance"] = perf

    found = db.update_student(original_name, original_roll, row_dict, CSV_PATH)
    if not found:
        return jsonify({"status": "error", "message": "Student not found."}), 404

    _reload_model()
    return jsonify({"status": "ok", "message": f"Student '{name}' updated successfully.",
                    "performance": perf})


@app.route("/delete_student", methods=["POST"])
def delete_student():
    data = request.get_json(force=True)
    name = str(data.get("name", "")).strip()
    roll = str(data.get("roll", "")).strip()

    found = db.delete_student(name, roll, CSV_PATH)
    if not found:
        return jsonify({"status": "error", "message": "Student not found."}), 404

    _reload_model()
    return jsonify({"status": "ok", "message": f"Student '{name}' deleted successfully.",
                    "total": len(df)})


# ── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  🎓  Student Performance Predictor — Web App")
    print("="*55)
    print(f"  Open in browser  →  http://localhost:5000")
    print(f"  Students loaded  →  {len(df)}")
    print(f"  Model accuracy   →  {accuracy*100:.2f}%")
    print(f"  Storage mode     →  {'PostgreSQL' if db.USE_DB else 'CSV (local)'}")
    print("="*55 + "\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
