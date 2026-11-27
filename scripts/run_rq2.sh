#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."
source "$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")/etc/profile.d/conda.sh"
conda activate co2full-public
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p logs/rq2
models=(
  qwen2.5-7b-8k
  qwen2.5-14b-8k
  qwen2.5-coder-14b-8k
  deepseek-r1-14b-16k
)
common=(-data_path DBs/xm-full_top5-rq2-ready.csv -url http://localhost:11434/v1 -api_key sk-null -n_jobs 2 -save_dir rq2_ollama)
run_job() {
  label=$1
  logfile=$2
  shift 2
  echo "START $label $(date -Is)" | tee -a logs/rq2/progress.log
  if "$@" >>"$logfile" 2>&1; then
    echo "DONE $label $(date -Is)" | tee -a logs/rq2/progress.log
  else
    status=$?
    echo "FAILED $label exit=$status $(date -Is)" | tee -a logs/rq2/progress.log
    exit "$status"
  fi
}
for model in "${models[@]}"; do
  run_job "prompt/$model" "logs/rq2/prompt_${model}.log" \
    python -u LLM_exp.py -exp prompt_exp "${common[@]}" -model "$model"
  run_job "settings/$model" "logs/rq2/setting_${model}.log" \
    python -u LLM_exp.py -exp setting_exp "${common[@]}" -model "$model"
  ollama stop "$model" >/dev/null 2>&1 || true
done
date -Is > logs/rq2/RQ2_COMPLETE
echo "RQ2_ALL_JOBS_DONE $(cat logs/rq2/RQ2_COMPLETE)" | tee -a logs/rq2/progress.log
