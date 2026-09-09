# Choral Sheep — UE Direct Work Plan (2026-09-08)

**Replaces:** execution order in `CHORAL_SHEEP_INTEGRATION_RUNBOOK.md` + 08-25/26/28 docs (all retained as rationale).
**Recorded decisions:** Wool Lab = **A (ship flat)** per lab recommendation (sat 0.38, Worley/fibers deferred) · reframe: `choralsheepbase_*` PNGs are legacy single-texture exports; **12 PC coat albedos are the real color system** (`Saved/Audit/choral_sheep/houdini_variants/`). **Owner material lock (2026-09-09): final Sheep lookdev MUST use the approved Nikki-derived character material path + existing cymatics/Chladni consumer; the older standalone wool-master proposal is superseded.**
**Editor state:** NOT running (port 9316 down) → Phase 1 is owner-less, Phase 2 waits for a clean reservation.

## Phase 1 — offline (do today, no editor)
| # | Task | Where | Status (2026-09-08 13:1x) |
|---|---|---|---|
| 1.1 | Stage sculpted normal 4K→2048 `T_ChoralSheep_Normal.png` | inbox + manifest | **DONE** — `ingest_sheep_normals.py --verify` clean ("2048x2048 RGB POT ok"), manifest written, awaits editor apply (2.2) |
| 1.2 | Weight-paint truth check | headless probe | **DONE — BLOCKER IS STALE.** Retopo mesh: 106 vgroups exactly == 106 deform bones (set-identical), 550/550 verts weighted. Variants.json status string and retarget-doc caveat need updating at next doc pass |
| 1.3 | Hue-wheel re-key → `houdini_variants_v2/` | PIL, reversible | **DONE, review PASSED** — even +30°/semitone from rose C, sat uniform 0.302, beige outlier + periwinkle clump both resolved; "player can name sheep by note." Awaiting owner pick to promote v2 over v1 |
| 1.4 | Groom real-strand cook | hython, heavy | DEFERRED ticket (placeholders policy-safe; contact sheet correct ordering) |
| 1.5 | Nikki material authority | current Sheep MI + Chladni child | **LOCKED / SUPERSEDES OLD SPEC** — do **not** create `M_Chorus_Wool_Master` as P0 authority. Keep `/Game/Melodia/Companions/ChoralSheep/MI_ChoralSheep_Body` on the approved character-side Nikki lookdev path (current parent: `M_Master_Toon_Character`) and layer cymatics through `/Game/Melodia/Companions/ChoralSheep/Materials/MI_ChoralSheep_Body_Chladni_C`, which inherits the body MI and consumes `T_Chladni_C_ROOT`. PC coat albedos / sculpted normal / roughness remain inputs to this approved material family. |

**Offline remainder:** promote-v2 decision (owner eyes) · doc-status refresh (1.2 findings).
**Next editor actions = Phase 2 rows 2.1→2.6 in order; 2.2 apply script exists and reads the manifest now on disk.**

## Phase 2 — editor reservation (one editor, RenderTests map only)
| # | Task | Command path |
|---|---|---|
| 2.1 | Import/reimport FBX → `/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep`; verify deform-bone count 106, no c_* control bones | editor Python import settings |
| 2.2 | `apply_choral_sheep_normals.py` — wire Normal to all 12 MIs | exec per inbox README |
| 2.3 | Verify / finish the approved **Nikki + cymatics** Sheep material family; preserve `MI_ChoralSheep_Body → M_Master_Toon_Character`; wire / validate `MI_ChoralSheep_Body_Chladni_C` for ROOT_C; keep pitch-class coat identity as material/data variants without replacing the body authority | owner material lock + Chladni consumer contract |
| 2.4 | `DA_ChoralSheepDefinition` from `UMelodiaCompanionDefinitionAsset` per contract (180/75 cm, Graze/Harmonize/Guide) | runbook step 3 |
| 2.5 | `BP_ChoralSheep` from `AMelodiaChoralSheepActor`, definition-only reference | runbook step 4 |
| 2.6 | Prototype smoke in `L_ChoralSheep_Prototype` (RenderTests only): follow, graze pulse, harmonize emissive | PIE evidence + ledger row if gate-claimed |

## Phase 3 — polish queue (after 2.6 green)
- 3.1 emission lane authoring (nodal wool glow on Harmonize, MPC read-only) · 3.2 Worley12 hero-LOD hybrid revisit · 3.3 KawaiiPhysics ears/tail/bell · 3.4 groom real cook if hero shots need it

## Hard rules
Never touch protected maps for the prototype (RenderTests only) · groom stays optional · **Nikki material MUST be used for final Sheep lookdev/proof** · do not create or substitute a standalone wool master · do not reparent to water/landscape/random Nikki masters · 1 SK serves all 12 variants (material/data identity) · gate claims need ledger rows, prose is not a row. See `Docs/Production/P0_RECRUITER_SENDOFF_AND_CHORAL_SHEEP_VISUAL_QUEUE_2026-09-09.md`.
