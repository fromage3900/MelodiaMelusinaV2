# Living Storybook Landscape Master

## Authority and recovery lineage

The active master is `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend`.

- `..._BACKUP_20260728` is the preserved pre-fallback authored source.
- `..._SAFE_FALLBACK_20260729` preserves the compile-safe minimal landscape; it is a recovery reference, not the artistic source.
- `..._AUTHORED_RESTORED_20260729` and `..._LIVING_STORYBOOK_PRETRIPLANAR_20260729` are checkpoint packages from the restoration process.
- Work candidates remain retained for forensic comparison. Never delete or broadly reassign them while validating Zen Forest.

Do not run `rebuild_landscape_safe_fallback.py` or force-run `setup_landscape_height_blend.py` against the active master: both clear and rebuild material graphs.

## Surface ownership

- Rock, Grass, and Mud are normalized painted base layers with `MF_LandscapeHeightCompete` preserving paint authority.
- Path is an ordered traversal overlay: it replaces visible ground treatment without erasing base paint data and suppresses base grass eligibility.
- Wonder is an independent Landscape paint layer. It owns only presentation masks, never collision, terrain paint authority, or global lighting.
- Physical surface mapping remains Rock→Stone, Grass→Grass, Mud→Soil, Path→Path, Wonder→Grass.

## Living Storybook lanes

- `MF_LandscapeMacroVariation` provides seeded world-space macro breakup. `MacroVariationStrength=0` by default; `RockMacroStrength`, `GrassMacroStrength`, `MudMacroStrength`, and `PathMacroStrength` shape enabled instances.
- `MF_LandscapeDistanceBands` provides Near 0–2500 cm and Far 8000–30000 cm weights. Near detail normals and far atmospheric convergence are feature-weight fades, never opacity/dither fades.
- `MF_LandscapeStorybookSDF` creates a non-raymarched world-space clover/petal pool. It is multiplied by Wonder paint and defaults off through `WonderStrength=0`.
- Rock-only triplanar projection uses UE’s WorldAlignedTexture on steep Rock-painted surfaces. Defaults are neutral: `TriplanarBlend=0`, start `0.35`, end `0.72`.
- `bLandscapeHeroTier=false` and `bLandscapeFastTier=false` is Standard. Hero gates Wonder sparkle; Fast takes precedence over Hero for that overlay. Keep the switches mutually exclusive in material instances.
- `MF_DF_ContactBlend` remains a mesh/Universal-master feature. It may darken or roughen nearby props at terrain contact but is never sampled by this Landscape master.

## PBR import contract

Until authored maps are complete, the active defaults remain CC0: Marble012 Rock, Ground037 Grass/Mud, and PavingStones070 Path. Each authored layer replaces all four slots as one validated set:

`T_Land_<Surface>_{BC|BaseColor,N|Normal,ORM,H|Height}` under `/Game/Melodia/Art/Materials/Landscape/<Surface>/Textures`.

- Albedo uses sRGB.
- Normal, ORM, and Height are linear; ORM channels are AO/Roughness/Metallic.
- `bUseLayerORM` stays false until a complete authored ORM set is present. The temporary sample fallback is safe but not art direction.

## Controls and validation

- Wonder zone: paint Wonder, enable Hero, then raise `WonderStrength`; optionally add `WonderSparkleBoost` and capped `AudioReactiveStrength`.
- Debug: `bLandscapeDebugMasks` displays Wonder, Path, and a distance-band mask. The named Debug Height/Path/Slope/Distance/Wonder switches are reserved for focused profile diagnostics.
- `Saved/Audit/landscape_aaa_audit.json` must remain 91/91 before a broad reassignment.
- Sign-off requires close, traversal, distant, and debug-mask Zen Forest captures; compare Standard shader instructions with the restored baseline before enabling Hero outside capture zones.
- RVT integration is intentionally deferred until the base master is visually approved and measured.
