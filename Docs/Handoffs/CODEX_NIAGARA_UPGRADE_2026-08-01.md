# Handoff: Niagara Systems Upgrade — for Codex

**Read `_AGENT_WORKING_AGREEMENT.md` first. It is binding.** Do the job asked, ship it, stop. Never
add a mechanism that compensates for a problem — fix the cause. A fix request is not a review
request. If genuinely blocked, say so in a sentence and stop rather than guessing.

**STATUS UPDATE 2026-08-01, late — P0 independently verified done.** All 4 previously-empty systems
now have real content, confirmed via `niagara_query get_system_summary`: `NS_Uni_DustShafts` (2
emitters, `ShaftPlanes`+`DustMotes`, GPU, sprite renderers, 16 modules), `NS_Uni_PollenSparkle` (1
emitter, GPU, sprite, 10 modules), `NS_Uni_Fireflies` (1 emitter, sprite **+ light renderer** —
correct flicker approach), `NS_Uni_LeafDrift` (1 emitter, GPU, mesh renderer, 13 modules). Good work.
**P1 (de-duplicate the copy-paste clusters) and P2 (GPU migration/renderer correctness) not
independently verified this session** — status unknown, check in directly. No progress logged to
`_TASK_QUEUE.md`/`_DECISION_LOG.md` from your side yet as of this update — if P0 report writing is
still pending, that's the one process item outstanding (see "Before you call anything done" below,
still applies).

One thing you should know about even though it's not your lane: the PPV that places some of your
systems in-level (`PPV_NikkiDream`, via `M_PP_StorybookOutline`) had a real depth-edge-detection bug
today that caused broad black regions on-screen — now fixed. Unrelated to Niagara, but if you're
looking at a level and something still looks visually wrong, check
`Docs/Handoffs/PPV_STORYBOOK_OUTLINE_INTEGRATION_2026-08-01.md` first before assuming it's a VFX
issue — there's a known, undiagnosed "outline cuts off" bug still open there as of this handoff.

## Context

A deep audit (2026-08-01, read-only, full findings in
`Docs/NIAGARA_INFINITY_NIKKI_UPGRADE_PLAN_2026-08-01.md`) found that of the 28 Niagara systems under
`/Game/EnvSandbox/VFX/Systems/{Ambient,Magical,Universal,Sakura}/`, there are really only ~9-10
distinct emitter graphs — the rest are the same handful of templates copy-pasted and renamed. Four
systems are completely empty stock shells (0 modules, 0 renderers) that compile and activate without
error but render nothing. This is your lane exclusively — environment/art (maps, materials, PCG, VFX
placement, lighting) is Claude's lane today; you own the Niagara graphs themselves, not where they're
placed in levels.

**Reference standard**: `NS_SakuraPetals_v2` is the one system already built to the bar every other
system should hit — 3 emitters, 2 renderer types (sprite + mesh), real event-driven linkage
(`DeathEvent` triggers a pond-ripple + petal-pile spawn on death). Use it as your pattern, not a
theoretical ideal.

## Your lane — three priorities, in order

### P0 — Fix the live bug first (blocks a render-polish pass already in progress)

These 3 systems are placed in levels right now and are confirmed empty (emitter named `"Fountain"`
or `"Minimal"`, 0 modules, 0 renderers):

1. **`NS_Uni_DustShafts`** — placed in `L_MelusinaMorning` at the threshold pillars (actor label
   `FX_Morning_DustShafts_Threshold`). Needs a real volumetric/plane-aligned light-shaft approach —
   sprite motes alone won't read as light shafts.
2. **`NS_Uni_PollenSparkle`** — placed in `L_MelusinaMorning` over the bed (actor label
   `FX_Morning_Bed_PollenSparkle`). Sprite renderer is fine here; it just needs real modules (spawn
   rate, drift velocity, size-over-life, color-over-life).
3. **`NS_Uni_Fireflies`** — placed in `ZenForestTest` near the tea house (actor label
   `FX_Zen_TeaHouse_Fireflies`). Classic Niagara light-renderer use case (sprite + flickering point
   light per particle) — currently has neither.

Also author **`NS_Uni_LeafDrift`** (same empty-shell state, not yet placed anywhere, but will be used
soon — get it real before it's placed).

**Don't touch the level placements themselves** (actor transforms, which system is assigned to which
actor) — that's already correct, only the system assets are broken.

### P1 — De-duplicate the copy-paste clusters

For each cluster, either (a) keep one canonical emitter and differentiate the "duplicate" systems via
system-level parameters only, or (b) actually author each as a genuinely distinct effect if the name
implies a meaningfully different visual. Don't leave renamed clones and call it done.

- **Mote cluster** (same emitter GUID `FA602D88…`): `NS_EmberMotes`, `NS_FairyDust`,
  `NS_Uni_MistSheet`, `NS_Uni_WaterMist`, `NS_Uni_GroundWisps` — 5 systems, 1 real emitter.
- **Petal-mesh cluster** (same emitter GUID `5C1E89DE…`): `NS_CosmicPetalOrbit`,
  `NS_SakuraGroundPetals`, `NS_SakuraWaterPetals` — 3 systems, 1 real emitter.
- **Ribbon-burst cluster** (same 3-emitter GUID triplet `E1BA0F89…`/`01CF5F43…`/`780C20B9…`):
  `NS_MagicalHenshinBurst`, `NS_Uni_RainRipples`, `NS_SakuraPetalGust` — these three should almost
  certainly NOT share a template (a magical burst, rain ripples, and a petal gust are visually
  distinct). In every instance the `OmnidirectionalBurst` sub-emitter is disconnected from its own
  event chain — fix that as part of re-authoring, don't just retarget it.
- **Ribbon-gust cluster** (same 2-emitter GUID pair `07AFEF16…`/`D2740D71…`): `NS_SakuraCosmicAurora`,
  `NS_WindRibbonGust`.
- **Retire `NS_SakuraPetals` (v1)** once you've confirmed `_v2` is the full replacement (it was last
  modified 2026-07-27 vs 2026-07-15 for v1 — looks like the intended successor). Quarantine, don't
  delete, per this project's standing convention — move to a dated `_Quarantine*` folder with a
  README, same pattern as prior quarantines in this repo if you want a reference example.

### P2 — GPU migration + renderer correctness (after P0/P1)

- Move ambient/atmospheric systems to GPU sim once actually authored — no reason for CPU on
  motes/dust/sparkle/wisps.
- Add a ribbon renderer to `NS_MagicTrail` (currently sprite-only despite the name; sim target is
  already correctly GPU, just missing the ribbon).
- Consider mesh renderers for `NS_SDF_Foliage_Bush/Vine/Grass` (currently all sprite-only) if they're
  meant to read as dimensional foliage cards rather than flat sprites — your call on whether that's
  worth the cost for this use case.

## Not yours

- Where effects get placed in levels, level dressing, lighting, materials, PCG, camera work — that's
  Claude's lane today (environment/art), per the owner's explicit split.
- The hair component — stay out of it entirely, per standing instruction.
- P3 from the full audit doc (the doubled UltraDynamicSky asset-index entries) — low priority,
  informational only, not assigned to you.

## Before you call anything done

1. Per system: confirm `module_count > 0` and `renderer_count > 0` via Monolith's `niagara_query` —
   not just "compiles without error." The empty shells compiled fine; that's exactly how they went
   unnoticed. Check the actual module/renderer counts.
2. One line per system in your report: what changed, before/after module+renderer counts. Not a
   design document.
3. If you retire `NS_SakuraPetals` v1, confirm zero remaining referencers first (Monolith
   `project_query find_references`) before quarantining — same discipline as every other retirement
   in this project.

Full technical detail on every system (sim target, renderer types, module counts, exact GUID matches)
is in `Docs/NIAGARA_INFINITY_NIKKI_UPGRADE_PLAN_2026-08-01.md` — read that before starting, this
handoff is the summary, not the full audit.
