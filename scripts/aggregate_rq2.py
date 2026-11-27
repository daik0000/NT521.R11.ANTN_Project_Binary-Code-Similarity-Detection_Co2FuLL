#!/usr/bin/env python3
"""Aggregate RQ2 pair JSON into prompt and sampling-setting metrics."""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / Path("saved/Binkit-1.0-dataset/pairs/experiments/rq2_ollama")
DATA = REPO / Path("DBs/xm-full_top5-rq2-ready.csv")
OUT = REPO / Path("docs/rq2-metrics.csv")
TAG = re.compile(r"<same_source>\s*(yes|no)\s*</same_source>", re.I)

with DATA.open(newline="", encoding="utf-8-sig") as fh:
    source_rows = {
        f"{r['bin_name_1']}@{r['fva_1']}#{r['bin_name_2']}@{r['fva_2']}": int(r["label"])
        for r in csv.DictReader(fh)
    }
groups = defaultdict(dict)
for path in ROOT.glob("*/*-pseudo_code/*.json"):
    model_dir = path.parents[1].name
    prompt_dir = path.parent.name.removesuffix("-pseudo_code")
    parts = model_dir.split("#")
    model = parts[0]
    params = tuple(parts[1:3]) if len(parts) >= 3 else ()
    try:
        data = json.loads(path.read_text())
    except Exception:
        data = {}
    pair = path.stem
    label = source_rows.get(pair)
    if label is None:
        continue
    output = data.get("output", "") if isinstance(data, dict) else ""
    match = TAG.search(output if isinstance(output, str) else "")
    pred = None if not match else int(match.group(1).lower() == "yes")
    if prompt_dir == "few_shot" and params:
        groups[(model, "prompt:few_shot")][pair] = (label, pred)
        condition = f"setting:top_p={params[0]},temperature={params[1]}"
        groups[(model, condition)][pair] = (label, pred)
    else:
        groups[(model, f"prompt:{prompt_dir}")][pair] = (label, pred)

fields = ["model", "condition", "expected", "found", "valid", "malformed", "tp", "fp", "tn", "fn", "precision", "recall", "f2"]
with OUT.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fields)
    writer.writeheader()
    for (model, condition), records in sorted(groups.items()):
        valid = [(y, p) for y, p in records.values() if p is not None]
        tp = sum(y == 1 and p == 1 for y, p in valid)
        fp = sum(y == 0 and p == 1 for y, p in valid)
        tn = sum(y == 0 and p == 0 for y, p in valid)
        fn = sum(y == 1 and p == 0 for y, p in valid)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        denom = 4 * precision + recall
        f2 = 5 * precision * recall / denom if denom else 0.0
        writer.writerow({
            "model": model, "condition": condition,
            "expected": len(source_rows), "found": len(records),
            "valid": len(valid), "malformed": len(records) - len(valid),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": round(precision, 6), "recall": round(recall, 6),
            "f2": round(f2, 6),
        })
print(f"wrote {OUT} with {len(groups)} available conditions")
