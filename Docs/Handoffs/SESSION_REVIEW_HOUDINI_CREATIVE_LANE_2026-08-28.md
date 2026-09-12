# Session Review — Houdini Creative Lane — Everything Shipped, Everything Open

**Date:** 2026-08-28 (night closeout)
**Scope:** the entire day's creative-pipeline work, reviewed with eyes on the actual renders.
**Companion docs:** `HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28.md` (plan + R-execution
log) · `Docs/Production/HOUDINI_CREATIVE_PIPELINE_REFERENCE_2026-08-28.md` (verified facts) ·
`Tools/Houdini/sea_above_reef/README_texture_suite.md` (runbook) ·
`Docs/Plans/HOUDINI_LOOKDEV_WEIGHT_PLAN_STARSKIFF_SHOREWAKE_2026-08-28.md` (dress/skiff).
This document is the single entry point for "what happened and what to trust."

---

## 1. The numbers (all counted on disk at closeout)

| Bucket | Count |
|---|---|
| Lane scripts (generators, verifiers, stagers, probes, QA) | **27** in `Tools/Houdini/sea_above_reef/` |
| Audit texture PNGs | 52 in `Saved/Audit/sea_above/houdini_variants/` |
| Audit mesh/JSON files | 45 in `Saved/Audit/sea_above/meshes/` |
| QA renders | 121 in `Saved/Audit/sea_above/renders/` (+ contact sheets) |
| Melusina lookdev audit | 11 files (dress 4 + skiff 4 + manifests) |
| **Staged into game content, hash-verified** | **55 in Reef/** (+8 dress/skiff in `Clothes/`) |

## 2. Delivered systems (what each thing IS)

| System | Generator | Deliverable | Verified |
|---|---|---|---|
| **R5 texture suite v1** | `tilable_sand_suite/shell_masks/clutter_atlas` | sand material set, caustics, 4 shell masks, 12 clutter sprites + atlas, floor mask | ingest 2-axis pass; U-loops by generator |
| **R1 corals** | `build_coral_generator.py` + `coral_textures.py` | 6 code-grown meshes (staghorn 1920 prims … reef cluster) + CoralSkin set | manifests + renders |
| **R3 kelp** | `build_kelp_vat.py` + `kelp_vat_textures.py` | 3 ribbon meshes + **sway LUT** (U=time, V=height), U-loop 1.246 | generator check |
| **R4 islands** | `build_island_generator.py` | 3 plateau+drip islands (2870/3486 prims) + 2 rock chunks | cook + manifest |
| **R5 v2** (subagent) | `texture_suite_v2.py` | droplet flipbook atlas, membrane reveal/ripple, wet-rock suite, barnacle crust, 12-PC pulse-band LUT, foam, sediment ramp | ingest pass (19/0 at the time) |
| **R6 jellyfish** | `build_jellyfish.py` + `jelly_surreal_lut.py` + `jelly_shapekeys.py` | **90 m bell with 3 morph targets** (topology-verified across poses) + **8 ribbon arms × 320 m (3.5 football fields)** as morph-bearing/static FBX + ArmLogic/Biolum LUTs | topology `True` ×3, U-loops 0.94/0.85, FBX 507/450 KB, **renders verified visually** |
| **R6 v2 iridescence** | `jelly_lookdev_v2.py` | veil BaseColor/Normal/Opacity/CanalMask/Irid_Mottle + **Iridescence LUT** + nematocyst glints | ingest 25/0 with the new U-only category |
| **Starskiff + Shorewake** | `starskiff_lookdev.py`, `dress_lookdev.py`, `dress_weight_lab.py` | 8 lookdev textures staged to `Clothes/`; weight lab **authored, not yet run** | 8/8 hash-OK; lab gated on a dress mesh |
| **Render QA suite** | `render_qa_blender.py` + `assemble_contact_sheets.py` | headless Blender Cycles clay/flat/sphere renders + labeled sheets | **used to catch 3 real defects** (§4) |
| **Probes** | `probe_hython_license.ps1`, `probe_file_write.py`, `probe_fbx_import.py` | license verdict; format discovery; FBX-import (GREEN) | all evidence-grade |

## 3. Verification ledger (every gate, final verdict)

- Texture ingest: **25 tiling targets pass / 0 fail**, 22 excluded (sprites, atlases, ramps,
  half-wrap LUTs) — under the three-category wrap semantics (2-axis / U-only / none).
- Jelly pose topology: **all `topology_matches: True`**.
- Hash staging: **55/55 Reef + 8/8 Clothes OK**; lookdev staging refuses overwrites (0 refused).
- License verdict: hython 22.0.368 GREEN headless; **no Engine license** (HDA-in-UE parked).
- FBX: **export blocked** on Apprentice, **import works** — the weight lab's read path is real.
- FBX morph payload: `JELLY_Bell.fbx` exports with Basis + 3 morph targets + root armature.

## 4. Review findings — the visual pass caught three real defects (and they are FIXED)

The closing review actually LOOKED at the renders (Read on the PNGs), which the byte counts and
logs had already side-eyed:

1. **Jelly QA frames were blank.** Two stacked causes: the fixed 4200 cm camera and all three
   lights sat **inside the opaque 4500 cm bell**, and the scene's 4,500–32,000 cm extents
   overflowed Blender's default **100-unit camera far clip**. Fixed: bbox auto-fit camera,
   inverse-square-scaled rig, `clip_end = 1e7`. Post-fix overview shows the scalloped bell and
   all 8 sweeping ribbon arms — the structure is real and reads beautifully.
2. **Mesh clay renders were near-black.** The rig used fixed ~2.6-unit light offsets (meter
   thinking) against centimeter-scale meshes — lights inside the geometry. Fixed: rig distances
   and energies now scale with the bounding diag. All 18 mesh renders re-shot bright.
3. **The re-render initially no-op'd** — my clip-line referenced `dist` before assignment
   (`UnboundLocalError` aborting the pass). Fixed; 18/18 fresh renders confirmed by mtime.

**Honest residue:** the staghorn render is still a rim-lit silhouette (thin branches +
clay) — acceptable for QA, but a **textured-material render pass** is the next QA upgrade.
The two jelly renders now differ (582 KB / 566 KB) and were verified visually.

## 5. Lessons ledger (consolidated — the session's durable engineering value)

1. Apprentice blocks **FBX and Alembic ROP export**; **FBX import works** (`hou.hipFile.importFBX`,
   no `suppress_warnings` kwarg). Geometry leaves via File SOP `filemode="write"` (menu token
   `"write"` — index 3 means "No Operation") as `.obj` + `.bgeo.sc`.
2. H22 Python SOP does **not prebind `geo`**; `errors()` returns a tuple; `ParmTuple` has no
   `.size()`; the Sweep SOP produced 0 prims headless (tubes are built in code); `_inject`
   placeholders must not be pre-quoted in templates (double-wrapping); `hou.Vector3` lacks
   `rotateAroundAxis` (Rodrigues); noise periods must divide the grid (powers of two on 1024);
   Python 3.14 hard-errors `global` after use.
3. **OBJ carries one UV set** → per-vertex VAT is impossible via OBJ; the LUT pattern
   (U=time loop, V=growth axis) is the shipping answer; half-wrap textures need a U-only seam
   check (a V-axis check false-fails by design).
4. Radial-domain textures (bell maps) are **U-only wrap** — the verifier now has three wrap
   categories, and its gradient-relative seam metric (plus flat-field floor) is the honest judge.
5. **Background Blender: always `-b --factory-startup -noaudio`** — user addons abort scripts;
   5.2 can hang at exit after all work flushes (kill-safe once the manifest exists); camera
   `clip_end` defaults to 100 units and silently blanks cm-scale scenes; light/energy/camera
   distances must scale with the bounding box; deselect before `join()`.
6. **Subagent reports are claims; disk is truth** — one subagent returned "completed" with an
   empty report and no file. `Test-Path` + `py_compile` before building on delegated work.
7. Never run hython bare in a shared console (license-server hangs wedge the shell) — the
   isolated-probe pattern exists and works.
8. Evidence culture paid repeatedly: the ingest verifier caught a real Voronoi edge-band bug,
   the seam-metric false positives, and this review's blank-frame catch — every one was a bug
   that would otherwise have shipped invisible.

## 6. What is NOT proven / open (the honest list)

1. **Nothing is in the engine yet.** The editor was down all session; all UE wiring (texture
   imports, MI bindings, morph skeletal import, WPO materials, wardrobe slot) is queued and
   specified in `IMPORT_QUEUE.md` — including the full iridescent bell recipe and parameter
   manifest. First import session must confirm: morph targets visible on the bell skeletal
   mesh, LUT-driven WPO on arms at 24 m amplitude reads well (not clipped/jittery).
2. **Weight lab never ran** — authored and gated, waiting on the Blender dress mesh
   (adapt V2 skirt) and the owner inputs (Cos id, skirt-slot vs full-body, v22 texture set).
3. **Bell closeup camera** frames the margin + arms; a dedicated full-bell beauty shot with the
   iridescent material is queued for the first editor session (clay-only tonight).
4. **Performance unknowns:** arms are Nanite-able statics, but the morph-bearing bell imports
   as a **skeletal mesh — no Nanite on skeletal**; at 4320 verts that is fine, recorded so
   nobody "fixes" it later. WPO at 24 m needs an in-engine look.
5. **Overnight learn loop remains demo-mode**; groom real-ABC remains impossible on Apprentice
   (both documented corrections).
6. **P0 is untouched by all of this** — the five open gates still close only through the PIE +
   ledger path (the creative lane shares the one-writer rule and nothing else with P0 systems).

## 7. Documentation map (who owns what)

| Doc | Owns |
|---|---|
| `HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28.md` | the plan + R1–R6 execution log + red lines |
| `HOUDINI_CREATIVE_PIPELINE_REFERENCE_2026-08-28.md` (Production/) | verified facts, patterns, probes, render QA — read before ANY Houdini work |
| `README_texture_suite.md` (sea_above_reef/) | runbook: cook commands, import tables, determinism contract |
| `HOUDINI_LOOKDEV_WEIGHT_PLAN_STARSKIFF_SHOREWAKE_2026-08-28.md` (Plans/) | dress/skiff lookdev + weight-paint pipeline + execution log |
| `IMPORT_QUEUE.md` (Reef/ in Content) | the editor holder's per-file import contract + iridescent recipe + parameter manifest |
| This document | the session-wide review + inventory + open items |

## 8. Next-session queue (priority order)

1. **Editor import session** (holder): execute `IMPORT_QUEUE.md` end-to-end — textures, meshes,
   FBX morphs — then re-read bound parameters through Monolith as evidence.
2. **In-engine jellyfish look**: iridescent bell material per the recipe; verify morphs + WPO on
   camera; retune `SweepAmplitudeMetres`/`CanalGlow` to taste.
3. **Shorewake dress mesh** (Blender, adapt V2 skirt) → run the weight lab to GREEN → apply
   weights → FBX → wardrobe slot (owner inputs §5 of the lookdev plan first).
4. **Textured render pass** for the QA suite (albedo/normal materials instead of clay) so future
   sheets judge shading, not just form.
5. P0 continues independently: the five open gates close through PIE + ledger only.

---

## 9. Addendum — post-review work (same session, later)

After this review was written, the lane delivered: **THE LEVIATHAN** (ribcage + iridescent
scale shingles), **THE DROWNED ORGAN** (12 pitch-class pipe ranks), **the Dreams Lane**
(3 VDB volumes for UE Sparse Volume Textures, frozen-cloth morph FBXs, code-L-system
flora), **the Starskiff MK2** (owner's desktop project expanded on a copy), and the
**Shorewake dress arc**: 48 labeled material slots (`SW_Dress_P01–48`, verified 48/0) for
Substance, the owner's own rigged/weighted import superseding the automated path, the
magical layer on the posed rig (4,120 fluff tufts + 7,258 scale plates + flip/inflate
variants — all three steps green), and the **shine kit** (iridescent scale-shimmer overlay
+ coverage mask, 33/0 ingest, staged to `Clothes/`).

**New verified facts:** Blender **5.2 background-mode color pipeline is broken on this
machine** (pure-red world renders black/white; **4.3/4.5 render correctly — all QA renders
must use 4.5**); 5.2's compositor is always-on via `compositor_node_group`
(`scene.node_tree` removed in 5.2) and a USD import can leave a graph that whites out
renders; USD imports also leave stray root objects that must be deleted; USDZ garments
import as per-panel meshes whose materials need full graph rebuilds (no "Principled BSDF"
node to patch). Owner's editor was live throughout — the stager's lock-handling skipped
held files gracefully with zero Content conflicts.

**Open:** Pass C (merge magical layer + 5 morphs + 48 slots onto the owner's rigged dress,
one Blender pass), in-engine iridescent material verification, dress posing QA.
