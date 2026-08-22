# Blender Hand-Keyed Animation Import Pipeline — BS_GodFile (canonical)

**Established:** 2026-08-22, from live evidence (see `Docs/Evidence/2026-08-22_melusina_idle_glide/`)
**Applies to:** owner hand-keyed clips authored on `character_rig` in the Melodia stage blends
(v16+), NLA track per clip (e.g. `idle_animation`).
**Companion skill:** `.agents/skills/melusina-blender-handkeyed-import/` (also installed at
`%USERPROFILE%\.agents\skills\`).

---

## 0. What we learned the hard way (2026-08-22)

Two Blender-sourced idles were imported **directly onto `SK_Melusina_Skeleton`**
(name-matched tracks) and both render as an exploded/lying-down pile:

| Clip | Import route | cm probe | Visual result |
|---|---|---|---|
| `A_Melusina_Idle_v22` (Authored/) | unguarded FBX import | none | lying flat + collapsed |
| `Cascadeur/A_BL_Melusina_Idle_Loop` | guarded importer (`import_blender_melusina_idle.py`) | **passed** (`spine_y ≈ −12.84`) | exploded black pile |

Meanwhile every mocap clip retargeted through the IK chain renders correctly
(Aug-20 captures: standing idle, run, sprint — coherent deformation).

**Root cause:** the cm-probe validates *units* on one bone. It does not validate
*per-bone rest-pose rotation*. The ARP `character_rig` (1124 bones) and the UE-built
465-bone `SK_Melusina_Skeleton` do not share per-bone rest orientations; name-matched
animation tracks therefore apply source-local rotations into target-local spaces and
shred the mesh. This is the same four-axis doctrine as `TRIPLE_A_MELUSINA_ANIMATION_PIPELINE`
plus a fifth: **rest-pose alignment. Name matching is never sufficient. Retarget or fail.**

## 1. The five stages

```
A Author (stage blend)  →  B Export headless  →  C Offline gate (remap + sidecar)
   →  D Guarded UE import (source skeleton)  →  E IK-RETARGET onto SK_Melusina_Skeleton
   →  F Bind into ABP via Monolith  →  G Evidence
```

### Stage A — Author (stage blend)
- One NLA track per clip on `character_rig`; track NAME is the clip identity.
- Never save the stage blend (AGENTS stage-save gate). All edits in memory.

### Stage B — Export headless (Blender CLI)
```powershell
blender <stage>.blend -b -P Tools/export_melusina_idle_v22.py
```
Pattern: find action via NLA track → mute NLA → bind action → armature-only FBX,
baked, `axis_forward="-Z", axis_up="Y"`. Generalize by copying this script; keep
the report JSON in `Saved/Audit/`.

### Stage C — Offline gate (no editor needed)
```powershell
python Tools/remap_arp_fbx_to_ue.py <in.fbx> <out.fbx>   # dots→underscores, ×100 units
```
Produces `<out>.remap.json`. Write a sidecar contract JSON next to it:
```json
{ "schema_version": "1.0", "clip_name": "...", "source_name": "...",
  "expected_skeleton": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton",
  "loop": true, "root_motion": "in_place", "fps": 30,
  "ue_import": false, "notes": "..." }
```
Flip `"ue_import": true` only after Stage E verification passes.

### Stage D — Guarded UE import (onto a SOURCE skeleton, NOT the live one)
Use `Content/Python/import_blender_melusina_idle.py` as the template:
- animation-only `FbxImportUI`, explicit target skeleton, `replace_existing`,
- reject wrong skeleton; probe `c_spine_02_x` Y at frame 0; ×100 if meters
(`melusina_anim_unit_guard.classify_spine_translation`),
- destination under `Animations/Cascadeur/` (or `Animations/MocapInbox/`), never
  straight to `Authored/`.

### Stage E — IK-RETARGET onto `SK_Melusina_Skeleton` (mandatory for BL clips)
Mirror the mocap chain: `SK_<Source> → IK_<Source> → RTG_<Source>_to_Melusina → IK_Melusina_Body_Current`.
1. One-time: create IK Rig for the imported source skeleton (retarget chains: spine,
   head, arms, legs) and a `RTG_BlenderARP_to_Melusina` mapping to `IK_Melusina_Body_Current`.
2. Retarget the clip (editor: right-click sequence → Retarget Animations; automation:
   Monolith `animation_query batch_retarget_animations`).
3. Validate the retargeted sequence: skeleton == `SK_Melusina_Skeleton`, bone count 465
   contract, fps 30, spine height ≈ −12.84 cm, then ONE preview capture must show an
   upright posed character before anything binds.
Only now flip the sidecar's `ue_import: true`.

### Stage F — Bind into `ABP_Melusina_Current` via Monolith
```python
monolith("animation_query", {"action": "set_state_animation",
    "asset_path": ABP, "machine_name": "MelusinaLocomotion",
    "state_name": "Idle", "anim_asset_path": NEW_CLIP, "loop": True})
monolith("blueprint_query", {"action": "compile_blueprint", "asset_path": ABP})
monolith("blueprint_query", {"action": "save_asset", "asset_path": ABP})
# verify by re-read:
monolith("animation_query", {"action": "get_state_info", ...})  # SequencePlayer node title
```
Rules: clear LFS ReadOnly first (`attrib -R` on that one .uasset — see Traps);
treat success only when uasset mtime is fresh (<10 min); re-read the binding from the
live graph afterwards.

### Stage G — Evidence
- `Saved/Audit/<topic>_<date>.json` for every apply (tools write these).
- `editor.capture_anim_frames`: **ONE call per editor session** — second call trips the
  documented `!IsRooted()` Monolith crash (`MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20`,
  Correction 2). Everything saved before capturing; expect a relaunch after.
- Real-input PIE before any gate claim (probe calls are not play evidence).

## 2. Current binding state (end of 2026-08-22 session)

| State | Clip | Why |
|---|---|---|
| Idle | `Locomotion/A_Melusina_Idle_Mocap_RootX` | proven upright; original T-pose was the old unsuffixed clip, not this one |
| Glide | `Mocap/A_Mocap_LittleDance_001` placeholder | entries on `bIsGliding`; exits via pre-existing `bRuntimeIsInAir/bRuntimeIsGrounded` |

Quarantine candidates (owner call): `Authored/A_Melusina_Idle_v22`,
`Cascadeur/A_BL_Melusina_Idle_Loop` — do not bind until Stage E passes.

## 3. Trap table (each cost real time)

| Trap | Symptom | Rule |
|---|---|---|
| LFS lockable ReadOnly | editor crash inside `save_packages` / silent `save_asset` failure | `attrib -R` the single target .uasset first (precedent: MF_Madoka 08-15) |
| `save_asset` lies | `saved:true`, mtime unchanged | always check uasset mtime <10 min |
| Monolith rule terms numeric-only | `expression` rejects bool operands | bools are `kind:"bool"` rules only; no compound AND with floats |
| Parallel-lane file reverts | tool edits vanish mid-session | don't fight over shared Tools/*; coordinate or use direct MCP calls |
| Capture budget | 2nd capture crashes editor later | one per session; save everything first |
| Editor churn | two instances, port flapping | one editor instance, always (AGENTS rule 7) |
