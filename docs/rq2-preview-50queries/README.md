# RQ2 preview: 50 queries

This folder contains an interim sample from the active RQ2 run on `rl`.

## Contents

- `rq2-preview-50queries-input.csv`: the 250 selected query-candidate pairs (50 queries, exactly five candidates each).
- `rq2-preview-50queries-results.csv`: pair labels, model predictions, raw model output, and per-call time.
- `rq2-preview-50queries-summary.csv`: counts and correct predictions grouped by query.
- `xm-full_top5-250515.csv`: original D2 Top-5 source data.
- `xm-full_top5-rq2-ready.csv`: full D2 input after excluding the 18 rows with empty pseudocode.
- `raw_pair_outputs/`: 250 original Qwen JSON records. Each includes the actual prompt/pseudocode supplied to the model and its response.
- `binaries/`: 235 binaries needed for the 50 queries and their candidates; `manifest.csv` records source paths and SHA-256 checksums.

## Sample and run details

- Selection: 25 queries with a positive candidate and 25 queries with no positive candidate; each has exactly five candidates.
- Model/condition: local Ollama `qwen2.5-7b-8k`, Zero-Shot, `top_p=1.0`, `temperature=0.0`.
- 248 of 250 outputs match the expected `<same_source>yes/no</same_source>` format; two are malformed.
- On the 248 valid pair predictions: TP=5, FP=2, TN=221, FN=20; accuracy=91.13%, precision=71.43%, recall=20.00%, F2=23.36%.
- This is a balanced sample by query class, but its 248 valid pairs contain 25 positive and 223 negative labels. It is the initial Qwen 7B Zero-Shot preview, not the complete 50-query matrix.

## Full 50-query matrix

- A separate run started on `rl` on 2026-11-09 at 10:06 +07.
- It uses the six source prompts and five sampling configurations in `setting_exp` (Few-Shot), across all four local Ollama models.
- The initial Qwen 7B Zero-Shot JSON files in `raw_pair_outputs/` are reused.
- New outputs are written under `saved/Binkit-1.0-dataset/pairs/experiments/rq2_preview_50queries/` on `rl`.
- Progress and per-job logs are under `logs/rq2_preview50/` on `rl`; completion marker: `logs/rq2_preview50/RQ2_PREVIEW50_COMPLETE`.
- The full-D2 run remains separate under `rq2_ollama/`.
