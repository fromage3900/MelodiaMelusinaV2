# Faraway Mother branch salvage — 2026-09-25

## Salvaged to fresh main

From `feature/universe-foundry-ue-staging-20260922`:

- `Tools/Houdini/floating_crystals/build_floating_crystals.py` — deterministic, source-only Hython generator for floating crystal meshes/textures/manifests; no Unreal mutation.
- `Tools/Houdini/vdm_fabric_mountains/faraway_alignment_diagnostic.py` — deterministic field-orientation diagnostic using the existing Faraway static-field convention; no Unreal mutation.

These fit the canonical Houdini/Hython forge and are now indexed/protected by the World Atlas.

## Deliberately not salvaged to Git authority

The same staging branch contains nine Faraway Mother Unreal packages (prototype map, crystal meshes/material/texture assets). They remain **UE/Perforce verification hold**. Do not copy the old Git binary state over the current editor/depot.

The older `feature/frequency-ecology-20260921` and `recovery/lookdev-frequency-ecology-20260921` pair also contain six one-shot Faraway Mother Unreal editor scripts:

- `Content/Python/faraway_mother_stage1_fixup_2026-09-21.py`
- `Content/Python/faraway_mother_stage1_force_2026-09-21.py`
- `Content/Python/faraway_mother_stage1_height_aware_2026-09-21.py`
- `Content/Python/faraway_mother_stage1_landscape_2026-09-21.py`
- `Content/Python/faraway_mother_stage2_mi_2026-09-21.py`
- `Content/Python/faraway_mother_stage2b_texbind_2026-09-21.py`

They are preserved by their branch refs but are **not promoted**: they hardcode the retired workstation path and broadly mutate/save Unreal packages, so they do not meet the current deterministic-owner / Perforce-aware production contract. Extract a specific missing semantic only if a current-world blocker proves it is needed.

## Retirement consequence

- `feature/universe-foundry-ue-staging-20260922`: source salvage is complete for the two reusable Hython tools; keep on P4_CONTENT_RECOVERY hold until its nine UE assets are compared with the live depot/editor.
- frequency-ecology pair: keep on P4_CONTENT_RECOVERY/SALVAGE hold until binary state and any genuinely needed Faraway staging semantics are reconciled.
