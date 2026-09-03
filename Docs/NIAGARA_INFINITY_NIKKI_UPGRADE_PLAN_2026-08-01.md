# Niagara Systems — Infinity Nikki Production-Grade Upgrade Plan

**Status: plan, not yet executed. Read-only audit complete (2026-08-01). No Niagara assets modified
by the audit itself.**

## Why this exists

A deep audit of all 76 Niagara systems in the project (28 project-authored under
`/Game/EnvSandbox/VFX/Systems/`) found that most are not distinct, authored effects — they're a
small number of template emitters copy-pasted and renamed. Specifically:

- **4 systems are empty stock shells**: `NS_Uni_Fireflies`, `NS_Uni_LeafDrift`, `NS_Uni_DustShafts`,
  `NS_Uni_PollenSparkle` — emitter literally named `"Fountain"` or `"Minimal"`, 0 modules, 0
  renderers. They compile and activate without error; they render nothing.
- **5 systems share one basic sprite-mote emitter** (same emitter GUID): `NS_EmberMotes`,
  `NS_FairyDust`, `NS_Uni_MistSheet`, `NS_Uni_WaterMist`, `NS_Uni_GroundWisps`.
- **3 systems share one mesh-petal emitter**: `NS_CosmicPetalOrbit`, `NS_SakuraGroundPetals`,
  `NS_SakuraWaterPetals`.
- **3 systems share one 3-emitter ribbon-burst template**, and in every instance the burst
  sub-emitter is disconnected from its own event chain: `NS_MagicalHenshinBurst`,
  `NS_Uni_RainRipples`, `NS_SakuraPetalGust`.
- **2 systems share one 2-emitter ribbon-gust template**: `NS_SakuraCosmicAurora`,
  `NS_WindRibbonGust`.
- Nearly everything is CPU-sim, sprite-dominant, with no LOD/distance culling.
- **One system, `NS_SakuraPetals_v2`, is genuinely well-built**: 3 emitters, 2 renderer types
  (sprite + mesh), real event-driven inter-emitter linkage (`DeathEvent` triggers a pond-ripple and
  petal-pile spawn). This is the reference pattern for everything else.

**Immediate live bug**: the night's render-polish pass (Decision 039) placed `NS_Uni_DustShafts`,
`NS_Uni_PollenSparkle`, and `NS_Uni_Fireflies` into `L_MelusinaMorning` and `ZenForestTest`. All
three are empty shells — those placements currently render nothing. Fixing this is P0 in this plan,
ahead of everything else, since it directly undoes work already reported as done.

## Reference standard: what "Infinity Nikki grade" means here

Not a new aesthetic — the existing `NS_SakuraPetals_v2` already demonstrates it:
1. **GPU sim by default** unless there's a specific reason for CPU (low count, needs game-thread
   collision query results, etc.) — most ambient/atmospheric effects here have no such reason.
2. **Renderer matches the name.** A "burst" gets sprites; a "trail" gets a ribbon; petals/leaves/
   debris that need volume and lighting response get mesh renderers, not flat sprites.
3. **Event-driven layering where the effect implies cause-and-effect** (petal lands → ripple; burst
   fires → trail follows) — not independent emitters coincidentally sharing a system asset.
4. **Fixed bounds + sane warmup** — several audited systems have 20-25s warmup times that read as
   copy-paste residue, not a deliberate choice.
5. **One emitter template per distinct visual idea.** Right now ~10 templates masquerade as 28
   systems; consolidating is not optional cleanup, it's the actual fix — renaming a clone doesn't
   make it a new effect.

## Priority order

### P0 — Fix the live bug (do first, before anything else)
Author real content for the 4 empty-shell systems, or swap the 3 currently-placed ones for a
working system as an interim fix while the real one is authored:
- `NS_Uni_DustShafts` (placed in `L_MelusinaMorning`) — needs an actual volumetric/plane-aligned
  light-shaft approach, not a sprite mote.
- `NS_Uni_PollenSparkle` (placed in `L_MelusinaMorning`) — sprite is fine for this one; just needs
  real modules (spawn rate, drift velocity, size-over-life, color).
- `NS_Uni_Fireflies` (placed in `ZenForestTest`) — sprite + light-flicker component; fireflies are a
  classic Niagara light-renderer use case, currently has neither.
- `NS_Uni_LeafDrift` — not yet placed anywhere but equally empty; author before it gets used.

### P1 — De-duplicate the copy-paste clusters
For each cluster below, decide: keep one canonical emitter and retarget the "duplicate" systems to
it via distinct system-level parameters (color/intensity/rate), OR actually author each as a
distinct effect if the names imply meaningfully different visuals. Don't leave clones renamed and
call it done — that's how this happened the first time.
- EmberMotes/FairyDust/MistSheet/WaterMist/GroundWisps (5→1 base, differentiate by system params)
- CosmicPetalOrbit/SakuraGroundPetals/SakuraWaterPetals (3→1 base + context-specific params)
- MagicalHenshinBurst/RainRipples/PetalGust (3 systems on 1 template — these three should almost
  certainly NOT share a template; a magical burst, rain ripples, and a petal gust are visually
  distinct ideas that got flattened into one graph). Fix the disconnected `OmnidirectionalBurst`
  event-chain gap while re-authoring.
- SakuraCosmicAurora/WindRibbonGust (2→1 base or genuinely differentiate)
- Retire `NS_SakuraPetals` (v1) once `_v2` is confirmed as the full replacement — don't run both.

### P2 — GPU migration + renderer correctness
Move ambient/atmospheric systems (motes, dust, sparkle, ground wisps) to GPU sim once they're
actually authored — no reason for CPU on these. Add ribbon renderers to `NS_MagicTrail` (currently
sprite-only despite the name). Consider mesh renderers for the SDF foliage trio
(`NS_SDF_Foliage_Bush/Vine/Grass`) if they're meant to read as dimensional foliage cards rather than
flat sprites.

### P3 — Third-party duplicate-index cleanup (low priority, not a quality issue)
46 UltraDynamicSky systems are indexed twice (`/Game/_ThirdParty/UltraDynamicSky/Particles/` and
`/Game/UltraDynamicSky/Particles/`, identical names). Likely an asset-registry artifact from a past
content migration (same shape as prior `.git`/LFS migration issues), not necessarily two real copies
on disk. Confirm which path is canonical before touching anything — cheap to check, not urgent.

## Sequencing with today's other work

- P0 blocks nothing else and should happen before any more level set-dressing — don't place more
  effects while 4 of the library's systems are confirmed empty.
- P1/P2 is real Niagara authoring work — reasonable to hand to whichever lane is doing VFX today
  (per Kiro's message, that's environment/art lane: you + Claude, not Kiro).
- P3 is a Monolith `project_query` check, five minutes, do whenever.

## Verification
- Per system: after re-authoring, confirm `module_count > 0` and `renderer_count > 0` via Monolith's
  `niagara_query` (not just "compiles without error" — the empty shells compiled fine, that's how
  they went unnoticed this long).
- Re-open `L_MelusinaMorning` and `ZenForestTest` in-editor after P0 and visually confirm the 3
  placed effects are now actually visible before considering the render-polish pass complete.
- No gameplay/Blueprint/C++ verification needed — this is content-only, matches the render-polish
  plan's own verification scope.

## P0-UI — Cosmic Orrery and interface feedback scope (added 2026-08-01)

This is a separate presentation lane from environmental set dressing and must not reuse known empty shells merely because their names sound appropriate.

### Canonical UI systems to author
1. `NS_UI_MelodiaClickSparkle`: short pooled 4pt/8pt burst using existing Melodia star textures; screen-space/UI-renderer compatible where practical.
2. `NS_UI_MelodiaOrreryOrbit`: restrained orbit around the currently selected Orrery destination.
3. `NS_UI_MelodiaCosmicDust`: low-density ambient field for the native main-menu scene.
4. `NS_UI_MelodiaShootingTrail`: infrequent one-shot trail matching the website hero reference.

### Rules
- Do not derive these from `NS_Uni_PollenSparkle`, `NS_Uni_DustShafts`, or `NS_Uni_Fireflies` until those empty shells are genuinely re-authored and verified.
- `NS_SakuraPetals_v2` is the structural quality reference for layered/event-driven effects, not an art-source dependency.
- UI FX are presentation-only and react to semantic feedback events or Orrery selection state.
- Full/Soft/Chrome/Off and reduced-motion settings scale spawn count, lifetime, camera motion, and ambient loops; Off still permits essential static focus indication.
- Fixed bounds, deterministic seed where useful, and explicit renderer/module-count verification are required.

### Native Orrery mapping from website motion
- Galaxy rotation → slow 3D ring rotation/material pan.
- Nebula drift → low-frequency material or GPU sprite field.
- Cosmic dust → low-density GPU sprites.
- Shooting stars → infrequent ribbon/sprite trail events.
- Constellation navigation → CommonUI focus plus material-line illumination.
- Selection orbit → `NS_UI_MelodiaOrreryOrbit` around the selected registry node.

No Niagara system may perform menu actions, travel, save, Quill advancement, or gameplay mutation.

## P0-UI — Cosmic Orrery and interface feedback scope (added 2026-08-01)

This is a separate presentation lane from environmental set dressing and must not reuse known empty shells merely because their names sound appropriate.

### Canonical UI systems to author
1. `NS_UI_MelodiaClickSparkle`: short pooled 4pt/8pt burst using existing Melodia star textures; screen-space/UI-renderer compatible where practical.
2. `NS_UI_MelodiaOrreryOrbit`: restrained orbit around the currently selected Orrery destination.
3. `NS_UI_MelodiaCosmicDust`: low-density ambient field for the native main-menu scene.
4. `NS_UI_MelodiaShootingTrail`: infrequent one-shot trail matching the website hero reference.

### Rules
- Do not derive these from `NS_Uni_PollenSparkle`, `NS_Uni_DustShafts`, or `NS_Uni_Fireflies` until those empty shells are genuinely re-authored and verified.
- `NS_SakuraPetals_v2` is the structural quality reference, not an art-source dependency.
- UI FX are presentation-only and react to semantic feedback events or Orrery selection state.
- Full/Soft/Chrome/Off and reduced-motion settings scale spawn count, lifetime, camera motion, and ambient loops; Off still permits essential static focus indication.
- Fixed bounds, deterministic seed where useful, and explicit renderer/module-count verification are required.

### Native Orrery mapping from website motion
- Galaxy rotation → slow 3D ring rotation/material pan.
- Nebula drift → low-frequency material or GPU sprite field.
- Cosmic dust → low-density GPU sprites.
- Shooting stars → infrequent ribbon/sprite trail events.
- Constellation navigation → CommonUI focus plus material-line illumination.
- Selection orbit → `NS_UI_MelodiaOrreryOrbit` around the selected registry node.

No Niagara system may perform menu actions, travel, save, Quill advancement, or gameplay mutation.
