# Long-Term Gameplay, Blueprint, and T3D Build Plan

**Date:** 2026-08-14  
**Status:** Architecture plan; protect the Core P0 First Dream slice while preparing
for long-term content production  
**North star:** approximately four musical movements / twelve hours, exploration-first,
with Melusina and Sir as the starting tandem and a found-family roster built through
reused systems rather than new authorities.

## Executive recommendation

Melodia does not need every future system immediately. It needs a reliable content
authoring kit:

```text
one authority per domain
  + data-driven definitions
  + thin Blueprint presentation shells
  + native state/transaction components
  + fixture maps and contract tests
  + fail-closed T3D mutation with postconditions
```

The long-term goal is that adding a skill, enemy, portal, traversal capability, or
world challenge means authoring a DataAsset plus a small verified Blueprint child—not
inventing a new subsystem or hand-wiring a new save/travel/battle path.

## Long-term scope to preserve

The existing loose north star is coherent and should remain the content target:

- exploration carries most playtime; QuillScript lives at seams;
- a hub leads through a resonant door into a deterministic expedition and back to a
  changed hub;
- four movements reuse the same loop while changing register, spaces, enemies, and
  reunions;
- Melusina and Sir are the base tandem; the final roster ceiling is six;
- the past duet-partner remains absent and fragmentary;
- rhythm is expressive and upside-only unless a deliberate difficulty mode says
  otherwise; it must not gate success or punish the player.

The Core P0 remains smaller: one authored Quill beat, one route, one encounter, one
typed result, and durable save/restart proof. Long-term infrastructure must not be
allowed to reopen that slice.

## What to borrow from Infinity Nikki

The useful lesson is not “make Melodia into Nikki.” It is the relationship between
exploration, identity, and abilities:

| Infinity Nikki pattern | Melodia translation | Boundary |
|---|---|---|
| Outfits grant exploration abilities | Resonant forms / instruments grant traversal or world-interaction verbs | No gacha or monetization dependency; cosmetics remain separate from capability ownership |
| A new ability makes previously visible spaces meaningful | Soft resonance gates advertise a future route, shortcut, collectible, or song fragment | Never hide the whole world; make the reason for the gate legible |
| Styling and exploration are connected | Optional “composition” or mood challenges use wardrobe, color, sound, and scene dressing | Keep these P2 until the core route and wardrobe authority are stable |
| Ability mastery and later ability fusion | A bounded song/verb progression can unlock combinations such as glide + water resonance | Use explicit combinations, not an unbounded skill tree |
| Photo and social discovery reinforce place attachment | A later memory/photo layer can record authored moments and world discoveries | No online/social service is required for the first long-term milestone |

Official descriptions of Infinity Nikki emphasize outfit abilities as exploration
verbs and challenges, while later official updates describe ability mastery, fusion,
and freer use after progression. Those are useful structural references, not a reason
to copy its economy or product model: [PlayStation’s gameplay overview](https://blog.playstation.com/2024/05/30/infinity-nikki-an-open-world-dress-up-adventure-is-coming-to-ps5/),
[Infinity Nikki’s official site on ability mastery/fusion](https://infinitynikki.infoldgames.com/en/news/294),
and [the official site on the exploration-first design](https://infinitynikki.infoldgames.com/en/m/news/148).

## Authority map for future content

| Domain | Runtime authority | Authoring surface | Blueprint rule |
|---|---|---|---|
| Campaign save/load | Stock `BP_JRPGSaveGame` / GameInstance route | Save schema + integration map fixtures | Never create `MelodiaSaveGame` content for campaign state |
| Narrative and Quill | `UMelodiaNarrativeSubsystem` + QuillScript | Script/intent data | BPs request intents; they do not mutate narrative records directly |
| Travel and portals | `UMelodiaTravelSubsystem` / `IMelodiaTravelProvider` | Allowlisted destination + spawn-tag data | No literal `OpenLevel` in new content |
| Battle turn/result | Stock JRPG controller + `BP_MelodiaBattleBridge` | Encounter/skill/enemy definitions | Presentation observes; it does not own damage, rewards, or turn release |
| Rhythm | `UMelodiaRhythmExecutionComponent` / stock resolver boundary | `UMelodiaRhythmSkillDefinition` and chart data | Rhythm may enrich the result; it cannot make the stock result fail |
| Party | `UMelodiaPartySubsystem` | Party member definition + acknowledgment intent | Roster additions must use the existing roster transaction |
| Traversal | `UMelodiaTraversalComponent` and water bridges | Capability/profile data + traversal volumes | State transitions are centralized; BPs request capabilities |
| World progression | Narrative record / Persona subsystem | Quest, gate, and reward data | Use stable IDs and idempotent intents; no hidden level-local flags |
| Wardrobe | `UMelodiaWardrobeSubsystem` when promoted | Catalog, outfit, dye, and presentation data | Keep cosmetic state separate from campaign progression and ability unlocks |

### Resonant Form capability bridge — new P0 design gate

The Wardrobe lane now has a read-only `UMelodiaWardrobeSubsystem` query surface for
unlocked forms and active `Glide`, `Dash`, and `Swim` capabilities. A source-level
`UMelodiaTraversalCapabilityRegistry` now bridges that provider into
`UMelodiaTraversalComponent`; native requests and jump-to-glide input use the same
gate when `bRequireCapabilityProviderForGlide` is enabled. This remains below L2
until the reflected source compiles in a clean editor-closed build and the live
context matrix is observed.

The module graph constrains the implementation. `MelodiaWardrobe` already depends on
`BS_GodFile`, so `BS_GodFile` must not include Wardrobe headers or add a reverse module
dependency. The next implementation must choose one of these explicit seams:

1. a module-neutral read-only capability-provider/registry contract owned by the game
   module and registered by Wardrobe; or
2. an explicit Blueprint bridge that queries Wardrobe and supplies a capability/context
   result to the traversal request API until the provider contract is compiled.

The implemented registry route preserves the authority split: Wardrobe answers
capability state, the narrative subsystem answers progression flags, and
`UMelodiaTraversalComponent` alone mutates movement. Unknown capability, missing
provider, blocked context, and progression lock fail closed. The contract is recorded in
`specs/traversal/melodia_traversal_capability.v1.json`; do not promote the Hover Gate
fixture above L1 until this seam has fresh compile, graph, and runtime evidence. The
default component flag remains opt-in during migration so Core P0 does not silently
lose legacy glide behavior before a starting Resonant Form is authored.

All seven gameplay families now share a second, cross-domain gate contract at
`specs/capability/melodia_capability_gate.v1.json`. It normalizes capability,
context, progression, region, traversal-mode, and snapshot inputs; returns a typed
allowed/blocked/preview-only/invalid decision; fingerprints the evaluated inputs;
and fails closed without mutation. Blueprint shells may present a result and forward
an allowed request, but may not grant capability, cache an allow across a
load/context transition, or create a local registry. This is the intended seam for
long-term additions such as glide, water-listening, echo-reveal, portal locks,
challenge availability, and skill unlock presentation.

The remaining progression adapters are now explicit as well. WorldChallenge uses
one atomic completion/intent/reward transaction; StateAnchor uses one stable-key,
multi-operation transaction and is distinct from the opening-specific anchor. Their
attempt/apply identities are checked against dedicated `UMelodiaIntegrationConfig`
allowlists, while uncommitted challenge attempt state remains BP-transient. The
generic StateAnchor template is an `AActor`; it must not inherit from the
opening-specific anchor. Their contracts live at
`specs/progression/melodia_world_challenge_adapter.v1.json` and
`specs/progression/melodia_state_anchor_adapter.v1.json`. Neither is live-promoted
until native reflection, rollback, save/load, and fixture evidence exist.

## Blueprint readiness kit

### Existing foundations to formalize

The repository already contains the beginnings of the kit:

- runtime shells: `BP_MelodiaJRPGGameInstance`, `BP_MelodiaJRPGGameMode`,
  `BP_MelodiaJRPGPlayerController`, `BP_MelodiaBattleBridge`,
  `BP_MelodiaTravelVolume`, and `BP_MelusinaJRPGCharacter`;
- battle/UI children: `BP_MelodiaBattleUI`, `BP_MelodiaActionsUI`,
  `BP_MelodiaActionButton`, `BP_MelodiaRhythmPrompt`, and
  `BP_MelodiaTurnOrderList`;
- skill content: `UMelodiaRhythmSkillDefinition` plus the existing Melusina and Sir
  skill children and Resonance buff;
- enemy foundations: `AMelodiaEnemyBase`, `UMelodiaEnemyDataAsset`, and
  `AMelodiaEncounterTrigger`;
- travel/traversal foundations: `UMelodiaTravelSubsystem`,
  `AMelodiaTravelInteractionPortal`, `UMelodiaTraversalComponent`,
  `BP_KaleidoNaveArrivalTrigger`, and water interaction bridges;
- persistence/state foundations: `UMelodiaNarrativeSubsystem`, the stock save path,
  `UMelodiaOpeningStateComponent`, and the canonical integration map.

These are foundations, not yet a “ready for any designer” kit. Each needs a contract
fixture, a validator, and one example asset that passes the validator.

### Production templates to create

Create these as small, documented shells only after the T3D contract is repaired:

1. `BP_MelodiaSkill_Base` — owns only presentation/config references; the DataAsset
   owns identity, target rules, effect family, cost, rhythm profile, and reward tags.
2. `BP_MelodiaEnemy_Base` — child of `AMelodiaEnemyBase`, with explicit mesh,
   animation, telegraph, hit, break, defeat, loot, and encounter-ID fields.
3. `BP_MelodiaEncounter_Base` — child/adapter for the stock encounter trigger with
   one encounter definition, one entry condition, one result policy, and one reward
   transaction.
4. `BP_MelodiaPortal_Base` — prompt, destination ID, spawn tag, unlock query,
   confirm/cancel, save-before-travel, cooldown, and input restoration.
5. `BP_MelodiaTraversalGate_Base` — required capability, readable locked state,
   optional alternate route, enter/exit feedback, and no direct movement mutation.
6. `BP_MelodiaWorldChallenge_Base` — a generic collectible, music-memory, styling,
   photo, or environmental puzzle shell driven by a definition asset.
7. `BP_MelodiaStateAnchor_Base` — authored checkpoint/return context that serializes
   through the canonical narrative/save seam and never stores a second save object.
   It is an `AActor` template; the opening-specific anchor remains a separate
   authority and is not its parent.

Do not make each future skill, enemy, or portal a bespoke graph. A content Blueprint
should mostly bind assets, expose tuning, and forward to the authority component.

## Readiness levels for every Blueprint

Every production Blueprint should have a row in a tracked readiness manifest:

- **L0 Inventory:** canonical `/Game/` path, owner, parent class, category, and
  duplicate-name check.
- **L1 Contract:** required interfaces/components, stable IDs, no forbidden direct
  authorities, and all soft references resolve or are explicitly optional.
- **L2 Graph:** compiles cleanly; no shadowed parent events, empty custom events,
  dead exec islands, stale map strings, or unreachable production asset.
- **L3 Fixture:** one disposable test map exercises its core behavior, save/load or
  teardown path, and failure path.
- **L4 Ship:** package/Gauntlet evidence, owner playtest, and a reviewed fingerprint
  baseline.

“All BPs ready” means every production gameplay BP is L2 at minimum and every
authority/template BP is L3. It does not mean every archived or experimental asset is
clean or promoted.

## T3D pipeline updates required before scaling authoring

The current `Tools/t3d_safe_wire.py` sequence is a strong starting point: it records
the pre-edit graph, checks the fingerprint, validates, mutates, compiles, asserts,
re-reads, saves, and emits evidence. Before it is used across production BPs, make
these changes:

### P0 — make the postcondition real and prove the graph delta

The current assertion passes the post-edit export back to `assert_graph_matches` as
the spec. That makes the assertion self-consistent but not intent-sensitive. The
request must instead carry an expected postcondition generated from the patch:

- required nodes/classes and stable semantic labels;
- required connections and pin defaults;
- forbidden nodes/links/classes;
- expected node/connection delta or an explicit allowed no-op;
- compile errors equal zero;
- post-save re-export equal to the verified in-memory result.

The implementation now requires `expected_postconditions.expected_delta` for a
committed mutation and checks that declared new nodes/connections were absent in
the pre-edit export and present in the post-edit export. A required node that was
already present cannot masquerade as a successful injection. The pipeline aborts if
any required postcondition is absent, even when the editor RPC itself returns
success.

### P0 — enforce transaction identity and scope

The schema and CLI now require a non-placeholder `request_id` and a live
`expected_before_fingerprint`; the transport still strips envelope metadata before
the editor mutation. Evidence manifests reject a reused request ID and record the
request ID, asset, graph, pre-edit fingerprint check, and final evidence path.
Approval scope, second-writer detection, and live package proof remain follow-up
gates before production-wide authoring.

### P1 — add reusable pattern contracts

Version each T3D pattern with:

- input schema and allowed target classes;
- semantic postconditions;
- fixture Blueprint;
- compile/readback test;
- forbidden direct-authority calls;
- rollback/export record;
- a golden evidence envelope.

Patterns needed first are `skill_effect`, `enemy_telegraph`, `portal_request_travel`,
`traversal_capability_gate`, `state_checkpoint`, `quest_intent`, and
`presentation_observer`. Keep one asset per transaction; never use T3D for bulk
generated-content churn.

### P1 — create a Blueprint readiness scanner

Extend `Tools/bp_sweep.py` and `Tools/bp_regression_checker.py` into a tracked
`bp_readiness` report that checks the L0–L4 levels, parent/interface contracts,
compile status, stale references, duplicate short names, shadowed events, empty
events, dead graphs, reachability, required components, stable content IDs, and
fixture coverage. Missing baselines must fail closed; never create a new baseline
from the current dirty state.

The first offline inventory exists as `Tools/melodia_bp_readiness.py`. It reports
disk inventory and contract-only fixture state without claiming live graph or runtime
readiness. The current report finds all seven canonical gameplay template assets
absent, seven L1 contract fixtures present, and the Kawaii probe present at L0 with live
evidence pending. `Tools/melodia_bp_materialization_preflight.py` now adds the
offline authoring gate: it checks registry completeness, planned `.uasset` collisions,
native-parent source coverage (including `Plugins/MelodiaCore`), fixture contracts,
and the explicit materialization order without contacting or mutating Unreal. The
current result is 6/7 templates ready to enter live authoring and 1/7 blocked on
the Skill definition bridge. WorldChallenge and StateAnchor now have source-wired
atomic adapters, but the future live extension must consume Monolith evidence and
promote no asset above L1 from disk presence alone.

The offline contract suite is now executed by `Tools/run_contract_tests.py` with a
fixed 16-suite coverage floor. Echo Gates and BuildGraph invoke it directly; pytest
collection is intentionally not the source of truth because most gate suites are
script-style and this runner may not have pytest installed.

### P2 — make editor and package proof symmetrical

For each promoted template, run the same contract fixture in the editor and in the
Development package. The evidence envelope should include the Blueprint path,
content revision, T3D request ID, graph fingerprint, compile result, fixture result,
and packaged smoke result.

## Gameplay expansion sequence

### P0: protect the slice and fix authoring safety

1. Complete the Core P0 golden route.
2. Repair and re-run the T3D postcondition proof against the disposable probe.
3. Produce the first L0–L2 readiness report for the existing Melodia gameplay BPs.
4. Quarantine or structurally disable the unused competing MelodiaCore save, quest,
   battle, roguelike, and outfit authorities before new content is added. The design
   documents already identify these duplicate authorities as the largest long-term
   hazard.

### P1: prove one reusable content family per domain

1. One new Resonance skill from a DataAsset and `BP_MelodiaSkill_Base`.
2. One new enemy from `UMelodiaEnemyDataAsset` and `BP_MelodiaEnemy_Base`.
3. One portal with a locked and unlocked path, save-before-travel, spawn context,
   and cancel/input restoration.
4. One traversal gate using glide or water state with a readable alternate route.
5. One world challenge that grants an idempotent narrative/reward intent.

Each proves that content can be added without changing the authority code.

## Kawaii Physics and placement readiness

The project has KawaiiPhysics `1.21.0`, a Melusina hair setup, and a disposable
`/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe` asset. The probe is
not yet a reusable production base or an L3/L4 fixture: `ABP_Melusina_WaterHair`
contains one Kawaii node rooted at `hair_root`, while root-body/limits compatibility,
map persistence, reachability, and deterministic PIE reset remain open. The existing
`BP_PhysicsPlacementSpawner` is only a generic static-mesh physics-drop test and is
ignored/untracked; it is not Kawaii evidence.

The next safe step is to finish the existing probe with explicit root-bone,
limits/constraints, reset/teardown, and runtime readback checks. Promote a reusable
physics presentation base only after that probe passes in the editor and Development
package. Full findings and acceptance criteria are in
`Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md`.

### P2: add the Nikki-inspired exploration layer

Introduce “resonant forms” as a small, authored capability set—such as glide,
water-listening, petal-clearing, echo-reveal, and a later combined form. Unlocks come
from story, mastery, and exploration; they are not gacha and do not replace the
wardrobe’s cosmetic role.

Then add optional composition challenges, memory/photo capture, dye/material styling,
and a home/hub layer only where each reinforces Melodia’s emotional and musical loop.

### P3: scale content, not machinery

Only after one full movement is stable should the project add seeded expeditions,
larger enemy pools, four movement registers, recruit acknowledgments, or deterministic
run history. The same DataAssets, authority subsystems, portal/traversal contracts,
and fixtures should carry the expansion.

## Definition of long-term readiness

The project is ready for sustained gameplay development when an agent or designer can
answer “yes” to all of these:

- Can I create a new skill without editing battle authority code?
- Can I create a new enemy with a telegraph, hit, break, defeat, and reward path?
- Can I place a portal without writing a map string or bypassing save/travel authority?
- Can I gate traversal by a capability while leaving a readable alternate route?
- Can I save and restore all persistent state without a second save system?
- Can the readiness scanner detect a shadowed event or dead graph before playtest?
- Can T3D prove the exact requested graph delta and stop on any mismatch?
- Can the packaged fixture reproduce the editor result?

That is the real long-term milestone—not the number of Blueprint assets in the
folder.
