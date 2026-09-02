# Faraway LOD Destruction — Fabric Mountains Dissolve via LOD (2026-09-02)

**Spec:** `faraway_lod_destruction_spec.v1.json`  
**Horizon twin:** `../horizon_eater/HORIZON_EATER_DESIGN.md`  
**Parent LOD:** `../lookdev/optical_lod_manifest.v1.json` (11 assets, 4 tiers, 563 textures)  
**VDM:** `Docs/Houdini/VDM_FABRIC_MOUNTAIN_SCAFFOLD_2026-09-02.md` + `Tools/Houdini/vdm_fabric_mountains/vdm_fabric_baker.py`  
**Klein veil precedent:** `../klein_veil/klein_veil_manifest.v1.json` (shared dither + LUT wiring)

---

## 1. Thesis — destruction is LOD, not simulation

> Do not sim the mountain collapsing at runtime. **LOD3 IS the crumbled mountain.** Tension decides how much of the vista has already become LOD3.

Runtime vista destruction must be HLOD/World Partition friendly, overdraw-safe, and deterministic. Chaos sim at horizon scale is not.

So:
- LOD0 (0-15m): intact close, POM32 deep crevices, full WPO.
- LOD1 (15-50m): still readable, POM16, stipple begins.
- LOD2 (50-200m): macro silhouette only, POM0, Toksvig stabilizes, WPO 30%, Bayer dither 0.35.
- LOD3 (200-5000m): **vista impostor crumble** — flat, Toksvig 1.0, rim 1.8, WPO 0, dither clip destroys to alpha 0.

Dither hides popping. Tension interpolates how many distant tiles have been forced to LOD3 early.

---

## 2. The four destruction operators

### A. Dithered opacity kill (MF_LODDitheredDestruction)

```
DitherValue = Bayer8x8(screen)*0.5 + BlueNoise64x64(worldUV)*0.5 + TemporalAAJitter(frame)*0.08
DestructionMask = VertexColor.R * VDM.A * HeightMask
Clip = DitherValue > (Tension * DestructionMask * lerp(1, HorizonEat, HorizonMask))
// Clip -> OpacityMask kill -> dithered stipple before hard pop
```

- `T_BayerDither_8x8` / `T_BlueNoise_64x64` / `T_Iridescence_LUT` live in `/Game/EnvSandbox/Textures/Copernicus/Shared/` (promote from `Saved/Audit/lookdev/optical_lods/shared/`).
- `VertexColor.R`: ridge 0.9 (dies first), valley floor 0.2 (persists). Painted or VDM-derived.
- `VDM.A`: pleat crests (mask) — same `RGBA32F proxy` encoding as Klein Veil: `R=X T, G=Y B, B=Z N lift, A=mask (0.5=zero)`.
- `HorizonMask`: distance>1500m && horizon-facing -> mix HorizonEat into threshold (same scalar as horizon eater).

### B. WPO fade (MF_FabricMountainWPO contract)

```
WPO_total = Macro*wp + Medium*wp*0.75 + Micro*wp*H_Cymatic + Wind
wp = WPO_Resonance_Scale per LOD: 1.0 | 0.75 | 0.3 | 0.0
Tension mod: wp *= (1 + BeatPulse*0.6) at LOD0, else *= (1 - Tension*0.8)
// At LOD3, no vertex moves — impostor flat.
```

Cymatic drive: `foldFreq = baseFreq(3) + BassIntensity*2.0`, `VDM.Z *= (1 + Bass*0.5)` — present contract.

### C. POM → Toksvig → Rim preservation

| LOD | POM | Toksvig | Rim | Read |
|-----|-----|---------|-----|-------|
| 0 | 32 | 0.0 | 1.0 | Deep crevice parallax, micro folds |
| 1 | 16 | 0.35 | 1.15 | Still parallax, adaptive |
| 2 | 0 | 0.75 | 1.4 | No parallax, Toksvig kills shimmer, rim restores edge |
| 3 | 0 | 1.0 | 1.8 | Impostor — only macro normal + grazing Fresnel, then erased |

Iridescence LUT (`T_LOD_Iridescence_ThinFilm_LUT`) still pulses via `BeatPulse` at LOD3 before erase — moon shimmer on dying silk.

### D. Niagara dust on crumble (budgeted)

`NS_FarawayMother_DustDrift` (Tier C instance): spawn **only** where dither clip just passed (band 0.4<Destruction<0.8), velocity = Tension vector + wind, rate = `Tension * Destruction * BeatPulse`. Reads `NPC_BeatPulse` (Niagara twin). Kills after LOD3 alpha 0 — prevents distant overdraw.

---

## 3. Tension-driven state (shared bus)

`WorldField.Tension 0..1` = `HorizonEatAmount 0..1` at horizon. `UMelodiaAudioReactivePresentationSubsystem` sole writer. All MIs read-only.

| Tension | Vista read | What the player can still do |
|---------|------------|------------------------------|
| 0.0-0.3 | Pristine — only LOD1 stipple | Full traversal, SeamWay unobstructed |
| 0.3-0.6 | Unease — LOD2, high ridges gone first | Wayfold still stable, high WeaveRidge gapped |
| 0.6-0.9 | Collapse — LOD3 dither 50-90%, filter corridors legible | Mother silhouette is haze only (production sheet: distant limbs = fog) |
| 0.9-1.0 | Eaten — LOD3 alpha 0, horizon gone | Only `MEL_mother_heart_gate` (Heart Gate) persists — Mara Anchor radius still holds 1m |

Per-biome gates:
- **WeaveRidge** (T>0.60, avg 0.96): threshold 0.35 — dies first. `MI_T_FarawayMother_Gown_CelestialSilkJacquard` boosted mask.
- **LaceCanopy** (0.40-0.60, avg 0.87): 0.50 — translucent lace hangs longer (Opacity map erodes).
- **FrillValley** (T<0.40 floor): persists to 0.85 — `MI_T_FarawayMother_Corset_GildedAcanthusBrocade`.
- **ResonantSeamWay** (`|Chladni|<0.12`): **never fully** — becomes the Wayfold path to horizon mouth. Gate 0.95 quest-locked.

MPC addition: `HorizonEatAmount`, `DestructionAmount` (Faraway local, can be `HorizonEat*0.9` coupling). Script `add_horizon_eater_mpc_params.py` adds all three if missing (safe no-op).

---

## 4. PCGEx + HLOD

- **Inputs:** 120 points from `faraway_mother_pcg_manifest.v1.json` (30 per biome, 4 biomes).
- **Graph:** `PCG_FarawayLOD_DestructionFilter` — `TensionCull` (density `*= 1 - Tension*BiomeFactor`), `DitherSpawn` (BlueNoise keep/discard), `AdvectTowardSeamWay` (destroyed points slide to nearest `|Chladni|<0.12`), `HeightAware` raycast (`Visibility 50000->-50000`).
- **Offline generator:** `Tools/PCG/build_faraway_lod_destruction_ecosystem.py` (SEED=20260829 deterministic, outputs manifest + placements with `destruction_t` per point).
- **HLOD:** `HLOD_FarawayMother_Instanced` + `HLOD_FarawayMother_Merged` keep bounds; LOD3 ISM swaps to impostor billboard + crumble mask. No new Landscape — Nanite terrain `SM_FarawayMother_FabricRidge` stays.

---

## 5. Houdini / VDM

- VDM already bakes fabric drape (`vdm_fabric_baker.py`: grid 200×200 → VEX fold → Labs Maps Baker → 32f EXR RGB=XYZ A=mask). Destruction adds `DestructionMask` bake (vertex color R) in same COP pass.
- WPO fade `1.0→0.75→0.3→0.0` baked to per-LOD material scalar; no new landscape HDA needed. Optional `HDM_LodDestructionMask` subnetwork if chaining.
- Cymatic `Z(u,v)=cos(nπu)cos(mπv)-cos(mπu)cos(nπv)` feeds `foldFreq = base + Bass*2.0` — Bass lifts pleat depth, BeatPulse ticks iridescence.

---

## 6. Material contract (no new masters)

Reuse: `M_Master_FarawayMother_Fabric` / `M_Universal_Enhanced_Fabric` / `M_Master_Nikki_Landscape` / `M_Master_Toon_Universal`. Add functions `MF_LODDitheredDestruction`, `MF_FabricMountainWPO`, `MF_ToksvigAntiAlias`. The 6 P2 MIs + 39 Copernicus MIs expose `DestructionAmount` scalar (default 0).

---

## 7. Weave with horizon eater

`HorizonEatAmount` is Faraway destruction envelope at horizon distance. Close mountains die from local `Tension` (dread); horizon mountains die from `HorizonEat` (eater eating the Mother). At full eater (1.0), only SeamWay Heart Gate remains — the seam that outlives the mountain, just as Klein Veil was the non-orientable seam that outlived fabric.

---

## 8. How to run

```bat
:: offline (no editor)
.venv\Scripts\python.exe Tools/PCG/build_faraway_lod_destruction_ecosystem.py --seed 20260829 --out specs/faraway_lod_destruction/faraway_lod_destruction_placements.v1.json
:: in-editor (closed -> headless MPC, then open)
UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="Content/Python/add_horizon_eater_mpc_params.py"
python Tools/ue_run_python.py --file Content/Python/faraway_lod_destruction_build.py
```

---

## 9. Evidence

Offline: `Saved/Audit/faraway_lod_destruction/` hashed manifest + placement JSONs.  
In-engine: 4 HDR captures (LOD0 crevice vs LOD3 flat vs dither band, Tension 0/0.5/1.0 + Wayfold).  
Ledger: `faraway_lod_destruction` row.
