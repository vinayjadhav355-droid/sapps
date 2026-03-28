# ============================================================
#  db.py  —  Database Abstraction Layer
#
#  Works in TWO modes automatically:
#  - LOCAL:  DATABASE_URL not set → reads/writes CSV file
#  - RENDER: DATABASE_URL is set  → reads/writes PostgreSQL
#
#  App code never needs to know which mode it's in.
# ============================================================

import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Fix Render's postgres:// → postgresql:// (psycopg2 requires postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_DB = bool(DATABASE_URL)


# ── Column order (must match CSV exactly) ────────────────────
SUBJECTS  = ["Maths", "English", "Science", "Kannada", "Hindi"]
ALL_COLS  = (
    ["Student_Name", "Roll_Number", "Attendance"] +
    [f"Assignment_{s}" for s in SUBJECTS] +
    [f"Internal_{s}"   for s in SUBJECTS] +
    [f"Exam_{s}"       for s in SUBJECTS] +
    ["Performance"]
)


# ─────────────────────────────────────────────────────────────
#  PostgreSQL helpers
# ─────────────────────────────────────────────────────────────

def _get_conn():
    """Open a new PostgreSQL connection."""
    import psycopg2
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    """
    Create the students table if it doesn't exist yet.
    Called once at app startup when DATABASE_URL is set.
    """
    if not USE_DB:
        return
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id               SERIAL PRIMARY KEY,
            student_name     TEXT NOT NULL,
            roll_number      TEXT UNIQUE,
            attendance       FLOAT,
            assignment_maths   FLOAT, assignment_english FLOAT,
            assignment_science FLOAT, assignment_kannada FLOAT,
            assignment_hindi   FLOAT,
            internal_maths     FLOAT, internal_english   FLOAT,
            internal_science   FLOAT, internal_kannada   FLOAT,
            internal_hindi     FLOAT,
            exam_maths         FLOAT, exam_english       FLOAT,
            exam_science       FLOAT, exam_kannada       FLOAT,
            exam_hindi         FLOAT,
            performance        TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Database table ready.")


def seed_db_from_csv(csv_path: str):
    """
    On first deploy, copy all CSV rows into PostgreSQL.
    Skips rows whose roll_number already exists in DB.
    """
    if not USE_DB:
        return
    conn = _get_conn()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM students")
    count = cur.fetchone()[0]
    if count > 0:
        logger.info(f"DB already has {count} students — skipping seed.")
        cur.close()
        conn.close()
        return

    df = pd.read_csv(csv_path)
    inserted = 0
    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO students (
                    student_name, roll_number, attendance,
                    assignment_maths, assignment_english, assignment_science,
                    assignment_kannada, assignment_hindi,
                    internal_maths, internal_english, internal_science,
                    internal_kannada, internal_hindi,
                    exam_maths, exam_english, exam_science,
                    exam_kannada, exam_hindi,
                    performance
                ) VALUES (
                    %s,%s,%s,  %s,%s,%s,%s,%s,  %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,  %s
                )
                ON CONFLICT (roll_number) DO NOTHING
            """, (
                str(row.get("Student_Name","")),
                str(row.get("Roll_Number","")) or None,
                float(row.get("Attendance", 0)),
                float(row.get("Assignment_Maths",   0)),
                float(row.get("Assignment_English",  0)),
                float(row.get("Assignment_Science",  0)),
                float(row.get("Assignment_Kannada",  0)),
                float(row.get("Assignment_Hindi",    0)),
                float(row.get("Internal_Maths",      0)),
                float(row.get("Internal_English",    0)),
                float(row.get("Internal_Science",    0)),
                float(row.get("Internal_Kannada",    0)),
                float(row.get("Internal_Hindi",      0)),
                float(row.get("Exam_Maths",          0)),
                float(row.get("Exam_English",        0)),
                float(row.get("Exam_Science",        0)),
                float(row.get("Exam_Kannada",        0)),
                float(row.get("Exam_Hindi",          0)),
                str(row.get("Performance", "")),
            ))
            inserted += 1
        except Exception as e:
            logger.warning(f"Skipped row: {e}")
            conn.rollback()
            continue
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Seeded {inserted} students from CSV into database.")


def _db_to_df() -> pd.DataFrame:
    """Fetch all rows from PostgreSQL and return as a DataFrame."""
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT student_name, roll_number, attendance,
               assignment_maths, assignment_english, assignment_science,
               assignment_kannada, assignment_hindi,
               internal_maths, internal_english, internal_science,
               internal_kannada, internal_hindi,
               exam_maths, exam_english, exam_science,
               exam_kannada, exam_hindi,
               performance
        FROM students
        ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    df = pd.DataFrame(rows, columns=ALL_COLS)
    return df


# ─────────────────────────────────────────────────────────────
#  Public API  (same interface whether CSV or DB)
# ─────────────────────────────────────────────────────────────

def load_all(csv_path: str) -> pd.DataFrame:
    """Load all students. Uses DB if available, else CSV."""
    if USE_DB:
        return _db_to_df()
    return pd.read_csv(csv_path)


def get_all_rolls(csv_path: str) -> list:
    """Return list of all existing roll numbers (strings)."""
    df = load_all(csv_path)
    return df["Roll_Number"].fillna("").astype(str).str.strip().tolist()


def roll_exists(roll: str, csv_path: str, exclude_roll: str = "") -> bool:
    """Check if a roll number is already taken (excluding one roll for edits)."""
    rolls = get_all_rolls(csv_path)
    if exclude_roll:
        rolls = [r for r in rolls if r != exclude_roll]
    return roll in rolls


def insert_student(row_dict: dict, csv_path: str):
    """Insert a new student into DB or append to CSV."""
    if USE_DB:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO students (
                student_name, roll_number, attendance,
                assignment_maths, assignment_english, assignment_science,
                assignment_kannada, assignment_hindi,
                internal_maths, internal_english, internal_science,
                internal_kannada, internal_hindi,
                exam_maths, exam_english, exam_science,
                exam_kannada, exam_hindi,
                performance
            ) VALUES (
                %s,%s,%s,  %s,%s,%s,%s,%s,  %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,  %s
            )
        """, (
            row_dict["Student_Name"],
            row_dict.get("Roll_Number") or None,
            row_dict["Attendance"],
            row_dict["Assignment_Maths"],   row_dict["Assignment_English"],
            row_dict["Assignment_Science"], row_dict["Assignment_Kannada"],
            row_dict["Assignment_Hindi"],
            row_dict["Internal_Maths"],     row_dict["Internal_English"],
            row_dict["Internal_Science"],   row_dict["Internal_Kannada"],
            row_dict["Internal_Hindi"],
            row_dict["Exam_Maths"],         row_dict["Exam_English"],
            row_dict["Exam_Science"],       row_dict["Exam_Kannada"],
            row_dict["Exam_Hindi"],
            row_dict["Performance"],
        ))
        conn.commit()
        cur.close()
        conn.close()
    else:
        existing = pd.read_csv(csv_path)
        if "Roll_Number" not in existing.columns:
            existing.insert(1, "Roll_Number", "")
        new_df  = pd.DataFrame([row_dict])
        updated = pd.concat([existing, new_df], ignore_index=True)
        updated.to_csv(csv_path, index=False)


def update_student(original_name: str, original_roll: str,
                   row_dict: dict, csv_path: str) -> bool:
    """
    Update a student's record. Finds by original_roll (or name if roll blank).
    Returns True if found and updated, False if not found.
    """
    if USE_DB:
        conn = _get_conn()
        cur  = conn.cursor()
        if original_roll and original_roll not in ("", "nan"):
            cur.execute("SELECT id FROM students WHERE roll_number = %s", (original_roll,))
        else:
            cur.execute("SELECT id FROM students WHERE student_name = %s", (original_name,))
        result = cur.fetchone()
        if not result:
            cur.close(); conn.close()
            return False
        sid = result[0]
        cur.execute("""
            UPDATE students SET
                student_name=%s, roll_number=%s, attendance=%s,
                assignment_maths=%s, assignment_english=%s, assignment_science=%s,
                assignment_kannada=%s, assignment_hindi=%s,
                internal_maths=%s, internal_english=%s, internal_science=%s,
                internal_kannada=%s, internal_hindi=%s,
                exam_maths=%s, exam_english=%s, exam_science=%s,
                exam_kannada=%s, exam_hindi=%s,
                performance=%s
            WHERE id=%s
        """, (
            row_dict["Student_Name"],
            row_dict.get("Roll_Number") or None,
            row_dict["Attendance"],
            row_dict["Assignment_Maths"],   row_dict["Assignment_English"],
            row_dict["Assignment_Science"], row_dict["Assignment_Kannada"],
            row_dict["Assignment_Hindi"],
            row_dict["Internal_Maths"],     row_dict["Internal_English"],
            row_dict["Internal_Science"],   row_dict["Internal_Kannada"],
            row_dict["Internal_Hindi"],
            row_dict["Exam_Maths"],         row_dict["Exam_English"],
            row_dict["Exam_Science"],       row_dict["Exam_Kannada"],
            row_dict["Exam_Hindi"],
            row_dict["Performance"],
            sid,
        ))
        conn.commit()
        cur.close(); conn.close()
        return True
    else:
        existing = pd.read_csv(csv_path)
        if "Roll_Number" not in existing.columns:
            existing.insert(1, "Roll_Number", "")
        norm_rolls = existing["Roll_Number"].fillna("").astype(str).str.strip()
        norm_names = existing["Student_Name"].fillna("").astype(str).str.strip()
        mask = (norm_names == original_name) & (norm_rolls == original_roll)
        if not mask.any():
            if not original_roll or original_roll in ("", "nan"):
                mask = norm_names == original_name
        if not mask.any():
            return False
        idx = existing[mask].index[0]
        for k, v in row_dict.items():
            existing.at[idx, k] = v
        existing.to_csv(csv_path, index=False)
        return True


def delete_student(name: str, roll: str, csv_path: str) -> bool:
    """
    Delete a student by roll number.
    Returns True if deleted, False if not found.
    """
    if USE_DB:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            "DELETE FROM students WHERE roll_number=%s AND student_name=%s",
            (roll, name)
        )
        deleted = cur.rowcount
        conn.commit()
        cur.close(); conn.close()
        return deleted > 0
    else:
        existing = pd.read_csv(csv_path)
        if "Roll_Number" not in existing.columns:
            existing.insert(1, "Roll_Number", "")
        norm_rolls = existing["Roll_Number"].fillna("").astype(str).str.strip()
        norm_names = existing["Student_Name"].fillna("").astype(str).str.strip()
        mask = (norm_names == name) & (norm_rolls == roll)
        if not mask.any():
            return False
        existing = existing[~mask]
        existing.to_csv(csv_path, index=False)
        return True


def get_all_records(csv_path: str) -> list:
    """Return all student records as list of dicts (for /all_students route)."""
    df = load_all(csv_path)
    records = []
    for _, row in df.iterrows():
        rec = {
            "name":        str(row.get("Student_Name", "")),
            "roll":        str(row.get("Roll_Number", "")),
            "attendance":  float(row.get("Attendance", 0)),
            "performance": str(row.get("Performance", "")),
        }
        for s in SUBJECTS:
            rec[f"assign_{s}"]   = float(row.get(f"Assignment_{s}", 0))
            rec[f"internal_{s}"] = float(row.get(f"Internal_{s}",   0))
            rec[f"exam_{s}"]     = float(row.get(f"Exam_{s}",       0))
        records.append(rec)
    return records
