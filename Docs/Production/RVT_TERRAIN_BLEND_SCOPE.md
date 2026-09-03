# RVT Terrain Blend — Long-Term Scope (MeshBlend replacement)

**Goal:** the modern UE 5.8 way to make props/rocks/cliffs *melt seamlessly into the
landscape* — the effect MeshBlend was meant to give, without its plugin/per-instance-
data/Substrate-AO baggage. Runtime Virtual Texturing (RVT) is native, Substrate-
compatible, and needs no runtime plugin.

## How it works
1. The **landscape material** writes its base color / normal / roughness (and optionally
   world height) into a **Runtime Virtual Texture** via a `Runtime Virtual Texture Output`
   node.
2. An **RVT Volume** actor bounds the area and owns the RVT asset(s).
3. **Blend materials** (the universal master, on rocks/props) *sample* that RVT at their
   world position and **height-blend** their own material toward the terrain near their
   base — so a boulder's foot takes on the ground texture and the seam disappears.

## Assets / setup required (one-time, project-level)
- 1–2 `RuntimeVirtualTexture` assets: `RVT_Terrain_BaseColor_Normal_Rough` (and optional
  `RVT_Terrain_Height` for displacement-aware blends).
- `RuntimeVirtualTextureVolume` actor sized to each render level's ground bounds.
- Landscape material (`M_Master_Toon_Landscape_HeightBlend`): add a
  `RuntimeVirtualTextureOutput` fed from its base color / normal / roughness.
- Project settings: enable Virtual Texture Support (`r.VirtualTextures=1`) — verify it's on
  (Nanite projects usually have it). Streaming VT is separate and not required here.

## Universal-master side (the addable feature)
Add a gated `bRVTBlend_Active` (default OFF) path, group `02b | RVT Terrain Blend`:
- `RuntimeVirtualTextureSample` node (World space) reading the terrain RVT.
- Blend mask = `smoothstep` over the mesh's **world-Z relative to a `RVTBlendHeight` param**
  (foot = full terrain, up = full own material), optionally modulated by a noise breakup so
  the transition line isn't flat.
- `lerp(ownBaseColor, rvtBaseColor, mask)` on base color + same on normal/roughness.
- Params: `RVTBlendHeight`, `RVTBlendSharpness`, `RVTBlendNoise`. Default OFF = zero change.

## Substrate caveats (verify during the spike)
- RVT sampling works with Substrate, but confirm the toon BSDF's base color/normal splice
  points accept the lerp cleanly (same tail-splice discipline as the dream system).
- RVT **output** from a Substrate landscape material: confirm the `RuntimeVirtualTextureOutput`
  reads the Substrate base color/normal correctly on 5.8 (this is the main unknown).

## Effort estimate
- **Spike** (RVT assets + volume + landscape output + one rock blending in a test level):
  ~0.5 day. Gating risk = Substrate RVT-output behavior; low, RVT is well-trodden.
- **Master `bRVTBlend_Active` path** (gated, verified): ~0.5 day.
- **Per-level RVT volume placement + tuning** across the 4 pillars: ~0.5–1 day.
- **Total ~1.5–2 days** — far cheaper than the 3–5 day MeshBlend path, and no per-instance
  custom-data pipeline.

## Relationship to other options (see MeshBlend discussion)
- **RVT** = object-into-terrain (this doc). Best terrain contact blending.
- **Global Distance Field proximity** (`DistanceToNearestSurface`) = arbitrary mesh-to-mesh
  crevice detail; easiest to add to the master, no project setup — good complementary quick win.
- **Pixel Depth Offset** = cheap soft-intersection finishing touch.
- **GeometryScript boolean+remesh** = real welded geometry for hero pieces only.

## Recommendation
Do the **DF proximity blend** first (fast, master-native, no setup), then this RVT spike
when a terrain-heavy shot needs it. Treat MeshBlend itself as deprecated.
