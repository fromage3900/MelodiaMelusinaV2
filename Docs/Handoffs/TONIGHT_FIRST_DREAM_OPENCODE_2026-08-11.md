# Tonight -- First Dream + OpenCode/Muse prep (2026-08-11)

**Goal:** After source-control + prep, close First Dream core gameplay with Rider + OpenCode
(B3 rhythm / B4 battle-result / B7 grade path), with Muse Code available as Meta terminal
companion. jcode remains the parallel **repo** swarm -- do not confuse lanes.

**Lane map**

| Lane | Tool | Tonight use |
|---|---|---|
| Repo swarm | jcode | Parallel docs/Python workers; not the C++/PIE driver |
| Gameplay IDE | OpenCode in Rider | MelodiaCore + Monolith-assisted Blueprint/PIE work |
| Meta agent | Muse Code (WSL) | Optional terminal agent; auth already DONE |

Refs: `Docs/Production/MUSE_CODE_LANE_2026-08-11.md`,
`Docs/PhoneOps/JCODE_SWARM_PIPELINE.md`, `.jcode/swarm-prompt.md` (MUSE role),
`Docs/Handoffs/CLOSEOUT_SOURCE_VERDICTS_2026-08-11.md`,
`.opencode/opencode.jsonc`.

---

## Tip state (check before Muse's "HEAD is 2623f02a" assumption)

Muse's study assumed V2 **HEAD = 2623f02a**. Local tip has moved.

```powershell
cd C:\EnvironmentPortfolio\BS_GodFile
git log -3 --oneline
git merge-base --is-ancestor 2623f02a HEAD; echo "ancestor_exit=$LASTEXITCODE"
```

- **2623f02a** is an ancestor; tip includes jcode harness, AGENTS section 5, LFS pointer fixes, CI, OpenCode/Muse lane wiring
- **Do not reset to 2623f02a.** Prep against current tip.

---

## Prep checklist (editor closed until the end)

### A. Source control

- [ ] `git status` -- reconcile dirty tree before surprise-commits
- [ ] `git lfs status`
- [ ] `git log --oneline -5` -- confirm no old 144-commit LFS history returned
- [ ] Note: push to github.com:443 may still be flaky; commit locally if needed, push later

Paste block when ready:

```text
git status:
Rider build: OK/FAIL
pie_smoke_runner: result
tip: <hash from git log -1>
```

### B. Rider build (no UE yet)

- [ ] Right-click `BS_GodFile.uproject` -> Generate Visual Studio Project Files
- [ ] Open in Rider -> Build **BS_GodFileEditor** Win64 Development
- [ ] Expect Target up to date or clean rebuild

### C. Tool smoke (no UE)

- [ ] `.\deploy\start_opencode_muse_lane.ps1` -- PASS for jcode + opencode; Muse optional
- [ ] `python Tools/pie_smoke_runner.py --help`
- [ ] `python Tools/regression_suite.py --help` (if present)
- [ ] `python Tools/playtest_harness.py --help` (agent infra 2026-08-11)
- [ ] Optional: `.\deploy\validate_collaborator_setup.sh` (Git Bash)

### D. OpenCode in Rider

- [ ] Rider plugin OpenCode installed (IDE 2025.2+)
- [ ] **Ctrl+\\** opens OpenCode terminal on 127.0.0.1:4096
- [ ] Tab: plan (readonly) vs build (edit)
- [ ] Project config: `.opencode/opencode.jsonc` (Monolith/Blender MCP disabled until editor up)

### E. Muse Code (optional companion)

- [ ] `wsl -e muse --version` -> Muse Code 0.1.0
- [ ] Auth already DONE per `Docs/Production/MUSE_CODE_LANE_2026-08-11.md`
- [ ] Workspace: `/mnt/c/EnvironmentPortfolio/BS_GodFile`

### F. Start editor only when prep is green

- [ ] Single UnrealEditor instance (one-editor rule)
- [ ] Monolith MCP live on **9316**
- [ ] Flip `.opencode/opencode.jsonc` `mcp.monolith.enabled` to `true` while editor is up
- [ ] Leave `Docs/ECHO/` ready for B3/B4/B7 rhythm gates

---

## Tonight execution block (after "ready")

1. **Gate 0:** `python Docs/T3D_Baseline/verify_baseline.py` (expect 55 clean)
2. **Travel/Input:** MelodiaCore authorities in Rider
3. **Battle closure:** OpenCode + Monolith -- Victory/Defeat/Fled/unavailable each resume/abort Quill exactly once
4. **Binary proof:** real keyboard path `BP_BattleUI::OnKeyDown` -> HitGrade -> DamageMultiplier with ledger row
5. **PIE smoke:** authored MorningIntro on `L_MelusinaMorning` via playtest harness / `pie_smoke_runner.py`

Route target:

`L_MelusinaMorning` -> `L_Melodia_Dreamstate` -> `L_KaleidoNave`

---

## Do not

- Start UE from `start_opencode_muse_lane.ps1`
- Overlap jcode MUSE workers with live Rider edits on the same `.cpp`
- Touch Sakura / `Content/_PROJECT/` / bulk `.uasset`
- Assume HEAD is still `2623f02a`
