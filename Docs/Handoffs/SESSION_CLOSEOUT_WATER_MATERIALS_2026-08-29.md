# Session Closeout - Water Convergence + Material Pass - 2026-08-29 ~01:30

Continues `P0_SHIP_NIGHT_BASELINE_2026-08-28.md`. Everything below verified on disk, in the
engine log, or by editor read-back - **never by a Monolith return value** (see section 5).

## 1. Water convergence - DONE

`/Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia` - a project-owned duplicate of
the plugin master `M_Oceanology` (plugin content never edited), with two grafted layers.

```
MF_Oceanology --+-> Scattering/Absorption/PhaseG/ColorScale -> SingleLayerWaterOutput
                +-> GetMA[Emissive Color] -> Add.A
                |     MF_WaterBioluminescence_v9.Emissive x Biolum_Weight -> Add.B
                |     Add -> SetMA_0[Emissive Color]
                +-> GetMA[Base Color] --+-> xToon_Bands -> Floor -> /Toon_Bands --+
                                        +--------------------------> Lerp.A  Lerp.B
                                                 Toon_Weight -> Lerp.Alpha
                                        Lerp -> SetMA_1[Base Color] -> material result
```

**Proof it is live:** pixel-shader instructions 1590 -> **1638**, expressions 22 -> 30. Every
earlier build compiled to exactly 1590 - byte-identical to stock `M_Oceanology` - so 1638 is
the first hard evidence the graft reaches the shader.

**121 parameters**: Oceanology 106 untouched + 15 new, all instance-tunable. Biolum set
(Weight, Intensity, Density, FlashRate, FlashThreshold, FlashDecay, ShearProxy, RippleMask,
CrestCompression, DepthMask + 3 tints), plus `Toon_Bands` (4) and `Toon_Weight` (0.65).
Toon_Weight 0 = pure Oceanology; 1 = full posterisation.

Instances (parallel, NOT reparented - see section 2):
- `MI_SeaAbove_FalseOcean_Oceanology` - 17 overrides, Beaufort 2, foam 0.08, Biolum_Weight 0.35
- `MI_SeaAbove_SurfaceOcean_Oceanology` - 17 overrides, Beaufort 3, foam 0.45, Biolum_Weight 0.25

Biolum tints ported verbatim from the authored v10 instances, not invented.

**NOT YET SEEN RENDERED.** Structurally verified only; the viewport was unusable most of the
session. First visual check is outstanding.

## 2. Why the v10 instances were NOT reparented

`MI_SeaAbove_FalseOcean` (40 overrides) and `MI_SeaAbove_SurfaceOcean` (39) are tuned for
`M_Water_Master_Grand_v10_Upgrade`. **None of those parameter names exist on Oceanology** -
BaseTiling, MacroScale, RippleCenterA/B/C, MagicalIntensity, POMDepth, the whole WaterV10 and
Bio families. Reparenting would destroy 79 authored values that match the documented Sea Above
spec line-for-line (NativeWaterAvailability=0, WorldUVBlend=1, WorldTextureScale=0.0012,
FoamIntensity=0.05, WaveSpeed=0.06).

Parallel instances instead: swap the material on `SeaAbove_FalseOcean_Plane` to A/B them. The
false ocean is presentation-only and is not gameplay-water authority, so this is free.

## 3. Oceanology capability audit (settles a recurring question)

Checked all 139 material functions, all 106 master parameters, the whole plugin tree.

| Claim | Verdict |
|---|---|
| Toon / cel / posterise / ramp shading | **None.** Zero such functions or parameters. |
| Substrate | **None** in plugin content. Legacy MSM_SINGLE_LAYER_WATER, auto-converting because r.Substrate=True (DefaultEngine.ini:39). |
| Bioluminescence | No system, but `Foam Emissive` (vector, default 0.03/0.10/0.06) exists - an emissive primitive, foam-scoped. |
| Customisation | **Extensive** - 82 scalar + 10 vector + 5 texture + 9 switch. More than the project own v10 master. |

Conclusion: Oceanology owns physics and gameplay-water authority; the project MF_Water v7/v9/v10
library owns the look. Complementary, not redundant. This session built the first joint.

## 4. Reef material pass - complete

All **25** reef meshes off placeholder materials. Five instances on `M_Master_Toon_Universal`:
MI_SeaAbove_CoralSkin, _CoralSkin_2S (two-sided, for Coral_Fan), _Kelp (two-sided), _Sand,
_WetRock. Jellyfish: MI_Jelly_Bell + MI_Jelly_Arms on `M_Master_Toon_Universal_Alpha` (opacity
+ emissive from T_Jelly_Biolum_LUT); bell morphs PulseContract/PulseExpand/SurrealLurch intact.

Late imports also fixed: SM_Flora_Fern/Reed/Chime, SM_Banner, SM_Shroud -> MI_SeaAbove_Kelp.
**SM_Banner and SM_Shroud are skeletal cloth with physics assets and want their own fabric
material - Kelp is an explicit placeholder, not a final look.**

29 texture import defects corrected overall (masks/LUTs arriving sRGB when they are data). The
load-bearing one: T_SeaAbove_KelpSway_LUT drives WPO via (rgb*2-1); an sRGB decode makes the
sway displacement numerically wrong.

## 5. Hard-won operational rules

1. **Monolith return values lie.** Confirmed on save_loaded_asset, stop_pie, save_current_level -
   all returned false while succeeding. Verify by mtime, on-disk grep, or engine log.
2. **get_expression_details can return stale data.** It reported AttributeGetTypes unset on a
   node that had it. Cross-check with a direct Python property read.
3. **Raw grep on .uasset gives false positives AND false negatives.** Old material names persist
   in the package name table after reassignment; new GUIDs hide in compressed sections.
4. **PIE teardown is async.** load_level straight after stop_pie crashes the editor. Poll
   is_in_play_in_editor() until False. Teardown measured at ~1s.
5. **Never write AttributeSetTypes / AttributeGetTypes via Monolith** - see
   `Docs/Reference/UE58_MATERIAL_ATTRIBUTE_GUIDS.md`. Set crashes instantly; Get corrupts
   silently and detonates on next load. Use the Details panel.
6. **2,719 read-only .uasset files under Content/** still. Saves against them fail and the API
   returns False rather than raising. Cleared only for ChoralSheep (14) and DA_MelodiaIntegrationConfig.

## 6. Open - needs a person

- **Five P0 gates**: rhythm_owner, rhythm_grade_to_result, wardrobe_equip_roundtrip,
  wardrobe_gameplay_hook, music_world_key. All need live PIE with real Q/W/O/P input; wardrobe
  needs a full process restart. music_world_key is wired and proven 5/5 at the bridge level but
  was driven by a delegate broadcast, not player input - correctly still open.
- **Six-pass playtest passes 3-6** were blocked by a corrupt material, now quarantined at
  `Saved/Quarantine/M_Water_Oceanology_Melodia.CORRUPT_AttributeGetTypes_2026-08-29.uasset`.
  **Unblocked; re-runnable.**
- **MelodiaQuillShorewake.qsc is doubly inert** - no compiled .uasset, and 4 of its 5 IDs are
  missing from the allowlist: quest.shorewake.initiation, flag.quest.shorewake_completed,
  flag.sea_above.starskiff_ready, reward.shorewake_weave. (melodia_resonance is present.) Same
  failure pattern as the four P0 scripts. Compile it AND extend DA_MelodiaIntegrationConfig.
- **6 textures staged, not imported**: T_Leviathan_Bone_{BaseColor,Normal,Roughness},
  T_Organ_Pipe_{BaseColor,Emissive,Normal}. SM_Leviathan.obj and SM_DrownedOrgan.obj also
  un-imported.
- **SK_MelusinaHair slot mis-assignment** - all four slots, including both outline slots, are on
  MI_GrandWater_SakuraPond1; the purpose-built MI_Melusina_WaterHair is unused.
  SK_Melusina_FIXED_Hair is worse (raw auto-import materials). Note: MI_Melusina_WaterHair sits
  on **v7 deliberately** - v7 has HairDripIntensity/DripSpeed/DripLength/SplashForce which v10
  dropped. Do not "upgrade" it to v10.
- **SK_Melusina_V2_Shirt has no outline material** (0 refs vs 3 on every other V2 piece).
- **Toon band unseen** - set Toon_Weight and look at it.
