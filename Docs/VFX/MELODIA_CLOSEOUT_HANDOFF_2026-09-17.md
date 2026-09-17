# Melodia closeout handoff — 2026-09-17 (org / QOL / reuse)

Owner: Fromage. Coordinator bot closing editor lane; work packages below are DELEGATED.

Landed in [`Docs/VFX/`](README.md) (existing Fix A / inventory home). Playbooks:

- [`Playbooks/PLAYBOOK_FLIPBOOK_FIXA.md`](Playbooks/PLAYBOOK_FLIPBOOK_FIXA.md)
- [`Playbooks/PLAYBOOK_SURREALFABRIC_FLIPBOOK_MASTER.md`](Playbooks/PLAYBOOK_SURREALFABRIC_FLIPBOOK_MASTER.md)
- [`Playbooks/PLAYBOOK_BEATPULSE_COMPANION_BUS.md`](Playbooks/PLAYBOOK_BEATPULSE_COMPANION_BUS.md)

## Owner (you) — 2 min

1. Ctrl+S: `MI_SurrealFabric_CelestialSilk`, `CymaticPulse`, `BrassPatina`, `MF_FlipbookScrub`
2. Optional PIE: `BP_ChoralSheep` BeatPulse + SurrealFabric MI on a plane
3. Decision later: Melusina V2Test 33 None SM slots → stub vs quarantine (study-bot will prepare matrix)

## Package A — Materials org (Study Melodia bot)

- Twin cleanup: Content vs Melodia/_PROJECT Static_Glint + Flipbook masters → one SHIP, other DUPLICATE→redirect
- Phase C stamp only (no polish): HeightBlend Toon LEGACY, SDF Enhanced QUARANTINE, EnvSandbox `MI_Orphan_*` + DemoRoom `*_BS` SCRATCH
- SurrealFabric Normal/ORM: inventory per-frame vs compact atlas gaps; write wire plan sharing FlipbookUV (do NOT invent atlases in editor without frames)
- Remaining Melodia* fabric folders: MI scaffold plan on `M_SurrealFabric_Flipbook` (template = CelestialSilk)

Hard rules: no Monolith `save_packages` / `recompile_material`; owner Ctrl+S only.

## Package B — Niagara AAA (Study Melodia bot)

Playbook-first, then live only if Monolith up on fromage:

1. BeatBurst — soft fleece collision, BeatPulse size/emissive curves, ≤2 secondary emitters
2. HybridSparkles — near/far LOD, spawnRate×ResonanceIntensity, slight orbit
3. PetalCascade → LeafPile-style settle (shared BeatPulse wind)

Defer: MotionTrails, FluidSplash. Quarantine Stub/TEMP/Test NS. Never reintroduce Niagara SubUV when material owns scrub (Fix A).

## Package C — Docs / reuse (this PR)

Done in #228:

- this file
- the three playbooks under `Docs/VFX/Playbooks/`
- `CURRENT_STATE.md` pointers; docs-only

## SSOT assets (live)

| Asset | Path | Status |
|---|---|---|
| `M_SurrealFabric_Flipbook` | `/Game/Melodia/Materials/Masters/` | on disk — Lane D live 2026-09-17 |
| `MF_FlipbookScrub` | `/Game/EnvSandbox/VFX/Materials/Functions/` | dirty until Ctrl+S |
| Lookdev MIs ×3 | `/Game/Melodia/Materials/Lookdev/` | dirty until Ctrl+S |
| `BP_ChoralSheep` BeatPulse | `/Game/Melodia/Companions/ChoralSheep/` | saved |
| Fix A LeafPile | `NS_Melodia_LeafPileLoop` | SubUV off, 2×2 kept |
| PR #228 | Docs/VFX inventory + Fix A | draft, CLEAN_FIXA, **RISK_DOUBLE=0** |

## Do not reopen

Universal Cymatic bus, oceanology, FluidSplash polish, new sticker MFs.
