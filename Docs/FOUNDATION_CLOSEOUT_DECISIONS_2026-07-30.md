# Foundation Closeout — Decisions Needed Today

**Date:** 2026-07-30
**Context:** native build green; Persona-lite persistence and musical-time delegation landed.
**Purpose:** the remaining *decisions* (not tasks) that close the turn-based Persona-lite loop.

---

## 0. Build result

`BS_GodFileEditor Win64 Development` — **Succeeded**, 28.6s, both DLLs linked, zero errors.
Log: `Saved/Logs/ClaudeNativeBuild_20260730_foundation.log`.

Bakes: music-clock delegation (Decision 012), narrative record v2 + migration (013),
`IsGatedContentAvailable` (014), project-wide musical time (015), plus the previously staged hair
`head_x` fallback and the "hair only" one-tick deferral.

Only warnings are pre-existing `FSlateFontInfo` deprecations in `MelodiaMinimalHUD.cpp`, unrelated
to this work. They will become errors in a future engine version — worth a ticket, not today.

---

## 1. Deep comparison: MelodiaCore vs. what you have now

### The number that matters

MelodiaCore is **~19,600 lines across 70 headers**. `Source/BS_GodFile/` includes exactly **five**
of them:

| Live | Role |
| --- | --- |
| `MelodiaAudioComponent.h` | Quartz battle transport — now feeding the music clock |
| `MelodiaBattleSession.h` | battle-phase observation for presentation |
| `MelodiaCoreRulesLibrary.h` | rhythm windows, grades — the typed vocabulary |
| `MelodiaOpeningFlowSubsystem.h` | opening phase state |
| `MelodiaPartySubsystem.h` | Sir flight pawn possession (exploration only) |

The other **65 headers are dead code that still compiles into the DLL.**

### Why that is a live hazard, not housekeeping

Among the 65 unreferenced-but-instantiable classes:

- `MelodiaSaveGame` + `MelodiaSaveGameSubsystem` — a complete second save system
- `MelodiaQuestManagerBase` — a second quest manager
- `MelodiaGameMode`, `MelodiaMobileGameMode` — competing game modes
- `MelodiaBattleArena`, `MelodiaCombatStateComponent`, `MelodiaBattleInputComponent` — a second battle stack
- `MelodiaRoguelikeRunSubsystem`, `MelodiaDungeonRunCoordinator`, `MelodiaRoguelikePersistence` — the whole deferred roguelike
- `MelodiaEntitlementSubsystem` — monetization scaffolding
- `MelodiaOutfitComponent` — the deferred wardrobe

Every one is `BlueprintSpawnable` or subsystem-auto-instantiating. **Nothing prevents an agent — or
you at 2am — from dropping `MelodiaSaveGame` into a Blueprint and creating exactly the second
authority every doc in this project forbids.** That is not hypothetical: it is precisely the shape
of the rhythm-combat incident, and the docs did not stop it. Only the absence of the class will.

### What MelodiaCore is genuinely worth keeping

`Plugins/MelodiaCore/Rules/melodia_rules.json` is **not junk — it is a versioned, tested game-design
specification** with 11 domains: `rhythm`, `turn_economy`, `songcraft`, `ultimate`, `toughness`,
`defense`, `flee`, `opening_flow`, `elements`, `modifiers`. It is backed by 285 passing Python
tests and declares itself the single source of truth for tuning numbers.

That file is the most valuable artefact in the plugin. It answers questions the current stack has
not had to answer yet (what is a break? what is an ultimate? how do elements interact?) and it does
so in data, which is portable to stock JRPG content.

**So the correct reading of MelodiaCore is: a design document that was mistakenly executed as a
runtime.** Mine the specification. Delete the runtime.

---

## 2. What OMORI and Infinity Nikki actually teach here

### OMORI — one legible state, deeply integrated

OMORI's battle system runs on a four-emotion cycle (Happy > Angry > Sad > Afraid > Happy) where an
advantaged attack deals 1.5x and shifts the target's state. Emotions last three turns, modify
Attack/Defense/Speed, and are set up via a Follow-Up system so a player can chain state changes
without burning a turn.

Three transferable lessons, in order of importance:

1. **The depth comes from one mechanic, not many.** OMORI ships a full-length RPG on a single
   status triangle. Everything else — skills, items, follow-ups — exists to manipulate that one
   axis. Your `_VERTICAL_SLICE_SCOPE.md` stop rule already says this; OMORI is the proof it works.
2. **The mechanic is the theme.** Emotions are the combat system *and* the game's subject
   (grief, avoidance). Melodia's equivalent is not emotion — it is **musical call-and-response**,
   which you already have in Petal Cadence → Resonance → Skybound Refrain.
3. **Set-up is a decision, not an execution test.** The Follow-Up system rewards *planning*, not
   reflexes. This is the single most important finding for your rhythm question — see §3.2.

**Do not import the emotion wheel.** You would be bolting OMORI's theme onto Melodia's. Import the
structure: one readable state, applied by one action, exploited by another.

### Infinity Nikki — soft gates and the cozy contract

Nikki is built on **soft gates**: "the place was not useless before, you just did not have the
right outfit yet." Traversal abilities (Float, Glide, Shrink) are the progression axis, exploration
is vertical, and the design philosophy is explicitly Believable / Comfortable / Attractive. It is
an open-world platformer with a dress-up layer, *not* a combat RPG.

Transferable:

1. **Gating should read as invitation, not as a wall.** A player who sees an unreachable ledge and
   understands *why* is being taught the progression system. Your minimap markers already do this
   — `RequiredQuestId` collapses a marker rather than showing a lock. Consider showing the
   collapsed state instead of hiding it, so the world advertises its own depth.
2. **You already have Nikki's core verb.** Jump and glide are PIE-verified, and double-tap space
   initiates glide mid-jump. That is the traversal foundation; it needs *level design that asks for
   it*, not more mechanics.
3. **The cozy contract is about failure, not visuals.** Nikki's audience overlap with Melodia's is
   high, and that audience treats a failure state as a cost, not a challenge.

**Scope warning:** Nikki's outfit-ability system is the deferred wardrobe, and `MelodiaOutfitComponent`
already exists in the dead 65. Researching Nikki is exactly the kind of input that reopens that
scope. Take the gating philosophy; leave the wardrobe deferred.

---

## 3. Decisions to make today

### 3.1 What happens to MelodiaCore's 65 dead headers — **decide today**

| Option | Effect |
| --- | --- |
| **A. Move to `Plugins/MelodiaCore/_Reference/` (out of the compiled module)** | Classes cease to exist at runtime; source stays readable. Cheap, reversible, removes the hazard. |
| B. Delete outright | Loses design intent recorded in code. |
| C. Leave as-is | The hazard persists indefinitely. |

**Recommendation: A.** Keep `melodia_rules.json`, its generator, the Python tests, and the five
live headers. Everything else moves out of the build. This is the single highest-value cleanup
available and it makes the "never create a second authority" rule structural rather than
aspirational.

Sequence it *after* today's testing so the working build is proven first.

### 3.2 Is rhythm evaluative or expressive? — **decide today**

This is the decision the whole rhythm lane hangs on, and it has never been stated outright.

`melodia_rules.json` still encodes an evaluative model: `grade_multipliers` from 1.5 down to
**0.55 on a miss** — a 45% damage penalty for bad timing. Decision 009 already stripped that from
the JRPG lane, but the tuning data still says the old thing, and nobody has said what replaces it.

Given OMORI (depth from planning, not execution), Nikki (cozy audience), and your own scope doc
("without making rhythm mandatory"):

**Recommendation: rhythm is expressive, with an upside-only bonus and no miss state.**

- Good timing: extra flourish, VFX, a small stock-legal bonus.
- Bad timing: the normal stock result. **No penalty, ever.**
- The rhythm layer never gates, blocks, or reduces.

Deciding this today unblocks the rhythm profile authoring, because it settles what
`PresentationScalar` is allowed to reach. If you later want an evaluative mode, it becomes a
difficulty option, not the default.

### 3.3 What is *the* combat decision? — **decide today**

The loop needs exactly one interesting choice. Candidates present in your data:

| Candidate | Status | Cost |
| --- | --- | --- |
| **Resonance call-and-response** | Built. Petal Cadence applies, Skybound Refrain exploits. | One Blueprint branch. |
| Toughness / break | Fully specified in `melodia_rules.json`, unimplemented in stock lane | High — new bar, new UI, new enemy data |
| Elements | Specified, unimplemented | Medium — but adds no decision without more skills |

**Recommendation: Resonance is the mechanic.** It is thematically exact (music answering music),
it is the OMORI structure (one state, applied then exploited), it is already stock-native, and it
is one branch from done. Defer toughness and elements until Resonance's decision loop is proven fun
per the stop rule.

Corollary: **make Resonance visible.** An invisible one-turn buff is a mechanic the player never
learns. This is the highest-value UI task in the slice.

### 3.4 What raises social stats? — **decide today**

`SocialStats` now persists, but nothing writes it, so the Persona loop still does not turn.

**Recommendation: Quill dialogue choices only, via allowlisted `melodia:` intents.** Not combat, not
pickups, not exploration. One source keeps it legible and keeps the allowlist as the validation
choke point. Stats then gate quest availability, which gates markers, which lead to encounters.

Concretely: add one `melodia:stat:<id>` intent to `DA_MelodiaIntegrationConfig` and one Quill choice
that raises it. That single wire closes the loop end to end.

### 3.5 Save cadence — **decide today**

Autosave at exactly these boundaries, nowhere else:

- after a completed battle result (post-terminal, pre-control-return)
- on authored map travel
- on quest state change

Never mid-battle (already a gate), never mid-dialogue. Write to a temp file and atomically rename —
a crash during save otherwise destroys the only slot.

---

## 4. Clean finish to the foundational phase

Ordered. Items 1–2 are today; the rest follow.

| # | Item | Gate |
| --- | --- | --- |
| 1 | Test the new build: PIE the route, one battle, hair on `head_x`, full body visible | Your afternoon |
| 2 | Save round trip **including one social stat** | Set → save → full exit → relaunch → load → value intact |
| 3 | Skybound Refrain conditional bonus + make Resonance visible in the battle UI | One command, one buff shown, one payoff, one turn release |
| 4 | Decisions 3.1–3.5 recorded in `_DECISION_LOG.md` | Written down, not just agreed |
| 5 | MelodiaCore `_Reference/` move + rebuild | Build green with 65 headers out |
| 6 | Content promotion out of `Experiments/` | All references resolve |
| 7 | Cook exit 25 | Route packages |
| 8 | Harmonix content pass | One MIDI, one clock, one profile, identical with layer off |

Foundational phase is done when **2, 3, 5, 6, and 7** are green. That is a defensible line: state
persists, the loop has one proven decision, no second authority can be instantiated, content lives
where it ships from, and the thing builds.

---

## Sources

- OMORI battle/emotion system: [OMORI Wiki — Battle System](https://omori.fandom.com/wiki/BATTLE_SYSTEM),
  [OMORI Wiki — Emotions](https://omori.fandom.com/wiki/EMOTIONS), [omori.wiki — Battle system](https://omori.wiki/Battle_system)
- Infinity Nikki design: [Infold level designer interview, AUTOMATON WEST](https://automaton-media.com/en/column/infinity-nikki-level-designer-talks-about-philosophy-behind-large-scale-gameplay-and-map-expansions-in-version-2-0/),
  [Apple Developer — How Infold fashioned an open world](https://developer.apple.com/news/?id=9mgkwjnm),
  [Push Square review](https://www.pushsquare.com/reviews/ps5/infinity-nikki)
