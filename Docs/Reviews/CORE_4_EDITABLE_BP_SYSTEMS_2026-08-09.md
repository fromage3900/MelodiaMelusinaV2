# Core 4 editable BP systems — long-term game-dev review (2026-08-09)

**Scope:** the four gameplay mechanics the owner designated as Melodia-focused BP
surfaces for long-term dev: **traversal state**, **rhythm skills**, **party &
switching**, **narrative & flags**. Everything below was verified against source
and the live editor this session; no claim rests on an older doc.

**Lens:** what is authority vs what is content. A system is long-term editable
when the *content* (roster, skills, volumes, flags) is authored in Blueprint or
data and the *authority* (turn math, allowlist, travel, session state) stays in
the existing C++/stock systems. The four systems below already mostly satisfy
this; the gaps are specific and small. Do not build new authorities.

---

## Verdict table

| System | Authority (keep) | Content surface today | Long-term gap |
|---|---|---|---|
| Traversal state | `UMelodiaTraversalComponent`, `UMelodiaInputContextSubsystem`, `UMelodiaTravelSubsystem` | Component `EditDefaultsOnly` tuning + `Blueprintable` native volumes + `UMelodiaMapTransitionComponent` (BP component) | No authored to/from **travel volume** BP convention; volumes are native actors, level BP must wire travel by hand |
| Rhythm skills | Stock `UseSkill` (BP_BattleSkillBase) + `UMelodiaRhythmCombatSubsystem` sessions + `UMelodiaRhythmSkillDefinition` DataAssets | 8 rhythm DataAssets (tempo, pattern, grades, effect); skill BPs are stock children; `StockSkillRhythmIds` map on config (now seeded) | Skill→rhythm-id lives in the central map keyed by generated class name; skills are not self-describing |
| Party & switching | Stock `partyMembers` / `AddPlayerUnit`; `UMelodiaPartySubsystem` roster/cycling | `PartyPawnClasses` is `EditAnywhere` but **self-seeded in C++** (`MelodiaPartySubsystem.cpp:16-21`); LeftControl bound in C++ on both pawns | New party members require a C++ edit (seed + pawn); input is C++-constructed, not an authored asset; RightControl/gamepad unmapped |
| Narrative & flags | QuillScript interpreter + `UMelodiaNarrativeSubsystem` (7 verbs, exactly-once) | `.qsc` text assets; allowlists on `DA_MelodiaIntegrationConfig`; intents idempotent per IntentId | None structural; new ids must be allowlisted (fails closed in Shipping) |

---

## 1. Traversal state

**Authority (do not touch):**
- `UMelodiaTraversalComponent` — movement state (walk/sprint/glide/swim/dive/dash),
  stamina, breath. Applies only while `UMelodiaInputContextSubsystem::IsMovementAllowed()`.
- `UMelodiaTravelSubsystem::TravelTo(LevelId, SpawnTag)` — the one travel path,
  allowlist-validated, spawn-tag placement on arrival.
- `UMelodiaMapTransitionComponent` — already a BP component; routes through
  `TravelTo`, defers while Dialogue/Menu owns input.

**Editable today:**
- All traversal tuning is `EditDefaultsOnly` on the component — speeds, dash
  impulse/cooldown, glide feel, stamina rates, water thresholds. Per-pawn in BP.
- `AMelodiaExplorationInteractionVolume` / `AMelodiaPuzzleRelayVolume` are
  `Blueprintable` native actors with editable `InteractionId`, `PromptText`,
  `bOneShot`, `bRequireMelusina` and three assignable events.

**Gap — the authored to/from travel volume:**
There is no dedicated editable volume that authors *destination level + spawn tag
+ condition* and calls `TravelTo`. `UMelodiaMapTransitionComponent` provides the
mechanics, but every transition is currently hand-wired in level Blueprint.

**Recommendation (content, no new authority):**
1. Author **one** editable Blueprint (e.g. `BP_MelodiaTravelVolume`) that carries
   `TargetMapId` + `TargetSpawnTag` + optional `bRequireMelusina`, and on overlap
   calls `UMelodiaTravelSubsystem::TravelTo(TargetMapId, TargetSpawnTag)`.
2. Place it in the Morning map as the exit pair; levels then author routes in the
   editor with zero code.
3. Do **not** add a second travel path — every new volume still routes through the
   same allowlisted `TravelTo`. If a volume's id is not in `TravelLevelIds`, the
   travel must fail loudly (it already returns false).

---

## 2. Rhythm skills

**Authority (do not touch):**
- Stock skill execution: `UseSkill` on `BP_BattleSkillBase` children; the stock
  turn loop calls `UseSkillWithRhythm(currentSkill)` (verified live:
  `UseMP → UseSkillWithRhythm(currentSkill) → HideSkillActionButtons`).
- `UMelodiaRhythmCombatSubsystem` — session state, grading, `FinishSession`
  latches the damage scalar before the deferred `UseSkill` fires (verified in
  source and the live graph).
- `UMelodiaRhythmSkillDefinition` DataAssets — tempo, pattern, niche, effect,
  per-grade multipliers, SP cost, presentation theme. **8 authored and auto-scanned.**

**Editable today:**
- Everything about a rhythm skill's *data* is content: 8 DataAssets in
  `/Game/MelodiaIntegration/Config`.
- `StockSkillRhythmIds` on `DA_MelodiaIntegrationConfig` now maps
  `BP_MelusinaPetalCadence_C → cadence_strike` (verified readback this session).

**Gap — skills are not self-describing:**
The id is resolved by keying the map on the *generated class name*. A new rhythm
skill requires editing the central map; a renamed skill silently unmaps. The
owner-endorsed improvement in the handoff: put the rhythm id on the skill itself
and keep the map only as a legacy fallback that warns.

**Recommendation:**
1. Add one `EditAnywhere` `FName RhythmSkillId` to a Melodia skill base class (or
   a data-only base BP under the stock `BP_BattleSkillBase` child chain).
2. `ResolveRhythmSkillId`: read the property first; fall back to the map with a
   warning log. **Header change → closed-editor rebuild.**
3. Then author future rhythm skills as: stock child BP + `RhythmSkillId` set +
   DataAsset row. No map edit, no C++.

---

## 3. Party & switching

**Authority (do not touch):**
- Stock combat roster: `partyMembers` / `AddPlayerUnit` on the stock controller —
  the only authority for who fights.
- `UMelodiaPartySubsystem` — explore roster, lazy-spawn/park pawns, `SwitchToNext`
  cycling, `RegisterPawn(Pawn, Index)`.
- `MelodiaJRPGPartyBootstrapSubsystem` — one-way recruitment adapter; unlocks
  exploration possession only after the stock party accepted Sir (read-back probe).

**Editable today:**
- `PartyPawnClasses` is `UPROPERTY(EditAnywhere, BlueprintReadWrite)` — but
  `Initialize()` self-seeds index 1 with `BP_SirMelodious_Flight_C` when empty
  (`MelodiaPartySubsystem.cpp:16-21`), so the authored content is the seed, not a
  design surface.
- Unlock chain verified: `melodia:flag:melodia_smoke_complete` →
  `NotifySirRescued()` (strict phase gate) → `AddPlayerUnit` → probe →
  `SetSirMelodiousExplorationUnlocked(true)`.
- LeftControl is bound in C++ on both pawns (`MelodiaCharacterBase` +
  per-pawn bindings) — works, but it is code, and only LeftControl.

**Gap:**
1. Roster lives in a C++ seed, so a third party member is a C++ change.
2. Switch input is a `NewObject<UInputAction>` in code — no authored input asset,
   no RightControl/gamepad.

**Recommendation (content-first):**
1. Move the roster seed out of C++ into an editable data surface — either leave
   `PartyPawnClasses` empty in code and populate it from a DataAsset referenced
   by the GameInstance (or `DA_MelodiaIntegrationConfig`-style asset). Keep the
   C++ seed only as a first-boot fallback that warns when used.
2. Author the switch as a real `UInputAction` asset (LeftControl today; add
   RightControl + gamepad chord in the same asset — pure content).
3. Do not touch `SwitchToNext` / `RegisterPawn` / the stock `AddPlayerUnit`
   contract.

---

## 4. Narrative & flags

**Authority (do not touch):**
- QuillScript interpreter; authored `.qsc` text assets compiled to
  `UQuillscriptAsset`.
- `UMelodiaNarrativeSubsystem` — the seven verbs, allowlist validation,
  exactly-once consumption (`ConsumedIntentIds` per `<IntentId>`), battle-result
  exactly-once, `ResumeQuillOnce()`.

**Editable today — effectively complete:**
- All narrative is content: `.qsc` source, compiled assets, allowlists on
  `DA_MelodiaIntegrationConfig`. No BP surface is needed; the "Blueprint" for this
  system is the authored script + the config asset.
- Intents are idempotent per IntentId (verified in source and campaign docs), so
  replayed beats and reloaded saves are no-ops by design.

**Gap — none structural, one discipline item:**
- New ids must be allowlisted or they fail closed in Shipping (editor builds pass
  with a warning while `bRelaxedAllowlistInEditor=true`). Run verification passes
  with relaxed mode off.
- Optional tooling later: a sweep that cross-checks every `melodia:` id in the
  `.qsc` sources against the config allowlists (the `echo_run.py validate-spec`
  contract already does this shape for specs).

---

## Cross-cutting rules (from the working agreement)

1. **No compensating mechanisms.** Every recommendation above removes a
   code-located value (seed, map, keybinding) in favour of content — none adds a
   flag or branch that cancels another behaviour.
2. **No speculative interfaces.** `MelodiaSharedAuthorityInterfaces.h` doctrine:
   a stale uncalled interface method is worse than none. Extend the authority
   locator only when a real MelodiaCore call site needs it.
3. **Content vs authority:** the stock JRPG template remains the combat/party/
   save authority; MelodiaCore owns integration contracts; Melodia BPs and data
   author *content*. Nothing here moves class paths.
4. **Build implications:** rhythm-skill-id property (item 2) is the only header
   change → closed-editor rebuild. Traversal volume BP, party roster data, and
   the input action asset are pure content — no build.
5. **29 reflection seams:** convert only the gameplay-critical ones (the four
   above). Leave the rest; a working seam is cheaper than a converted one.

---

## What is already correct (do not "improve")

- `UseSkillWithRhythm` sequencing — the montage damage notify reads the latched
  scalar; verified in the live graph.
- Lane input Q/W/O/P both key-down and key-up; `ShowRhythmGrade` signature.
- Party unlock chain idempotence and the strict `NotifySirRescued` phase gate.
- Narrative exactly-once (battle result, stat intents, rewards).
- Traversal input gating through `UMelodiaInputContextSubsystem` (no ad-hoc
  input-mode toggles).
