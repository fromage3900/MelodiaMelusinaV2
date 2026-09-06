# Universal Garment — S4 Gate Advance (MI Materialization) 2026-09-02

**Session:** late-night 09-02 daemon tick. Editor was **UP** on :9316 (pid 15272,
1426 tools), so Goal-1 real UE work was unblocked. This closes the **S4**
`universal_garment_s4_per_garment_mi` MI-materialization portion on the verified
small family. *(Phantom-master remap + water-zone MI + live ground-snap remain
open; this doc records the garment-layer MI materialization honestly.)*

## What was done (all editor-written via Monolith material_query, the sanctioned .uasset writer)

1. **Imported the cymatic 9-map garment kit** (10 layers × 8 importable channels =
   80 textures) from
   `Saved/Audit/melusina_lookdev/garment_refresh/cymatic/` into
   `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Textures/GarmentCymatic/`.
   per-channel compression/sRGB correctness: Normal→`Normalmap`, Height/
   Roughness/Metallic/ORM→`Grayscale`, Opacity→`Alpha`, BaseColor/Emissive→`Default`.
2. **Created 10 MIs** `MI_Melusina_Toon_Cymatic_<Layer>` parented **only** to the
   verified `M_Master_Toon_Universal_Alpha` (masked/lace family). **No new master.**
3. **Wired 8 texture slots + 4 static switches per MI** via
   `set_instance_parameters`:
   - textures: `Albedo`←BaseColor, `NormalMap`←Normal, `HeightMap`←Height,
     `RoughnessMap`←Roughness, `MetallicMap`←Metallic, `ORM`←ORM,
     `EmissiveMap`←Emissive, `OpacityMap`←Opacity
   - switches: `bUseSeparateRoughnessMap`, `bUseSeparateMetallicMap`,
     `bUseEmissiveMap`, `bUseOpacityMap`
4. **Saved** all 10 MI `.uasset` (clean-scoped, `fail_on_unrequested_dirty` with
   scope `/Game/.../SeaAbove/Prototype`); `list_dirty_packages` recheck → **0 dirty**.
5. **Verified by read-back**, not prose: `get_instance_parameters` on all 10 →
   PER-FILE sha256 + byte size, parent match, all 8 slots + 4 switches present.
   → **PASS=True, layers_pass=10/10.**
6. **Vocab gate still PASS:** `universal_garment_vocab_check.py` →
   `14 articles | 14 unique modes | 0 collisions | 0 registry issues`.

## Master choice rationale

`M_Universal_Enhanced_Fabric` exposes **no texture slots** (generated/flipbook
master via AutoBlendID/static switches) — not a texture-wiring target. The masked
`M_Master_Toon_Universal_Alpha` exposes the full garment 9-map slot contract
(Albedo/NormalMap/HeightMap/RoughnessMap/MetallicMap/ORM/EmissiveMap/OpacityMap +
the four per-channel switches), so **all 10 cymatic garment layers were parented
there** (masked→Toon_Alpha per S4 tier rule). Satin/sheet layers that belong on
`M_Master_Nikki` (only Albedo/NormalMap/HeightMap/ORM slots) are a follow-up.

## Evidence (seed 20260902, sha256-locked)

- `Saved/Audit/universal_garment/s4_mi_materialize_report.json` — runtime
  driver log (80 imports, per-source sha256; Skirt_Full logged expected
  "already exists" from its pilot creation).
- `Saved/Audit/universal_garment/s4_mi_materialize_verified.json` — the
  authoritative read-back verification (PASS=True, 10/10, per-uasset sha256).
- `Saved/Audit/universal_garment/garment_vocab_check.json` — vocab gate PASS.

## Next tick (in priority order)

1. Same editor-up path: **water-zone S4** — materialize 4 `MI_*_SingingWater_*`
   zones (parent to the verified small family or reuse verified SeaAbove MIs),
   import `singing_water/cymatic/` 9-map sets.
2. **S5 live ground-snap** — load `LV_SeaAbove_Prototype`, raycast the 120
   `garment_veil_staging_placements.json` points onto CanonicalLandscape
   (mesh handle `create_handle` + `snap_to_surface`), if the referenced
   `MEL_garment_*` meshes exist.
3. **Phantom master remap** — reparent MIs off `M_Master_FarawayMother_Fabric`
   (0-byte phantom) to the small family.