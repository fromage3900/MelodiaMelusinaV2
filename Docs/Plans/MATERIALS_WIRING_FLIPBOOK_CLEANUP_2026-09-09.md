# Materials wiring + flipbook cleanup — 2026-09-09

**Status:** PLAN (post ALL_MATERIALS gate)  
**Pair:** Melodia study bot + New Bot  
**Index:** [Docs/Materials/README.md](../Materials/README.md) · **Labels:** [LABEL_MAP_2026-09-09.md](../Materials/LABEL_MAP_2026-09-09.md)  
**Prior gate:** [RECEIPT_ALL_MATERIALS_MERGED_2026-09-09.md](../Materials/RECEIPT_ALL_MATERIALS_MERGED_2026-09-09.md) (`#156` → `b0441cbb`) — soft-freeze **COMPLETE**; this plan is the follow-on.

## Why now

UE closed after Monolith AVs. Owner asked for a step-back: finalize project-wide material wiring, label/clean flipbook work, and deprecate engine materials / stubs for an absolute clean working environment.

## Retrospective (brief)

### What worked
- Materials index + three lane receipts + ALL gate on main (`#151` / `#152` / `#156`).
- Isolated docs PRs off **main** (not mixed with sheep / LiveLink).
- Validate/read-back without recompile once Monolith recompile proved toxic.
- Wool Chladni knobs mostly survived on disk.
- SDF Enhanced correctly quarantined instead of shipping.
- Restart unlock did its job without pretending caveats were gone.

### What went wrong
1. Monolith `recompile_material` → AV in `FMonolithMaterialActions::RecompileMaterial`.
2. Monolith `save_packages` → AV in `HandleSavePackages` on `M_Water_Oceanology_Melodia`. Agent called save after knowing it was toxic.
3. ALL_MATERIALS was **DOC-FINAL**, not ship: Nikki validate open, ocean graph edits possibly unsaved, Hero MI parents plugin, Universal Cymatic incomplete, HeightBlend MI reparents unfinished.
4. Crash wiped live Universal Cymatic bus (re-wired; wool ModeN/M still 0).
5. Dirty worktree mixed sheep + materials + uproject LiveLink — PR contamination risk.
6. Do not invent UI excuses for a loading editor.

## Hard rules (non-negotiable)

- Agents **never** call Monolith `save_packages` or `recompile_material`.
- Owner **Ctrl+S** only for intentional package saves.
- Agents: `validate_material` / graph read-back / parameter set only.
- One concern per PR off **main**. Sheep Root-C, Rokoko/LiveLink `.uproject`, and materials stay separate.

## Label taxonomy

Every master gets exactly one: **SHIP** · **LEGACY** · **QUARANTINE** · **SCRATCH** · **DUPLICATE**. See [LABEL_MAP_2026-09-09.md](../Materials/LABEL_MAP_2026-09-09.md).

Retirement process: **label → redirect consumers → archive → delete** (dedicated PR; never cold-delete).

---

## Phase A — Batch 4 wiring closeout

| Item | Action |
|------|--------|
| Nikki `M_Master_Nikki_Landscape` | Fresh `validate_material`; list remaining HeightBlend-parented MIs |
| Ocean `M_Water_Oceanology_Melodia` | Owner Ctrl+S if Toon_Weight / OrnamentLayer dirty; keep Hero MI parent quirk documented (plugin `M_Oceanology_Inst` vs Melodia master) |
| Universal `M_Master_Toon_Universal` | Finish `Cymatic_*` bus; wool ModeN/M only if intentional |
| SDF `M_SDF_OrnamentLayer_Enhanced` | Stay **QUARANTINE** until UtilityToolkit MF restored |

**Done when:** `Docs/Materials/RECEIPT_WIRING_BATCH4_*.md` + zero hard errors on SHIP authorities.

## Phase B — Flipbook as Lane D

Canonical refs: [FLIPBOOK_STATUS_2026-09-02.md](../FLIPBOOK_STATUS_2026-09-02.md), [MF_FlipbookScrub.v1.json](../../specs/materials/MF_FlipbookScrub.v1.json) (`awaiting-editor-batch`).

| Lane | Truth | Needed work |
|------|-------|-------------|
| PearlWoven / SurrealBrick | Frames + many uassets | Label SHIP; optional PearlWoven 4×4 atlas for perf |
| Brass atlas | `T_Brass_Flipbook_30_Atlas_4x4` is **16 cells** | Rename → `_16_`; wire via MF |
| SurrealFabric (CelestialSilk / CymaticPulse / BrassPatina) | ~462 png + ~462 uasset on disk | Still **no** `M_SurrealFabric_Flipbook` master — build/wire BeatPulse time from `MPC_Cymatics_Driver` |
| `MF_FlipbookScrub` | Spec only | Editor-create once (new MF only; never graph-clear existing) |
| Niagara flipbook | **DUPLICATE** `Content/_PROJECT/...` vs `Content/Melodia/_PROJECT/...` | Melodia path = authority; redirect refs; archive the other |
| Alpha atlases | `Alphas_Sparkles` + Melodia VFX copies | Label; one import root |

Textures PASS ≠ materials wired. **Done when:** `Docs/Materials/RECEIPT_FLIPBOOK_*.md` + Lane D live in Materials README.

## Phase C — Deprecate for clean env

**LEGACY** (after consumers reparent): HeightBlend masters + Inst; older landscape blends; water Grand v7/v9/v10 + `MI_Water_v10_HeroFLIP` when Melodia Oceanology is sole SHIP ocean; NikkiChain repair stacks once Universal is one authority.

**QUARANTINE:** Enhanced SDF; `_Scratch` / `_Archive` / `00_Archive` / `_Quarantine*` / VFX `Quarantine_*`; Cosmo `*_PRE_EXPANSION_*`.

**DUPLICATE:** `Content/_PROJECT/VFX` MelodiaFlipbook set → archive after Melodia/_PROJECT is sole authority.

**Engine materials:** Offline audit for actors/MIs still on `/Engine/EngineMaterials/WorldGridMaterial` (and friends); reparent to Melodia SHIP/stub — no engine defaults on Melodia showcase levels.

**Clean-env gate:** `Docs/Materials/RECEIPT_MATERIALS_CLEAN_ENV_*.md` when every master under `EnvSandbox/Materials/Masters` has a label, no SHIP hard-errors, no engine defaults on Melodia levels, duplicates archived, Enhanced quarantined or fixed.

## Lane ownership (proposed)

| Who | Owns |
|-----|------|
| **Melodia study bot** | Nikki leftover validate + HeightBlend reparent list |
| **New Bot** | Batch 4 Universal Cymatic + flipbook Lane D + deprecate / label map |

## Out of scope

- Shorewake PearlWoven Phase 1–4 art track
- Rokoko Live Link verify / Meet2 capture
- Sheep Root-C material proof (own branch)

## Findability

1. Open `Docs/Materials/README.md`
2. Follow Lane A–D + LABEL_MAP + this plan
3. Receipts under `Docs/Materials/RECEIPT_*`
