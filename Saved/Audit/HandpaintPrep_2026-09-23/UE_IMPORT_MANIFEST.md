# UE Import Manifest — Handpaint Prep 2026-09-23 (9 assets)

Staging root: `Saved/KimiWork/HandpaintPrep_2026-09-23/` (gitignored work area).
Paint targets: `substance/meshes/*_low.fbx` (or single FBX where self-baking).
Bake sources: `*_high.fbx`. Bake maps: `Bakes_Cymatic/FrozenFracture/` (9 channels:
BaseColor, Normal, ORM, Roughness, Metallic, Height, Opacity, Emissive, Iridescence).
Visual proof: `contact_sheets/MASTER_contact_sheet.png` + per-asset `strip_*.png`.

Proposed Content layout (new folders, follow existing MI_Universal_Lookdev_* convention):
- Meshes:   `Content/Melodia/Props/Handpaint/<Asset>/SM_<Asset>.uasset`  (import low FBX)
- Textures: `Content/Melodia/Textures/Handpaint/<Asset>/T_<Asset>_<Channel>.uasset`
- Materials:`Content/Melodia/Materials/Handpaint/MI_Handpaint_<Asset>.uasset`
  (parent: toon/stub master already in repo, e.g. `Masters/M_SurrealFabric_Flipbook`
  or `Lookdev/MI_Melodia_Stub_Toon` — pick per asset feel; Nikki lens = soft toon)

| # | Asset | Import mesh FBX | Faces | Bake source | Proposed MI | Notes |
|---|-------|-----------------|-------|-------------|-------------|-------|
| 01 | StylizedCrossProp | `01_StylizedCrossProp/substance/meshes/StylizedCrossProp.fbx` | 2,344 | self | MI_Handpaint_StylizedCrossProp | single mesh, authored UV; dims ~2.0×4.1×5.7 m |
| 02 | ZenLantern | `02_ZenLantern/substance/meshes/ZenLantern.fbx` | 3,270 | self (hi-poly unrecoverable, stage v14) | MI_Handpaint_ZenLantern | authored UV; tall ~7.2 m — scale to set dressing on import |
| 03 | MelodySlime | `03_MelodySlime/substance/meshes/MelodySlime_low.fbx` | 54,993 | `MelodySlime_high.fbx` (282,873 f) | MI_Handpaint_MelodySlime | low = single mesh `slimebasicnormals_LO`; rigged retopo leftovers excluded |
| 04 | CosmicReaver | `04_CosmicReaver/substance/meshes/CosmicReaver_low.fbx` (2 meshes) | 2×22,158 | `CosmicReaver_high.fbx` (CAGE+LOW, 2×81,995) | MI_Handpaint_CosmicReaver | **shape keys on high** — import with morph targets; renders head-down in rest pose: verify up-axis at import |
| 05 | MelodyTokens | `05_MelodyTokens/substance/meshes/SM_MelodyToken.fbx` | 996 | sculpt refs only (Star/Swirl/Water) | MI_Handpaint_MelodyToken | one shared mesh for all token variants; owner cylinder bakes already apply |
| 06 | TreasureChest | `06_TreasureChest/substance/meshes/TreasureChest_low.fbx` | 224,975 | `TreasureChest_high.fbx` (2.4 M) | MI_Handpaint_TreasureChest | Smart UV; dims 3.8×5.3×4.5 m — scale check on import |
| 07 | FallenMoon | `07_FallenMoon/substance/meshes/FallenMoon_low.fbx` | 364,218 | `FallenMoon_high.fbx` (3.07 M) | MI_Handpaint_FallenMoon | Smart UV; crescent seat |
| 08 | CosmicReaverBase | `08_CosmicReaver_USDZ/substance/meshes/CosmicReaverBase_low.fbx` | 81,995 | `CosmicReaverBase_high.fbx` (CAGE) | MI_Handpaint_CosmicReaverBase | identical mesh family to 04; upright rest pose |
| 09 | MelodiaMelusinaFlowers | `09_MelodiaMelusinaFlowers/substance/meshes/MelodiaMelusinaFlowers_low.fbx` (3) | 23,534/103,560/110,696 | `_high.fbx` (3) | MI_Handpaint_MeliusinaFlowers | **cm-import scale — scale ×100 on UE import**; verify against Melusina |

## Import checklist (per asset)
1. Import low FBX into `Content/Melodia/Props/Handpaint/<Asset>/` (static mesh; #04 enable morph targets).
2. Scale: #02/#06 scale-check vs set; #09 apply ×100 first.
3. Build `MI_Handpaint_<Asset>` parented to the toon master; wire cymatic FrozenFracture
   set as base layers under the handpaint (per-asset `substance/bake_recipe.json`).
4. After Substance paint export: `T_<Asset>_{BaseColor,Normal,ORM,Emissive}` → texture folder,
   sRGB on BaseColor/Emissive only.
5. Lookdev pass in the L_FallenMoon / L_KaleidoNave context per CURRENT_STATE lookdev lane.

Audit trail: prep reports + polish reports + vcol reports in each staging folder; Phases 1–5a audit in
`Saved/Audit/HandpaintPrep_2026-09-23/HANDPAINT_PREP_CLOSEOUT_2026-09-23.md` (commit 60f3e0609).

## Vertex color contract (Phase 5a — present on ALL paint-target FBX)

Every paint-target FBX carries exactly one color attribute, `vcol_melodia`
(BYTE_COLOR, corner domain — verified by FBX round-trip re-import):
- **R** = wear mask (inverted Cycles AO bake) → grunge/wear layers in Substance and UE
- **G** = decoration density (GN/PCG scatter mask; 1.0 on authored zones: lantern eaves, cross arm tips, token rims, chest lid, petals)
- **B** = audio-reactivity weight (height falloff 0..1) → UE vertex color node → pulse amplitude (read-only vs MPC_Melodia_Palette)
- **A** = emissive zones (lantern fire box, cross crystal, slime core, chest cavity, reaver torso, flower centers)
UE import: enable vertex-color import; sample `vcol_melodia` as the single color set (stale layers were stripped 2026-09-23 so channel 0 is unambiguous). sRGB OFF.
FBX were re-exported after this contract — sizes in the table above are pre-vcol; staging folder holds the vcol-carrying files.
