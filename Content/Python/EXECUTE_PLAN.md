# Environment Material Expansion — Execute Plan

## Phase Order (Highest ROI first)

### Phase A: Gradient Tint Rock + Detail Normal Wiring (2 sessions)
- Implement Genshin-style altitude-based rock coloring using `MF_ColorRamp3`
- Wire the 28 unwired DetailNormal samplers in the universal master
- Create unified `MF_EnvironmentalWeathering` combining slope/height/curvature

### Phase B: Gemstone/Crystal Stack (2 sessions)
- Promote `MF_Gemstone` from scratch to production
- Wire IOR-aware refraction path on the universal master
- Integrate 15 BlingVol3 rhinestone textures into material instances

### Phase C: Triplanar Single-Calc (2 sessions)
- Replace 18 WAT/WAN calls with one custom HLSL computing triplanar UVs
- Add `bTriplanar_Active` gate + per-channel `TriplanarBlend`
- Add `TriplanarSlopeStart/End` for angle-based gating

### Phase D: FabricType + Dream Compositor + Layered Stack + Face SDF (4 sessions)
- FabricType enum (silk/velvet/satin/lace/brocade)
- Dream glow as unified compositor layer
- Material stack (base → trim → jewel)
- Face SDF shading

---

## What I Can Execute Right Now

1. **Gradient Tint Rock** — code first, uses existing `MF_ColorRamp3`
2. **Wire existing BlingVol3 textures** — raw imports just need material instances
3. **Design unified weathering MF** — document the function interface

Delegate research sub-agents for:
- Gemstone refraction shader techniques
- FabricType anisotropic specular implementations
- Face SDF shading in UE5

Ready to begin Phase A. Start with Gradient Tint Rock on the Landscape master?
