# Material Takeover — Deep Research + Staleness Review — 2026-08-29 (evening, 2-hour box)

Scope: finalize material wiring + instance work across the toon/water/SDF lane. Every execution
claim in §5 is read-back verified; research claims cite their source. Note: the request said
"UE 6.8" — this project is **UE 5.8** (`++UE5+Release-5.8-CL-55116800`, verified in the editor log
and Monolith status); no UE 6.8 exists. All research below is 5.8 ground truth.

---

## 1. Oceanology — state of the union (verified against plugin source + disk)

The authoritative study is `Docs/OCEANOLOGY_STYLIZATION_AND_TRAVERSAL_INTEGRATION_RESEARCH_2026-08-29.md`
(447 lines, source-checked). Its load-bearing conclusions, re-verified tonight where execution
depends on them:

1. **The graft is live and assigned.** `M_Water_Oceanology_Melodia` (1590 → 1638 PS instr is the
   only hard "reaches the shader" proof) is already assigned on the placed
   `AOceanologyInfiniteOcean` in `LV_SeaAbove_Prototype` (World Partition external actor,
   08-29 01:40). Outstanding: only the eyeball + `Toon_Weight` dial-in.
2. **The one hard rule: stylize shading, never displacement.** Oceanology's CPU wave solver is a
   literal C++ clone of its HLSL (`OceanologyComputeSpectralGerstnerUtils.cpp`). Any GPU-only WPO
   stylization desyncs swimming from the visible surface. The current graft obeys (Base Color
   banding + Emissive biolum only). **Do not let a later pass add a WPO branch.**
3. **Substrate Toon BSDF on the ocean is a verified dead end** (Substrate.ush: material mode is
   one field — SLWATER *or* SLAB_COMPLEX/TOON, never both). Reef/characters CAN go native
   Substrate-toon; the ocean cannot. Water bands must be hand-matched to the reef's band count.
4. **Beat-to-ocean is dead code** (§2.5 there): `UOceanologyWaterMeshComponent::SetMaterial` has
   an empty body; the correct path is `AOceanologyWaterParent::SetScalarParameterValue` onto OUR
   param names (`Biolum_*`, `Toon_Weight`). This is a C++ lane fix — flagged, not in tonight's
   material scope.
5. Plugin presets `DA_Color_AnimeLightBlue` + `DA_Foam_Stylized` are the intended starting
   palette; `FoamContrastLevel` is the strongest cartoon-foam lever. Preset application is queued
   as instance work (§5 queue).

## 2. SDF lane — orphaned

`MF_SDF_BandRelief.t3d` (355 KB) and `MF_LandscapeStorybookSDF.t3d` (27 KB), both exported
08-28 23:09, are **referenced by no master** (`rg` across all 40 T3D exports: only their own
files). `M_Master_SDF_Toon` exists separately. Verdict: fresh authored work, not yet wired —
a deliberate follow-up decision is needed (which master takes the SDF band-relief input, and on
what switch). Not improvised tonight.

## 3. Toon master inventory + the Madoka/Itto lane map

From `Docs/T3D_Baseline/materials/` (08-28 23:09 exports) + tonight's live reads:

| Master | Role | Madoka/Itto | Notes |
|---|---|---|---|
| `M_Master_Toon_Universal` | reef/prop workhorse | ✓ referenced | reef MIs live here |
| `M_Master_Toon_Landscape_HeightBlend` | terrain | ✓ referenced | tonight's Nikki wiring (§5.1) |
| `M_Master_Toon_Cosmic` | showcase | ✓ referenced | |
| `M_Master_Nikki` / `M_Master_Nikki_Landscape` | character/terrain NikkiX chain | — | use the newer PastelGrade/TwinkleIris/SDFRibbon/PearlSheen/DreamWatercolor chain; they do **not** call `MF_NikkiDreamGrade` |
| `M_Master_SDF_Toon` | SDF lane | — | no consumers found for the SDF functions |
| `M_Master_Impressionist_Toon(_Landscape)` | alternate style | — | |

**The ~53 orphaned parameters on HeightBlend are enumerated by `validate_material`** (all
`Madoka*`, `Itto*`, `ShadowDream*`, `ShadowFlower*`, `Sparkle*`, `Rim*`, `Iridescence*`, … —
the full machine census is reproducible with one call). Because `MF_NikkiDreamGrade` takes only
`BaseColorIn`, these cannot hook into that call site; the in-repo reference wiring for them is
`M_Master_Toon_Universal` (same function family, wired). Follow-up: mirror Universal's
Madoka/Itto input wiring onto HeightBlend behind a switch — owner decision on look first.

## 4. Staleness review (docs vs disk, tonight)

| Doc claim | Verdict |
|---|---|
| `_SESSION_HANDOFF.md`: "C++ TREE DOES NOT COMPILE" | **Stale** — DLL 08-28 16:50 ≥ newest header; already documented in the Oceanology research doc §2.1 |
| `SESSION_CLOSEOUT_WATER_MATERIALS` §6: "`MI_Melusina_WaterHair` is unused" (implying it exists) | **Wrong** — the MI does not exist anywhere in `Content/` (globbed). Tonight creates it (§5.4) |
| `LANDSCAPE_MASTER_REPAIR` §6: "`bTriplanarPro_Active` still False on MI_Landscape_CliffGrass" | **Stale within hours** — owner re-enabled it (now True, plus `bNikkiFast`/`bNikkiHero` True and painted-layer enables). Instance left dirty deliberately: owner was mid-tuning at handoff (undo transactions observed 18:19) |
| `SESSION_CLOSEOUT_WATER_MATERIALS` §1 "NOT YET SEEN RENDERED" | Superseded by Oceanology research §2.4: wiring done + assigned; visual pass still owed |
| Mesh-assembly doc: "SM_Leviathan/SM_DrownedOrgan not imported; 6 textures staged" | Half-stale: the 6 PNGs are already staged **inside Content** `Reef/Textures/`; only the imports are missing (crash autosaves of lost uassets exist under `Saved/Autosaves/`) |
| P0 six-pass playtest doc | Current. Both completed passes failed on D3D12 render-target ensures; same ensure recurred at 16:26 today |

## 5. Execution log (read-back verified)

### 5.1 Nikki glow wiring on `M_Master_Toon_Landscape_HeightBlend` — DONE (in-session; see incident)

Applied the §8 recipe from `LANDSCAPE_MASTER_REPAIR_2026-08-29.md`, via Monolith in one undo
transaction, with a full-material rollback duplicate first
(`..._PRE_NIKKIGLOW_20260829` in the same archive folder):

- `Constant_1` (R=0), `StaticSwitchParameter_0` (ParameterName=`bNikkiFast`, shared switch,
  Group `10 | Nikki Rim & Glow`, default False), `Add_0`.
- Wiring (read back through `get_expression_connections`): `SSP_0.True ← MFC_5 output 0
  "Emissive"`, `SSP_0.False ← Constant_1`, `Add_0.A ← Multiply_6`, `Add_0.B ← SSP_0`,
  `SubstrateToonBSDF_0.EmissiveColor ← Add_0` (was Multiply_6). Roughness chain untouched.
- `validate_material`: **0 errors**, 121 issues — the +1 vs the repair doc's 120 is the
  intentional `duplicate_parameter_name bNikkiFast (2)` warning, same accepted pattern as the
  existing `bUsePaintedLayers (4)`.
- `recompile_material` include_stats: default config **593 PS / 153 VS — identical to the
  all-off baseline** → the glow branch prunes exactly as designed.
- `get_compilation_stats` on `MI_Landscape_CliffGrass` (bNikkiFast/Hero/Triplanar all True):
  **910 PS / 13 samplers, compiled clean** with the glow live. (Not directly comparable to the
  doc's 684: the owner enabled painted-layer lanes on this instance after that measurement.
  Sampler ceiling respected at 13/16.)
- **Incident:** the save failed twice (`saved:false, was_dirty:true`) — the file was **read-only
  on disk** (the `.uasset` read-only population strikes again; my first attribute read was
  label-inverted and wrong). While diagnosing, the editor session (PID 31180) **died on a fatal**
  (`StaticShutdownAfterError`, 18:27 local) — the unsaved wiring was lost with it. Read-only
  cleared on disk; re-application queued the moment the replacement editor (owner relaunch,
  PID 61112) is live. The proven call sequence is recorded here so the redo is mechanical.

### 5.2 Nikki glow wiring — RE-APPLIED AND SAVED (final)

The replacement editor (owner relaunch) came up at 18:33. The §5.1 sequence was re-applied
mechanically (same node names `Constant_1` / `StaticSwitchParameter_0` / `Add_0`, same six
connections, read back through `get_expression_connections`), the transaction closed, and with
read-only cleared on disk the save **succeeded**: `saved:true`, on-disk mtime 15:55:45 →
**18:39:49**, size 214,246 → 216,708 bytes. Post-save recompile on the saved asset: **593 PS /
153 VS, compiled clean** — default configuration identical to the pre-wiring baseline, glow
branch pruned. `MI_Landscape_CliffGrass` (all Nikki lanes True) compiles clean at **910 PS /
13 samplers** with the glow live. Rollback duplicate `_PRE_NIKKIGLOW_20260829` retained in the
archive folder.

### 5.3 Shorewake dress — material fixed (was `Material_001`)

- Created `MI_Melusina_Dress_Shorewake` (parent `M_Master_Toon_Universal`): Albedo ←
  `T_MelusinaC_DressShorewake_BaseColor`, NormalMap ← `_Normal`, EmissiveMap ← `_Emission`,
  `bUseEmissiveMap=true`. (Roughness map intentionally not wired: Universal's separate-roughness
  param gating was not verified in the time box — one `set_instance_parameter` follow-up.)
- Assigned to `SK_ShorewakeDress` slot 0 via the `FSkeletalMaterial.material_interface` array
  replace (the struct-copy no-op trap), **read back from a fresh load** and saved
  (`SAVED=True`). The dress no longer references `Material_001`.

### 5.4 Leviathan + Drowned Organ textures — imported (was: staged only)

All six PNGs (already staged in `Content/.../Reef/Textures/`) imported with correct flags —
Normals as `TC_Normalmap`/linear (`WorldNormalMap` LOD group), Roughness linear
(`WorldSpecular`), color maps sRGB `TC_Default`: `T_Leviathan_Bone_{BaseColor,Normal,Roughness}`,
`T_Organ_Pipe_{BaseColor,Normal,Emissive}`. This closes the water-closeout §6 "6 textures staged,
not imported" item and avoids the documented sRGB-on-data-mask defect class.

### 5.5 New instances for the two meshes (mesh imports still queued)

- `MI_SeaAbove_Leviathan_Bone` (Albedo + NormalMap) on `M_Master_Toon_Universal`.
- `MI_SeaAbove_Organ_Pipe` (Albedo + NormalMap + EmissiveMap, `bUseEmissiveMap=true`).
- `SM_Leviathan.obj` / `SM_DrownedOrgan.obj` asset imports still queued (mesh lane) — both now
  have ready-made MIs waiting; note the crash autosaves of earlier partial imports exist under
  `Saved/Autosaves/` as reference.

### 5.6 Not reached inside the 2-hour box (handed to the next lane)

1. `MI_Melusina_WaterHair` creation on `M_Water_Master_Grand_v7` + `SK_MelusinaHair` 4-slot fix
   (hair file read-only cleared already; the water-closeout claim that the MI exists was wrong).
2. `SK_Melusina_V2_Shirt` outline slot — reference wiring exists on the other V2 pieces
   (`MI_Melusina_Outline_004/_005` family).
3. OBJ mesh imports for Leviathan/Drowned Organ + slot assignment.
4. CliffGrass: owner's live retune was lost unsaved with the 18:27 editor death — two autosave
   copies exist at `Saved/Autosaves/.../MI_Landscape_CliffGrass*` for recovery (owner call).
5. Ocean visual pass + preset application (§6 items 1–2), C++ fixes (§6 item 2).

## 6. Needs-love list (for the next lane)

1. Ocean visual pass: open `LV_SeaAbove_Prototype`, sweep `Toon_Weight` 0→1, `Toon_Bands` 2→8,
   then apply `DA_Color_AnimeLightBlue` + `DA_Foam_Stylized` on the two `MI_SeaAbove_*_Oceanology`.
2. C++ (shared rebuild): beat-drive via `SetScalarParameterValue` on our param names; Oceanology
   water-query adapter (proximity events currently read Z=0).
3. Mirror `M_Master_Toon_Universal`'s Madoka/Itto input wiring onto HeightBlend behind a switch.
4. Decide the SDF lane's consumer (§2) or archive it.
5. Shorewake dress: morph carry-over check (Bloom/Swirl/ShimmerWave on the owner's rig) still
   unverified in-engine.
6. The `MF_NikkiDreamGrade.Emissive` visual: once the wiring is re-applied and saved, look at
   `bNikkiFast=True` shimmer on camera and tune `Rim*`/`Sparkle*` params (currently all 0).
