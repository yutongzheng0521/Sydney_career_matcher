from dataclasses import dataclass, field
from typing import Dict

TRAITS = ["E", "C", "O", "A", "N", "M"]  # Extraversion, Conscientiousness, Openness, Agreeableness, Neuroticism, analytical Mindset

@dataclass
class Question:
    id: int
    text: str
    trait: str
    reverse: bool = False

@dataclass
class UserProfile:
    raw: Dict[str, float] = field(default_factory=lambda: {t: 0.0 for t in TRAITS})
    cnt: Dict[str, int] = field(default_factory=lambda: {t: 0 for t in TRAITS})
    traits: Dict[str, float] = field(default_factory=dict)  # normalized 0–1

    def update_trait(self, trait: str, score: int, reverse: bool = False):
        if trait not in self.raw:
            self.raw[trait] = 0.0
            self.cnt[trait] = 0
        val = 6 - score if reverse else score  # Likert 1..5
        self.raw[trait] += val
        self.cnt[trait] += 1

    def finalize(self):
        self.traits = {}
        for t in self.raw:
            if self.cnt[t] == 0:
                avg = 3.0
            else:
                avg = self.raw[t] / self.cnt[t]
            self.traits[t] = (avg - 1) / 4.0  # scale to 0..1

@dataclass
class Preferences:
    salary: int = 3
    stability: int = 3
    creativity: int = 3
    social: int = 3

    def to_weights(self) -> Dict[str, float]:
        vals = {
            "salary": max(1, self.salary),
            "stability": max(1, self.stability),
            "creativity": max(1, self.creativity),
            "social": max(1, self.social),
        }
        s = sum(vals.values())
        return {k: v / s for k, v in vals.items()}


