# ============================================================
#  MODULE 4: interface.py
#  Responsibility: All terminal input/output and display logic
#  Renders professional, structured report output in the CLI.
# ============================================================

import os
import sys
import logging
import textwrap

logger = logging.getLogger(__name__)


# ── Terminal color codes (ANSI) ──────────────────────────────
class Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    # Foreground
    WHITE   = "\033[97m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    ORANGE  = "\033[38;5;208m"
    RED     = "\033[91m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    GRAY    = "\033[90m"

    # Background
    BG_DARK  = "\033[40m"
    BG_GREEN = "\033[42m"


CATEGORY_COLORS = {
    "Good":    Color.GREEN,
    "Average": Color.YELLOW,
    "Bad":     Color.ORANGE,
    "Fail":    Color.RED,
}

CATEGORY_ICONS = {
    "Good":    "★  GOOD",
    "Average": "◆  AVERAGE",
    "Bad":     "▲  BAD",
    "Fail":    "✖  FAIL",
}

SUBJECT_EMOJIS = {
    "Maths":   "📐",
    "English": "📖",
    "Science": "🔬",
    "Kannada": "✍️ ",
    "Hindi":   "📜",
}


# ─────────────────────────────────────────────────────────────
#  HELPER DISPLAY FUNCTIONS
# ─────────────────────────────────────────────────────────────

def _clear():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def _bar(pct: float, width: int = 30) -> str:
    """
    Generate a horizontal ASCII progress bar.
    Example: [████████████░░░░░░░░]  60%
    """
    filled = int((pct / 100) * width)
    empty  = width - filled
    bar    = "█" * filled + "░" * empty
    return f"[{bar}]"


def _wrap(text: str, indent: int = 4, width: int = 74) -> str:
    """Wrap long text with consistent indentation."""
    prefix = " " * indent
    return textwrap.fill(text, width=width,
                         initial_indent=prefix,
                         subsequent_indent=prefix)


def _divider(char: str = "─", width: int = 78) -> str:
    return Color.GRAY + (char * width) + Color.RESET


def _section_header(title: str) -> str:
    return (
        f"\n{Color.BOLD}{Color.CYAN}  ▌ {title.upper()}{Color.RESET}\n"
        f"  {Color.GRAY}{'─' * 60}{Color.RESET}"
    )


# ─────────────────────────────────────────────────────────────
#  SPLASH SCREEN
# ─────────────────────────────────────────────────────────────

def show_banner():
    """Display the application banner on startup."""
    print("\n" + _divider("═"))
    print(f"{Color.BOLD}{Color.CYAN}")
    print("       ╔═══════════════════════════════════════════════╗")
    print("       ║    🎓  STUDENT PERFORMANCE PREDICTOR          ║")
    print("       ║        AI-Powered Academic Analysis Tool      ║")
    print("       ╚═══════════════════════════════════════════════╝")
    print(Color.RESET)
    print(f"  {Color.GRAY}Designed for Parent-Teacher Meetings{Color.RESET}")
    print(f"  {Color.GRAY}Powered by Random Forest Machine Learning{Color.RESET}")
    print(_divider("═") + "\n")


# ─────────────────────────────────────────────────────────────
#  SYSTEM STATUS MESSAGES
# ─────────────────────────────────────────────────────────────

def show_status(message: str, status: str = "info"):
    """
    Print a colour-coded status line.
    status: 'info' | 'success' | 'warn' | 'error'
    """
    icons  = {"info": "ℹ", "success": "✔", "warn": "⚠", "error": "✖"}
    colors = {
        "info":    Color.CYAN,
        "success": Color.GREEN,
        "warn":    Color.YELLOW,
        "error":   Color.RED,
    }
    icon  = icons.get(status, "·")
    color = colors.get(status, Color.WHITE)
    print(f"  {color}{icon}  {message}{Color.RESET}")


def show_training_summary(accuracy: float, num_students: int):
    """Show a brief model training summary."""
    print()
    print(_divider())
    show_status(f"Dataset loaded  →  {num_students} student records found.", "info")
    show_status(
        f"Model ready     →  Test Accuracy: "
        f"{Color.BOLD}{accuracy * 100:.2f}%{Color.RESET}",
        "success"
    )
    print(_divider())
    print()


# ─────────────────────────────────────────────────────────────
#  MAIN REPORT RENDERER
# ─────────────────────────────────────────────────────────────

def display_report(result: dict):
    """
    Render the full professional prediction report to the terminal.

    Args:
        result (dict): Output from predictor.predict_student()
    """
    cat    = result["category"]
    color  = CATEGORY_COLORS.get(cat, Color.WHITE)
    sdata  = result["suggestion_data"]
    scores = result["subject_scores"]
    weak   = result["weak_subjects"]
    tips   = result["subject_tips"]

    print("\n")
    print(_divider("═"))

    # ── Header ───────────────────────────────────────────────
    print(f"\n  {Color.BOLD}{Color.WHITE}STUDENT PERFORMANCE REPORT{Color.RESET}")
    print(f"  {'─' * 40}")
    print(f"  {Color.BOLD}Student   :{Color.RESET}  {result['name']}")
    print(f"  {Color.BOLD}Attendance:{Color.RESET}  {result['attendance']:.1f}%   "
          f"{_attendance_badge(result['attendance'])}")
    print(f"  {Color.BOLD}Overall   :{Color.RESET}  {result['overall_avg']:.1f} / 100  "
          f"({result['overall_pct']:.1f}%)")
    print(f"  {Color.BOLD}Confidence:{Color.RESET}  {result['confidence']}%  (model certainty)")

    # ── Category badge ───────────────────────────────────────
    print()
    badge_text = f"  {CATEGORY_ICONS[cat]}  "
    print(f"  {color}{Color.BOLD}{'─' * 40}{Color.RESET}")
    print(f"  {color}{Color.BOLD}  PERFORMANCE CATEGORY :  {CATEGORY_ICONS[cat]}{Color.RESET}")
    print(f"  {color}{Color.BOLD}  {sdata['headline']}{Color.RESET}")
    print(f"  {color}{Color.BOLD}{'─' * 40}{Color.RESET}")

    # ── Subject score table ──────────────────────────────────
    print(_section_header("Subject-wise Score Breakdown"))
    print()
    print(f"  {'Subject':<12} {'Assign':>7} {'Internal':>9} {'Exam':>6} "
          f"{'Total':>7} {'Grade':>6}  Progress")
    print(f"  {'─'*12} {'─'*7} {'─'*9} {'─'*6} {'─'*7} {'─'*6}  {'─'*30}")

    for subj, sc in scores.items():
        emoji = SUBJECT_EMOJIS.get(subj, "  ")
        grade_color = _grade_color(sc["grade"])
        bar   = _bar(sc["percent"], width=20)
        weak_flag = f" {Color.RED}← WEAK{Color.RESET}" if subj in weak else ""
        print(
            f"  {emoji} {subj:<10} "
            f"{sc['assignment']:>5.1f}/20 "
            f"{sc['internal']:>6.1f}/30 "
            f"{sc['exam']:>4.1f}/50 "
            f"{Color.BOLD}{sc['total']:>5.1f}{Color.RESET}/100 "
            f"{grade_color}{Color.BOLD}{sc['grade']:>5}{Color.RESET}  "
            f"{Color.DIM}{bar}{Color.RESET} {sc['percent']:.0f}%"
            f"{weak_flag}"
        )

    # ── Assessment overview ──────────────────────────────────
    print(_section_header("Academic Assessment"))
    print()
    print(_wrap(sdata["overview"], indent=4, width=76))

    # ── Action plan ──────────────────────────────────────────
    print(_section_header("Recommended Action Plan"))
    print()
    for idx, step in enumerate(sdata["action_plan"], 1):
        bullet = f"{color}{Color.BOLD}  {idx:>2}.{Color.RESET}"
        print(f"{bullet}  {_wrap(step, indent=6, width=74).lstrip()}")
        print()

    # ── Subject-specific tips for weak areas ─────────────────
    if weak and tips:
        print(_section_header(f"Subject-Specific Guidance — Weak Areas ({', '.join(weak)})"))
        print()
        for subj, subj_tips in tips.items():
            emoji = SUBJECT_EMOJIS.get(subj, "  ")
            print(f"  {color}{Color.BOLD}{emoji} {subj}{Color.RESET}")
            for tip in subj_tips:
                print(f"    {Color.DIM}•{Color.RESET}  {tip}")
            print()

    # ── Parent note ──────────────────────────────────────────
    print(_section_header("Note for Parents / Guardians"))
    print()
    print(_wrap(sdata["parent_note"], indent=4, width=76))
    print()

    print(_divider("═"))
    print()


# ─────────────────────────────────────────────────────────────
#  INPUT PROMPT
# ─────────────────────────────────────────────────────────────

def prompt_student_name() -> str:
    """
    Ask the teacher to enter a student name.

    Returns:
        str: The name entered, stripped of whitespace.
             Returns empty string if the teacher wants to quit.
    """
    print(f"\n  {Color.BOLD}Enter student name{Color.RESET}"
          f"  {Color.GRAY}(or type 'exit' / 'quit' to close){Color.RESET}")
    name = input(f"\n  {Color.CYAN}→  {Color.RESET}").strip()
    return name


def show_not_found(name: str):
    """Display a clear 'student not found' message."""
    print()
    print(f"  {Color.RED}{Color.BOLD}✖  Student Not Found{Color.RESET}")
    print(f"  {'─' * 44}")
    print(f"  No record found for: {Color.BOLD}\"{name}\"{Color.RESET}")
    print()
    print(f"  {Color.GRAY}Possible reasons:{Color.RESET}")
    print(f"  {Color.GRAY}  • The name may be spelled differently in the CSV.{Color.RESET}")
    print(f"  {Color.GRAY}  • The student may not have been added to the dataset yet.{Color.RESET}")
    print(f"  {Color.GRAY}  • Check case sensitivity — search is case-insensitive.{Color.RESET}")
    print()


def show_goodbye():
    """Show a goodbye message when the user exits."""
    print()
    print(f"  {Color.CYAN}Thank you for using Student Performance Predictor.{Color.RESET}")
    print(f"  {Color.GRAY}Session ended.{Color.RESET}\n")
    print(_divider("═") + "\n")


def ask_continue() -> bool:
    """Ask if the teacher wants to analyse another student."""
    print(f"\n  {Color.GRAY}─────────────────────────────────────────{Color.RESET}")
    choice = input(
        f"  {Color.BOLD}Analyse another student?{Color.RESET}"
        f"  {Color.GRAY}[Y/n] → {Color.RESET}"
    ).strip().lower()
    return choice not in ("n", "no", "exit", "quit")


# ─────────────────────────────────────────────────────────────
#  HELPER COLOUR FUNCTIONS
# ─────────────────────────────────────────────────────────────

def _grade_color(grade: str) -> str:
    """Return a color code based on letter grade."""
    if grade in ("A+", "A"): return Color.GREEN
    if grade == "B":          return Color.CYAN
    if grade == "C":          return Color.YELLOW
    if grade == "D":          return Color.ORANGE
    return Color.RED


def _attendance_badge(pct: float) -> str:
    """Return a color-coded attendance tag."""
    if pct >= 85:
        return f"{Color.GREEN}[Excellent Attendance]{Color.RESET}"
    if pct >= 75:
        return f"{Color.YELLOW}[Satisfactory Attendance]{Color.RESET}"
    if pct >= 60:
        return f"{Color.ORANGE}[Poor Attendance — Needs Improvement]{Color.RESET}"
    return f"{Color.RED}[Critical Attendance — Immediate Action]{Color.RESET}"
