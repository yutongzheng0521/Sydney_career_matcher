# Sydney_career_matcher
Personality-based career recommendation system for COMP project.
Author: yutong zheng
Email: yzhe0888@uni.sydney.edu.au
Date: October 10-28, 2025
Course: COMP9001 - The University of Sydney

Personality → Career Matcher

A lightweight Python app that maps a short personality survey to top career recommendations with human-readable explanations.

Language: Python 3.9+

Third-party libs: None (Ed-safe).

I/O: JSON data files, text report, CSV history.

1) How to Run
# in the project root
python3 main.py


You will be asked to:

Set your preferences (salary / stability / creativity / social).

Answer a Likert 1–5 survey.

Receive Top-K careers with reasons, plus a saved report.

2) Project Structure
career_matcher/
├─ main.py                # CLI entry; config load, input flow, reporting
├─ models.py              # dataclasses: Question, UserProfile, Preferences
├─ engine.py              # Strategy scorers, Recommender, explanations, normalization
├─ io_utils.py            # JSON/text IO, history CSV, config loader
├─ data/
│  ├─ questions.json      # survey items (trait, reverse)
│  └─ careers.json        # career weights + preference profile
├─ config.json            # (optional) mode/top_k/report_dir
└─ README.md

3) Features

Survey → Traits: computes six normalized traits
E (Extraversion), C (Conscientiousness), O (Openness), A (Agreeableness), N (Emotional Stability), M (Analytical Mindset).

Two scoring algorithms (Strategy Pattern):

weighted (dot product)

cosine (cosine similarity)

Preference-aware tie-break: small boost if your preferences align with a career’s emphasis.

Readable explanations: 2 strengths + 1 watch-out with a concrete tip.

Min–Max normalization: scores printed as 0..1 for easy comparison.

Reports & history: saves reports/report.txt and appends to history.csv.

4) Configuration (optional)

config.json (auto-loaded with defaults if absent):

{
  "mode": "weighted",        // or "cosine"
  "top_k": 3,                // number of recommendations to show
  "report_dir": "reports"    // output folder for report.txt
}

5) Data Formats
data/questions.json
[
  {"id": 1, "text": "I enjoy focusing...", "trait": "M", "reverse": false}
]


trait ∈ {E,C,O,A,N,M}

reverse: true means the item is reverse-scored (5→1, 4→2, …).

data/careers.json
[
  {
    "name": "Data Analyst",
    "weights": {"M":0.40,"C":0.30,"O":0.15,"E":0.05,"A":0.05,"N":-0.05},
    "preferences": {"salary":0.8,"stability":0.7,"creativity":0.3,"social":0.3},
    "desc": "..."
  }
]


weights map traits to importance (negative means a trait tends to hurt fit).

preferences describe what the career typically values (used for small tie-break).

6) Advanced Concepts 

OOP (classes & composition): dataclasses for domain models; Strategy Pattern to swap scorers (WeightedScorer / CosineScorer).

File I/O & JSON parsing: loads questions/careers/config; writes report & CSV history.

Exception handling & validation: robust CLI input checks; JSON schema/keys validation; friendly error messages.

Algorithm design: scoring, min–max normalization, ranking, and explanation generation (strengths + watch-out + improvement tip).

(Optional engineering): logging for key steps.

7) What’s Produced

Terminal summary: trait bars, Top-K, explanations.

reports/report.txt: normalized scores, ranked careers, explanations.

history.csv: your trait vector and top picks per run.

