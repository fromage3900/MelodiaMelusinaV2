# Next-Editor-Window Runbook — PPV Drift Fix + CaptureRender Live Proof

**Status:** READY — fires the moment the editor is closed for a rebuild, then reopened with Monolith on :9316.
**Sources:** `Docs/Plans/PPV_DRIFT_T3D_FIX_SPEC_2026-08-31.md`, `Docs/Handoffs/QOL_EXECUTION_QUEUE_2026-08-30.md` (order 1 → 2), `Docs/DASH_RENDER_SYSTEM_SPEC_2026-08-30.md`, `Source/BS_GodFile/MelodiaIntegration/MelodiaCaptureRenderSubsystem.*`.
**Naming note:** the render system is now `MelodiaCaptureRenderSubsystem` (renamed `05ff9755` to de-collide with the Polygonflow "Dash" toolchain SSOT). The "dash" wording below only refers to the gameplay `DashTrailGhost` surface.

---

## Phase 0 — Preconditions (all must be true)

1. **Editor closed** (rebuild window). Verify: `Get-Process UnrealEditor` → none.
2. **No lane committing to main** (history rewrite / merge / commit must be idle). Check `git status --porcelain` clean (except known peer AGENTS.md edit — leave it).
3. **Full closed-editor rebuild** of the CaptureRender rename (header change → UHT + relink, ~35s adaptive):
   ```powershell
   & "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" -WaitMutex
   ```
   Expect `Result: Succeeded`. Grep the log for `MelodiaCaptureRenderSubsystem`.
4. **Reopen editor**, confirm **single** UnrealEditor process + Monolith :9316 healthy (not a modal): `curl http://localhost:9316/health` → 200.

---

## Phase 1 — PPV drift fix (QOL #1; CaptureRender's `IsPPVStackCanonical` gate)

Canonical target: actor `PPV_NikkiDream`, blendables `MI_MelodiaInk 1.0` / `MI_MeluColorGrade 0.69` / `MI_StarryNight_Hero 1.0`, all `MD_POST_PROCESS`.

| # | Step | Tool | Verify |
|---|---|---|---|
| 1.1 | Rename actor `PPV_Dreamprint_Candidate` → `PPV_NikkiDream` | `ppv_set_label` | `ppv_find_actor` finds it |
| 1.2 | Set grade weight 0.18 → **0.69** | `ppv_set_blendable_weight` | re-read weight |
| 1.3 | Set outline weight 0.57 → **1.0** | `ppv_set_blendable_weight` | re-read weight |
| 1.4 | Replace `MI_StarryNight_VanGogh` (MD_SURFACE) → `MI_StarryNight_Hero` (MD_POST_PROCESS) | `ppv_remove_blendable` + `ppv_add_blendable` | `mi_get_domain` → MD_POST_PROCESS |
| 1.5 | Compile-check all 3 | `melodia_material_get_compile_stats` | 0 errors |

**Guard:** batch saves must use `unattended:true` (`Content/EnvSandbox/*` gitignored → a non-unattended save spawns one checkout-modal per package; observed 4:47 min for ~250 packages). Do NOT interleave with any other bulk-save lane.

After Phase 1, `UMelodiaCaptureRenderSubsystem::IsPPVStackCanonical` should return true (the gate becomes meaningful).

---

## Phase 2 — CaptureRender live proof (first real capture)

On `L_KaleidoNave` (beauty/wireframe/material/PCG 4-view cycle) via the subsystem API or direct Python:

1. Spawn/route a `USceneCaptureComponent2D` (HDR `RTF_RGBA16f`) — or call the subsystem:
   ```python
   # editor Python / Monolith editor_query
   # ConfigureSurface(Gameplay, FIntPoint(1920,1080)) -> IsPPVStackCanonical -> CaptureToRenderTarget -> CaptureToFile("L_KaleidoNave", Gameplay)
   ```
2. **DoD — all three evidence artifacts (AGENTS.md standard, never probe-only):**
   - 4 PNGs (`Saved/DashCaptures/L_KaleidoNave_{beauty,wireframe,materials,pcg}.png`)
   - assertion report JSON next to the frames (state, PPV canonical true/false, damage/resolution, error count)
   - the committed harness that produced both (`Tools/test_dash_capture.py` extended for live, or a new live harness — commit before run)
3. **DashTrailGhost surface:** trigger a dash (Glide/Dash/Swim traversal) mid-capture and confirm the ghost composite renders once. This is the only legit "dash" in the renderer.
4. Record a ledger row only from the live run: `Tools/echo_run.py record <gate> pass` — never from the offline probe.

---

## Phase 3 — Follow-ups (same window, in order)

| # | Item | Gate |
|---|---|---|
| 3.1 | Dead-node cleanup (QOL #2: 15 Niagara in `BP_MelusinaJRPGCharacter`, 5 in `WBP_MelodiaQuillDialog`, 1 in `BP_JRPGPlayerController`) — **re-derive live** with `blueprint_query search_nodes` before removal; compile + PIE smoke after | `dead_node_cleanup` |
| 3.2 | Echo preflight triage (`Saved/Audit/echo_preflight_triage_2026-08-31.json`): 6 gates were BLOCKED by the editor modal — now unblocked, re-run | echo gates |

---

## Phase 4 — Commit + push

1. Commit CaptureRender live harness + evidence (`Saved/Audit/capture_probe_*.{json,md}` + PNGs under `Saved/DashCaptures/`).
2. `git fsck` clean.
3. **Push is still gated on the assbin history purge** — do NOT attempt `git push` expecting success. Run the purge (`Docs/ASSBIN_HISTORY_PURGE_RUNBOOK.md`) in THIS quiet window first, then push.

---

## Hard rules (unchanged)

- One editor, one 9316 listener. Never two MCP surfaces on one graph.
- Never `git clean -fd` / `git checkout -- .` / `delete_asset` on foreign assets.
- No `Content/_PROJECT/` writes; no parallel material masters. CaptureRender drives the existing spine.
- `IsPPVStackCanonical` failure is a **warning** (log + evidence), never an auto-fix.
- Spec precedes mutation; batch saves `unattended:true`.