# Melusina Gen-3 Migration — Execution Record — 2026-09-10

**Target look:** newest Blender PNG set, all pieces. Branch:
`cleanup/melusina-gen3-accessories-hair-2026-09-10`.

## Done

1. **Imported 70 gen-3 textures** (all present PNGs lacking `.uasset`):
   Boot BC/N/ORM, Bow/Shirt/Skirt/SkirtPanel/Sleeve/FrontPanel/Gloves/Shawl/
   IrisBack/IrisFront × {BC,Emission,H,Mask,N,ORM} + FrontPanel_Sheen +
   Sleeve_Alpha + UpdatedShirt BC/H/Mask/N/ORM. Per-suffix compression:
   BC/Emission sRGB, N → TC_NORMALMAP linear, H/ORM/Mask/Alpha/Sheen linear.
   70/70 imported, 0 failed.
2. **Migrated 6 accessory MIs to gen-3** (31 params, live `texture_parameter_values`
   is ground truth): Albedo←BC, NormalMap←N, HeightMap←H, MetallicMap←ORM,
   RoughnessMap←ORM; skirt `EmissiveMap` was a neutral-utility placeholder and
   now binds real `T_Melusina_Skirt_Emission`. Mask maps imported but unbound
   (Toon Universal exposes no Mask param — recorded for later).
3. **V2 slot surgery:** `SK_Melusina_V2_Accessories` had scrambled assignments
   (sleeve slot→GLOVES MI, bow slot→sleeve MI, frontpanel→catch-all
   `Material_023`). Remapped idx1–4 by slot name; **023 is off V2**.
   `SK_Melusina_V2_Shirt` had a **null** slot (no MI_Material_008 existed):
   created it from existing 008 textures + assigned.
4. **Proof:** PIE smoke MelodiaIntegrationMap (session pie_smoke_2_190119):
   62 samples, 0 errors, clean teardown. 0 errored Blueprints, 0 dirty packages
   at close. Live-param redump confirms 100% gen-3 on all 6 MIs.

## Found but NOT fixed (flagged, owner/Blender lane)

- **Duplicate slot names on V2 Accessories:** 6 sections all named `SHAWL_001`
  holding SBW_007 / Outline_005 ×2 / bow_002 / frontpanel_001 / SHAWL_001.
  Entries9057 hold foreign MIs that may be mislabeled geometry — needs Blender
  slot rename at source, then re-import. Same pattern: Body 3×
  `Gradient__Radial__002`, Skirt 2× `skirtpanel_002`, Boots 2× `Material_017`.
- **Boot incomplete at source:** Emission/H/Mask PNGs do not exist — Blender
  re-export required (HOLD for owner art lane).
- **Hair untouched by choice:** `MI_Melusina_Hair` binds only body-bake Albedo;
  no hair maps exist. Removing the binding changes the look immediately, so it
  stays until owner blesses procedural-Toon hair or authors maps. `SK_MelusinaHair`
  carries a `/Game/Melodia/_Probe` dep; V2Test static hair is reference-only.
- **Latent strings:** stale `/Game/frontpanel_BaseColor`, JRO-mask dual-home
  (`/Game/Textures/` vs `EnvSandbox/Textures_Shared/`), Microscope/Marble refs
  persist as unbound strings only (live params are clean) — material-graph
  follow-up, no render effect today.
- **Read-only landmine:** the 6 MIs + 2 SKs were ReadOnly on disk (09-02
  stamps); editor saves silently returned False until flags were cleared.
  Worth a repo-wide read-only audit before the next material pass.

**Evidence level:** live-proven (import reports + param redumps + PIE smoke);
Blender-source slot renames + Boot maps still owed.
