#!/bin/bash
# RLCD stage 3: the nine pre-registered tagger runs, then the dev evaluation (docs/RLCD_TRANSITION_PLAN.md).
# One job at a time on the GPU; a failed run is logged and the queue goes on. Dev only.
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python
LOG=runs/queue-stage3-tagger.log
mkdir -p runs
step() { echo "=== $(date '+%H:%M:%S') $*" | tee -a "$LOG"; }

step "queue start"
for system in N1 N2 N3; do
  for seed in 7 11 19; do
    if [ -e "runs/tagger-$system-seed$seed/tagger.pt" ]; then step "skip $system seed $seed (done)"; continue; fi
    step "train $system seed $seed"
    $PY scripts/train_tagger.py --system $system --seed $seed > "runs/tagger-$system-seed$seed.log" 2>&1 \
      && tail -1 "runs/tagger-$system-seed$seed.log" | tee -a "$LOG" || step "FAILED $system seed $seed"
  done
done
step "evaluate"
$PY scripts/eval_tagger.py >> "$LOG" 2>&1 || step "FAILED evaluate"
step "queue done"
