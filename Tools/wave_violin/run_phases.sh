#!/usr/bin/env bash
# WaveViolin "Night Reel" overnight runner — sequential, idempotent, headless.
# Each phase exits non-zero on crash; log records; later phases still attempt.
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
T="/c/EnvironmentPortfolio/BS_GodFile/Tools/wave_violin"
L="/c/EnvironmentPortfolio/BS_GodFile/Saved/Portfolio/wave_violin"
mkdir -p "$L/render_out"
LOG="$L/pipeline.log"
: > "$LOG"
for p in p00_stage p01_blockout p02_body_mats p03_transform p04_cymatics p05_ribbon_beads p06_drape p078_polish_export; do
  echo "=== $p start $(date +%T) ===" >> "$LOG"
  if [ -f "$L/render_out/${p%%_*}_report.json" ] || [ -f "$L/render_out/$(echo $p | cut -d_ -f1)_report.json" ]; then
    echo "skip $p (report exists)" >> "$LOG"; continue
  fi
  "$B" -b -P "$T/$p.py" >> "$LOG" 2>&1
  echo "=== $p exit=$? $(date +%T) ===" >> "$LOG"
done
echo "ALL DONE $(date +%T)" >> "$LOG"
