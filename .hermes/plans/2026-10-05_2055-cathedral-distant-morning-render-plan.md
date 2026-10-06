# Crystal Cathedral — Finish + Distant Staging in L_MelusinaMorning (Render Night Plan)

**Date:** 2026-10-05 20:55 (EDT)
**Author:** Melusina (Hermes)
**Status:** PLAN — awaiting go
**Goal:** Finish the Baroque Crystal Cathedral's critical path, export it from hython, import it into UE 5.8 as a new asset, place it in the distance of `L_MelusinaMorning`, and produce tonight's render plates.

---

## 0. TL;DR

The cathedral is **not lost** — it lives on the portable drive, built during the school session (2026-09-29). The C: workstation only has its pre-finish ancestors. Tonight's path:

1. Bring the foundry lane from `G:` into the C: repo (this is also the second copy — the foundry repo is local-only).
2. Rebuild + re-measure the HDA in **hython** (works on C:, Education-license-safe, no UE cook needed).
3. Stage 1 critical path: re-measure non-manifold (the known source was already removed — the README's "241" may be stale), prove the bevel, and add the **undulation** (the Baroque correction — the actual point of this lane).
4. Export post-finish geometry as OBJ (new small export script), import to UE as **new** assets under `/Game/Melodia/HoudiniFoundry/Cathedral/`, assign `MI_Copernicus_CrystalCathedral`, place in the horizon band (~2 km, ~9× scale), capture-iterate from the hero cameras, then 4K plates.

**Why hython export, not a UE Houdini Engine cook:** the school machine's Education license cannot cook HAPI inside UE, and a UE-side cook is unproven on C:. hython authoring/export is proven (it ran at school and runs here). HAPI cook is Stage 2's gate — not tonight's dependency.

**Current editor state:** UnrealEditor.exe is OPEN and in PIE on `L_MelusinaMorning` (log shows UEDPIE_0 worlds at 20:50–20:51). Do not disturb; stop PIE before any editor mutation, and never `load_level` immediately after a PIE stop (known crash).

---

## 1. Review — what exists, where (all verified tonight)

| Artifact | Location | State |
|---|---|---|
| HDA builder (authority) | `G:/Melodia_Houdini_Foundry/Tools/Houdini/cathedral/build_crystal_cathedral_hda.py` | 27,689 B, Sep 29. Self-contained VEX network; self-verifies Gate-2 counts in hython. No machine-specific paths. |
| Measurement tool | `G:/Melodia_Houdini_Foundry/Tools/Houdini/cathedral/measure_cathedral.py` | `hython measure_cathedral.py [--json]` → thickness mm, open/non-manifold edges, degenerate faces, bounds cm, walkable floor. |
| The HDA | `G:/Melodia_Houdini_Foundry/hda/HDA_Melodia_CrystalCathedral_1.0.hda` | 14,325 B. md5 `dc6ea1a4b579ed4e92cfa82c9a07557c` — byte-identical in the school mirror (`G:/BS_GodFile_School_20260925/hda/`). |
| Goal/audit doc | `G:/Melodia_Houdini_Foundry/GOAL_BAROQUE_CATHEDRAL.md` | Stage 0 DONE · Stage 1 UNPROVEN · Stage 2 pending. |
| School outputs | `G:/BS_GodFile_School_20260925/Saved/Audit/cathedral/` | `crystal_cathedral_manifest.json` + 2 OBJs (pre-finish, 2706/2101 & 1032/290). |
| C: repo scripts | `Tools/Houdini/cathedral/` | Only the OLD numpy builders (Sep 2, tracked). No HDA script, no measure tool, no `hda/` entry. |
| C: UE meshes | `Content/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_*` (8) | Sep 11, pre-finish. **Sea Above references them — never overwrite.** |
| C: hython | `C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe` | Works: 22.0.368, numpy 2.3.2. License server up (localhost:1715). |
| Distance band in Morning | `HorizonRidge_*` actors (4, saved in level) | Placed 2026-10-03 via `Saved/Audit/melusina_morning/_spawn_horizon_ridges_20261003.py`: south y≈−103k, north y≈+123k, west x≈−260k, east x≈+125k cm; up to 600 m tall; `NO_COLLISION`. |
| Playable clearance box | FORBIDDEN = x[−20000,15000], y[−15000,25000] cm | Keep every distant prop outside this box (ridge script enforces it). |
| Existing cathedral-ish level content | `SM_FloatingCrystal_Cluster_A/B` with `MI_Copernicus_CrystalCathedral` | The Sep 30 framing clusters — the material already lives in Morning and reads. |
| Horizon System Plan (active) | `Docs/Production/PCG/HORIZON_SYSTEM_PLAN_2026-10-04.md` | Silhouette layering / atmospheric perspective language; the cathedral is a natural distant landmark for it. |

**Stage 0 numbers (proven in hython at school):** base 2706 v / 2101 f · rose 1032 v / 288 f · post-finish 9278 v / 8641 f · collision 1682 v / 1608 f · walls 35 cm thick · walkable floor 529 upward faces / 67 m² · **241 non-manifold edges open at last README measurement** (but the current NAVE_VEX already removed the floor-quad coincidence that caused them — re-measure first, the number may have moved).

**Stage 1 open items (from the goal doc):** non-manifold → 0 · bevel proof · **undulation (Baroque correction)** · rose radial depth · hand-height ornament band.

---

## 2. Decisions needed (recommendation first)

1. **Rose face count 288 vs 290** — the recipe expected 290; the goal doc says "the 290 encoded a real bug" and calls it an owner decision.
   → **Recommend: accept 288** (current HDA), update the recipe's expected value with a note. Investigating the old 290 bug is not render-critical.
2. **Undulation amplitude** — the silhouette's new rhythm.
   → **Recommend: ship amp = 0.08 × span** (≈0.8 m at span 10 m); optional 3-variant contact sheet (0 / 0.08 / 0.15) if you want to choose by eye — default is ship-then-compare, not compare-then-ship.
3. **Placement sector & scale** — starting guess, confirmed by capture.
   → **Recommend: bearing ≈ hero-cam yaw −25°** (lands in the open left-third sky seen in both the Sep 30 beauty and the Oct 3 overview), **distance 200,000 cm (2 km), scale 9×** (≈230 m tall ≈ 16% of frame height at 40° FOV). Iterate from captures; prefer raising scale over moving closer.
4. **Save the level tonight?** — `L_MelusinaMorning` is ask-first.
   → **Recommend: yes, after you approve the capture round** — additive-only, labeled, receipted. (This request covers the ask.)

---

## 3. Track A — Finish geometry (hython on C:, no UE)

Run everything from repo root `C:/EnvironmentPortfolio/BS_GodFile`. hython = `"C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe"`.

### A1. Sync the foundry lane into C: (also = the second copy)
```bash
cp /g/Melodia_Houdini_Foundry/Tools/Houdini/cathedral/build_crystal_cathedral_hda.py Tools/Houdini/cathedral/
cp /g/Melodia_Houdini_Foundry/Tools/Houdini/cathedral/measure_cathedral.py Tools/Houdini/cathedral/
mkdir -p hda && cp /g/Melodia_Houdini_Foundry/hda/HDA_Melodia_CrystalCathedral_1.0.hda hda/
```
Keep the old numpy builders (they are the tracked ancestors). Commit these three files (Tools/ is not gitignored; `hda/` is tracked — `hda/ArpeggioStair_1.0.hda` is the precedent). No push without permission.

### A2. Rebuild + verify (proves the source still reproduces the HDA)
```bash
"/c/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" Tools/Houdini/cathedral/build_crystal_cathedral_hda.py
```
Success = rc 0, **no `FAIL` lines**, collision output present, and the rose reports 1032/288. (The main mesh prints `INFO ... changed the count, which is expected` for the finish stage — that is correct behavior, not a failure.)

### A3. Re-measure (current truth for the 241 claim)
```bash
"/c/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" Tools/Houdini/cathedral/measure_cathedral.py --json > Saved/Audit/cathedral/measure_post_sync.json
```
Record: `nonmanifold_edges`, `open_edges`, thickness mm, walkable m². If non-manifold is already 0, mark the goal doc's Stage-1 item as resolved-by-current-source and move on.

### A4. Stage 1 critical path (timeboxed, in this order)
- **A4a — non-manifold hunt (timebox 45 min, cuttable).** If count > 0: dump the non-manifold edge endpoint positions in hython; test the three suspects — (a) crystal prism base rings coincident with shell faces, (b) rib quads, (c) residual bay-seam points. Fix scoped (group-scoped fuse / generator nudge), re-measure, and require non-manifold = 0 **before** claiming the bevel does real work.
- **A4b — bevel proof (30 min, cuttable).** Compare edge counts at the bevel node's input vs output and confirm a chamfer ring exists on a sampled thickened wall edge (poly count delta alone is not proof). Receipt: `Saved/Audit/cathedral/bevel_proof.json`. Honest note: at 2 km the bevel is invisible — this is asset-standard work, not tonight's silhouette; do not let it block the render.
- **A4c — undulation (the Baroque correction; do this one).** Add controls `undulation_amp` (default 0.08·span) and `undulation_period` (default bay_len·√3 — the San Carlo 1:√3 armature); in `NAVE_VEX` apply lateral X offset `ox(y) = amp · sin(2π·y/period)` **per y-station** (both rings of a bay take the same offset at a shared y, so seams stay coincident), and apply the same `ox(y0)/ox(y1)` to the rib quad endpoints so ribs follow the wall. Rebuild → A2 checks still pass → re-measure (non-manifold must not regress).
  - Optional variants for the eye: amp 0 / 0.08 / 0.15 (three exports; only if you want the contact sheet).
- **A4d — rose radial depth (30 min, optional tonight).** Give the rose fan Z variation from its existing Chladni field; keep counts unless you chose to chase the 290.
- **A4e — hand-height ornament band: EXPLICITLY DEFERRED.** Invisible at distance; it belongs to the walkable-path pass.

### A5. Export for UE (new script)
Create `Tools/Houdini/cathedral/export_cathedral_obj.py` (hython): instantiate `HDA_Melodia_CrystalCathedral` from `hda/`, write OBJ via the existing `write_obj` helper pattern (already in `build_fractal_cathedral.py`):
- `Saved/Audit/cathedral/final/SM_Melodia_Cathedral_Crystal_6Bays.obj` (OUT_Cathedral)
- `Saved/Audit/cathedral/final/SM_Melodia_Cathedral_Crystal_Rose_6Bays.obj` (OUT_Rose)
- `Saved/Audit/cathedral/final/export_manifest.json` — counts, params, sha256 per file.

Run twice; **sha256 must match** (determinism receipt, per FoundryDay evidence standard).

---

## 4. Track B — UE integration + distant staging

### B0. Preconditions (once)
- You stop PIE. Then: editor liveness check (`tasklist | grep UnrealEditor`, port 9316 listener, `/health`, `MODAL_OPEN` grep in `Saved/Logs/BS_GodFile.log`).
- **One surface only**: run all in-editor Python through a single surface for the whole night (the established one for the Oct 3 ridge work). Never two (Claireon + Monolith) at once.
- No `deploy/*_LOOP_STOP` conflicts; snapshot the before-state (target folder list + actor list) as `before.json`.

### B1. Import (new script `Content/Python/import_cathedral_distant.py`)
- Destination: `/Game/Melodia/HoudiniFoundry/Cathedral/` (new folder — Sea Above's `SM_P4_*` stay untouched).
- Assets: `SM_Melodia_Cathedral_Crystal_6Bays` + `SM_Melodia_Cathedral_Crystal_Rose_6Bays`; import scale ×100 (meters→cm); normals computed on import; collision off.
- Assign `MI_Copernicus_CrystalCathedral` (existing, compiled, already reads in Morning) — single slot.
- Read back bounds and record (expect ≈1000 × 4550 × 2560 cm at scale 1, before undulation). Save assets; receipt `import_receipt.json`.

### B2. Place in the distance (new script `Content/Python/spawn_distant_cathedral_morning.py`, pattern = `Saved/Audit/melusina_morning/_spawn_horizon_ridges_20261003.py`)
- Guards: world is `L_MelusinaMorning` and not PIE; label `Distant_Cathedral_Morning_6Bays` not already present; FORBIDDEN-box clearance check; receipt JSON; actor folder `DistantLandmarks`; `NO_COLLISION`.
- Read (read-only) the transforms of `CAM_Hero_01_Meadow`, `CAM_Hero_03_RimOverlook`, `RENDERCAM_FLOATING_ISLANDS`; set bearing ≈ hero yaw −25°.
- Start: distance 200,000 cm; scale 9.0; yaw toward the hero area; base at z=0 (the ridge convention).

### B3. Capture-iterate (proven tool: `Content/Python/mi_preview_scenecapture.py` → `capture_still_from_camera`)
- 1920×1080 stills from the 3 cameras → `Saved/Audit/morning_distant_cathedral_20261005/`.
- Judge: does the silhouette read in the open sky? Is the crystal bloom sane (this MI was tamed once — watch for re-blowout at distance)? Adjust bearing / distance / scale / yaw. **Max 3 rounds.**

### B4. Approve → save
- You look at the captures. On approval: save the level (clear LFS read-only flags first), then close→reopen→recount sanity check per `12_UE_INTEGRATION_GATES.md`.

### B5. Render plates
- 3840×2160 stills from `CAM_Hero_01_Meadow`, `CAM_Hero_03_RimOverlook`, `RENDERCAM_FLOATING_ISLANDS` → `Saved/Audit/morning_distant_cathedral_20261005/plates/` (portfolio copies only after your pick).
- Stretch (only if stills finish early): MRQ loop via `MRQ_Preset_MI_Loop_1080` (note: `run_mrq_capture.py` is SakuraPath-bound; adapt the pattern, don't modify the original).

---

## 5. Evidence, receipts, commits

- `Saved/Audit/cathedral/` — `measure_post_sync.json`, `bevel_proof.json`, `final/export_manifest.json` (+ variant exports if requested).
- `Saved/Audit/morning_distant_cathedral_20261005/` — spawn receipt, capture rounds, plates.
- `CURRENT_STATE.md` — one new row, only with evidence (e.g. "Crystal Cathedral → UE distant staging | EDITOR PROVEN (scoped) 2026-10-05 | receipt + capture paths"). No other status doc.
- Commits: lane commits OK (standing authorization). `Saved/*` is ignored → `git add -f` for receipts. **No push without explicit permission.**

## 6. Risks / traps

- **PIE is live now** — stop it before mutations; never `load_level` right after a PIE stop (editor crash).
- **One editor, one writer surface** — no parallel MCP surfaces.
- **Do not overwrite `SM_P4_Cathedral_*`** — Sea Above references them.
- **Scale convention** — verify imported bounds ×100 before placing; a silent ×1 import would make the cathedral 45 m tall at 2 km (invisible).
- **Bloom** — distant crystal emissive can blow out; check the tamed MI params before touching the material.
- **Undulation must not open seams** — offset by y-station, never per-bay-ring; re-measure non-manifold after.
- **G: git** needs `git config --global --add safe.directory G:/Melodia_Houdini_Foundry` to read the foundry history (optional tonight; files read fine regardless).
- **Time discipline** — if A4a/A4b overrun, cut them (silhouette doesn't need them). Never cut A1–A3, A5, B1–B5.

## 7. Tonight's clock (suggested)

| Window | Work |
|---|---|
| 21:00–21:45 | A1–A3 sync, rebuild, re-measure |
| 21:45–22:45 | A4c undulation (+variants if wanted) |
| 22:45–23:30 | A4a/A4b if time · A5 export + determinism |
| 23:30–00:00 | B0–B2 import + first placement |
| 00:00–01:00 | B3 capture rounds (max 3) |
| 01:00–01:45 | B4 save · B5 plates |
| 01:45–02:15 | Receipts · CURRENT_STATE row · commit |

## 8. Files likely to change

- Add: `Tools/Houdini/cathedral/build_crystal_cathedral_hda.py` (synced), `measure_cathedral.py` (synced), `export_cathedral_obj.py` (new)
- Add: `hda/HDA_Melodia_CrystalCathedral_1.0.hda` (synced)
- Add: `Content/Python/import_cathedral_distant.py`, `Content/Python/spawn_distant_cathedral_morning.py`
- Edit: `recipes/houdini_foundry/crystal_cathedral_6bay_harmony.v1.json` (rose expected value — only if decision 1 confirmed)
- UE: new assets under `/Game/Melodia/HoudiniFoundry/Cathedral/`; `L_MelusinaMorning` (additive: one actor + its receipted save)
- Evidence: `Saved/Audit/cathedral/**`, `Saved/Audit/morning_distant_cathedral_20261005/**`
- `CURRENT_STATE.md` (one row)

## 9. Open questions

- Rose 288 vs 290 (decision 1) — default: accept 288.
- Undulation contact sheet — default: ship 0.08, compare later.
- Placement sector/scale — default: hero yaw −25°, 2 km, 9×; confirm from round 1.
