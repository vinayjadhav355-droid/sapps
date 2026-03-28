# 🎓 Student Performance Prediction System

> A Machine Learning-powered CLI tool designed to help teachers during **Parent-Teacher Meetings** by predicting student academic performance and generating professional, personalised improvement reports.

---

## 📌 Project Overview

| Item | Details |
|------|---------|
| **Algorithm** | Random Forest Classifier (scikit-learn) |
| **Interface** | Interactive CLI (Terminal) |
| **Data Source** | CSV file (`data/students.csv`) — acts as a live database |
| **Smart Caching** | Retrains only when CSV data changes (MD5 hash comparison) |
| **Output** | Full professional report with scores, category, action plan & parent notes |

---

## 🗂️ Project Structure

```
StudentPerformancePredictor/
│
├── main.py                     ← Entry point — run this
├── requirements.txt            ← Python dependencies
├── README.md                   ← This file
│
├── data/
│   └── students.csv            ← Student dataset (add new rows here)
│
├── model/                      ← Auto-created on first run
│   ├── model.pkl               ← Trained Random Forest model
│   ├── label_encoder.pkl       ← Fitted label encoder
│   └── model_meta.json         ← CSV hash + accuracy metadata
│
├── modules/
│   ├── __init__.py
│   ├── data_loader.py          ← MODULE 1: Load & validate CSV
│   ├── model_trainer.py        ← MODULE 2: Train / reload model
│   ├── predictor.py            ← MODULE 3: Predict + generate suggestions
│   └── interface.py            ← MODULE 4: All CLI display & input
│
└── logs/
    └── app.log                 ← Auto-created: debug logs
```

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the system
```bash
python main.py
```

That's it. The system will:
- Load the CSV automatically
- Train the model on first run (saved to `model/`)
- Reload the cached model on subsequent runs (if CSV hasn't changed)
- Retrain automatically whenever you add new data to the CSV

---

## 🔄 Real-World Workflow

### Adding new students
Simply open `data/students.csv` and add new rows at the bottom following the same column format. On the next run, the system detects the change (via file hash) and **automatically retrains** the model with the updated data.

### CSV Column Format
```
Student_Name, Attendance,
Assignment_Maths, Assignment_English, Assignment_Science, Assignment_Kannada, Assignment_Hindi,
Internal_Maths, Internal_English, Internal_Science, Internal_Kannada, Internal_Hindi,
Exam_Maths, Exam_English, Exam_Science, Exam_Kannada, Exam_Hindi,
Performance
```

### Marks breakdown per subject
| Component | Max Marks |
|-----------|-----------|
| Assignment | 20 |
| Internal | 30 |
| Final Exam | 50 |
| **Total** | **100** |

---

## 📤 Performance Categories

| Category | Overall Score | Meaning |
|----------|-------------|---------|
| 🟢 **Good** | ≥ 75% | Outstanding — consistent excellence |
| 🟡 **Average** | 55–74% | Satisfactory — room to grow |
| 🟠 **Bad** | 35–54% | Below expectations — intervention needed |
| 🔴 **Fail** | < 35% | Critical — immediate action required |

---

## 📋 Sample Report Output

```
══════════════════════════════════════════════════════════════════════════════

  STUDENT PERFORMANCE REPORT
  ────────────────────────────────────────
  Student   :  Aarav Sharma
  Attendance:  92.0%   [Excellent Attendance]
  Overall   :  82.5 / 100  (82.5%)
  Confidence:  94.5%  (model certainty)

  ────────────────────────────────────────
    ★  GOOD  
    Outstanding Academic Performance
  ────────────────────────────────────────

  ▌ SUBJECT-WISE SCORE BREAKDOWN
  ────────────────────────────────────────────────────────────
  Subject      Assign  Internal   Exam   Total  Grade  Progress
  ──────────── ─────── ───────── ────── ─────── ─────  ──────────────────────────────
  📐 Maths      18.0/20   27.0/30  45.0/50  90.0/100    A+  [████████████████████]  90%
  📖 English    17.0/20   25.0/30  43.0/50  85.0/100    A   [█████████████████░░░]  85%
  🔬 Science    19.0/20   28.0/30  46.0/50  93.0/100    A+  [████████████████████]  93%
  ...

  ▌ RECOMMENDED ACTION PLAN
  ────────────────────────────────────────────────────────────
   1.  Maintain the current study schedule — consistency is the
       foundation of sustained success.
   2.  Challenge yourself with advanced reading materials...
  ...
══════════════════════════════════════════════════════════════════════════════
```

---

## 🧠 Technical Details

- **Algorithm:** Random Forest (200 estimators, max_depth=10)
- **Train/Test Split:** 80% / 20% (stratified)
- **Smart Caching:** MD5 hash of CSV → only retrains on data change
- **Missing Value Handling:** Numeric columns filled with column median
- **Label Encoding:** `sklearn.preprocessing.LabelEncoder`
- **Logging:** Full debug log saved to `logs/app.log`

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| ML | scikit-learn (Random Forest) |
| Data | pandas, numpy |
| Model persistence | pickle + json metadata |
| Interface | Pure Python CLI with ANSI colours |
| Logging | Python `logging` module |

---

*Built for educational use. Predictions are indicative and should complement teacher judgment during parent-teacher meetings.*
