# Playbook — SurrealFabric flipbook master

Lane D live 2026-09-17. One master, one scrub function, instances per family.

## Paths (SSOT)

| Asset | Path |
|---|---|
| Master | `/Game/Melodia/Materials/Masters/M_SurrealFabric_Flipbook` |
| Scrub MF | `/Game/EnvSandbox/VFX/Materials/Functions/MF_FlipbookScrub` |
| Lookdev MIs | `/Game/Melodia/Materials/Lookdev/` — `MI_SurrealFabric_CelestialSilk`, `MI_SurrealFabric_CymaticPulse`, `MI_SurrealFabric_BrassPatina` |

Time is a **reader** of engine Time / optional `MPC_Melodia_Palette` beat lane.
The MF never writes an MPC.

## MI recipe (template = CelestialSilk)

| Param | Value |
|---|---|
| Grid / Atlas | **6×5** (`AtlasCols=6`, `AtlasRows=5`) |
| FlipFPS / FrameRate | **12** |
| FrameCount | **30** (6×5) |
| BaseColor | family `*_Atlas_6x5` / compact atlas if present |

Clone this onto remaining Melodia* fabric folders. Do not invent a second master.

## Normal / ORM atlas debt

SurrealFabric families were imported as mixed per-frame Texture2Ds and compact
6×5 atlases. BaseColor often has an atlas; **Normal and ORM may not**.

Study-bot Package A:

1. Inventory per-frame vs compact atlas **gaps** per family (BC / N / ORM / Height).
2. Write a wire plan that **shares FlipbookUV** from `MF_FlipbookScrub` across channels.
3. Do **not** invent Normal/ORM atlases in the editor without real frames.

Until those atlases exist, leave N/ORM on a still or a proven compact sheet — do
not fake a 6×5 chop on a single frame.

## Editor rules

- Additive authoring only. Never `build_material_graph` on an existing asset
  (it wipes the graph). HLSL / `create_custom_hlsl_node` on **new** functions only.
- No Monolith `save_packages` / `recompile_material`. Owner **Ctrl+S**.
- If Niagara samples this master: follow
  [`PLAYBOOK_FLIPBOOK_FIXA.md`](../PLAYBOOK_FLIPBOOK_FIXA.md) (SubUV off, SubImage 1×1).

Spec sibling: `specs/materials/MF_FlipbookScrub.v1.json`.
Atlas-gap evidence: [`../../Audits/SURREALFABRIC_NORMAL_ORM_INVENTORY_2026-09-17.md`](../../Audits/SURREALFABRIC_NORMAL_ORM_INVENTORY_2026-09-17.md).
