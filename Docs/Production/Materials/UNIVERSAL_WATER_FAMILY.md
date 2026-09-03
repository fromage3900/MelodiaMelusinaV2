# Universal Water Family

`/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6` is the canonical
surface-water master. Its instances cover lakes, ponds, rivers, shoreline
surfaces, swamp water, frozen ponds, and waterfall sheets. Do not revive
`M_Master_Toon_Water` or assign a surface-water instance to Melusina's hair.

## Current line (2026-08-14): v10_Upgrade is canonical

`M_Water_Master_Grand_v10_Upgrade` is the canonical v10 master — an additive
V9 upgrade preserving the V9 art-direction graph (wave, ripple, proximity-foam,
bioluminescence, normal, WPO, Substrate water outputs) with the native
interaction compatibility layer (`MF_WaterNativeInteraction_v10`) inserted.
Compile-verified: 16 samplers, 260 VS / 1727 PS, zero validation issues
(see `WATER_V10_FINALIZATION_STATUS_2026-08-09.md`). The five integrated
instances under `Instances/Water/v10/Integrated/` parent here.

- `M_Water_Master_Grand_v10_Substrate` is the **study line** for the UE 5.8
  native-water/Substrate integration (CalmPond + HeroFLIP parent there). Its
  promotion gates are still open — do not treat it as production.
- v6/v7/v9 masters remain in service for their existing instance families
  (`MI_GrandWater_*` → v6, `MI_Melusina_WaterHair`/`MI_Preset_WaterBeauty` →
  v7, `MI_WaterV9_*` → v9). No reparenting of those families.
- `MI_WaterV10_NativeDefault` intentionally parents to
  `MI_WaterV10_Integrated_CalmPond` (MI-of-MI) so it inherits the family
  overrides — allowlisted in `audit_mi_runtime.py`.

## Roadmap: v11 + UE water integration

UE 5.8-native Water Body integration is **on the roadmap**. `v11` (next-gen
master) will be authored only after the native integration study closes its
gates (see `WATER_V10_NATIVE_NIAGARA_SUBSTRATE_TOON_2026-08-09.md` and the
promotion gates list in `WATER_V10_FINALIZATION_STATUS_2026-08-09.md`): native
height/velocity replay on a real Water Body, project-owned Data Channel
consumer, PIE water traversal, audio activation, Tier 2/3/4 performance
captures, and the packaged World Partition audit.

Melusina's authored source identity is `Water (Advance).001`. Her runtime hair
uses the verified dedicated instance
`/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair` on
`/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair` (four material slots),
reusing only
safe water-family color, wetness, caustic, and `MPC_Portfolio_Audio` functions.
It disables large Gerstner displacement, screen refraction, shoreline foam,
world-volume depth fade, and uncontrolled translucent layering. Hair response
is cosmetic and never gates combat.

Use WaterBody actors for lakes, ponds, and broad rivers. Use spline sheets or
mesh strips for narrow streams, authored edges, and waterfalls. `BP_InstanceOnSpline`
is hand-authored dressing for wet stones, reeds, debris, foam cards, and
reflection markers; it is not a water simulation system. PCG owns static
shoreline dressing and Niagara owns mist, spray, droplets, ripples, and impacts.

Water intent uses `gmm_water_surface_request_v1` in
`Content/Python/gmm/geometry/water.py`. GMM validates schema, role, dimensions,
asset paths, flow, and spline requirements; Unreal owns runtime assets. The
fixture is `Content/Python/gmm/fixtures/water_surface_request.json`.

```powershell
python -m unittest discover -s gmm -p "test_*.py" -q
```

With UE access, run `Content/Python/validate_water_surface.py`; it writes
`Saved/Audit/water_surface_validation.json` and never edits
`BP_InstanceOnSpline_Old`. Run `audit_melusina_water_hair.py` after reopening
the project to verify the saved parent, overrides, and material slots. Shared rhythm reactivity may drive small beat
sparkle, crescendo lift, command glint, break splash, and victory ripples via
the MPC. Signals reset on encounter exit. Mobile disables mandatory spectrum
analysis, expensive refraction, camera impulses, and costly Niagara.

Translucent water remains platform-sensitive. A fresh UE graph audit must prove
whether `RefractionStrength` is connected; otherwise remove it from the public
contract rather than relying on a stale report.

## Infinity Nikki presentation lens

The target is readable fantasy spectacle: silhouettes and traversal remain clear
at a distance, while close-range water earns attention through layered motion,
controlled glints, and short event accents. Keep the base surface calm enough
for navigation; reserve stronger sparkle, spray, and color lift for authored
landmarks, rhythm commands, breaks, and victory. The profile fixture
`Content/Python/gmm/fixtures/water_family_profiles.json` records the intended
mobile/PC split and the hair-specific safety boundary.
