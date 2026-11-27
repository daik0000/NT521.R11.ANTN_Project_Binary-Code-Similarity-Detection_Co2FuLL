#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."
source "$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")/etc/profile.d/conda.sh"
conda activate co2full-public
while [[ ! -f logs/rq2/RQ2_COMPLETE ]]; do sleep 60; done
python scripts/aggregate_rq2.py
python - <<'PY'
import csv
from pathlib import Path
src = Path("docs/rq2-metrics.csv")
rows = list(csv.DictReader(src.open()))
completed = Path("logs/rq2/RQ2_COMPLETE").read_text().strip()
lines = ["# RQ2 Ollama Results", "", f"Completed: {completed}", "", "Metrics use only valid yes/no tags; malformed responses are counted and excluded from metric denominators.", "", "| Model | Condition | Found / Expected | Valid | Malformed | Precision | Recall | F2 |", "|---|---|---:|---:|---:|---:|---:|---:|"]
for r in rows:
    lines.append(f"| {r['model']} | {r['condition']} | {r['found']} / {r['expected']} | {r['valid']} | {r['malformed']} | {float(r['precision']):.3f} | {float(r['recall']):.3f} | {float(r['f2']):.3f} |")
Path("docs/rq2-results.md").write_text("\n".join(lines) + "\n")
n_json = sum(1 for _ in Path("saved/Binkit-1.0-dataset/pairs/experiments/rq2_ollama").rglob("*.json"))
with Path("docs/rq2-execution.md").open("a") as f:
    f.write(f"\n## Final run status\n- Completed: {completed}\n- Aggregated conditions: {len(rows)}\n- JSON result count: {n_json}\n- Metrics: docs/rq2-metrics.csv and docs/rq2-results.md\n")
print("WROTE docs/rq2-results.md")
PY
