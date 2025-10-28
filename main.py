"""
Personality → Career Matcher  (main.py)

Run:
    python3 main.py

Requires (same folder structure):
    io_utils.py  (load_json, save_text, append_history, load_config)
    models.py    (Question, UserProfile, Preferences)
    engine.py    (Recommender, minmax_normalize)
    data/questions.json
    data/careers.json
    config.json  (optional; see DEFAULT_CONFIG for keys)
"""

from pathlib import Path
import logging
from typing import List, Dict, Any

from io_utils import load_json, save_text, append_history, load_config
from models import Question, UserProfile, Preferences
from engine import Recommender, minmax_normalize

# ---------------------- Paths & Config ---------------------- #
DATA_DIR = Path("data")
QUESTIONS_FILE = DATA_DIR / "questions.json"
CAREERS_FILE = DATA_DIR / "careers.json"
CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "mode": "weighted",     # "weighted" or "cosine"
    "top_k": 3,             # number of recommendations to show
    "report_dir": "reports" # where to save report.txt
}

# ---------------------- Logging Setup ----------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("career-matcher")


# ---------------------- CLI Utilities ----------------------- #
def ask_likert(prompt: str, low: int = 1, high: int = 5) -> int:
    """Ask for an integer in [low, high] with validation."""
    while True:
        try:
            val = int(input(f"{prompt} ({low}-{high}): "))
            if low <= val <= high:
                return val
            print(f"Please enter an integer between {low} and {high}.")
        except ValueError:
            print("Invalid input. Please enter an integer.")


def intro():
    print("=" * 72)
    print(" Personality → Career Matcher ")
    print("=" * 72)
    print("Answer a short personality survey. We'll recommend careers with reasons.\n")


def collect_preferences() -> Preferences:
    print("Before we start, tell us what you value more.")
    salary = ask_likert("I value high salary", 1, 5)
    stability = ask_likert("I value job stability", 1, 5)
    creativity = ask_likert("I value creativity", 1, 5)
    social = ask_likert("I enjoy frequent social interaction", 1, 5)
    return Preferences(
        salary=salary, stability=stability, creativity=creativity, social=social
    )


def take_survey(questions_data: List[Dict[str, Any]]) -> UserProfile:
    print("\nSurvey begins. Rate each statement 1 (Strongly Disagree) to 5 (Strongly Agree).\n")
    q_objs = [Question(**q) for q in questions_data]
    profile = UserProfile()
    for q in q_objs:
        score = ask_likert(q.text)
        profile.update_trait(q.trait, score, reverse=q.reverse)
    profile.finalize()
    return profile


def show_summary(topk, explanations, profile, scores_normalized: Dict[str, float], mode: str):
    print(f"\nScoring mode = {mode}")
    print("\nYour trait scores (0–1 scaled):")
    for t, v in profile.traits.items():
        bar = "█" * int(v * 20)
        print(f"  {t}: {v:0.2f} {bar}")

    print("\nTop Recommendations:")
    for i, (name, _) in enumerate(topk, 1):
        s_norm = scores_normalized.get(name, 0.0)
        why = explanations.get(name, "")
        print(f"  {i}. {name} — normalized score {s_norm:0.3f}\n     Why: {why}")

    print("\n(Notes: higher score indicates better match; normalized scores are 0..1.)\n")


# ---------------------- Data Validation --------------------- #
def validate_questions(questions: Any):
    if not isinstance(questions, list) or not questions:
        raise ValueError("questions.json must be a non-empty list")
    required_q_keys = {"id", "text", "trait", "reverse"}
    valid_traits = {"E", "C", "O", "A", "N", "M"}
    for q in questions:
        if not required_q_keys.issubset(q):
            raise ValueError(f"Bad question item: {q}")
        if q["trait"] not in valid_traits:
            raise ValueError(f"Unknown trait in question: {q['trait']}")


def validate_careers(careers: Any):
    if not isinstance(careers, list) or not careers:
        raise ValueError("careers.json must be a non-empty list")
    valid_traits = {"E", "C", "O", "A", "N", "M"}
    for c in careers:
        if "name" not in c or "weights" not in c:
            raise ValueError(f"Bad career item (needs 'name' & 'weights'): {c}")
        for t, w in c["weights"].items():
            if t not in valid_traits:
                raise ValueError(f"Unknown trait key in weights: {t} for {c['name']}")
            float(w)  # ensures numeric


# -------------------------- Main ---------------------------- #
def main():
    intro()

    # Load config (fallback to defaults on error)
    cfg = load_config(CONFIG_FILE, DEFAULT_CONFIG)
    mode = str(cfg.get("mode", "weighted")).lower()
    top_k = int(cfg.get("top_k", 3))
    reports_dir = Path(cfg.get("report_dir", "reports"))
    logger.info("Config loaded: mode=%s, top_k=%s, report_dir=%s", mode, top_k, reports_dir)

    # Load data
    questions = load_json(QUESTIONS_FILE)
    careers = load_json(CAREERS_FILE)
    logger.info("Loaded %d questions, %d careers", len(questions), len(careers))

    # Validate data structure
    validate_questions(questions)
    validate_careers(careers)

    # Collect inputs
    prefs = collect_preferences()
    logger.info("Preferences collected")
    profile = take_survey(questions)
    logger.info("Survey completed with traits: %s", profile.traits)

    # Recommend
    rec = Recommender(careers, mode=mode, preferences=prefs)
    raw_scores = rec.score(profile.traits)          # original scores
    norm_scores = minmax_normalize(raw_scores)      # 0..1 for display/report
    topk = rec.top_k(raw_scores, k=top_k)           # ranking from raw (same order as normalized)
    explanations = rec.explain(topk, profile.traits)

    # Output
    show_summary(topk, explanations, profile, norm_scores, mode)

    # Save report
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "report.txt"
    content = rec.make_report(profile, norm_scores, topk, explanations)
    save_text(report_path, content)
    print(f"Report saved to: {report_path.resolve()}")
    logger.info("Report written to %s", report_path)

    # Persist history (CSV)
    append_history("history.csv", profile, raw_scores, topk)
    logger.info("History appended.")


# --------------------- Error Handling ----------------------- #
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Exited by user.")
    except FileNotFoundError as e:
        print(f"[ERROR] Missing file: {e}. Did you place data/ JSON files correctly?")
    except Exception as e:
        print(f"[ERROR] {e}")

