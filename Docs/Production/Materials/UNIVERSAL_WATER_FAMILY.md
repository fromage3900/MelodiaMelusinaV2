# Universal Water Family

`/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6` is the canonical
surface-water master. Its instances cover lakes, ponds, rivers, shoreline
surfaces, swamp water, frozen ponds, and waterfall sheets. Do not revive
`M_Master_Toon_Water` or assign a surface-water instance to Melusina's hair.

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
