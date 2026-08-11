# Scaffolding Deep Review — What's Gating Infinity Nikki-Scale Ambition

Reviewed through the lens of: could this codebase carry resource gathering, a turn-based rhythm roguelike, Persona-grade character presentation with reusable animation/character assets, immersive story, and songcraft — as a professional studio's core systems, not a solo demo? Verdict per pillar below, each backed by direct code inspection (paths/lines cited), not impression.

## The one-sentence diagnosis

**Every system here has a well-shaped schema and a broken or missing wire from that schema to actual content.** This isn't "the architecture is bad" — the C++ patterns (UGameInstanceSubsystem, USTRUCT data models, delegate-driven battle flow) are genuinely competent. The gate is that **content authoring never got connected to the systems built to consume it**, and **the character/animation layer has no reuse infrastructure at all**, which are the two things "Infinity Nikki scale" is actually made of.

---

## Pillar 1 — Character, Animation, Outfit (the Nikki-specific gate)

**This is the single biggest gap for the stated ambition, and it's not partially built — it's unstarted.**

- No shared character base class. `AMelodiaSmokeCharacter` and `AMelodiousFlightCharacter` both derive directly from `ACharacter` and duplicate ~150-250 lines each (input mapping context construction, party-swap handling, camera boom setup) — byte-for-byte copy-paste patterns, not inheritance. A third character costs exactly what the second one cost: a full bespoke class.
- **SK_Melusina is one monolithic skinned mesh.** Outfit is baked in, not assembled from separable garment pieces. There is no `SkeletalMeshMerge`, no clothing-slot system, zero hits for `ClothingAsset`/`EquipmentMesh` anywhere in the plugin.
- The *only* multi-component precedent is hair (`WaterHairMesh`), and it deliberately avoids the standard `LeaderPoseComponent` sharing mechanism because the hair has its own skeleton — it's a one-off hack, not a generalizable pattern for "swap 40 dresses on one body."
- Only 7 AnimBPs exist, 6 belong to Melusina; Sir Melodious has **zero** — his animation is entirely inside a Blueprint, invisible to any code-level reuse pattern. No Animation Layer Interfaces, no shared locomotion library anywhere.
- The harvested JRPG template's `BP_EquipmentBase`/`BP_EquipmentMeshBase` — exactly the kind of thing you'd want here — sit completely unwired. Zero references from any Melodia system.
- The one genuinely good bone: `MelodiaPartySubsystem`'s roster array (`TArray<TSoftClassPtr<APawn>>`) is architecturally arbitrary-size and would scale fine *if* the characters behind it were built to share infrastructure.

**What "gates" this specifically:** a dress-up game needs (a) a shared character base class, (b) a real modular outfit system (garment meshes leader-posed onto one skeleton, swappable per slot), (c) an Animation Layer Interface so locomotion/combat anims are authored once and reused. None of the three exist. This is greenfield work, not a fix.

## Pillar 2 — Content Authoring (the "professional studio volume" gate)

**The schema-to-content wire is broken almost everywhere, and in a uniquely misleading way.**

| System | Schema quality | Actual content | Non-programmer editable? |
|---|---|---|---|
| Enemies | Good (`FMelodiaEnemyDef`) | 0 DataAsset instances; 13 hardcoded in `GetDemoEnemies()` | No — C++ recompile |
| Songs/Skills | Good (`FMelodiaSongSkillRecipe`) | 0 `.uasset` instances; hardcoded builder | No |
| Quests | Adequate (`FMelodiaQuestDef`) | Per-NPC hand-authored only, no catalog | Partially, doesn't scale |
| Dialogue | **Stub.** `DialogueTree : FName` resolves to nothing, anywhere. Real path is a flat `TArray<FText>` — no branching, no conditions | 11 NPCs hardcoded | No |
| Roguelike meta (rooms/blessings/tokens/artifacts) | Good, real data | **86 authored rows sit in `Content/Melodia/DataStuctures/*.json` — completely dead.** Zero references outside the JSON files themselves. No matching `.uasset` DataTable. | No — inert |
| Resource gathering / crafting / economy | **Doesn't exist.** Not stubbed — absent. | 0% | 0% |

The DataStuctures JSON files are the most dangerous artifact in the repo precisely *because* they look like the data-driven layer is done — real stat curves, real skill charts, 86 rows of legitimate design work — and do nothing at runtime. Anyone (including a future agent) glancing at that folder would reasonably conclude content authoring is solved. It isn't wired to a single line of C++.

**What "gates" this:** three concrete, mechanical (not architectural) fixes would close most of this — (1) convert the JSON rows into real imported `UDataTable` assets, (2) replace every `Get*Demo*()` hardcode with an asset-registry/DataTable lookup, (3) build an actual dialogue-tree data structure from scratch (branches, choices, conditions — currently zero infrastructure). Resource gathering/crafting is a genuine net-new system, not a wire-up.

## Pillar 3 — Module Architecture (the "can this scale to a bigger team/codebase" gate)

Test coverage is a real strength (9 automation test files, non-trivial breadth) — worth explicitly not breaking as this grows.

Three patterns will not survive scaling past solo-project size:
- **Single monolithic module** (133 files, one `.Build.cs`, one `MELODIACORE_API`). No sub-module boundaries (Combat/Save/Narrative/Economy). At current size tolerable; touching a shared header already risks near-full-module recompiles because of point 2.
- **Save/roguelike layers directly `#include` battle internals** (`MelodiaSaveGameSubsystem.cpp` pulls in 8 sibling headers including `MelodiaBattleSession.h`; `MelodiaRoguelikeRunSubsystem.cpp` does too). No interface/DTO boundary — persistence is coupled to combat's internal shape, so refactoring combat risks silently breaking saves.
- **Three competing idioms for "find the one global thing"**: proper subsystems (8 classes, correct), static blueprint-function-library statics (5 classes, adjacent job), and `TActorIterator` world-scanning (8 files). No enforced house style.
- Minor but real: raw OSC/UDP socket code lives *inside* `MelodiaRhythmReactivitySubsystem.cpp` (gameplay authority owning network I/O) rather than behind an interface the presentation/tooling layer could swap.

---

## What this means for the stated ambition, plainly

- **Turn-based rhythm roguelike**: the actual battle/turn/AV/roguelike-run kernel is the most mature part of this codebase — real subsystems, real delegates, staged turns, feel layer, tests. This pillar is closest to professional-shape already.
- **Songcraft mechanics**: schema exists and is well-designed; zero authored content reaches the game. This is a data-pipeline fix, not a redesign.
- **Resource gathering**: does not exist in any form. Net-new system.
- **Persona-like polish, reusable animations/characters**: this is the deepest hole. No shared base class, no outfit system, no animation reuse layer. Everything built so far (Melusina, Sir Melodious) was built as one-offs, meaning the *pattern* to replicate for future characters/outfits doesn't exist yet either — there's nothing to copy that's actually reusable.
- **Immersive story**: dialogue is a stub pointing at nothing; no branching system exists.

**The honest read**: this project has spent its architecture budget on the *systems* layer (battle, roguelike, save, subsystem patterns) and none of it yet on the *content* layer (data authoring) or the *presentation* layer (character/outfit/animation reuse) — which are precisely the two layers "Infinity Nikki × Persona" lives or dies on. The systems work is not wasted; it's a legitimate foundation. But scaling to the stated ambition requires greenfield investment in outfit/animation architecture and a real data-authoring pipeline before more battle/roguelike systems work would even be the right next spend.

## Recommended sequencing (not yet executed — for discussion)

1. **Character base class + Animation Layer Interface** — refactor `AMelodiaSmokeCharacter`/`AMelodiousFlightCharacter` onto a shared `AMelodiaCharacterBase`, extract the duplicated input-mapping/party-swap code once. This unblocks every future character AND is a prerequisite for outfit work.
2. **Modular outfit system** — the actual Nikki-defining system. Garment meshes as separate skeletal mesh components leader-posed onto the body skeleton, an equipment-slot data model (the orphaned JRPG template `BP_EquipmentMeshBase` is a legitimate starting reference, not a rebuild-from-zero).
3. **Wire the dead DataStuctures JSON into real DataTables**, replace `Get*Demo*()` hardcodes — this alone unlocks non-programmer content authoring for enemies/skills/room-mods/blessings with the design work already done.
4. **Real dialogue-tree data structure** — smallest net-new system needed for "immersive story."
5. **Resource gathering/crafting** — greenfield, sequence after the above since it likely wants to hang off the same inventory/economy shape as outfits/crafting materials.
6. Module hygiene (sub-module split, save/battle decoupling via interface) — worth doing, but lower urgency than 1-4 since it's a "won't survive scaling" risk, not a "can't build the game" blocker today.
