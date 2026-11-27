# RQ2 Ollama Execution Record

Status: running in detached screen session rq2; final metrics pending.

## Scope and input
- Host: rl-vm2; project: /home/rl/Co2FuLL-public.
- Source D2: DBs/xm-full_top5-250515.csv (5,001 rows).
- Excluded 18 rows whose query or candidate has empty pseudo-code; input: DBs/xm-full_top5-rq2-ready.csv (4,983 rows: 488 positive, 4,495 negative).
- The original D2 CSV is preserved. One query still has a tied sixth candidate from the supplied Top-5 CSV.
- Pseudo-code: 2,209 JSON files, 5,841 function references; 10 functions have empty code, and all 18 affected rows were excluded as directed.

## Changes made on rl
- Installed openai==2.48.0 into Conda env co2full-public solely as the OpenAI-compatible client required by the source. All requests use http://localhost:11434/v1; no OpenAI API or key is used.
- Created Ollama tags from existing local weights: qwen2.5-7b-8k (num_ctx=8192), qwen2.5-14b-8k (8192), qwen2.5-coder-14b-8k (8192), deepseek-r1-14b-16k (16384).
- Modified LLM_exp.py so setting_exp includes all five required (top_p, temperature) tuples, including (1.0,0.0).
- Added scripts/prepare_rq2_input.py, which reproducibly builds the filtered D2 CSV and DBs/rq2_input_stats.json.
- Added scripts/run_rq2.sh and scripts/aggregate_rq2.py.

## Preflight
- python -m py_compile LLM_exp.py scripts/prepare_rq2_input.py passed.
- One source-code pair was run through all six prompts with Qwen 7B; six per-pair JSON files were produced.
- Direct source-client calls to all four context tags returned nonempty output.
- The model smoke was isolated under save_dir=rq2_preflight; full runs use rq2_ollama.

## Full run
- Screen session: rq2.
- Start: see logs/rq2/progress.log.
- Commands: scripts/run_rq2.sh; each job writes logs/rq2/{prompt,setting}_<model>.log.
- Output: saved/Binkit-1.0-dataset/pairs/experiments/rq2_ollama/.
- The script runs prompt and setting experiments sequentially by model, uses 2 request workers, and can be restarted; existing pair JSON is skipped by the repository code.
- Expected unique outputs: up to 199,320 JSON files (4 models × 4,983 pairs × 10 unique conditions). The Few-Shot (1.0,0.0) condition is shared between the two experiment modes.
- No final RQ2 metrics have been computed yet. When jobs finish, run python scripts/aggregate_rq2.py; malformed responses are counted separately and excluded from metric denominators. Metrics use valid responses only.

Run start: 2026-11-08T18:41:30+07:00
Current job: prompt_exp for qwen2.5-7b-8k, logged in logs/rq2/prompt_qwen2.5-7b-8k.log
Preflight: all four source-client model calls returned nonempty output; six prompt files produced for one Qwen 7B pair.

## Reproduction snapshot
- Captured: 2026-11-08T18:44:28+07:00.
- Full run began: START prompt/qwen2.5-7b-8k 2026-11-08T18:41:30+07:00.
- Active job: START prompt/qwen2.5-7b-8k 2026-11-08T18:41:30+07:00.
- Current JSON count: 21.
- SHA256 LLM_exp.py: 250085a5a365ea8f6f1d3f24c63945d9191bf7a3027a4898c8bfab0bb3c1c2ff.
- SHA256 filtered D2: 5c6f5e865e33c87ba7a0dd4a2c0d82b563a4af902abd6e87260b87ae850cc6e9.
- Python: Python 3.9.24; OpenAI-compatible SDK: 2.48.0.
- Final metrics: pending until all model/experiment jobs complete.

## Progress update
- Snapshot: 2026-11-08T18:47:11+07:00.
- Host: 16 vCPU, 60 GiB RAM; Ollama ollama version is 0.40.15; inference uses CPU (no nvidia-smi).
- Full-run JSON files currently present: 33.
- Current experiment: START prompt/qwen2.5-7b-8k 2026-11-08T18:41:30+07:00; prompt job progress is in logs/rq2/prompt_qwen2.5-7b-8k.log.
- Final metrics remain pending.

## Runtime snapshot
- Captured 2026-11-08T19:14+07:00: Qwen 7B Zero-Shot was at 175/4,983 pairs after 32m29s; current per-condition ETA was about 8h48m.
- This is one condition of one model. The complete matrix includes six prompts plus four additional Few-Shot settings per model, on four CPU-only Ollama models; end-to-end duration is likely multiple weeks and may vary with reasoning output and retries.
