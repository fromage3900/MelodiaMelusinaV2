# BS_GodFile Git Health — Overnight Triage Plan

## Goals
1. Get all commits pushed to remote
2. Resolve LFS missing objects (272 stale large files)
3. Update docs/task ledger with recent claims
4. Leave the repo in a clean, long-term-stable state

## Active Cron
- `d710a3d6e26e` — git-push-retry every 30 min
- Disables itself on success

## Triage Checklist (run each wake cycle)

### 1. Network Check
```bash
ping -n 2 github.com
```
If no response → skip push retry, document in log

### 2. Push Attempt
```bash
cd C:/EnvironmentPortfolio/BS_GodFile
git push origin feature/repo-lockin-20260813
```

### 3. If push fails on LFS (GH008 missing objects):
```bash
# Identify which objects are actually needed
git lfs ls-files -s HEAD | wc -l
git lfs ls-files -s HEAD | grep -E '(4thtimestillnobones|Nebula|ZenFallenMoon|KaleidoNave|vocoder|Backup)' | wc -l

# Option: identify truly-missing vs just-unpushed
git lfs fetch --all 2>&1 | tail -5
```

### 4. Doc Updates
- Fold `Docs/GIT_HEALTH_2026-08-19.md` into `Docs/Handoffs/RUNTIME_CONSOLIDATION_V3_2026-08-18.md`
- Update `Docs/P0_TASK_LEDGER.json` with any new claims from Kimi's session
- Update `AGENTS.md` with any new ground rules

### 5. Final Verification
```bash
git status
git log --oneline -5
git diff --stat HEAD~5 HEAD
```

## End State
- [ ] All commits pushed to remote
- [ ] Working tree clean
- [ ] LFS objects resolved (either uploaded or excluded)
- [ ] Docs updated with recent claims
- [ ] Task ledger current
- [ ] Cron job disabled (push succeeded)
