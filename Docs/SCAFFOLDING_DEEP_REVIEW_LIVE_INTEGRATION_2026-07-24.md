# Deep Review: Live BP↔C++ Integration, Musical Reactivity, RPG Mechanics, Cross-System Latency

Companion to `SCAFFOLDING_DEEP_REVIEW_2026-07-24.md` (character/outfit/content pillars). This pass studies whether real-time visual feedback, musically-reactive gameplay, basic RPG mechanics, and cross-system data flow can run without lag.

## Finding 1 (FIXED THIS SESSION): the reactivity pipeline was doing real per-frame waste

`UMelodiaRhythmReactivitySubsystem` is a `UTickableWorldSubsystem` that called `Publish()` **unconditionally every single frame**, regardless of whether any music/rhythm event had happened. Each `Publish()` did:
- 14 `SetMPCScalar` calls, each re-resolving `UMaterialParameterCollection*` via `LoadObject(nullptr, *PathString)` — a string-path object load, every call, every frame, forever (`MelodiaRhythmReactivitySubsystem.cpp:255`, pre-fix).
- 6 unconditional UDP `SendOSCFloat` packets to TouchDesigner, even at idle with nothing to report.
- A delegate broadcast (`OnSignalChanged`) to every bound Blueprint/widget, every frame.

This ran in every scene, all the time — exploration, menus, idle — not just combat. **Fixed**: `CachedCollection` resolved once in `Initialize()` (removes the 14x/frame LoadObject); `IsSignalAtRest()` early-out in `Tick()` skips the whole `Publish()` when every pulse/decay value is already settled (removes the OSC/broadcast spam at idle). `Notify*()` calls still `Publish()` immediately on their own regardless, so no responsiveness is lost — only the redundant at-rest repetition. Compiled and verified.

## Finding 2: the BP↔C++ presentation-hook surface may be silently no-op-ing

`MelodiaCombatPresentationInterface` and `MelodiaEnemyPresentationInterface` declare 7 `BlueprintImplementableEvent`s total — this is the hook surface for "battle events trigger character/enemy presentation" (hit reactions, victory poses, etc.). A text grep of `BP_Melusina`/`ABP_Melusina` found **zero references** to these interface/event names. Binary `.uasset` grep is not proof of absence (names could differ, or logic could live in a linked layer), but it's a real flag: **verify in-editor whether Melusina's Blueprint actually implements these events** — if not, every hit/victory/break presentation call from C++ is currently going nowhere. `MelodiaRhythmHUDWidget` is the opposite case — 13 `BlueprintImplementableEvent`s, clearly the intended primary beat→UI hook surface, worth confirming that one over the combat-presentation interfaces if only one gets checked first.

## Finding 3: reflection-by-name calls are NOT on the hot path (good)

Only one `FindFunction`/`ProcessEvent`-by-name call exists in the whole plugin (`MelodiaSmokeCharacter.cpp:411`, the Orrery menu toggle) — one-shot, input-bound, not per-frame. This is not a lag source. The reactivity pipeline's cost (Finding 1) was real object/network overhead, not reflection overhead — worth being precise about which perf story is actually true here.

## Finding 4: "basic RPG mechanics" are real but two disconnected islands

`MelodiaProgressionComponent` (XP/Level/Currency/Inventory) and `MelodiaCombatStateComponent` (gauges/toughness/buff-debuff modifiers) do not talk to each other:
- **Leveling has zero effect outside the Progression component itself.** Nothing else in the plugin reads `Level`. Movement speed, unlock gates, stat scaling — none are wired to it.
- **The `ApplyModifier`/buff-debuff pipeline is real and used** (spellcasting, tests) but only ever called from battle code — there's no equipment/item path that feeds a modifier in. Three separate inventory shapes exist (`FMelodiaInventoryItem`, NPC `ShopInventory : TArray<FName>`, roguelike `FMelodiaRunRewardCandidate`) with no shared struct or glue code converting between them.
- **Verdict**: this isn't "RPG mechanics are unbuilt" — the individual mechanics (leveling math, buff stacking, inventory tracking) are each real and reasonably well-tested. The gate is that they were each built to serve one system (battle) rather than as a shared cross-cutting RPG layer that exploration, shops, and equipment all read from the same place.

## Finding 5: the delegate backbone is a real strength, with one blind spot

18 dynamic multicast delegates form the actual "systems push information to each other" backbone, and it's healthy: battle, roguelike (richest, 6 delegates), save, opening flow, and quest can all notify listeners without being polled. **`UMelodiaPartySubsystem` is the one system with zero outbound delegates** — every consumer of "who's the active party member" must call `Get()` and poll it; the party subsystem can never push a change notification. Given the roster is about to grow (outfit system, more characters), this is worth a `FMelodiaOnActivePawnChanged` delegate before more systems start polling it.

`UMelodiaBattleSession::Get()` is looked up repeatedly (20 call sites, not cached) including inside the hottest path — `BeginBasicExecution`/`BeginSkillExecution`, once per player rhythm input. This is a minor style inconsistency, not a real perf bug (UE's `GetSubsystem<T>()` is a cheap indexed lookup, not a search) — noted for consistency, not flagged as urgent.

## Recommended sequencing (not yet executed beyond Finding 1)

1. **Done**: reactivity pipeline lag fix (this session).
2. **Verify in-editor**: does Melusina's BP/ABP actually implement `MelodiaCombatPresentationInterface`/`MelodiaEnemyPresentationInterface`? If not, wire it — this is the direct blocker on "Persona-style" hit/victory presentation actually showing anything.
3. **Give `UMelodiaPartySubsystem` an outbound delegate** (`FMelodiaOnActivePawnChanged`) before the outfit/roster work adds more listeners that would otherwise poll it.
4. **Unify the RPG layer**: one shared item/stat struct that Progression, NPC shops, and roguelike rewards all speak, and at least one real cross-system effect of Level (even something small, like a movement-speed or SP-max scalar) to prove the wire actually carries load.
