# ============================================================
#  MODULE 3: predictor.py
#  Responsibility: Predict performance and generate rich,
#  professional suggestions with per-subject insights.
# ============================================================

import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from modules.data_loader import FEATURE_COLUMNS

logger = logging.getLogger(__name__)


# ── Subject display names ────────────────────────────────────
SUBJECT_MAP = {
    "Maths":   ("Assignment_Maths",   "Internal_Maths",   "Exam_Maths"),
    "English": ("Assignment_English", "Internal_English", "Exam_English"),
    "Science": ("Assignment_Science", "Internal_Science", "Exam_Science"),
    "Kannada": ("Assignment_Kannada", "Internal_Kannada", "Exam_Kannada"),
    "Hindi":   ("Assignment_Hindi",   "Internal_Hindi",   "Exam_Hindi"),
}

# Max marks per component (matches your CSV)
MAX_ASSIGN   = 25
MAX_INTERNAL = 50
MAX_EXAM     = 100
MAX_TOTAL    = 175  # 25 + 50 + 100


# ─────────────────────────────────────────────────────────────
#  PROFESSIONAL SUGGESTION BANK
# ─────────────────────────────────────────────────────────────

SUGGESTIONS = {

    "Good": {
        "headline": "Outstanding Academic Performance",
        "overview": (
            "This student demonstrates consistent excellence across all subjects "
            "and shows strong academic discipline. Their performance reflects "
            "dedicated effort, sound time management, and a genuine commitment "
            "to learning. This is exactly the level of achievement that opens "
            "doors to advanced academic opportunities."
        ),
        "action_plan": [
            "Maintain the current study schedule — consistency is the foundation of sustained success.",
            "Challenge yourself with advanced reading materials, reference books, and competitive exam preparation.",
            "Participate actively in school olympiads, science exhibitions, and inter-school competitions to benchmark skills nationally.",
            "Mentor classmates who are struggling — teaching others deepens your own understanding significantly.",
            "Set progressive goals each term: aim for distinction-level scores and explore scholarship opportunities.",
            "Begin exploring career pathways and entrance exam patterns early to align academic preparation strategically.",
        ],
        "parent_note": (
            "Your child is performing at an exceptional level. Continue providing a "
            "supportive home environment, encourage intellectual curiosity beyond "
            "the syllabus, and celebrate this achievement meaningfully."
        ),
        "color": "GREEN",
        "icon": "★",
    },

    "Average": {
        "headline": "Satisfactory Performance — Room for Growth",
        "overview": (
            "This student is meeting the minimum academic expectations and shows "
            "a reasonable understanding of core concepts. However, there is clear "
            "potential that is not yet being fully realized. With focused effort, "
            "structured practice, and minor adjustments to the study approach, "
            "this student can move firmly into the 'Good' category."
        ),
        "action_plan": [
            "Identify the 2–3 weakest subjects and dedicate an additional 30–45 minutes daily to those specific areas.",
            "Solve at least 10 practice problems per subject each day to build speed, accuracy, and exam confidence.",
            "Prepare topic-wise summary notes after each chapter — this reinforces retention and aids quick revision.",
            "Actively participate in classroom discussions and ask questions whenever a concept is unclear.",
            "Review all returned assignments and tests carefully — understanding past mistakes is key to improvement.",
            "Create a structured weekly timetable that balances all subjects, including adequate breaks to prevent fatigue.",
            "Attempt previous years' question papers to familiarise yourself with the exam format and frequently tested topics.",
        ],
        "parent_note": (
            "Your child has solid foundational knowledge but needs consistent encouragement "
            "and a structured home study environment. Monitor daily study hours, "
            "reduce screen distractions during study time, and stay in regular "
            "communication with the class teacher."
        ),
        "color": "YELLOW",
        "icon": "◆",
    },

    "Bad": {
        "headline": "Below Expected Performance — Immediate Action Required",
        "overview": (
            "This student is currently performing below the acceptable academic "
            "threshold. There are visible gaps in foundational understanding across "
            "multiple subjects, and without targeted intervention, these gaps will "
            "widen further. A structured recovery plan, combined with increased "
            "teacher and parental involvement, is strongly recommended at this stage."
        ),
        "action_plan": [
            "Go back to chapter basics — do not proceed to advanced topics until the fundamentals are clearly understood.",
            "Dedicate a minimum of 3–4 hours of focused, distraction-free study every day without exception.",
            "Break the syllabus into small weekly targets and track completion — progress must be measurable.",
            "Schedule regular one-on-one sessions with each subject teacher to identify and resolve concept gaps.",
            "Use visual learning tools such as diagrams, flowcharts, and mind maps to simplify complex topics.",
            "Limit recreational screen time strictly during the academic term to reclaim productive study hours.",
            "Attempt chapter-end exercises multiple times until accuracy reaches at least 80% before moving ahead.",
            "Request additional worksheets and practice materials from teachers for home study.",
        ],
        "parent_note": (
            "This situation requires your direct and sustained involvement. "
            "Please ensure a quiet, dedicated study space at home, monitor daily "
            "homework completion, and consider engaging a subject tutor for the most "
            "struggling areas. Attend the next parent-teacher meeting and request "
            "a personalised academic plan from the school."
        ),
        "color": "ORANGE",
        "icon": "▲",
    },

    "Fail": {
        "headline": "Critical Academic Concern — Urgent Intervention Needed",
        "overview": (
            "This student is facing serious academic difficulties and is at significant "
            "risk of not clearing the current academic year. The performance across "
            "multiple subjects indicates a fundamental disconnect from the learning "
            "process — whether due to conceptual gaps, motivational challenges, "
            "attendance issues, or external factors. Immediate, coordinated action "
            "from teachers, parents, and the student is essential."
        ),
        "action_plan": [
            "Conduct an urgent one-on-one counselling session to identify the root cause — academic, personal, or emotional.",
            "Design a subject-by-subject remedial plan starting from the very beginning of the current year's syllabus.",
            "Enroll the student in all available school remedial classes, extra sessions, and doubt-clearing programs immediately.",
            "Assign a dedicated peer tutor or senior student mentor for daily academic support.",
            "Break the day into timed study blocks (45 min study + 10 min break) to build concentration gradually.",
            "Set small, achievable daily goals and celebrate every milestone — rebuilding confidence is equally critical.",
            "Ensure at least 8 hours of sleep and regular physical activity — cognitive performance is directly linked to health.",
            "Parents must monitor attendance strictly; even a single unexcused absence at this stage causes further setback.",
            "Schedule a formal academic intervention meeting involving the class teacher, subject teachers, and school counsellor.",
        ],
        "parent_note": (
            "This is a critical moment that requires your full and immediate attention. "
            "Your child needs both academic support and emotional encouragement. "
            "Please arrange for private tuition in failing subjects, create a strict "
            "daily routine at home, and maintain open communication with the school. "
            "Early intervention at this stage significantly improves the outcome."
        ),
        "color": "RED",
        "icon": "✖",
    },
}


# ─────────────────────────────────────────────────────────────
#  SUBJECT-SPECIFIC TIP BANK
# ─────────────────────────────────────────────────────────────

SUBJECT_TIPS = {
    "Maths": [
        "Practice a minimum of 15 problems daily covering all topic types.",
        "Master formulae by writing them out by hand every morning before studying.",
        "Always show full working — partial marks are awarded for correct method even if the final answer is wrong.",
    ],
    "English": [
        "Read one full passage or editorial daily to improve comprehension and vocabulary.",
        "Maintain a vocabulary journal — write 5 new words with meanings and usage sentences each day.",
        "Practice timed essay writing weekly to improve structure, coherence, and fluency under exam conditions.",
    ],
    "Science": [
        "Draw and label all diagrams from memory — this is a high-scoring area that many students neglect.",
        "Understand the 'why' behind every concept before attempting to memorise the 'what'.",
        "Relate scientific principles to real-world examples — this dramatically improves retention and application.",
    ],
    "Kannada": [
        "Read Kannada passages aloud daily to strengthen pronunciation, fluency, and comprehension.",
        "Practice grammar rules with dedicated worksheets — grammar carries significant weight in exams.",
        "Write short essays or paragraphs in Kannada regularly to build writing confidence and vocabulary.",
    ],
    "Hindi": [
        "Revise Hindi vocabulary for 15 minutes every evening without fail.",
        "Practice comprehension passages from previous years' question papers under timed conditions.",
        "Learn and practise grammatical constructions — sentence formation is critical for scoring well.",
    ],
}


# ─────────────────────────────────────────────────────────────
#  CORE PREDICTION FUNCTION
# ─────────────────────────────────────────────────────────────

def predict_student(student_row: pd.Series,
                    clf: RandomForestClassifier,
                    le: LabelEncoder) -> dict:
    """
    Predict the performance category for a single student and
    generate a comprehensive, professional suggestion report.

    Args:
        student_row (pd.Series): Full row from the CSV dataframe.
        clf: Trained Random Forest model.
        le: Fitted LabelEncoder.

    Returns:
        dict: Contains name, category, scores, suggestions, confidence.
    """

    # ── Step 1: Extract features for prediction ──────────────
    feature_df = student_row[FEATURE_COLUMNS].to_frame().T.astype(float)
    feature_df.columns = FEATURE_COLUMNS  # ensure correct column names

    # ── Step 2: Predict ──────────────────────────────────────
    encoded_pred = clf.predict(feature_df)[0]
    proba        = clf.predict_proba(feature_df)[0]
    category     = le.inverse_transform([encoded_pred])[0]
    confidence   = round(float(np.max(proba)) * 100, 1)

    # ── Step 3: Compute per-subject scores ───────────────────
    subject_scores = {}
    weak_subjects  = []

    for subj, (a_col, i_col, e_col) in SUBJECT_MAP.items():
        a = float(student_row[a_col])
        i = float(student_row[i_col])
        e = float(student_row[e_col])
        raw   = round(a + i + e, 1)                   # out of 175
        total = round((raw / MAX_TOTAL) * 100, 1)     # normalised to /100
        pct   = total                                  # percent == total

        subject_scores[subj] = {
            "assignment": a,
            "internal":   i,
            "exam":       e,
            "total":      total,
            "percent":    pct,
            "grade":      _score_to_grade(pct),
        }

        if pct < 50:
            weak_subjects.append(subj)

    # ── Step 4: Overall score ────────────────────────────────
    all_totals   = [v["total"] for v in subject_scores.values()]
    overall_avg  = round(sum(all_totals) / len(all_totals), 1)
    overall_pct  = overall_avg   # both /100 now
    attendance   = float(student_row["Attendance"])

    return {
        "name":           student_row["Student_Name"],
        "category":       category,
        "confidence":     confidence,
        "overall_avg":    overall_avg,
        "overall_pct":    overall_pct,
        "attendance":     attendance,
        "subject_scores": subject_scores,
        "weak_subjects":  weak_subjects,
        "suggestion_data": SUGGESTIONS[category],
        "subject_tips":   {s: SUBJECT_TIPS[s] for s in weak_subjects},
    }


def _score_to_grade(pct: float) -> str:
    """Convert a percentage score to a letter grade."""
    if pct >= 90: return "A+"
    if pct >= 75: return "A"
    if pct >= 60: return "B"
    if pct >= 50: return "C"
    if pct >= 35: return "D"
    return "F"
