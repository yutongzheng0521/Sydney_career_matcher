import json
from pathlib import Path
from typing import Dict, List, Tuple

def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def append_history(filename: str, profile, scores: Dict[str, float], topk: List[Tuple[str, float]]):
    p = Path(filename)
    headers = ["E", "C", "O", "A", "N", "M", "top1", "top2", "top3"]
    new = not p.exists()
    with open(p, "a", encoding="utf-8") as f:
        if new:
            f.write(",".join(headers) + "\n")
        row = [f"{profile.traits.get(t, 0.0):0.3f}" for t in ["E","C","O","A","N","M"]]
        row += [n for n, _ in topk] + [""] * max(0, 3 - len(topk))
        f.write(",".join(row) + "\n")

def load_config(path: Path, defaults: dict) -> dict:
    try:
        data = load_json(path)
        if not isinstance(data, dict):
            raise ValueError("config must be a JSON object")
        # 合并默认值
        merged = {**defaults, **data}
        return merged
    except FileNotFoundError:
        return defaults
    except Exception as e:
        print(f"[WARN] Failed to read config: {e}. Using defaults.")
        return defaults

