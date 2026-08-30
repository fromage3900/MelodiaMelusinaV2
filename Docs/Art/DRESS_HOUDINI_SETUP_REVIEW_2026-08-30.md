# Shorewake Dress — Houdini/Blender Setup Review (2026-08-30)

Audit scope: every dress-specific setup under `Tools/Houdini/sea_above_reef/` plus the
manifests in `Saved/Audit/melusina_lookdev/`. Every claim below was verified by reading
the file and checking the output path on disk on 2026-08-30. Line references are
`file:line`.

---

## (a) Inventory

### Geometry / mesh setups

| Setup | Runtime | What it does | Inputs | Outputs | Run command | Seed | Outputs on disk? |
|---|---|---|---|---|---|---|---|
| `dress_48_materials.py` | Blender (`-b --factory-startup`) | Rebuilds dress from source USDZ with **one labeled material per panel** (`SW_Dress_P01..P48`), joins panels, scales m→cm (×100), fixes normals, exports Substance-ready FBX | `C:\Users\froma\Downloads\melusinashorewake.usdz` (`dress_48_materials.py:22`) | `Saved/Audit/melusina_lookdev/Shorewake_48MAT.blend`, `SM_ShorewakeDress_48MAT.fbx`, `dress_materials_manifest.json` | `blender -b --factory-startup -noaudio --python dress_48_materials.py` | None needed (no RNG); manifest has **no seed field** | ✅ all three (blend 2026-08-29 23:07, fbx 2026-08-29 01:39, manifest slot_count=48, `empty_slots: []`) |
| `shorewake_pass_a.py` | Blender | **PASS A** — inspect owner's posed `shorewake.fbx`, dump inventory JSON (objects/armatures/morphs/materials), export all meshes as world-space Y-up OBJ for Houdini | `C:\Users\froma\OneDrive\Desktop\shorewake.fbx` (`shorewake_pass_a.py:17`) | `Saved/Audit/melusina_lookdev/magical/passA_inventory.json`, `magical/posed/shorewake_all_meshes.obj` | `blender -b --factory-startup -noaudio --python shorewake_pass_a.py` | None (no RNG) | ✅ both (inventory 8.5 KB; posed OBJ 25.6 MB) |
| `build_dress_magical.py` | Houdini hython | **PASS B v2** — self-writing Python SOPs: boundary-loop detect → hem fluff tufts (`magical_ridges.obj` + inflate offsets) → bodice hex scale plates (`magical_scales.obj` + `scales_plates.json`) | posed OBJ from Pass A (`build_dress_magical.py:20-21`) | `magical/boundary_loops.json`, `magical_ridges.obj`, `ridges_inflate.json`, `magical_scales.obj`, `scales_plates.json`, `dress_magical_manifest.json` | `hython Tools/Houdini/sea_above_reef/build_dress_magical.py` | **SEED=20260828, recorded** in manifest (`build_dress_magical.py:23`, manifest `"seed": 20260828`) | ✅ all; manifest `steps_ok: {detect,ridges,scales}=true`, `hython: 22.0.368`; 4120 tufts / 10901 plates |
| `shorewake_pass_c.py` | Blender | **PASS C** — import owner FBX, relabel 48 slots, join, transfer skin weights from dress onto magical geometry, join, author 5 morphs (Nikki_Bloom/Swirl, ShimmerWave, ScaleFlip, FluffInflate), parent to armature, export FBX + 2 QA Cycles renders + manifest | owner `shorewake.fbx` (`shorewake_pass_c.py:29`) + Pass B outputs | `Saved/Audit/sea_above/skiff/SK_ShorewakeDress_Magical.fbx`, `DRESS_Neutral.png`, `DRESS_Transform.png`, `shorewake_magical_manifest.json` | `blender -b --factory-startup -noaudio --python shorewake_pass_c.py` | None (no RNG) | ✅ all (FBX 25.1 MB 2026-08-29 15:52; manifest verts=268281, ridges=8240, plates=10901) |
| `dress_transform.py` | Blender | Earlier standalone USDZ→FBX transformation lane: 3 morphs (Bloom/Swirl/ShimmerWave) + root armature + QA render + manifest. **Superseded by Pass C for the rigged dress** but outputs still current on disk | same USDZ as 48MAT (`dress_transform.py:24`) | `Saved/Audit/melusina_lookdev/SK_ShorewakeDress.fbx`, `shorewake_transform_manifest.json`, `Saved/Audit/sea_above/renders/skiff/SHOREWAKE_TRANSFORM_QA.png` | `blender -b --factory-startup --python dress_transform.py` | None | ✅ all (FBX 13.5 MB 2026-08-29 02:41, manifest panels=48 verts=183741, QA render present) |

### Texture setups (pure Python, `reef_common` based)

| Setup | Runtime | What it does | Outputs | Run command | Seed | Outputs on disk? |
|---|---|---|---|---|---|---|
| `dress_lookdev.py` | python+numpy+PIL | Fitted-cloth texture set `T_MelusinaC_DressShorewake_{BaseColor,Normal,Emission,Roughness}` 1024px — seafoam→teal gradient, hem foam crest, Worley silk mottle, static emission (no MPC writer by design) | `Saved/Audit/melusina_lookdev/houdini_variants/T_MelusinaC_DressShorewake_*.png` + `dress_shorewake_manifest.json` | `python Tools/Houdini/sea_above_reef/dress_lookdev.py [--seed N --size N]` | **20260828, recorded** via `rc.write_manifest` (`reef_common.py:234` writes `"seed"` key) | ✅ all 4 PNGs + manifest (2026-08-28 18:56) |
| `dress_shine_kit.py` | python+numpy+PIL | Iridescent overlay pair `T_DressShorewake_ScaleShimmer` (RGB, toroidal hex lattice, per-plate spectral hue) + `T_DressShorewake_ScaleMask` (gray coverage) for the UE material Lerp | `Saved/Audit/sea_above/houdini_variants/T_DressShorewake_Scale{Shimmer,Mask}.png` + `dress_shine_kit_manifest.json` | `python Tools/Houdini/sea_above_reef/dress_shine_kit.py [--seed N --size N]` | **20260828, recorded** in manifest | ✅ all (2026-08-29 15:26) |

### QA / weight lab

| Setup | Runtime | What it does | Outputs | Run command | Seed | Outputs on disk? |
|---|---|---|---|---|---|---|
| `render_48mat.py` | Blender | Visual proof of 48 slots: opens `Shorewake_48MAT.blend` read-only, strips Blender 5.2 compositor group + stray USD root objects, rebuilds each material graph with a distinct pastel, 3/4 Cycles render | `Saved/Audit/sea_above/renders/skiff/SHOREWAKE_48MAT_SLOTS.png` | `blender -b --factory-startup --python render_48mat.py` | None; **no manifest written** | ✅ PNG present |
| `dress_weight_lab.py` | Houdini hython | Bone Capture (biharmonic) of dress mesh against deform bones, clamp 4 influences, QA gate (`weight_qa.json`: zero-weight verts == 0, over-4 == 0) + `weights.json` for a Blender applier | `Saved/Audit/melusina_lookdev/weight_lab/{weight_qa.json,weights.json}` | `hython dress_weight_lab.py --mesh <dress.fbx> --skeleton <melusina.fbx>` | None | ❌ **never run** — `weight_lab/` directory does not exist |

---

## (b) How the pieces chain

```text
OWNER FILES (outside repo — single copies):
  C:\Users\froma\Downloads\melusinashorewake.usdz   (48 USDZ panels, unposed)
  C:\Users\froma\OneDrive\Desktop\shorewake.fbx     (48 posed panels on v22 rig)

TEXTURING LANE (Substance-bound):
  dress_48_materials.py ──► Shorewake_48MAT.blend + SM_ShorewakeDress_48MAT.fbx
        │                    + dress_materials_manifest.json (slot↔panel map)
        └─► render_48mat.py (opens blend read-only) ──► SHOREWAKE_48MAT_SLOTS.png

MAGICAL LANE (posed, rigged):
  shorewake_pass_a.py ──► posed/shorewake_all_meshes.obj + passA_inventory.json
        │
        ▼ (hython)
  build_dress_magical.py  [PASS B, seed 20260828]
        │                  ──► magical_ridges.obj (+ridges_inflate.json, 4120 tufts)
        │                     magical_scales.obj (+scales_plates.json, 10901 plates)
        ▼
  shorewake_pass_c.py     [PASS C]  owner FBX + Pass B OBJs
        │                  ──► SK_ShorewakeDress_Magical.fbx (268281 verts, 48 slots,
        ▼                     5 morph targets) + 2 QA renders + manifest
  → UE import (FBX w/ morphs + armature)

TRANSFORMATION LANE (superseded, still on disk):
  dress_transform.py ──► SK_ShorewakeDress.fbx (183741 verts, 3 morphs) + QA render
                          + shorewake_transform_manifest.json

TEXTURE LANES (UE-facing):
  dress_lookdev.py  ──► T_MelusinaC_DressShorewake_*  (base cloth set)
  dress_shine_kit.py ──► T_DressShorewake_ScaleShimmer/Mask  (overlay layer)
  both record seed via reef_common.write_manifest; textures later ingested into
  Content/ per the reef ingest flow (commit 0fe7b877 ingested the wider suite).

WEIGHT LAB (dead-end, unrun):
  dress_weight_lab.py ──► weights.json ──► apply_houdini_weights.py  ← DOES NOT EXIST
```

The chain that actually reaches the engine today is: owner FBX → Pass C
(`SK_ShorewakeDress_Magical.fbx`) for geometry, plus the two Python texture sets for
materials. The 48MAT lane feeds Substance (external, not automated here).

---

## (c) Gaps and risks (with line-level evidence)

1. **Hardcoded owner-machine paths — chain is unreproducible off this workstation.**
   - `dress_48_materials.py:22` and `dress_transform.py:24`: `C:\Users\froma\Downloads\melusinashorewake.usdz`
   - `shorewake_pass_a.py:17` and `shorewake_pass_c.py:29`: `C:\Users\froma\OneDrive\Desktop\shorewake.fbx`
   No committed copy of either source asset exists in the repo or the Saved backup; if
   the owner cleans Downloads/Desktop, the entire geometry chain is unreproducible.
   `passA_inventory.json` records `source` but not a hash, so source drift is undetectable.

2. **Pass C panel-stagger uses a uniform-panel assumption that is false.**
   `shorewake_pass_c.py:135` computes the panel index as `pi = min(i // 3828, 47)`
   (comment: "183741/48 ≈ 3828"), but `dress_materials_manifest.json` shows panels range
   from 168 verts (P03/P04) to 23058 verts (P02). The true per-panel vertex ranges are
   computed at `shorewake_pass_c.py:59-65` (`ranges` list) and then **never used** for the
   morphs. Result: the panel-cascade stagger of Nikki_Bloom/Swirl/ShimmerWave is
   misaligned — dress panels with 168 verts blend across ~23 "virtual panels". Not fatal
   (morphs still deform), but the authored "cascade" feel is not what the code intends.

3. **`dress_weight_lab.py` chain is a dead end.**
   Outputs never produced (`Saved/Audit/melusina_lookdev/weight_lab/` absent). Its
   docstring (`dress_weight_lab.py:18`) names the downstream Blender applier
   `apply_houdini_weights.py` — **no such file exists anywhere under `Tools/`** (verified
   by recursive search). Even a green QA gate today has nowhere to land its weights.

4. **Fragile `import math` placement — two scripts import math only inside `__main__`.**
   `shorewake_pass_c.py:263` and `dress_transform.py:237` do `import math` immediately
   before `main()` at module bottom, while `main()` bodies use `math.radians` /
   `math.sin` (`shorewake_pass_c.py:143,145`; `dress_transform.py:111,122`). Works when
   run as `--python` scripts; breaks with `NameError` if either module is ever imported,
   or if someone runs a different entry point. Same latent pattern in
   `render_48mat.py:96-97`: `Vector` is referenced in a dead line (`if False`) *before*
   the `from mathutils import Vector` on line 97 — harmless only because the line is dead.

5. **Determinism is recorded in the Houdini pass and texture lanes, but not in the
   Blender geometry lanes.** `build_dress_magical.py:23` (SEED=20260828, in manifest) and
   both texture scripts record seeds via `reef_common.write_manifest`
   (`reef_common.py:234-244` writes a `"seed"` key). `dress_48_materials`,
   `shorewake_pass_a/c`, `dress_transform`, and `render_48mat` use no RNG today, so
   results are operationally deterministic — but their manifests carry no seed/hash
   fields, and `render_48mat.py` writes **no manifest at all**, so a future RNG addition
   or a different Blender version would be invisible to any audit.

6. **Stale/contradictory docstrings.**
   - `dress_transform.py:1` says "**45 USDZ panels**"; the manifest it writes records
     `panels: 48`. The docstring is wrong.
   - `shorewake_pass_c.py:6-7` says its magical inputs come from "Pass B" — the file is
     actually named `build_dress_magical.py` (self-described "PASS B v2"); there is no
     `shorewake_pass_b.py`.
   - `shorewake_pass_a.py:24` is a dead statement: `bpy.ops.wm.open_mainfile(...) if
     SRC.suffix == ".blend" else None` followed by a proper `if/else` on the same
     condition — the first branch would re-open a file Blender hasn't imported yet if the
     source were ever a `.blend`.

7. **Inconsistent panel ordering between lanes.** `dress_48_materials.py:44` sorts
   panels **numerically** (`panel_index()` extracts digits), while
   `dress_transform.py:36-37` sorts **lexicographically** by name. Lexicographic order
   puts `dressedit10` before `dressedit7`, so the transform lane's join order (and its
   per-panel vertex ranges) differs from the 48MAT/pass-C lane. Any consumer that assumes
   both lanes agree on `P01..P48` semantics is wrong.

8. **Output sprawl with no manifest cross-reference in `melusina_lookdev/` root.**
   Beyond the manifest-referenced outputs sit: `SM_ShorewakeDress_48MAaaaaattttfbx.fbx`
   (typo-named, 8.3 MB), `Shorewake_48MAT.blend1` (Blender backup), `_frozen_snapshot`
   and `_consolidated` blend/FBX variants, `SK_ShorewakeDress.assbin`, and
   `SM_AOFixShorewakeDress.fbx` + `SM_ShorewakeDress_48MAT_AO_4096.png` — none produced
   or referenced by any tracked script in this directory. Provenance unknown; safe-delete
   requires an owner decision (per project rule: ORPHAN means prove it, not delete it).

9. **`shorewake_pass_c.py:86` assumes a single new object per OBJ import**
   (`[o for o in bpy.data.objects if o not in before][0]`) — a multi-object OBJ or an
   import that also creates empties silently grabs the wrong object.

10. **Weight-transfer warnings are swallowed.** `shorewake_pass_c.py:97-101` catches all
    exceptions during skin-weight transfer and only prints a truncated warning; a failed
    transfer still proceeds to join + export, so `SK_ShorewakeDress_Magical.fbx` could
    ship with unweighted magical geometry and nothing in the manifest records whether
    transfer succeeded.

---

## (d) Recommended cleanup list (priority order)

1. **Copy the two owner source assets into the repo** (e.g.
   `Saved/Audit/melusina_lookdev/sources/` — gitignored if too large, but at least into
   the `CompatibilityLabs`/`Saved` backup), and record their SHA-256 in the manifests so
   source drift is detectable. Replace the four hardcoded absolute paths with
   `PROJECT_ROOT`-relative paths or a small config.
2. **Fix Pass C stagger** to use the `ranges` list already computed at
   `shorewake_pass_c.py:59-65` instead of `i // 3828` (line 135), and record
   `transfer_ok: true/false` per magical object in the manifest instead of swallowing the
   exception.
3. **Delete or complete the weight-lab chain**: either author
   `apply_houdini_weights.py` and run `dress_weight_lab.py` against the Pass C mesh, or
   mark `dress_weight_lab.py` explicitly dead in its docstring so no lane plans around it.
4. **Move `import math` to module top** in `shorewake_pass_c.py` and `dress_transform.py`;
   delete the dead lines (`shorewake_pass_a.py:24`, `render_48mat.py:96`); correct the
   "45 panels" docstring in `dress_transform.py`.
5. **Add a manifest to `render_48mat.py`** (input blend hash, Blender version, slot
   count) and add a `seed`/`blender_version` field to the geometry manifests so all six
   dress setups report determinism uniformly.
6. **Reconcile panel ordering**: make `dress_transform.py` use the same numeric
   `panel_index` sort as `dress_48_materials.py`, or document that the transform lane is
   superseded and freeze it.
7. **Triage the unlabeled outputs** in `Saved/Audit/melusina_lookdev/` root
   (`*48MAaaaaa*`, `.blend1`, `assbin`, AO variants): identify their producers, then ask
   the owner before removing anything.

---

*Audit method: all 9 scripts read end-to-end; every manifest read from disk; output
existence checked with filesystem enumeration on 2026-08-30. No `.uasset`, no
`Content/**`, no primary-agent write paths touched.*
