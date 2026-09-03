# Reef Import Queue — editor holder's checklist

Raw assets staged by `Tools/Houdini/sea_above_reef/stage_to_sandbox.py`
(sha256-verified against `Saved/Audit/sea_above/` sources; see `stage_manifest.json`).
Contact sheets and audit copies were deliberately NOT staged.

Import target namespace: `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/…`
(UE 5.x: enable *Show External Files* in the Content Browser to import in place,
or use Add → Import from this folder.)

> **STATUS 2026-08-29 (materials takeover, commit `2c201fe3`) — most of this queue is DONE.**
> - **Textures: 35/41 imported** (incl. the whole table below with the flags listed, plus the
>   sRGB-on-data defects corrected in the 01:16 water-materials session). The last six —
>   `T_Leviathan_Bone_{BaseColor,Normal,Roughness}` + `T_Organ_Pipe_{BaseColor,Normal,Emissive}` —
>   were imported 2026-08-29 evening with correct flags (normals `TC_Normalmap`/linear,
>   `WorldNormalMap`; roughness linear `WorldSpecular`; color maps sRGB).
> - **Meshes: all coral/kelp/island/rock/flora/cloth/jelly uassets exist** (morphs on
>   `JELLY_Bell` verified intact). **Still missing: `SM_Leviathan.obj` + `SM_DrownedOrgan.obj`
>   mesh imports** — their MIs are ready and waiting
>   (`MI_SeaAbove_Leviathan_Bone`, `MI_SeaAbove_Organ_Pipe`, created + saved 2026-08-29 on
>   `M_Master_Toon_Universal`, Organ Pipe with `bUseEmissiveMap=true`).
> - **Instances: reef MI set live** (CoralSkin/2S, Kelp, Sand, WetRock on
>   `M_Master_Toon_Universal`; Jelly_Bell/Arms on the Alpha master). Kelp/Banner/Shroud are on
>   Kelp as an explicit placeholder (Banner/Shroud want a fabric master eventually).
> - **Shorewake dress**: `SK_ShorewakeDress` slot 0 now on
>   `MI_Melusina_Dress_Shorewake` (auto-import `Material_001` retired).
> - Remaining material work: ocean visual pass + `Toon_Weight` dial (§7 of
>   `Docs/OCEANOLOGY_STYLIZATION_AND_TRAVERSAL_INTEGRATION_RESEARCH_2026-08-29.md`),
>   Banner/Shroud fabric master, textured render QA pass.

## Textures → `Reef/Textures/`

| File | sRGB | Compression | LOD Group | Notes |
|---|---|---|---|---|
| `T_SeaAbove_Sand_Albedo` | **true** | TC_Default | World | tiling base |
| `T_SeaAbove_Sand_Height` | false | TC_Default (grayscale ok) | World | height/blend |
| `T_SeaAbove_Sand_Normal` | false | TC_Normalmap | World | **OpenGL Y+** — uncheck "Flip Green" only if authored DirectX |
| `T_SeaAbove_Sand_WetMask` | false | TC_Masks | World | darken/roughness |
| `T_SeaAbove_Sand_RippleMask` | false | TC_Masks | World | ripple breakup |
| `T_SeaAbove_Caustics` | false | TC_Masks | **Effects** | **two-panner blend**: sample twice, offset (0.03,0.0)/(−0.02,0.04), combine `max` or screen |
| `T_SeaAbove_ShellMask_Nautilus/Scallop/Conch/SandDollar` | false | TC_Masks | World | material masks |
| `T_SeaAbove_Clutter_Atlas` | **true** | TC_Default | Effects | 4×4 decal atlas, straight alpha, 256px cells |
| `T_SeaAbove_ClutterFloor_Mask` | false | TC_Masks | World | debris breakup |
| `T_SeaAbove_CoralSkin_Albedo` | **true** | TC_Default | World | tint per pitch class in MI (12 PCs, matches Choral Sheep chromatic set) |
| `T_SeaAbove_CoralSkin_Normal` | false | TC_Normalmap | World | OpenGL Y+ |
| `T_SeaAbove_CoralSkin_EmissiveMask` | false | TC_Masks | Effects | emissive × `User.SeaAbovePulse` MPC param — **the only pulse writer is `BP_SeaAbove_PrototypeDirector`** |
| `T_SeaAbove_KelpSway_LUT` | false | TC_Default (RGB data) | **Effects** | **half-wrap**: sampler Wrap on U (time), Clamp on V (height). See the sway recipe below |
| `T_SeaAbove_Droplet_Atlas` | false | TC_Default (RGB data) | **Effects** | 4×4 flipbook, 512 cells, luminance in RGB; feeds the Niagara droplet system (flipbook plan §3 target state) |
| `T_SeaAbove_Membrane_Reveal` | false | TC_Masks | Effects | centered radial (non-wrapping); drives `RadialReveal` in `M_SeaAbove_Membrane_Prototype` |
| `T_SeaAbove_Membrane_Ripple_N` | false | TC_Normalmap | Effects | centered radial ripple normal (non-wrapping) |
| `T_SeaAbove_WetRock_Albedo/_Normal/_Wetline` | albedo true; others false | Default/Normalmap/Masks | World | tilable wet-rock set for island cliffs |
| `T_SeaAbove_BarnacleCrust_Mask` | false | TC_Masks | World | tilable crust rings |
| `T_SeaAbove_PulseBand_LUT` | **true** | TC_Default | Effects | 12 pitch-class pastel ramp; tint band by PC index |
| `T_SeaAbove_Foam_Mask` | false | TC_Masks | World | tilable foam streaks (waterline) |
| `T_SeaAbove_Sediment_Ramp` | **true** | TC_Default | Effects | vertical gradient ramp (64×1024, clamp sampling) |

All tiling maps: set sampler **Wrap**, texture group already suggested above; all verified
seam-free (14/14 by `ingest_reef_textures.py`).

## Meshes → `Reef/Meshes/`

Import `.obj` (Interchange or legacy importer): **Uniform Scale 100** (Houdini metres → UE cm),
Nanite **on**, combine meshes off (one asset per file).

| File | Contents | Material notes |
|---|---|---|
| `SM_Coral_Staghorn` | recursive downward-branching tube tree (1920 prims) | CoralSkin + per-PC tint; emissive from CoralSkin_EmissiveMask × SeaAbovePulse |
| `SM_Coral_Table` | hanging ribbed disk, 720 prims | two-sided not required |
| `SM_Coral_TubeSponges` | 5 open-topped tubes | emissive rim: uv.y ≈ 1 at rim |
| `SM_Coral_Fan` | warped fan plate + stem | **needs two-sided material** |
| `SM_Coral_Brain` | folded displaced sphere | CoralSkin normal at high contrast |
| `SM_Coral_ReefCluster` | 26-arm composition scatter | LOD/PCG scatter starter |
| `SM_Clutter_PebbleSet` | 14 squashed UV spheres | sand/pebble MI |
| `SM_Clutter_Starfish` | puffed star profile | clutter MI |
| `SM_Clutter_SpiralShell` | log-spiral tube (610 prims) | shell mask + CoralSkin |
| `SM_Clutter_SeaWeed` | sway-curved tapered tube (200 prims) | two-sided; VAT sway is a later upgrade (plan §3A R3) |
| `SM_Kelp_Tall` | ribbon, h=2.0 m, uv.y = growth axis (R3) | **Kelp Sway recipe below** |
| `SM_Kelp_Mid` | ribbon, h=1.5 m, wider (R3) | **Kelp Sway recipe below** |
| `SM_Kelp_Cluster` | 3 merged stalks (R3 scatter starter) | **Kelp Sway recipe below** |
| `SM_Island_A` | r≈6 m dome, flat plateau, 7 hanging drips (R4) | WetRock set; drips darker via Cd (bgeo only) |
| `SM_Island_B` | r≈4 m, steeper, 5 drips (R4) | WetRock set |
| `SM_Island_C` | r≈8 m, broad plateau, 10 drips + tendril (R4) | WetRock set |
| `SM_RockChunk_M/L` | displaced 3-lump scatter rocks 0.8/1.6 m (R4) | WetRock set |

## THE JELLYFISH (R6) — bell morphs + football-field ribbon arms

| Asset | Contents | UE wiring |
|---|---|---|
| `JELLY_Bell.fbx` | ~90 m bell, **morph targets**: `PulseContract`, `PulseExpand`, `SurrealLurch` (basis = Neutral), single-root armature | import as **Skeletal Mesh** so morphs are drivable; swim pulse = crossfade Contract↔Expand on a sine; `SurrealLurch` rare (holder BP; no new MPC writer) |
| `JELLY_Arms.fbx` | 8 ribbon arms, ~320 m each (**3.5 football fields**), Moebius half-twist, bifurcation drift, anti-gravity rise baked into the rest shape | import as static mesh, **Nanite on**; motion via WPO recipe below |
| `T_Jelly_ArmLogic_LUT` | 512² RGB data; U = time loop, V = along-arm (`uv.y`) | arms WPO: `(rgb*2−1) * SweepAmplitudeMetres` (default **24 m**); `Amp *= (1 + 1.5 * User.SeaAbovePulse)`; sampler Wrap U / Clamp V |
| `T_Jelly_Biolum_LUT` | 512×256 sRGB emissive; U = time, V = along-arm | arms emissive lookup — traveling cyan→magenta pulse bands, pooled where the arm folds |
| `T_Jelly_Bell_*`-style veil materials | bell = translucent veil | Two-Sided, `surface_render_method` BLENDED, fresnel-driven opacity; emissive canal mask optional |

**Scale note:** the FBX geometry is already in UE cm (×100 applied in Blender) — import at scale 1.0.
QA renders: `Saved/Audit/sea_above/renders/jelly/JELLY_Overview.png`, `JELLY_Bell.png`.
Source of truth: `jellyfish_mesh.json` + `jellyfish_mesh_manifest.json` + `jelly_fbx_manifest.json`
(topology match across all poses: verified True). One-writer rule intact: `User.SeaAbovePulse` only.

## Iridescent bell recipe (R6 v2) — the magical parameter manifest

**MI_JellyBell** (two-sided blended veil; parent = existing translucent master, instance only):

| Parameter | Range / Default | Wiring |
|---|---|---|
| `IridescenceIntensity` | 0–2, **1.2** | scales the LUT emissive contribution |
| `IridescencePower` | 0.5–8, **2.5** | exponent on Fresnel before the LUT U lookup |
| `FilmPhaseSpeed` | 0–0.2, **0.05** loops/s | pans `T_Jelly_Bell_Irid_Mottle` → added to the LUT **V** (film phase) |
| `VeilOpacity` | 0–1, **0.75** | multiplies `T_Jelly_Bell_Opacity` |
| `CanalGlow` | 0–5, **2.0** | `T_Jelly_Bell_CanalMask` emissive, × `(0.4 + 1.6 * User.SeaAbovePulse)` |
| `BellShimmerMetres` | 0–1, **0.25** | veil WPO: slow LUT-free sine shimmer (two axes, 0.15/0.23 Hz) |

**Node chain (bell):**
1. `Fresnel(exp=IridescencePower)` → **U** of `T_Jelly_Iridescence_LUT`.
2. `Time × FilmPhaseSpeed` → panner on `T_Jelly_Bell_Irid_Mottle` → **+ LUT V** (film thickness).
3. LUT RGB × `IridescenceIntensity` → **Emissive** (additive over BaseColor).
4. `T_Jelly_Bell_BaseColor` → BaseColor; `T_Jelly_Bell_Normal` → Normal (OpenGL Y+).
5. Opacity = `T_Jelly_Bell_Opacity × VeilOpacity`; Two-Sided; BLENDED render method.
6. Canal emissive = `T_Jelly_Bell_CanalMask × CanalGlow × (0.4 + 1.6·SeaAbovePulse)`.

**MI_JellyArms parameters** (adds to the WPO recipe above):

| Parameter | Default | Effect |
|---|---|---|
| `SweepAmplitudeMetres` | **24** | lateral bend from `T_Jelly_ArmLogic_LUT` (baked h-cascade + bifurcation) |
| `FlutterAmplitudeMetres` | **6** | fast small-scale flutter: second LUT sample at 4× time speed, blended 20% |
| `PulseGain` | **1.5** | `Amp *= (1 + PulseGain * User.SeaAbovePulse)` |
| `BiolumSpeed` | **0.5** loops/s | `T_Jelly_Biolum_LUT` U panner |
| `BiolumIntensity` | **3** | emissive scale (multiply by bend-magnitude mask baked in the LUT) |
| `GlintPannerSpeed` | **0.3** | `T_Jelly_Nematocyst_Glints` pan along uv.x → stinging-cell sparkle |
| `GlintIntensity` | **1.5** | glint emissive additive |

**Morph driver table (bell, holder BP — no new MPC writer):**
- Swim pulse: `PulseContract` ↔ `PulseExpand` crossfade, sine at **0.25 Hz**, bias 0.1 toward Expand.
- `SurrealLurch`: weight 0 normally; trigger every 20–40 s (rng), ramp 0→1 over 0.6 s, hold 0.8 s, fall 1.5 s.
- All morph weights written by ONE bell director BP reading `User.SeaAbovePulse` for amplitude only.

**Sampler notes:** `T_Jelly_Iridescence_LUT` — Clamp U (facing), Wrap V (phase).
`T_Jelly_ArmLogic_LUT` / kelp LUT — Wrap U (time), Clamp V. Bell maps — Wrap U, Clamp V
(radial domain; verified U-only by ingest).

## DREAMS LANE — volumetrics, frozen cloth, flora, Starskiff MK2

**Volumes (UE 5.3+ Sparse Volume Textures):** `Volumes/VOL_GodRays.vdb`,
`VOL_GhostFog.vdb` (leviathan's ghost — place at the ribcage), `VOL_NebulaVeil.vdb`
(above the jellyfish). Import: Content Browser → import .vdb → Sparse Volume Texture;
material maps the grid as density/mask — colour, noise and animation live in the
material (noise-in-material by design; grids are smooth SDF shells).

**Frozen cloth morphs:** `SM_Banner.fbx` (morphs SwayA/SwayB/Billow) and
`SM_Shroud.fbx` (Gather/Drift/Settle) — skeletal with root bone; drive like the bell
morphs (slow crossfades; gust coupling to SeaAbovePulse optional). Silk = the
Shorewake dress material family.

> **SUPERSEDED (2026-08-29):** `Meshes/SK_ShorewakeDress.fbx` (the flat-layout join with
> Nikki morphs) is superseded by the OWNER's rigged, posed, weighted dress import
> (Blender + Substance, imported into UE). Do not import the flat one — it is kept only as
> the morph-authoring reference. Re-author the morphs on the owner's rig if they are absent
> in-engine (one Blender pass; math in `dress_transform.py`).

**Dream flora:** `SM_Flora_Reed/Chime/Fern` (code-L-system) — PCG scatter through the
reef kit; tips take CoralSkin/Iridescence; chime bells = the Bell motif seed.

**Starskiff MK2** (`SM_Starskiff_MK2.fbx`, built on a COPY of the owner's desktop
project): hull assembly + `GunwaleGlow` + `MastLantern` + FX sockets
(`FX_WakeEmitter_L/R`, `FX_SailCloth`, `FX_Lantern`). Materials: hull = the staged
`T_Starskiff_Hull_*` set; wake emitters = `T_Starskiff_Wake_Emission` with amplitude
× `(1 + 1.5 * SeaAbovePulse)`; mount `SM_Banner.fbx` at `FX_SailCloth`. Boat
traversal/gameplay is game-code (owner design) — the asset is traversal-READY.

## Kelp sway material recipe (R3) — no runtime sim, one MPC reader

For `MI_Kelp_Sway` (parent: any two-sided master you already own — **do not edit masters**):

1. **WPO** = `(TextureSample(T_KelpSway_LUT, UV) .rgb * 2 − 1) * SwayAmplitudeMetres`
   where `UV = (Time * TimeLoopSpeed, mesh uv.y)`. TimeLoopSpeed in cycles/sec (LUT is one
   full loop per U unit — e.g. `0.08` ≈ 12.5 s sway cycle).
2. `SwayAmplitudeMetres` scalar param (default ≈ **0.35**; LUT already bakes the h^1.8
   shaping, so the base stays pinned — do not re-multiply by uv.y).
3. **Pulse reaction**: `SwayAmplitudeMetres *= (1 + 1.5 * CollectionParam.User.SeaAbovePulse)`
   — the kelp visibly stiffens/flicks when the membrane pulses. `SeaAbovePulse` is read via
   the existing MPC collection; **`BP_SeaAbove_PrototypeDirector` remains the only writer**.
4. Texture sampler: **Wrap U / Clamp V** (V is the height axis; row 0 is the pinned base).
5. Material: Two-Sided on (single-layer ribbons); BaseColor = CoralSkin_Albedo tinted;
   normal from CoralSkin_Normal.
6. Verified: LUT U-loop is seam-free (wrap step 0.254 levels vs 0.204 gradient, ratio 1.246,
   `kelp_vat_textures.py` output). If sway ever looks clipped, raise the LUT → WPO scalar,
   never edit the texture.

True per-vertex FLIPBOOK VAT (per-vertex ID, non-uniform motion) is the Engine-license
upgrade path — meshes also exist as `.bgeo.sc` in `Saved/Audit/sea_above/meshes/` for it.

Meshes carry point `uv` attributes; OBJ carries no vertex colors — pulse-band breakup uses
`uv.y` (growth axis) in the material, per `coral_mesh_manifest.json`.

## After import

1. Nanite enabled, `Is Spatially Loaded` true (WP map), Data Layer: `DL_…` per level convention.
2. Materials: instances only — masters untouched.
3. Scatter via PCG or manual ISM; the composed `SM_Coral_ReefCluster` is a drop-in starter.
4. Record the import in the task ledger; the stage manifest is the source-of-truth file list.
