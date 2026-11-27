#!/usr/bin/env python3
"""Create the D2 input after excluding rows with missing pseudo-code."""
import csv
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / Path("DBs/xm-full_top5-250515.csv")
CODE_ROOT = REPO / Path("DBs/Binkit-1.0-normal-strip-top_k_code")
OUTPUT = REPO / Path("DBs/xm-full_top5-rq2-ready.csv")
STATS = REPO / Path("DBs/rq2_input_stats.json")

empty_functions = set()
for path in CODE_ROOT.rglob("*.json"):
    data = json.loads(path.read_text())
    for ea, item in data.items():
        if not item.get("pseudo_code", "").strip():
            empty_functions.add(f"{path.stem}@{ea}")

with SOURCE.open(newline="", encoding="utf-8-sig") as fh:
    reader = csv.DictReader(fh)
    fieldnames = reader.fieldnames
    rows = list(reader)

kept = []
excluded = []
for row in rows:
    q = f"{row['bin_name_1']}@{row['fva_1']}"
    c = f"{row['bin_name_2']}@{row['fva_2']}"
    if q in empty_functions or c in empty_functions:
        excluded.append(row)
    else:
        kept.append(row)

with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(kept)

stats = {
    "source": str(SOURCE.relative_to(REPO)),
    "output": str(OUTPUT.relative_to(REPO)),
    "source_rows": len(rows),
    "excluded_rows": len(excluded),
    "kept_rows": len(kept),
    "empty_function_keys": sorted(empty_functions),
    "excluded_labels": dict(Counter(r["label"] for r in excluded)),
    "kept_labels": dict(Counter(r["label"] for r in kept)),
}
STATS.write_text(json.dumps(stats, indent=2) + "\n")
print(json.dumps(stats, indent=2))
if len(rows) != 5001 or len(excluded) != 18 or len(kept) != 4983:
    raise SystemExit("Unexpected D2 row counts; refusing to continue")
