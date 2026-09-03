---
name: melusina-blender-handkeyed-import
description: Land owner-authored hand-keyed Blender animations (character_rig NLA clips from Melodia stage blends) onto Melusina's 465-bone skeleton in BS_GodFile UE5.8 and bind them into ABP_Melusina_Current via Monolith MCP. Use when importing Blender-authored idles/animations, wiring NLA clips into Unreal, fixing an exploded or lying-down or T-posing idle, retargeting ARP/Blender rigs, or when the user mentions hand-keyed clips, the v22 stage blend, A_BL exports, cm probes, or Melusina animation bindings.
---

# Melusina Blender Hand-Keyed Animation Import

Canonical reference: `Docs/Production/BLENDER_HANDKEYED_ANIM_IMPORT_PIPELINE_2026-08-22.md`
(in BS_GodFile). This skill is the operational checklist; the doc carries the evidence.

## Hard rules (each one cost a real failure)

1. **Never bind a Blender clip that was imported directly onto `SK_Melusina_Skeleton`.**
   Name-matched tracks explode the mesh (rest-pose rotations differ). It MUST pass through
   an IK-retargeter chain first — same as mocap.
2. **cm-probe passing is not enough.** It validates units on one bone only.
3. **One `capture_anim_frames` per editor session.** Second call trips the documented
   Monolith `!IsRooted()` crash. Save everything first.
4. **LFS lockable makes .uassets ReadOnly.** `attrib -R <file>` before saving or the
   editor crashes in `save_packages` (precedent: MF_Madoka 2026-08-15).
5. **`save_asset` lies.** Success = uasset mtime < 10 min old AND re-read of the live
   graph shows the new binding.
6. **Monolith transition rules:** bools are `{kind:"bool", variable}` only;
   `expression`/`compare` terms accept numeric operands exclusively.
7. **One editor instance** (port 9316 exactly one listener). Parallel lanes revert shared
   `Tools/*` files — prefer direct MCP calls over editing contested tooling.

## Workflow

```
[ ] A  Author in stage blend; NLA track NAME identifies the clip; never save the stage
[ ] B  Export headless: blender <stage>.blend -b -P Tools/export_melusina_idle_v22.py
       (armature-only FBX, baked, axis_forward="-Z" axis_up="Y"; generalize by copy)
[ ] C  Offline gate: python Tools/remap_arp_fbx_to_ue.py in.fbx out.fbx  (dots→underscores, ×100)
       + sidecar contract json ("ue_import": false until Stage E passes)
[ ] D  Guarded import onto SOURCE skeleton via Content/Python/import_blender_melusina_idle.py
       pattern (animation-only, skeleton checked, spine_y cm probe ≈ −12.84)
[ ] E  IK-RETARGET: SK_source → IK_source → RTG_BlenderARP_to_Melusina → IK_Melusina_Body_Current
       (one-time rig setup, then Monolith animation_query batch_retarget_animations).
       Validate: skeleton == SK_Melusina_Skeleton, upright pose in ONE preview capture.
[ ] F  Bind via scripts/bind_and_verify.py (set_state_animation loop=true → compile →
       attrib -R + save_asset → mtime check → re-read binding)
[ ] G  Evidence: Saved/Audit/<topic>_<date>.json + capture frames + real-input PIE
```

## Binding a verified clip (Stage F)

```powershell
python .agents/skills/melusina-blender-handkeyed-import/scripts/bind_and_verify.py `
  --state Idle --clip /Game/Melodia/Characters/Melusina/Animations/<verified clip>
```

The script wraps: `animation_query.set_state_animation` → `blueprint_query.compile_blueprint`
→ ReadOnly clear + `save_asset` → mtime assertion → `get_state_info` re-read. Exit code 0
only if all pass. Requires Monolith live (UE editor open, port 9316).

## Current state (2026-08-22)

| ABP state | Clip | Status |
|---|---|---|
| Idle | `Locomotion/A_Melusina_Idle_Mocap_RootX` | proven upright, bound |
| Glide | `Mocap/A_Mocap_LittleDance_001` | placeholder; entries `bIsGliding`, exits `bRuntimeIsInAir/bRuntimeIsGrounded` |

Quarantined (exploded in capture, do NOT bind): `Authored/A_Melusina_Idle_v22`,
`Cascadeur/A_BL_Melusina_Idle_Loop`.

## References

- Pipeline + evidence: `Docs/Production/BLENDER_HANDKEYED_ANIM_IMPORT_PIPELINE_2026-08-22.md`
- Session record: `Docs/Handoffs/MELUSINA_IDLE_GLIDE_2026-08-22.md`
- Four-axis doctrine: `Docs/TRIPLE_A_MELUSINA_ANIMATION_PIPELINE_2026-08-18.md`
- Capture-crash bug: `Docs/MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md` Correction 2
