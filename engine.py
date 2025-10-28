from typing import Dict, List, Tuple
from math import sqrt
from abc import ABC, abstractmethod
from models import Preferences

Career = Dict[str, object]

# ---------------- Human-readable labels & tips ----------------
TRAIT_LABEL = {
    "E": "Extraversion (social expression)",
    "C": "Conscientiousness (planning & execution)",
    "O": "Openness (creativity & novelty)",
    "A": "Agreeableness (collaboration & empathy)",
    "N": "Emotional stability (stress tolerance)",
    "M": "Analytical mindset (logic & abstraction)",
}

# One-line “positive effect” per trait
TRAIT_STRENGTH = {
    "E": "supports clear communication and influencing others",
    "C": "helps break tasks down and deliver reliably",
    "O": "brings creative solutions and fresh perspectives",
    "A": "builds trust and smooth teamwork",
    "N": "stays calm and steady under pressure",
    "M": "enables structured thinking and data/logic reasoning",
}

# One-line improvement tip per trait
IMPROVE_TIP = {
    "E": "prepare talking points and practice concise presentations",
    "C": "use pomodoro + kanban/checklists and review weekly",
    "O": "keep an idea backlog and schedule regular creative time",
    "A": "run more user interviews and practice empathy mapping",
    "N": "learn stress management (chunk work, exercise, breathing)",
    "M": "do more data analysis/logic drills and write out reasoning",
}

# Preference key → English label
PREF_EN = {
    "salary": "compensation",
    "stability": "stability",
    "creativity": "creativity",
    "social": "social interaction",
}

# ---------------- Scoring strategies (Strategy pattern) ----------------
class Scorer(ABC):
    @abstractmethod
    def score(self, traits: Dict[str, float], weights: Dict[str, float]) -> float:
        ...

class WeightedScorer(Scorer):
    def score(self, traits: Dict[str, float], weights: Dict[str, float]) -> float:
        return sum(traits.get(t, 0.0) * w for t, w in weights.items())

class CosineScorer(Scorer):
    def score(self, traits: Dict[str, float], weights: Dict[str, float]) -> float:
        num = sum(traits.get(t, 0.0) * w for t, w in weights.items())
        den1 = sqrt(sum((traits.get(t, 0.0)) ** 2 for t in weights))
        den2 = sqrt(sum((w ** 2) for w in weights.values()))
        if den1 == 0 or den2 == 0:
            return 0.0
        return num / (den1 * den2)

# ---------------- Min–Max normalization (0..1) ----------------
def minmax_normalize(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    mn, mx = min(vals), max(vals)
    if mx == mn:
        # if all equal, set to 1.0 so everything reads as “best match”
        return {k: 1.0 for k in scores}
    return {k: (v - mn) / (mx - mn) for k, v in scores.items()}

# ---------------- Recommender ----------------
class Recommender:
    def __init__(self, careers: List[Career], mode: str = "weighted", preferences: Preferences = None):
        self.careers = careers
        self.pref_w = (preferences or Preferences()).to_weights()
        self.scorer: Scorer = WeightedScorer() if mode == "weighted" else CosineScorer()

    def score(self, user_traits: Dict[str, float]) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for c in self.careers:
            name = str(c["name"]).strip()
            w = c.get("weights", {})
            base = self.scorer.score(user_traits, w)
            # light tie-break via preferences
            prefs = c.get("preferences", {})
            tb = sum(self.pref_w.get(k, 0.0) * float(prefs.get(k, 0.0)) for k in self.pref_w)
            scores[name] = base + 0.05 * tb
        return scores

    def top_k(self, scores: Dict[str, float], k: int = 3) -> List[Tuple[str, float]]:
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

    def explain(self, topk: List[Tuple[str, float]], traits: Dict[str, float]) -> Dict[str, str]:
        """
        Produce readable explanations for top-K results:
        - highlight 2 strongest positive contributing traits (strengths)
        - highlight 1 weakest/negative trait (watch-out) with a tip
        - add a short note if user preferences align with the career’s emphasis
        """
        explanations: Dict[str, str] = {}

        def preference_blurb(career_item) -> str:
            prefs = career_item.get("preferences", {})
            if not prefs:
                return ""
            top_pref = max(prefs.items(), key=lambda x: x[1])[0]
            en = PREF_EN.get(top_pref, top_pref)
            return f"In addition, this career values “{en}”, which aligns with your preferences; a small tie-break boost was applied."

        for name, _ in topk:
            career_item = next(c for c in self.careers if c["name"] == name)
            weights = career_item.get("weights", {})

            # contribution per trait = user_trait * career_weight
            contrib = {t: traits.get(t, 0.0) * w for t, w in weights.items()}
            pos_sorted = sorted(contrib.items(), key=lambda x: x[1], reverse=True)
            neg_sorted = sorted(contrib.items(), key=lambda x: x[1])

            strengths = [(t, v) for t, v in pos_sorted if v > 0][:2]
            watch = neg_sorted[0] if neg_sorted else None

            parts: List[str] = []

            # strengths paragraph
            if strengths:
                s_bits = [f"{TRAIT_LABEL.get(t, t)}: {TRAIT_STRENGTH.get(t, '')}" for t, _ in strengths]
                parts.append("Why it fits: " + "; ".join(s_bits) + ".")
            else:
                parts.append("Why it fits: your overall profile aligns with this role’s weighting.")

            # watch-out and tip
            if watch:
                t, v = watch
                if v <= 0:
                    parts.append(
                        f"Watch-out: {TRAIT_LABEL.get(t, t)} is relatively weaker or conflicts with this role’s weighting; "
                        f"{IMPROVE_TIP.get(t, '')}."
                    )
                else:
                    parts.append(
                        f"Potential growth: {TRAIT_LABEL.get(t, t)} still has room to improve; "
                        f"{IMPROVE_TIP.get(t, '')}."
                    )

            # preference alignment
            p_text = preference_blurb(career_item)
            if p_text:
                parts.append(p_text)

            explanations[name] = " ".join(parts)

        return explanations

