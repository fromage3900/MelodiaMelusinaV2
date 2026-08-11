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
| **C — Repo hygiene** | Git / CI / docs | Live-ops SOP, 50 MB slices, LFS audit, Echo promote hygiene | Public V2 done |
| **D — Swarm / phone** | jcode + cloud agents | Recipes A/B accepted; keep docs/audit only until A is green | Do not overlap editor with A |
| **E — Universal placement** | EnvSandbox PCG/materials (Windows LFS) | `placement50` manifest; lock Universal BPs | EnvSandbox absent on some cloud checkouts |

Cloud agents stay in **C/D** unless explicitly handed an editor-free **B** task. Never two editors. Never probe-only as `runtime` pass.

**Echo (current):** `author → spec_validate → inject → compile → static_gates → runtime_gates → record → promote` — [`specs/echo_pipeline.json`](../specs/echo_pipeline.json). Live-ops SOP: [`LIVEOPS_GIT_SOP_2026-08-11.md`](LIVEOPS_GIT_SOP_2026-08-11.md).

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

- Untracked Zbrush brush pack; MeshBlend LFS EOL; RestorePartyAfterBattle wired; `curentMP` → `currentMP`.
- Live-ops: `Docs/LIVEOPS_GIT_SOP_2026-08-11.md` aligned to current Echo pipeline.
- Collab slices: `specs/collab_slices/{docs50,slice50,placement50}.json` + onboarding tiers (gameplay ≈2 GB renamed from “lightweight”).
- Hooks: `cursor/*` allowed; dual LFS budget 50/512; `Tools/lfs_health_audit.py`; CI audits PR `base..HEAD`.
- Duplicate mirror inventory: `Docs/Reports/DUPLICATE_TREE_INVENTORY_2026-08-11.md` (33 tracked; no deletes).

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

- Text often; binaries once (`Docs/GIT_BATCH_DISCIPLINE.md` + `Docs/LIVEOPS_GIT_SOP_2026-08-11.md`).
- `python Tools/git_safe_push.py --check-only` before LFS pushes (50 MB on collab/cursor/docs).
- No `git clean -fd`, no `git checkout -- .`, no skill-Blueprint Python loads.
- Public V2: `https://github.com/fromage3900/MelodiaMelusinaV2`.
