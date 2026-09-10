# Receipt — Nikki landscape — 2026-09-09

**Status:** DOC-FINAL for authority + wiring map; **editor re-validate still open** (fresh `validate_material` tonight).  
**Batch:** 1 of 3 — `materials/nikki-landscape-2026-09-09`  
**Index:** [Docs/Materials/README.md](README.md)

## Authority (corrected 2026-09-09)

| Role | Path |
|------|------|
| **ACTIVE landscape authority** | `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` |
| Legacy Living Storybook | `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend` (retire after remaining MI reparents) |
| Scratch ignore | `/Game/EnvSandbox/Materials/_Scratch/M_Master_Nikki_Landscape` |

**Source of truth for the authority flip:** `Saved/Audit/landscape_authority_convergence_2026-09-03.json`  
Decision: Nikki landscape is the new owner authority; HeightBlend retires after reparent.

## What already landed (verified in that session report)

- **MPC_Cymatics_Driver** populated (`/Game/Melodia/Cymatics/MPC_Cymatics_Driver`) — silent empty collection eliminated for garment/landscape consumers.
- **Master graft** on Nikki landscape: +25 params / +85 expressions (Snow/Water/Mud/Path, Gaea masks, `CymaticsLandscapeAmount`, etc.), zero-delta defaults (`CymaticsLandscapeAmount=0`, extended layers gated).
- **MI reparent:** 19/37 core landscape/Gaea MIs → Nikki authority (incl. `MI_Glacier_Landscape_Layered`). Remaining showcase/test MIs deferred.
- Graph snapshot: `Saved/Audit/nikki_landscape_graph_2026-09-06.json`.

## Cymatics / Chladni on this master

| Param / path | Role |
|--------------|------|
| `CymaticsLandscapeAmount` | Landscape emissive/reactivity tap; **default 0** (off) |
| `MPC_Cymatics_Driver` | Collection driver from `UMelodiaCymaticsWriterSubsystem` |

Not a Chladni fleece master — body fleece cymatics live on `M_Chorus_Wool_Master` (sheep batch, separate).

## Do not run against active Nikki master

- `rebuild_landscape_safe_fallback.py`
- Force `setup_landscape_height_blend.py` (clears/rebuilds HeightBlend graph)
- Broad delete of work-candidate packages while validating Zen Forest / Sea Above

## Still open before merge stamp FINAL+SHIPPED

- [ ] Fresh editor `validate_material` on `M_Master_Nikki_Landscape` — hard errors: ___
- [ ] List remaining MIs still parented to HeightBlend (finish or explicitly defer with owner names)
- [ ] Confirm Sea Above / Glacier instances read Nikki parent in PIE
- [ ] Owner Ctrl+S if any Monolith graph touch tonight
- [ ] PR from clean `materials/nikki-landscape-2026-09-09` off **main** (docs-first OK; uassets only if touched)

## PR / merge

- Branch: `materials/nikki-landscape-2026-09-09`
- PR: _pending_
- main SHA: _pending_
- Files expected (docs-first): `Docs/Materials/README.md`, this receipt, optionally pointer update in `Docs/Plans/MATERIALS_NIKKI_OCEAN_SDF_FINALIZATION_2026-09-09.md`

## Notes for New Bot

HeightBlend is **legacy**, not the wiring target for cymatics tonight. Prefer Nikki landscape + Oceanology Melodia master + SDF blessed parents.
