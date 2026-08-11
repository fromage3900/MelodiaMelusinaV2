# Game Foundation Plan — MelodiaMelusinaV2
**Date:** 2026-08-11  
**Purpose:** One executable plan for long-term solid game building on the public V2 repo.  
**Folds:** `CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11`, `CLOSEOUT_SOURCE_VERDICTS_2026-08-11`, Echo campaigns 01–04, `GIT_BATCH_DISCIPLINE`, jcode acceptance, AGENTS evidence standard.

Done means a ledger row in `Saved/gate_ledger.json` — not prose.

---

## North star

Ship and prove this loop, then expand:

```text
Quill dialogue → allowlisted encounter → JRPG battle (+ optional rhythm)
  → typed result → Quill resumes once → exploration → canonical save
```

Route: `L_MelusinaMorning` → `L_KaleidoNave` (Dreamstate merged).

Authority: JRPG template owns combat/save; `UMelodiaNarrativeSubsystem` is the narrow bridge; Quill is narrative only; MelodiaCore is presentation.

---

## Parallel lanes (do not contend)

| Lane | Owner surface | Now | Blocked on |
|------|---------------|-----|------------|
| **A — Play proof** | One UE editor / Monolith 9316 | Campaign 1 real-input runtime gate | Windows workstation |
| **B — Source seams** | C++ (editor closed for header changes) | Post-battle restore wired; highway ownership already in tree | Full closed-editor build + PIE observe |
| **C — Repo hygiene** | Git / CI / docs (this PR) | LFS dirt, onboarding, CI budget gate, foundation docs | Public visibility (owner Settings click) |
| **D — Swarm / phone** | jcode + cloud agents | Recipes A/B accepted; keep docs/audit only until A is green | Do not overlap editor with A |

Cloud agents stay in **C/D** unless explicitly handed an editor-free **B** task. Never two editors. Never probe-only as `runtime` pass.

---

## Sequenced gates (single critical path)

1. **Static** — `python Tools/echo_run.py run static_gates` (or CI `echo_gates.yml` on self-hosted UE58).
2. **Observe highway ownership** — PIE stock rhythm; ambient tick must not clear stock highway (`bExecutionDrivingHighway`).
3. **Damage scalar** — source verdict PASS (2026-08-11); do not re-litigate; A/B uses `melodia.Rhythm.Disable`.
4. **`runtime`** — real Q/W/O/P through `BP_BattleUI::OnKeyDown`; assertion JSON + frames + `MELODIA_RHYTHM session=`; then Campaign 4 result matrix (Victory/Defeat/Fled/unavailable, Quill once).
5. **`save_load` + `repeat_consume`** — process restart; `melodia:stat:` idempotent per IntentId.
6. **`package_launch`** — Development cook + launch outside editor (gate is launch, not cook).
7. **Hygiene** — `bp_sweep.py` project-wide; duplicate MelodiaIntegration mirror only after owner sign-off (relocate, never delete).

---

## Done this foundation pass (cloud, 2026-08-11)

- Untracked `86419_Zbrush_Orb_Brushes_pack_for_Blender_3D/` (Blender tooling, not game) — files remain on disk, gitignored.
- MeshBlend LFS pointer EOL renormalize.
- Fixed `deploy/collaborator_onboarding.sh` (syntax + tier/REPO_DIR).
- Added `Tools/git_safe_push.py`; CI calls Python, not a missing `.ps1`.
- Ledger path exception in `.gitignore` for `Saved/gate_ledger.json` + `Saved/Echo/`.
- Wired `RestorePartyAfterBattle` on stock `OnBattleOver` before `CompleteBattle`; fixed map field `curentMP` → `currentMP`.
- Folded planning into this doc; refreshed README / PhoneOps / session handoff pointers.

---

## Workstation next (cannot fake from cloud)

```text
1. One editor, port 9316 only
2. Full closed-editor build (highway + restore landed in source)
3. PIE observe highway ownership
4. Campaign 1 real keys → record_gate.py runtime pass|fail
5. Campaign 4 → 2 → 3
```

Evidence standard: AGENTS.md § “Evidence standard — runtime/rhythm gates (2026-08-11)”.

---

## Repo rules that keep the game buildable

- Text often; binaries once (`Docs/GIT_BATCH_DISCIPLINE.md`).
- `python Tools/git_safe_push.py --limit-mb 512` before LFS pushes.
- No `git clean -fd`, no `git checkout -- .`, no skill-Blueprint Python loads.
- Public V2: `https://github.com/fromage3900/MelodiaMelusinaV2` (owner must flip visibility if still private).
