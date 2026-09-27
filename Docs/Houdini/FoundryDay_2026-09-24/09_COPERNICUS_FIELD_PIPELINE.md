# 09 — Gate 9 (P1): Copernicus field-driven materials

| | |
|---|---|
| **Purpose** | Let FieldAtlas channels drive material maps through the **existing** Copernicus/cymatic map contracts. There is no second material pipeline. |
| **Authority** | Map contract: the 9-map family (`BaseColor, Normal, Roughness, Metallic, Height, ORM, Emissive, Iridescence, Opacity`) from `copernicus_cymatic_parallax.py`, the Copernicus UE compression contract in `Tools/Houdini/copernicus/README.md`, and the validator `Content/Python/verify_tex_contract.py`. Masters are unchanged (`M_Master_Toon_Universal` family; editing a master is ask-first). MPC writers are unchanged. |
| **Inputs** | FieldAtlas tile EXRs; an existing variant's palette/look; seed. |
| **Outputs** | A new **variant** in the existing family (e.g. `T_Cymatic_<Variant>_<Map>`) at 2K test / 4K hero, plus a manifest. |
| **Evidence** | `Saved/Audit/houdini_foundry/<recipe_id>/` + `verify_tex_contract.py` output |
| **Status** | STAGED. Real COP networks exist: `copernicus_dress_bake.py` (needs the missing `reef_common.py`), `copernicus_terrain_height_to_nanite.py`, `copernicus_fabric_sheen.py`. The cymatic family generator is numpy with non-deterministic `hash()` seeding (`00_INTAKE.md` §3.6). |

## Channel → map mapping (proposed)

| FieldAtlas channel | Map effect |
|---|---|
| `sediment` | BaseColor pigment blend toward the variant's sediment tint |
| `wetness` | Roughness down, BaseColor value down (darken) |
| `concavity` | accumulation mask → Height fill + BaseColor accumulation tint |
| `exposure` | bleaching: BaseColor saturation down, value up |
| `resonance` | cymatic pattern visibility (lerp amount of the Chladni layer into Height/Emissive) |
| crystal mask (cathedral groups / `sparkle`) | Iridescence strength + Emissive sparkle |

## Rules

1. Build it as a COP network (real Copernicus) in a new script `Tools/Houdini/copernicus/copernicus_field_driven.py` (`git add -f`), with a CLI seed. **Seed with `stable_int`, never `hash()`.**
2. Output names, bit depths and channel packing follow the existing 9-map contract exactly. ORM packing stays as the existing family does it.
3. 4K hero bakes run on the heavy lane. Iterate at 1K.
4. Fixing the `hash()` seeding in `copernicus_cymatic_parallax.py` itself would change every existing variant's pixels. That is **ask-first** because tracked assets were made from the old outputs. Offer it; don't do it silently.

## Done when

One field-driven variant for the Gate 4 tile passes `verify_tex_contract.py`, two cooks give identical hashes, and Brennan picks it from a contact sheet. UE application uses an MI of an existing master and is saved/reloaded.
