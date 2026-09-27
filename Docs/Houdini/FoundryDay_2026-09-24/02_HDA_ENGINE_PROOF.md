# 02 — Gate 1 (P0): custom HDA → Houdini Engine → UE 5.8 cook → bake → save → reload → audit

| | |
|---|---|
| **Purpose** | Close the one proof `CURRENT_STATE.md` says is missing: a **custom Melodia HDA** cooked and baked inside UE, with a receipt. |
| **Authority** | Houdini authors the HDA; UE owns the baked result (static mesh actors). No runtime HDA cook; the cooked Houdini Asset Actor is removed or left un-cooked after bake. |
| **Inputs** | `recipes/houdini_foundry/hda_engine_smoke_arpeggio_stair.v1.json`; `Content/Python/create_hda_arpeggio_stair.py` (existing generator); `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` §4–6. |
| **Outputs** | `hda/ArpeggioStair_1.0.hda`; baked static mesh(es) under `/Game/Melodia/HoudiniFoundry/HDA/`; `bake_manifest.json`. |
| **Dependencies** | Gate 0 PASS; licence that writes commercial `.hda`; Houdini Engine plugin matching the college Houdini build; UE 5.8 + project. |
| **Evidence** | `Saved/Audit/houdini_foundry/hda_engine_smoke_arpeggio_stair/` |
| **Status** | STAGED. `.hda` not on `main`; no cook receipt exists anywhere. |
| **At college** | Everything below. |

**Reuse, do not rebuild:** ArpeggioStair is the existing smoke design (16 × 4 = 64 pads, seed 1337). Do not author a second smoke HDA. If `create_hda_arpeggio_stair.py` fails on H22 API drift, fix it in place (it is the owning script) and note the fix in the commit.

## Steps

1. **Houdini side (agent).**
   ```powershell
   python Tools/Houdini/foundry/houdini_foundry.py validate recipes/houdini_foundry/hda_engine_smoke_arpeggio_stair.v1.json
   & $env:HOUDINI_HYTHON_EXE Content/Python/create_hda_arpeggio_stair.py --out hda/ArpeggioStair_1.0.hda
   ```
   Record: Houdini version (`hou.applicationVersionString()`), licence category, the HDA's type name/version, sha256 of the `.hda`.
2. **UE preflight (editor closed).** `py Content/Python/smoke_houdini_engine_pcg.py --json`. It hardcodes `C:\Program Files\Side Effects Software\Houdini 22.0.368` — on a different build, expect `hython` FAIL there. Record the actual paths instead of editing the script mid-gate.
3. **Open UE 5.8.** Confirm the Houdini Engine session connects (Houdini Engine menu → Session status). Record the plugin version string.
4. **Import** `hda/ArpeggioStair_1.0.hda` into `/Game/Melodia/HoudiniFoundry/HDA/`.
5. **Place** a Houdini Asset Actor. **Map choice is ask-first:** either a new `L_HoudiniFoundry_Smoke` map (default; zero risk to other tests) or an **additive** labelled fixture `HoudiniFoundry - HDA Smoke ArpeggioStair` in `MelodiaIntegrationMap` (never reorganise existing actors). Wrap spatial edits in `scene_context_cycle.begin()/end()`.
6. **Cook** with seed 1337, stepCount 16, laneCount 4. Capture: cook log, output count, the point attributes `seed, midiNote, lane, stepIndex` present on output.
7. **Bake** (Houdini Engine → Bake → to Actors or Blueprint), output folder `/Game/Melodia/HoudiniFoundry/HDA/Baked/`. Record baked asset paths.
8. **Before/after state:** actor list + baked asset list before cook and after bake (use `scene_context_cycle`).
9. **Save** (one writer; clear LFS read-only flags first). **Close the map, reopen it**, and recount the baked actors and assets. They must be equal.
10. **Audit:** write `bake_manifest.json` (schema `melodia.houdini_foundry_bake_manifest.v1`) with the `ue` block filled: `engine_version`, `houdini_engine_plugin_version`, `baked_asset_paths`, `saved: true`, `reloaded_equal: true`. Then run `python Tools/Houdini/foundry/houdini_foundry.py verify <manifest>`.
11. Optional musical chain (smoke spec §6): only if the pad Blueprint wiring exists. It is **not** required for Gate 1 PASS.

## Failure handling

If any step fails, still write the manifest with `status: "FAIL"` or `"HOLD"` and a `failure_log`: the exact error text, the step number, and versions. A clean FAIL receipt is useful evidence; a missing receipt is not.

## Done when

The manifest verifies, the baked assets are saved and survive a reload, and `CURRENT_STATE.md`'s Houdini Engine row can honestly change from "LIVE UE HDA COOK NOT PROVEN" to "LIVE PROVEN (smoke)" with a link to the evidence. The owner makes that edit or approves it.
