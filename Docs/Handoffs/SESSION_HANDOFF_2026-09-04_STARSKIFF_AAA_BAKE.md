# Session Handoff — Starskiff AAA Bake + Cymatic Research (2026-09-04)

> **Timestamp:** 2026-09-04 21:46 EDT (session active)
> **Lane:** asset-prep / Blender-Houdini offline bake (safe lane, no editor)
> **Branch:** `codex/game-state-2026-09-04` (handoff committed here; parallel lane
> active — branch switched off `llm/fromage/BS_GodFile/shorewake-chapter-loop`
> mid-session). Remote for sync: `legacy-melodia`.

---

## What happened this session (the short version)

Deep intake → safe-lane asset prep → Starskiff Houdini texture bake fixed +
staged → audio-reactive GN research → AAA polish review. **No editor was up, so
no `.uasset` was written.** Everything shipped is offline-authored + staged.

---

## 1. Starskiff texture bakes (DONE, verified)

Two suites authored Sep 4, both re-baked at 2048, seed `20260904`:

**Regal suite** — `Tools/Houdini/sea_above_reef/refined_starskiff_regal.py`
- Fixed a **32 GiB OOM bug** in `build_rope_normal` (`fbm()[...,None]` inflated
  2048² → 2048³). Full 13-map suite now cooks clean.
- Fixed **NaN in jewel + nail normals** (div-by-zero where blob→0, `mag` clamped
  to eps).
- **Rebuilt `Rope_Normal`** (was the AAA defect: 8 unique values, R=G=0.50 = flat
  emboss). Now a real braided helix: **138 unique, R/G lateral spread, min 0.263**.
- 13/13 outputs + manifest, NaN-free, fresh 20:54.

**Wood suite** — `Tools/Houdini/sea_above_reef/refined_starskiff_wood.py`
- 6/6 outputs (18-plank hull, barnacles, brass trim, wake emission), fresh 16:18.

**Known weakness (NOT fixed, flagged):** `T_Starskiff_Hull_Normal` (wood) is
near-flat — R std 0.0038, G std 0.037, B std 0.0026. The `np.roll` Sobel at
strength 4.5 isn't lifting subtle plank relief; reads smooth at distance. Worth
strengthening before it ships.

## 2. Import prep (STAGED, import BLOCKED on editor)

- **19 textures staged** into
  `Content/Melodia/Characters/Melusina/Textures/Clothes/` (regal 13 + wood 6),
  sha256-verified. Includes the **5 previously-missing** regal textures:
  `BrassFiligree_Normal`, `SternCrest_BaseColor`, `Jewel_BaseColor`,
  `Jewel_Normal`, `RegalEdgeWear_Mask`.
- Script: `Tools/Houdini/sea_above_reef/stage_starskiff_import.py`
- Manifest: `Saved/Audit/melusina_lookdev/starskiff_import_stage_manifest.json`
- **Import spec (one-shot contract):**
  `Saved/Audit/melusina_lookdev/starskiff_import_spec.md`
  (sRGB/compression/LOD per file, OpenGL Y+ normals, verify-by-re-read rule).

**BLOCKER:** No UnrealEditor process, Monolith :9316 down. Per one-editor gate,
do NOT fabricate `.uasset` from Python. When a single healthy editor is up, run
the import per the spec.

## 3. Audio-reactive GN research (partially wired, gap found)

Hull_Shell has two live GN modifiers in Blender 5.2:
- `MEL_starskiff_hull_form` (30 nodes) — procedural, music-driven shape.
- `MEL_starskiff_hull_audio` (20 nodes) — `GeometryNodeSampleSoundFrequencies`,
  band 40–320Hz, gain 1.2, stores float attr `audio_amplitude`, displaces along
  normal. Sound socket was `None`.

**Did:** synthesized a water-bed ambience + mixed the `128BPMarpeggiomelody_beatgrid.wav`
(30s mono 48k) into `Saved/Audit/sea_above/audio/Starskiff_Cymatic_Drive.wav`
(sha `d7f1ef5a`, generator `starskiff_cymatic_ambience.py`). Loaded it into the
GN sound datablock, set the group-input Sound socket, rewired the sample node.

**GAP:** evaluated mesh reads `audio_amplitude` = all-zero at every time. The
Sound socket on the modifier *instance* won't hold the loaded sound (resets to
None; `m['Sound']` not supported on NodesModifier in this Blender). Blender 5.2
sound-socket-override quirk. Cleanly separated from the texture import.

**Next step (future):** figure the Blender 5.2 way to pin a sound onto a
NodesModifier's exposed SOUND socket (or drive the sample node directly without
the group-input override), then the displaced hull + WPO bake works offline.

## 4. Stale docs found (fix or ignore)

- `Docs/Handoffs/SESSION_HANDOFF_2026-09-05_TONIGHT.md` cites 6 commit hashes
  (42cb25d7, 2326fbd0, …) that resolve on **no** branch — phantom hashes. The
  real StarskiffPawn C++ commit is `5d313567`. Doc's Starskiff status is misleading.
- `Docs/Plans/SEA_ABOVE_GIT_REVIEW_2026-09-04.md` says "main..HEAD has no
  commits" — now false (10+ ahead; `35805b25` landed during session).
- `Docs/LookDev/LOOKDEV_SESSION_BRIEF_2026-09-04.md` pins HEAD at 00f464b6 — stale.
- `CURRENT_STATE.md` "Starskiff Verified" is the Aug-13-era claim; C++ pawn
  (5d313567) still needs a closed-editor UBT rebuild + PIE to certify.

---

## Key files touched this session

| File | Purpose |
|---|---|
| `Tools/Houdini/sea_above_reef/refined_starskiff_regal.py` | regal suite (fixed OOM + NaN, rebuilt rope normal) |
| `Tools/Houdini/sea_above_reef/refined_starskiff_wood.py` | wood suite (re-baked) |
| `Tools/Houdini/sea_above_reef/starskiff_cymatic_ambience.py` | water+beat drive audio |
| `Tools/Houdini/sea_above_reef/stage_starskiff_import.py` | staging script |
| `Saved/Audit/melusina_lookdev/starskiff_import_spec.md` | import contract |
| `Saved/Audit/melusina_lookdev/starskiff_import_stage_manifest.json` | staged files + sha |

## Next session — pick up here

1. Bring up **one** editor + Monolith :9316, run the Starskiff import per the spec.
2. OR lift the **wood hull normal** strength so planks read at distance.
3. OR solve the **Blender 5.2 sound-socket-override** to finish the cymatic hull bake.

*No `.uasset` was written this session; all editor steps queue through the single-editor holder.*
