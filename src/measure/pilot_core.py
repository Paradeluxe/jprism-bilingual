"""pilot_core.py — the locked scoring core, copied VERBATIM from
run_pilot_0.6b_n1000.py (2026-10-01) so the cluster can measure without that file.

Do not edit: MEASUREMENTS.md locks these definitions (euro/european exclusion,
honest_cues, rank_targets, pos=-1 primary read).
"""

import time
from pathlib import Path


CLASSIC = [
    ("boot_currency", "Fact: The currency used in the country shaped like a boot is",
     ["euro", "eur"], ["italy"]),
    ("spider_legs", "The number of legs on the animal that spins webs is",
     ["8", "eight"], []),
    ("france_capital", "The capital of France is",
     ["paris"], []),
    ("sport", "Think of a sport: people kick a round ball into a net. The sport is",
     ["football", "soccer"], []),
]

# Dense mid + sample early/late from every-2 fitted set
WANT_LAYERS = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]
POSITIONS = [-1, -2]


def now_hkt() -> str:
    return time.strftime("%Y-%m-%d %H:%M HKT", time.localtime())


def resolve_model_path(p: Path) -> str:
    if (p / "config.json").is_file():
        return str(p)
    snap = p / "snapshots"
    if snap.is_dir():
        for d in snap.iterdir():
            if (d / "config.json").is_file():
                return str(d)
    return "Qwen/Qwen3-0.6B"


def topk_pairs(tok, logits, k=5):
    values, indices = logits.topk(k)
    return [(tok.decode([int(i)]), float(v)) for i, v in zip(indices, values)]


def honest_cues(key: str, tokens: list[str]) -> list[str]:
    hits = []
    for t in tokens:
        ts = t.strip()
        low = ts.lower()
        if key == "boot_currency":
            if low in ("euro", "eur") or ts in ("Euro", "EUR"):
                hits.append(f"euro/{ts}")
            elif "euro" in low and "european" not in low:
                hits.append(f"euro~/{ts}")
            if low == "italy" or ts == "Italy":
                hits.append(f"Italy/{ts}")
        elif key == "spider_legs":
            if ts == "8" or low == "8":
                hits.append(f"8/{ts}")
            if low == "eight":
                hits.append(f"eight/{ts}")
        elif key == "france_capital":
            if "paris" in low:
                hits.append(f"Paris/{ts}")
        elif key == "sport":
            if "football" in low or "soccer" in low:
                hits.append(f"football/{ts}")
    out, seen = [], set()
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def rank_targets(tok, logits, targets, max_scan=500):
    values, indices = logits.topk(min(max_scan, logits.numel()))
    best = None
    best_tok = None
    for r, idx in enumerate(indices.tolist(), start=1):
        dec = tok.decode([int(idx)])
        dlow = dec.strip().lower()
        for t in targets:
            if dlow == t.lower() or dlow.strip() == t.lower():
                if best is None or r < best:
                    best, best_tok = r, dec
                break
            # euro-in-european does not count for euro
            if t.lower() == "euro" and "euro" in dlow and "european" not in dlow and dlow != "european":
                if dlow in ("euro", "eur") or dlow.startswith("euro"):
                    if len(dlow) <= 5:
                        if best is None or r < best:
                            best, best_tok = r, dec
                        break
    return best, best_tok


