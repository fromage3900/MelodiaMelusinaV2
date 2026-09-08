# Choral Sheep — UE Direct Work Plan (2026-09-08)

**Replaces:** execution order in `CHORAL_SHEEP_INTEGRATION_RUNBOOK.md` + 08-25/26/28 docs (all retained as rationale).
**Recorded decisions:** Wool Lab = **A (ship flat)** per lab recommendation (sat 0.38, Worley/fibers deferred) · reframe: `choralsheepbase_*` PNGs are legacy single-texture exports; **12 PC coat albedos are the real color system** (`Saved/Audit/choral_sheep/houdini_variants/`).
**Editor state:** NOT running (port 9316 down) → Phase 1 is owner-less, Phase 2 waits for a clean reservation.

## Phase 1 — offline (do today, no editor)
| # | Task | Where | Status (2026-09-08 13:1x) |
|---|---|---|---|
| 1.1 | Stage sculpted normal 4K→2048 `T_ChoralSheep_Normal.png` | inbox + manifest | **DONE** — `ingest_sheep_normals.py --verify` clean ("2048x2048 RGB POT ok"), manifest written, awaits editor apply (2.2) |
| 1.2 | Weight-paint truth check | headless probe | **DONE — BLOCKER IS STALE.** Retopo mesh: 106 vgroups exactly == 106 deform bones (set-identical), 550/550 verts weighted. Variants.json status string and retarget-doc caveat need updating at next doc pass |
| 1.3 | Hue-wheel re-key → `houdini_variants_v2/` | PIL, reversible | **DONE, review PASSED** — even +30°/semitone from rose C, sat uniform 0.302, beige outlier + periwinkle clump both resolved; "player can name sheep by note." Awaiting owner pick to promote v2 over v1 |
| 1.4 | Groom real-strand cook | hython, heavy | DEFERRED ticket (placeholders policy-safe; contact sheet correct ordering) |
| 1.5 | Fur master spec | this section | **DONE (spec)** — master `M_Chorus_Wool_Master` to be created in reservation: params `CoatHueShift, CoatSaturation, TrimEmissive, BellToneScale, WoolClumpScale(0.65), SheenResponse(0.45)`; texture inputs BaseColor(PC 2K), Normal(T_ChoralSheep_Normal 2K, TC_NormalMap), Roughness(flat 0.3→scalar), Emissive(PC glow lane, off default); TWO-SIDED off, no translucency; never parent from water/landscape masters (confirmed: Masters dir has none fur-shaped) |

**Offline remainder:** promote-v2 decision (owner eyes) · doc-status refresh (1.2 findings).
**Next editor actions = Phase 2 rows 2.1→2.6 in order; 2.2 apply script exists and reads the manifest now on disk.**

## Phase 2 — editor reservation (one editor, RenderTests map only)
| # | Task | Command path |
|---|---|---|
| 2.1 | Import/reimport FBX → `/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep`; verify deform-bone count 106, no c_* control bones | editor Python import settings |
| 2.2 | `apply_choral_sheep_normals.py` — wire Normal to all 12 MIs | exec per inbox README |
| 2.3 | Create fur master + reparent `MI_ChoralSheep_Coat_PC*` (12); scalars `CoatHueShift/CoatSaturation/TrimEmissive/BellToneScale`; reimport policy master-edit-only | master per 1.5 spec |
| 2.4 | `DA_ChoralSheepDefinition` from `UMelodiaCompanionDefinitionAsset` per contract (180/75 cm, Graze/Harmonize/Guide) | runbook step 3 |
| 2.5 | `BP_ChoralSheep` from `AMelodiaChoralSheepActor`, definition-only reference | runbook step 4 |
| 2.6 | Prototype smoke in `L_ChoralSheep_Prototype` (RenderTests only): follow, graze pulse, harmonize emissive | PIE evidence + ledger row if gate-claimed |

## Phase 3 — polish queue (after 2.6 green)
- 3.1 emission lane authoring (nodal wool glow on Harmonize, MPC read-only) · 3.2 Worley12 hero-LOD hybrid revisit · 3.3 KawaiiPhysics ears/tail/bell · 3.4 groom real cook if hero shots need it

## Hard rules
Never touch protected maps for the prototype (RenderTests only) · groom stays optional · no master reuse · 1 SK serves all 12 variants (material-slot only) · gate claims need ledger rows, prose is not a row.
