# SurrealFabric Normal / ORM inventory ΓÇö 2026-09-17

**Package:** A ΓÇö Materials org  
**Stamp:** 2026-09-17 ~18:25 EDT (America/Toronto)  
**Master:** `/Game/Melodia/Materials/Masters/M_SurrealFabric_Flipbook` (Lane D **on disk**)  
**Scrub:** `/Game/EnvSandbox/VFX/Materials/Functions/MF_FlipbookScrub` ΓåÆ outputs shared **FlipbookUV** / FrameUVs  
**Hard rule:** Do **not** invent atlas textures in editor without real frames.

## Families in scope (SurrealFabric flipbook set)

| Family | Lookdev MI (template path) | Intended grid |
|--------|----------------------------|---------------|
| CelestialSilk | `/Game/Melodia/Materials/Lookdev/MI_SurrealFabric_CelestialSilk` | **6├ù5**, FrameCount **30**, FlipFPS **12** |
| CymaticPulse | `/Game/Melodia/Materials/Lookdev/MI_SurrealFabric_CymaticPulse` | same |
| BrassPatina | `/Game/Melodia/Materials/Lookdev/MI_SurrealFabric_BrassPatina` | same |

Offline census (2026-09-09 WorldGrid/Flipbook receipt): each family Γëê154 png + Γëê154 uasset; atlases present as below.

## Per-channel atlas gap matrix

Status codes: **HAVE** = compact/full atlas on disk ┬╖ **GAP** = no compact atlas (per-frame only or missing) ┬╖ **STILL** = use single still until atlas exists ┬╖ **N/A** = channel not used

| Family | BaseColor | Iridescence / Roughness | Normal | ORM / Height |
|--------|-----------|-------------------------|--------|--------------|
| CelestialSilk | **HAVE** `*_Atlas_6x5` + `*_AtlasCompact_6x5` BaseColor | **HAVE** Atlas_6x5 Iridescence + Roughness | **GAP** ΓÇö no Normal Atlas_6x5 / Compact claimed | **GAP** ΓÇö no ORM Atlas_6x5 / Compact claimed |
| CymaticPulse | **HAVE** same pattern | **HAVE** same pattern | **GAP** | **GAP** |
| BrassPatina | **HAVE** same pattern | **HAVE** same pattern | **GAP** | **GAP** |

### Per-frame vs compact

- **Per-frame Texture2D sets:** historically imported alongside atlases for SurrealFabric families (mixed import). Useful for offline atlas bake later ΓÇö **not** a reason to fake 6├ù5 chops in material.
- **Compact atlas:** BaseColor Compact_6x5 exists for the three families. Prefer Compact for MI BaseColor when memory matters; full Atlas_6x5 OK for lookdev.
- **Normal / ORM:** treat as **atlas debt**. Until real Normal/ORM 6├ù5 (or Compact) sheets exist, wire **still** maps (frame 0 / hero still) sampled with **passthrough UVs**, not FlipbookUV.

Related naming hazard (Brass shared, not SurrealFabric family atlas): `T_Brass_Flipbook_30_Atlas_4x4` is **16 cells** ΓÇö rename/verify before any Brass atlas wire (out of Normal/ORM gap fix).

## Wire plan ΓÇö share FlipbookUV on `M_SurrealFabric_Flipbook`

Goal: one scrub ΓåÆ one UV ΓåÆ all channels that have matching atlases.

```
Time / Beat reader
        Γöé
        Γû╝
 MF_FlipbookScrub  (AtlasCols=6, AtlasRows=5, FrameCount=30, FrameRate=12)
        Γöé
        Γö£ΓöÇΓöÇ FlipbookUV (FrameUVs) ΓöÇΓöÇΓû║ sample BaseColor atlas
        Γö£ΓöÇΓöÇ FlipbookUV ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓû║ sample Iridescence atlas (if present)
        Γö£ΓöÇΓöÇ FlipbookUV ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓû║ sample Roughness atlas (if present)
        Γö£ΓöÇΓöÇ (NO FlipbookUV) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓû║ Normal STILL  (until N atlas exists)
        ΓööΓöÇΓöÇ (NO FlipbookUV) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓû║ ORM STILL     (until ORM atlas exists)
```

### Rules

1. **Single scrub instance** in the master graph; do not duplicate TimeΓåÆframe math per channel.
2. Channels with matching atlases **must** share the same FlipbookUV (and FrameOffset if phase-locked).
3. Channels with **GAP**: leave on still / proven non-atlas sheet; **never** apply 6├ù5 UV math to a non-atlas texture.
4. Do **not** call `build_material_graph` on existing master (wipes graph). Additive edits only; owner Ctrl+S.
5. Do **not** invent Normal/ORM atlases by cropping a single frame into a fake grid.

### When atlases arrive (owner / art)

1. Import real Normal + ORM (Height optional) Atlas_6x5 or Compact_6x5 per family.
2. Retarget MI texture params; switch those samples from still-UV ΓåÆ shared FlipbookUV.
3. Validate; owner Ctrl+S. No agent `save_packages`.

## Live verify owed (Monolith read-only when up)

- Confirm on-disk names for each familyΓÇÖs Atlas / Compact / per-frame Normal & ORM.
- Confirm CelestialSilk MI params match playbook (6├ù5 / 12 fps / 30 frames).
- Update this table if a Normal/ORM atlas already exists under an unexpected path ΓÇö do not invent.

## Related

- `Docs/VFX/Playbooks/PLAYBOOK_SURREALFABRIC_FLIPBOOK_MASTER.md` (#228)
- `specs/materials/MF_FlipbookScrub.v1.json`
- `Docs/Audits/MELODIA_FABRIC_MI_SCAFFOLD_PLAN_2026-09-17.md`
