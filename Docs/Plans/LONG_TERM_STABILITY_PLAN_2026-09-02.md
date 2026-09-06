# BS_GodFile — Long-Term Stability Plan (2026-09-02)

**Author:** Melusina (autonomous review)
**Trigger:** User moving between PC, laptop, and Humber Labs for final year
**Goal:** Zero-downtime cross-machine development, clean source control, no lost work

---

## Part 1: Source Control — The Non-Negotiables

### 1.1 Git is the only truth

Every machine switch follows this protocol:

**Leaving a machine:**
```powershell
git add -A
git commit -m "WIP: [what you were doing]"
git push origin feature/<branch>
```

**Arriving at a machine:**
```powershell
git fetch --all --prune
git checkout feature/<branch>
git pull origin feature/<branch>
git lfs pull
```

No exceptions. No "I'll commit later." No "it's just a small change."

### 1.2 Branch discipline

| Branch | Purpose | Protection |
|---|---|---|
| `main` | Stable, shippable, CI green | PR required, no direct push |
| `feature/<name>` | Active development | Push freely, merge via PR |
| `hotfix/<name>` | Urgent fixes to main | PR required, fast-track |
| `experiment/<name>` | Throwaway spikes | Delete after, never merge to main |

### 1.3 Commit discipline

- **One logical change per commit.** Not "fixed 12 things."
- **Commit messages:** `<type>(<scope>): <description>` — `feat(harp): add gold leaf material`
- **No commits that break the build.** If CI was green, your commit should keep it green.
- **No bulk binary commits.** LFS is metered at 10 GB. Track only shipped assets.

### 1.4 What to NEVER commit

| Pattern | Why | Where it goes |
|---|---|---|
| `Binaries/`, `Intermediate/`, `Saved/` | Machine-specific, regenerable | `.gitignore` |
| `DerivedDataCache/` | Cache, regenerable | `.gitignore` |
| `.vs/`, `*.sln`, `*.VC.db` | IDE state | `.gitignore` |
| `Content/Textures/` (raw Figma) | 200+ files, not shipped | `.gitignore` |
| `Exports/` (working) | Ship to Helix Core or cold archive | `.gitignore` |
| `*.pyc`, `__pycache__/` | Python bytecode | `.gitignore` |
| `.claude/settings.local.json` | Machine-local Claude state | `.gitignore` |
| `Saved/Autosaves/`, `Saved/Crashes/` | Editor recovery files | `.gitignore` |

### 1.5 What to ALWAYS commit

| Pattern | Why |
|---|---|
| `Content/Melodia/**/*.uasset` | Curated shipped assets (LFS) |
| `Content/EnvSandbox/**/*.uasset` | Environment assets (LFS) |
| `Source/**/*.cpp`, `Source/**/*.h` | All C++ code |
| `Tools/**/*.py` | All Python tools |
| `Docs/**/*.md` | All documentation |
| `specs/**/*.json` | All contract schemas |
| `deploy/**/*.ps1`, `deploy/**/*.bat` | Deployment scripts |
| `Plugins/` (source) | Plugin code (not Binaries/) |
| `Config/*.ini` | Configuration |
| `*.uproject`, `*.Target.cs` | Project files |

---

## Part 2: Cross-Machine Workflow

### 2.1 Machine roles

| Machine | Role | Tools | Cron jobs |
|---|---|---|---|
| Desktop PC (froma) | Primary authoring | UE 5.8, Blender 5.2, Rider, Houdini, Monolith | Hot loop, daemons, expanders |
| Laptop | On-the-go editing | UE 5.8, Blender 5.2, Rider | Read-only (git-health, qwen) |
| Humber Labs | College workstation | UE 5.8 (shared), Blender 5.2 | Read-only only |

### 2.2 Path handling

**Never hardcode paths.** Use these patterns:

```python
# Python — repo root
import os
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Python — UE paths (always use UE's API)
import unreal
project_dir = unreal.Paths.project_dir()

# Shell — repo root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Shell — temp files
TEMP_DIR="$LOCALAPPDATA/Temp"
```

### 2.3 Python version discipline

UE 5.8 uses **Python 3.11**. Not 3.14. Not 3.12. 3.11.

```powershell
# Check UE's Python
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" --version

# Install deps into UE's Python
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" -m pip install <package>
```

### 2.4 Plugin portability

All 16 project plugins must be present on every machine. Check `.uproject`:

```json
{
  "Plugins": [
    {"Name": "Monolith", "Enabled": true},
    {"Name": "QuillScript", "Enabled": true},
    {"Name": "MelodiaWardrobe", "Enabled": true},
    ...
  ]
}
```

**Rule:** If you add a plugin on one machine, commit the `.uproject` change immediately. Other machines must pull before opening the editor.

### 2.5 LFS portability

LFS is metered at 10 GB. Current usage: ~9.19 GB.

**Before adding large files:**
```powershell
git lfs footprint  # see current usage
git lfs ls-files | Measure-Object  # count tracked files
```

**If budget is tight:**
- Move old exports to Helix Core or cold archive
- Use `git filter-repo` to purge history (carefully — see Part 5)
- Track only what ships, not what experiments

---

## Part 3: Testing Strategy

### 3.1 Test categories

| Category | Location | Count | Runs on |
|---|---|---|---|
| GMM Python simulations | `Content/Python/gmm/tests/` | 307 | Any machine |
| P0 content & integration | `Content/Python/Tests/` | 48 | Any machine |
| ECHO pipeline contracts | `Tools/test_echo_contract.py` | 77 | Any machine |
| MCP regression | `Tools/test_melodia_mcp.py` | 38 | Primary PC only |
| Offline preflight | `Tools/verify_p0_offline.py` | 12 | Any machine |
| C++ automation tests | `Source/BS_GodFile/Tests/` | Varies | Primary PC only |

### 3.2 Test discipline

- **CI must be green before merge.** No exceptions.
- **New features need tests.** If you add a gate, add a test.
- **Broken tests get fixed or deleted.** No `@skip` without a ticket.
- **Run full suite before machine switch:**
  ```powershell
  python -m unittest discover -s Content/Python/Tests -p "test_*.py"
  ```

### 3.3 Current failures (under repair)

| Test | Issue | Fix |
|---|---|---|
| `test_qsc_allowlist_contract` | Allowlist mismatch | Update allowlist for new gate |
| `test_wardrobe_disk_textures_and_slot_mappings` | Slot binding drift | Re-verify slot bindings |
| `test_on_disk_authored_textures_toon_monotonicity` | Toon shadow assertion | Fix toon material |
| `test_real_world_generated_assets_verification` | PBR tier2 asset check | Update asset verification |

---

## Part 4: Packaging & Deployment

### 4.1 The package cook (NEVER succeeded)

This is the real closeout gate. Here's the procedure:

```powershell
# 1. Close editor
taskkill /F /IM UnrealEditor.exe

# 2. Clean cook cache
rm -rf Saved/Cooked/*

# 3. Run cook (output to G: drive — C: only has 78 GB free)
"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun `
  -project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" `
  -noP4 -platform=Win64 -clientconfig=Shipping `
  -cook -map="L_MelusinaMorning+L_KaleidoNave+LV_SeaAbove_Prototype+MelodiaIntegrationMap" `
  -build -stage -pak -archive `
  -archivedirectory="G:\BS_GodFile_Products\P0_Itch_Release" `
  -unattended -utf8output
```

**Estimated time:** 30-60 min (cold cook of 88 GB Content tree)
**Risk:** C: disk space. Use G: (431 GB free) for output.

### 4.2 itch.io deployment

Once package_launch passes:
```powershell
# Install butler (if not present)
# Download from https://itch.io/docs/butler/

# Login
butler login

# Push to itch.io
butler push "G:\BS_GodFile_Products\P0_Itch_Release" <user>/<project>:windows-first-dream
```

**itch.io project slug:** TBD (need owner input)

---

## Part 5: What to Omit (Pain Elimination)

These are the things that will cause you the most pain. Omit or automate them.

### 5.1 Omit: Bulk Python MI creation

**Why:** 4 editor crashes tonight. The editor dies when you force-delete packages in bulk.
**Solution:** Create MIs one at a time through the editor UI, or use Monolith's native path.

### 5.2 Omit: Working on main directly

**Why:** Branch protection + 406 commits ahead. Push rejected.
**Solution:** Always work on feature branches. Merge via PR.

### 5.3 Omit: Autonomous hot loops on shared machines

**Why:** Hot loop commits mid-session, grows divergence, conflicts with your work.
**Solution:** Hot loop only on primary PC. Laptop and Humber Labs are pull-and-work only.

### 5.4 Omit: Large file commits without LFS check

**Why:** 164 MB `choralsheephi.assbin` got into history, blocked push.
**Solution:** Pre-commit hook catches this. Don't bypass it.

### 5.5 Omit: Editor work without single-editor check

**Why:** Two editors on one project = crashes, lost packages, corrupt assets.
**Solution:** Always `tasklist | grep UnrealEditor` before opening.

### 5.6 Omit: Guessing provider/model slugs

**Why:** Guessing wrong = 404, wasted tokens, failed jobs.
**Solution:** Use proven `opencode-go/deepseek-v4-flash` (free). Don't guess undocumented slugs.

### 5.7 Omit: Probe-only evidence for gates

**Why:** Calling `subsystem.register_lane_hit()` from Python proves the seam responds — NOT that a player sees a highway.
**Solution:** Real keyboard input through `BP_BattleUI::OnKeyDown` for runtime gates.

### 5.8 Omit: Vision model for render QA

**Why:** vision_analyze returns "character leg" for harp renders. Hallucinates.
**Solution:** Pixel-sampling (PIL/numpy) for objective QA. Human eye for subjective.

### 5.9 Omit: Force-push to main

**Why:** Branch protection + rewrites 406 commits + destroys other people's work.
**Solution:** Feature branches + PRs. Never `--force` to shared branches.

### 5.10 Omit: `git clean -fd` / `git checkout -- .`

**Why:** Bulk Content/ is untracked. `clean` deletes it permanently. `checkout -- .` reverts all work.
**Solution:** If you need to undo, `git stash` or `git checkout <file>` for specific files.

---

## Part 6: Automation & Cron Jobs

### 6.1 Safe to run anywhere (read-only)

| Job | Schedule | Purpose |
|---|---|---|
| `bsgodfile-git-health` | 3am daily | Read-only git health triage |
| `bsgodfile-recruiter-packet` | 4am daily | Generate recruiter docs |
| `qwen-daemon-reader` | Every 60m | Daytime reader |
| `qwen-daemon-overnight` | 2am daily | Overnight researcher |

### 6.2 Primary PC only (mutating)

| Job | Schedule | Purpose |
|---|---|---|
| `melodia-8h-hot-loop` | Every 45m | Autonomous build loop (PAUSED) |
| `copernicus-pipeline-expand` | Every 120m | Add Copernicus variants (PAUSED) |
| `copernicus-session-saver` | Every 120m | Save session state (PAUSED) |
| `universal-garment-loom-8h` | Every 45m | Garment system evolution (PAUSED) |

### 6.3 Cron discipline

- **Never enable mutating jobs on shared machines.**
- **Monitor disk space.** Cron jobs that fill the disk = editor crash.
- **Review cron output weekly.** Stale jobs waste tokens.

---

## Part 7: Documentation Maintenance

### 7.1 Front-facing docs (rewrite when state changes)

| Doc | Purpose | Update when |
|---|---|---|
| `README.md` | Project overview, quickstart | Gates change, architecture changes |
| `CURRENT_STATE.md` | Current status, test results | Every session |
| `CURRENT_SYSTEM_MAP.md` | Architecture diagram | Architecture changes |
| `AGENTS.md` | Agent rules, authority | Rules change |
| `Docs/P0_TASK_LEDGER.json` | Task-level authority | Tasks change |
| `Saved/gate_ledger.json` | Gate evidence | Gates change |

### 7.2 Doc discipline

- **No prose without evidence.** "10/10 gates pass" is a lie without ledger rows.
- **Update docs at machine switch.** Before you leave, update CURRENT_STATE.md.
- **Delete superseded docs.** Move to `Docs/_Superseded/`. Don't let them confuse.

---

## Part 8: Backup Strategy

### 8.1 Git remote (GitHub)

- Code, configs, tools, specs, docs — all tracked
- LFS for curated assets (10 GB metered)
- Push at every machine switch

### 8.2 Helix Core (pilot)

- `Exports/` depot path (change 2, 50 files)
- Binary art that doesn't fit LFS budget
- Final cutover pending sign-off

### 8.3 AWS Glacier

- Started 2026-08-13
- Long-term cold archive

### 8.4 Local backups

- `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26`
- `Saved/Recovery/`
- Per-asset `_OLD` variants

---

## Part 9: Immediate Action Items

### Before next machine switch:
- [ ] Fix 4 test failures (allowlist, slot bindings, toon, PBR)
- [ ] Run package cook (output to G: drive)
- [ ] Record `world_field_bus_pie` and `gaeA_live_pie` ledger rows
- [ ] Push to feature branch (fix LFS orphans first)
- [ ] Update `Saved/gate_ledger.json` with current state

### Before laptop setup:
- [ ] Install Git for Windows + LFS
- [ ] Install Python 3.11 (NOT 3.14)
- [ ] Install UE 5.8, Blender 5.2, Rider
- [ ] Clone + `git lfs pull`
- [ ] Run full test suite
- [ ] Verify editor opens

### Before Humber Labs setup:
- [ ] Same as laptop
- [ ] Do NOT enable cron jobs
- [ ] Do NOT run hot loop
- [ ] Read-only workflow only

---

## Part 10: The Hard Lessons (from this session)

1. **Filter-repo breaks LFS.** Purging large files orphans LFS objects. Push gets rejected. Fix: `git lfs push --all` after re-adding origin.

2. **Index.lock kills git.** Stuck git process recreates lock. Fix: `taskkill /F /IM git.exe; rm -f .git/index.lock`.

3. **Bulk Python MI creation kills the editor.** 4 crashes. Fix: One MI at a time through editor UI.

4. **Vision model hallucinates.** "Character leg" for harp renders. Fix: Pixel-sampling for QA.

5. **Package cook has NEVER succeeded.** Stale 2026-08-14 baseline. Fix: Cold cook on closed editor, output to G:.

6. **Shorewake skeleton mismatch.** 2-bone dress vs 465-bone Melusina. Fix: IK Retargeter or re-author.

7. **Bedrock Claude account-level disabled.** Console use-case form required. Fix: Owner files form.

8. **Claireon MCP DOWN.** Server not running. Fix: Editor's Claireon panel or `-StartMCPServer`.

---

*Melodia © 2026. Stability is not a feature — it's the foundation.*