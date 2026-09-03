# GPT handoff — 2026-08-14 evening (Claude lane)

**Branch:** `feature/repo-lockin-20260813` @ `8d20b8b2`, **pushed**.
**Editor:** open, Live Coding active. Monolith 9316 has been listening since ~15:00.
**Worktree:** heavily dirty with parallel-agent changes. I staged only my own files throughout.

**BUILD STATUS: all C++ is compiled and green** as of the 15:39 closed-editor pass
(`Result: Succeeded`, 31s). Verified in the generated code, not just the exit code:
`FMelodiaResonantForm`, `EMelodiaStyleGrade`, `SlotStyleWeights` (enum-keyed TMap) and
`StockItemClass` all appear in the UHT output. **Exception:** `488b74f6` (style axis →
`EMelodiaSpellElement`) landed *after* that build and is **not compiled**.

---

## 1. Read this first — one commit still needs a closed-editor build

**`488b74f6` only.** It retypes `FMelodiaStyleScore`'s axis from `FName` to
`EMelodiaSpellElement` and deletes `StyleAxisIds` / `FindUndeclaredStyleAxes()`. Reflected
change, so **Live Coding cannot register it** — Ctrl+Alt+F11 will not do.

Everything earlier is compiled (15:39 pass). The risk here is low: it is one enum swap plus two
deletions, in a module that already compiles.

**Also owner-action, one line:** `Tools/wardrobe_draft_lint.py` is written, working, and
**untracked** — `.gitignore:195` ignores `Tools/*`. The pre-commit hook correctly refused my
carve-out because `.gitignore` is a protected file and the owner was away. That file already
has ~30 `!Tools/…` carve-outs, so this is routine, it just needs sign-off:

```
# add under the existing !Tools/ block, then:
SKIP_PROTECTION=1 git commit .gitignore Tools/wardrobe_draft_lint.py Tools/doc_link_check.py
```
`Tools/doc_link_check.py` has been untracked since I wrote it earlier today, same cause.

```
"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development -Project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" -NoUBA -MaxParallelActions=4 -Wait -NoProfiling
```

## 2. What is compiled and green

Editor-target build passed at 13:51, 44s, `Result: Succeeded`. Relinked:
`UnrealEditor-MelodiaCore.dll`, `UnrealEditor-MelodiaWardrobe.dll`, `UnrealEditor-BS_GodFile.dll`.
`MelodiaNPR` has no `Binaries/` — correctly skipped, it is parked.

Live in that binary:

- **Rhythm highway lane fix.** `PaintNoteHighway` ignored `FMelodiaHighwayNote::LaneIndex` and drew
  every note at one `Y = H * 0.65f`. Four lanes rendered as one strip — nothing on screen told the
  player which of Q/W/O/P a note was. Now four columns falling onto the UMG `LaneRow`.
  **`HighwayApproachHeight` is the pacing dial** (larger = more read time at the same BPM).
- **Wardrobe use-after-free.** `MelodiaWardrobeSubsystem.cpp:64` called `.Find()` on the temporary
  returned by `GetNarrativeRecord()` (returns **by value**) and kept the pointer past the full
  expression. Read plausible garbage rather than crashing, which is why it survived.

**Not yet observed in PIE.** The highway fix is compiled but nobody has looked at it. That is the
single highest-value three minutes available: PIE one encounter and confirm four distinct lanes.

## 3. Corrections to prior claims — do not re-derive these

| Claim | Reality |
|---|---|
| Rhythm HUD "shows the WRONG KEYS" (P0) | **False alarm, closed.** Verified live: `LaneLabel_D.Text` = `"Q"`, `LaneLabel_F.Text` = `"W"`. Only widget *names* are stale; `RegisterLaneHit(int32)` binds by index. Asset is at `/Game/Melodia/UI/Rhythm/`, **not** `/Game/MelodiaIntegration/UI/`. |
| `BP_BattleController` untracked | **Was never true.** It and `BP_BattleUI` are tracked via `.gitignore:128-134`. |
| ZenForestTest is "art/greybox, not the route" | **Wrong — mine.** Owner: **ZenForestTest is the authority exploration map.** I reverted my bad change to the NPC placeholder scripts in `889eeb85`. `MelodiaOpeningPortal.h:29`'s `/Game/ZenForestTest` default is **correct**. |
| `SK_Melusina` duplicate authority | Non-issue. One live mesh at `Content/Characters/Melusina/`, already tracked. |

## 4. T3D — postconditions repaired, ledger rows still invalid

`c6ef5f6c`. **Two** successive postconditions were tautological, not one:

1. asserted the **pre-edit** graph in subset mode — trivially true;
2. the 08-14 "fix" exported the **post-edit** graph and asserted it **against itself** — strictly
   cannot fail.

Repaired by deriving expected identities from the **request**: `expected_nodes_from_spec()` parses
top-level `Begin Object ... Name="..."` from the T3D payload (nested pins ignored) and ids from the
`{"nodes":[...]}` shape; `postcondition_satisfied()` requires each to be present afterwards. Fails
closed when the request declares nothing checkable, and when the export is unreadable.

Tests 20 → **30**, three of them explicit regression guards, plus a deliberate-failure check proving
the predicate returns `False` on missing nodes / absent expectations / unreadable exports.

**Still owed:** the `inject` and `blueprint_compile` PASS rows in `Saved/gate_ledger.json` cite the
old invalid run. **They must be re-recorded from a fresh probe.** The fix does not retroactively make
them true, and this has **never run against a production asset**.

## 5. Procedural dungeon — far more complete than the plans assume

The stack splits cleanly, and only half is quarantined:

| Clean (usable now) | Quarantined (Decision 016) |
|---|---|
| `RoguelikeRoomCustomData`, `MelodiaRoguelikeDefinitions`, `MelodiaRoomEntrance`, `MelodiaRoomExit`, `MelodiaFirstDungeonGate` | `MelodiaDungeonRunCoordinator`, `MelodiaRoguelikeRunSubsystem`, `MelodiaRoguelikePersistence` |

`ProceduralDungeon` v3.8.3 already enabled and a private dependency of MelodiaCore.
`MelodiaDungeonRunCoordinator.cpp` is **645 lines** of real, defensive implementation.

**Content exists and was entirely untracked** — now committed in `d43ff677` (26 assets, 1.8 MB):
`BP_RoguelikeDungeonGenerator`, `BP_MelodiaDungeonRunCoordinator`, `BP_MelodiaRoomExit`,
`BP_DungeonFloorManager`, and **22 RoomData assets covering all 8 `ERoguelikeRoomType` values**
(2–3 variants each, including `RD_BlessingAltar` ×2).

**First editor check:** `MelodiaDungeonRunCoordinator.cpp:355` refuses to generate unless the
generator implements `IMelodiaDungeonRecipeConsumer`, and **`BP_RoguelikeDungeonGenerator` is its
only possible implementor**. The C++ prints the exact fix:
*"Open BP_RoguelikeDungeonGenerator > Class Settings > Interfaces, add 'MelodiaDungeonRecipeConsumer', recompile, re-save."*
If it already implements it, you may be one placed actor from generation working.

**Keep persistence quarantined.** `UMelodiaRoguelikeProfileSaveGame.UnlockedCosmeticIds` duplicates
the wardrobe's `OwnedCosmeticIds`; `CompanionBond` duplicates `BondRanks`. `save_load` and
`repeat_consume` were both certified against `FMelodiaNarrativeRecord` as the single seam. Only
`DiscoveredDefinitionIds` is genuinely new — and `BondRanks` (`:132`) / `PhaseIndex` (`:140`) are
already reserved-and-unwritten in the record, designed for exactly this.

**`MelodiaRoomEntrance.cpp` is a 10-line stub** (constructor + `ArrivalTransform` only) while
`MelodiaRoomExit` is 81 real lines. Room *arrival* is where "UI traversal" work actually lands.

**"Burden" does not exist anywhere in the codebase.** Only `Blessing` is modelled. A paired
blessing/burden mechanic is new design, not reactivation.

Full analysis: `Docs/Handoffs/PROCEDURAL_DUNGEON_REACTIVATION_2026-08-14.md`.

## 6. Sir Melodious — why Ctrl party-switch never offers him

**The opening-flow phase ladder dead-ends.** Not an input or party-code problem.

| Transition | Shipping callers | |
|---|---:|---|
| `BeginMorning` | 1 | ok |
| `NotifySirDeparted` | 2 | ok |
| `NotifyDreamstateEntered` | 1 | ok (`MelodiaSirMelodiousIntroActor.cpp:252`) |
| **`NotifyDreamstateCompleted`** | **0** | **the break — tests only** |
| `NotifyZenEncounterVictory` | 1 | unreachable, needs `ZenExploration` |
| `NotifySirRescued` | 3 | always refuses |

Phase stops at `Dreamstate`, never reaches `FirstDungeonUnlocked`, so every `NotifySirRescued()`
refuses and `bSirMelodiousExplorationUnlocked` stays false. Both callers are dead ends anyway —
`MelodiaDungeonRunCoordinator` is quarantined *and* placed in no map.

Likely root cause: `L_Melodia_Dreamstate` was merged into KaleidoNave and deleted, so the beat that
would have signalled completion no longer exists, and no replacement was authored.

**Confirm in one PIE run:** grep the log for `MELODIA_A4`. The refusal line prints the exact phase
integer it stopped at.

**This intersects the dungeon lane** — the coordinator is the author's original rescue trigger, so
reactivating dungeons may be the intended fix. But the ladder break is *upstream*; close it first or
the coordinator refuses for the same reason.

## 7. Equipment / JRPG-template integration (`4af757eb`, unbuilt)

The bridge pattern already existed and is correct: **C++ describes, stock Blueprint owns, bridge
calls in by reflection.** The three "competing" equipment vocabularies are actually layered —
cosmetic (`FMelodiaCosmeticRecord`, zero stats) / bridge (`FMelodiaEquipmentDefinition`, carries
`StockItemAssetId`) / mechanical (stock `BP_EquipmentBase`).

Fixed:

1. `StockEquipmentPaths` was a hardcoded 3-entry `TMap` in the `.cpp` — every new item needed a C++
   edit and rebuild. Added `TSoftClassPtr<UObject> StockItemClass` to the definition so equipment is
   authoring work. Old table kept as fallback, documented to shrink not grow.
2. **`HandleEquipmentRequested` (the reward path) silently dropped equips.** Both
   `FindFunction("AddEquipmentToInventory")` and `FindFunction("WearEquipmentOnUnit")` were bare
   `if (...)` with no else — rename either BP function and the reward is consumed while nothing is
   equipped. `RequestEquip` validated them; this path did not. Now both resolve once, are checked
   together, and a miss is an Error naming which.
3. Both paths duplicated the lookup and could disagree. One shared resolver now.

Also: `UnitId == "melusina"` is hardcoded — **no other party member can equip anything.**
`ResolveUnitClass` now logs the unmapped unit instead of failing indistinguishably. Widening this is
required before party equipment works, and it is design work, not a mechanical fix.

**Open risk:** `FMelodiaEquipmentDefinition` carries Attack/Defense/Magic/Speed bonuses *and* points
at a stock item that likely carries its own. Two sources for one number will drift. Decide whether
the bridge is display-only or authoritative.

## 7b. Resonant Forms — the outfit gating layer (`988774d3`, `124a4d21`, unbuilt)

Added while the editor was open, source-only. This is the long-term gating spine for
outfit-driven abilities, and it applies your Infinity Nikki decision 3 (separate ability
identity from visual presentation) concretely.

**The gap it fills:** the wardrobe had *no unlock concept at all*. `FMelodiaCosmeticRecord` was
four fields (id, slot, rarity, mesh) and `EquipCosmetic` checked ownership only.

**`FMelodiaResonantForm`** — a distinct identity layer, not a cosmetic field:

| Field | Meaning |
|---|---|
| `RequiredFlagIds` | Gate, resolved against `FMelodiaNarrativeRecord::Flags` |
| `GrantedCapabilities` | `EMelodiaFormCapability { Glide, Dash, Swim }` |
| `RestrictedContextIds` | Named suppression contexts (boss arena, set piece) |

Cosmetics carry an optional `ResonantFormId`; `NAME_None` = decorative, which most should stay.

**Why separate:** binding capability to the cosmetic means every recolour, seasonal variant and
rarity tier needs its own gameplay wiring. Many cosmetics can share one `FormId` — the gate reads
the form, the wardrobe reads the mesh.

**`EMelodiaFormCapability` deliberately lists only what `UMelodiaTraversalComponent` implements
today** (glide with stamina, dash, swim). Adding a value without an implementation creates a form
promising what the traversal authority cannot deliver.

**Queries** (`124a4d21`): `IsFormUnlocked`, `GetEquippedFormId`, `GetActiveCapabilities(ContextId)`,
`IsCapabilityActive`. They **answer, they do not decide** — traversal and narrative remain the
authorities, this is the lookup they consult. Nothing writes state; no unlock state is cached
outside the canonical record.

Fails closed twice on purpose: an unknown `FormId` is *not* unlocked (a typo withholds an ability
rather than granting one), and a missing narrative subsystem yields no capabilities rather than all.

`FindCosmeticsWithDanglingForm()` + a `PostLoad` warning surfaces cosmetics naming a missing form —
they equip fine and grant nothing, which is the silent-no-op class this project keeps paying for.

**Sharp edge worth remembering:** `GetNarrativeRecord()` returns **by value**. The first draft of
`GetActiveCapabilities` called the public `IsFormUnlocked()` per equipped slot, copying every map
plus the Quill byte blob each iteration. Fixed by fetching once and passing to a helper. This is the
same by-value hazard that produced the use-after-free in `ffecf278` — treat it as a property of the
API, not a one-off.

**Not wired to traversal yet.** The data and queries exist; `UMelodiaTraversalComponent` does not
consult them. That wiring is the next step and is a deliberate design decision, not a mechanical one.

## 7c. Styling data model (`7e6e185a`, unbuilt)

Third wardrobe layer, grounded in how Infinity Nikki actually scores styling challenges
(per-garment grading per axis, slot weighting, flat bonuses separate from theme match).

  `EMelodiaStyleGrade`  D..SSS — a fixed SCALE, so an enum is correct
  `FMelodiaStyleScore`  `{ AxisId (FName), Grade }` — axis set IS content, so a name
  `StyleScores` on the cosmetic record
  `StyleAxisIds` on the catalog — the declared axis set
  `SlotStyleWeights` on the catalog — per-slot contribution weight

**Axis taxonomy deliberately left empty for authoring.** Melodia's axes should be musical
(resonance, cadence); pre-seeding another game's fashion-genre vocabulary would import their
identity. Slot weighting exists so a challenge is a composition decision — without it, challenges
degrade into "equip the maximum number of items", which is the documented complaint about the
reference game.

Two fail-safe defaults: an absent slot weight is **1.0, not 0.0** (forgetting to weight a slot must
not silently erase it), and an absent axis means "does not express" rather than "grade D".
`FindUndeclaredStyleAxes()` + `PostLoad` warning catches typo'd axes.

**No scoring engine.** Data model and validation only; how a challenge weighs and totals is a
design decision.

## 7e. Content-contract gaps — 40 drafts already exist and outrun the C++ model

`Docs/Reports/WARDROBE_CONTENT_CONTRACT_GAPS_2026-08-14.md`. **Read before importing cosmetics.**

`Imports/Data/Cosmetics/Cos_*.json` holds **40 authored drafts** (schema
`MelodiaCosmetic-draft-v1`) that are richer than the model meant to import them. Three fields
cannot round-trip; importing as-is loses authored data silently.

- **Rarity: 23 of 40 drafts are unrepresentable.** Drafts use `Common / Refined / Couture /
  Grandmaster`; `EMelodiaCosmeticRarity` is `Common / Uncommon / Rare / Epic / Legendary /
  Grandmaster`. `Refined` (14) and `Couture` (9) do not exist in code; `Uncommon`/`Rare`/`Epic`/
  `Legendary` are used by no draft. The enum models a generic MMO ladder, the content models a
  couture one. **Content is 40 assets deep and internally consistent — it is more likely right.**
- **Slot names don't map:** drafts say `dress`, the enum says `Body`. Cheap to fix with an explicit
  mapping table — but **do not renumber `EMelodiaWardrobeSlot`**, it is append-only and serialized
  into save records.
- **Two authored currencies, one implemented.** Every draft prices in `{heart, swirl}`;
  `PurchaseCosmetic` takes a single `int32 GoldenPrice`. This is economy design, not a mapping fix.
  **Do not add a second wallet** — that scaffold is already quarantined.
- `content_pack_id` (`Core` / `Pack_MoonlitSonata` / `Pack_GildedOverture`) is unmodelled, and is
  the natural boundary for the deferred collection layer.

**CORRECTED — the drafts are LLM output, not authored content.**
`deploy/ollama_wardrobe_catalog_daemon.py` generates them with `qwen2.5-coder:7b` at temperature
1.0, `CAP = 40`, sampling from hardcoded `SLOTS`/`RARITY`/`PACKS`/`ELEMENTS` lists. Their
consistency is a script picking from lists, so it confers **no authority** over the C++ model. My
"the content is more likely right" argument about rarity does **not** hold — that is an open design
question for the owner, not something content settled.

`element_mood` was likewise never a new vocabulary. The daemon's docstring names its anchor:
*"Schema anchors: EMelodiaSpellElement palette moods."* `EMelodiaSpellElement` already exists in
`MelodiaCore/MelodiaSpellTypes.h` — seven harmonic elements used by skills, enemies and equippable
keys. **I mistook a copy for a source.** Fixed in `488b74f6`: `FMelodiaStyleScore` now carries
`EMelodiaSpellElement` directly, and `StyleAxisIds` + `FindUndeclaredStyleAxes()` were **deleted**
as a redundant second copy of a fixed enum — the compiler is the validator now.

Side benefit: outfit styling and the weakness system now share one vocabulary.
`FMelodiaElementKeyDefinition` already matches an element for bonus damage, so a Tide-strong
outfit and a Tide harmonic key are relatable rather than coincidentally similar strings.

**Still standing regardless of provenance:** the slot mapping gap (`dress` → `Body`), the currency
gap (`{heart, swirl}` vs one `GoldenTokens`), and `content_pack_id` being unmodelled. No draft names
a Resonant Form, so all 40 are decorative — the correct default.

## 7f. Wardrobe draft linter (written, UNTRACKED — see §1)

`Tools/wardrobe_draft_lint.py`. Turns the content-contract report into a runnable check —
no editor, no build:

```
python Tools/wardrobe_draft_lint.py            # summary, exit 1 if blocking
python Tools/wardrobe_draft_lint.py --verbose  # per-draft detail
python Tools/wardrobe_draft_lint.py --json     # machine-readable
```

Current result: **40 drafts, 23 blocking (rarity: Refined 14, Couture 9), 80 unmodelled-field
notes** (`token_cost`, `content_pack_id`) — reproducing the report exactly.

Two things about it worth preserving if it is ever rewritten:

- **It reads enum values out of the C++ headers** rather than hardcoding them. A hardcoded list
  would be a second copy of a vocabulary that drifts from the enum — the exact defect it reports,
  and the exact mistake I made typing the style axis as an `FName`. A checker that can drift from
  the thing it checks is worthless.
- **`blocking` vs `unmodelled` is a real distinction.** Blocking = data is *silently* lost (an
  unmappable rarity takes the enum default and looks like a deliberate `Common`). Unmodelled = the
  field is visibly dropped. Only blocking sets exit 1. Exit **2** is a separate state for "could not
  read the C++ contract", so a zero finding from a broken parse is never mistaken for clean.

The run independently confirmed two things previously argued only on paper: the `dress → Body`
alias covers every draft (**zero** slot findings), and all seven `element_mood` values are already
in `EMelodiaSpellElement` (**zero** element findings) — which is what `488b74f6` acted on.

## 7g. Progression + gating design spec

`Docs/Plans/MELODIA_PROGRESSION_GATING_DESIGN_2026-08-14.md`. **Spec only, no types.**

Studied how Infinity Nikki structures long-term progression, because "gated setups for
long-term game building" is the problem it solved and Melodia has no answer for. The loop:

```
explore -> collect -> spend in a tree -> unlock an ability outfit
        -> that ability reaches collectibles you could not -> explore further
```

**The load-bearing part is the third acquisition tier** — collectibles that require an ability
you do not yet have. Without those it is a collectathon; with them, every new ability
retroactively reopens the map.

Melodia already has more of this than it looks: `FMelodiaResonantForm` is the ability outfit,
`EMelodiaFormCapability` the gating ability, `RestrictedContextIds` the region restriction,
`content_pack_id` a ready-made Shard grouping. **The genuine gap is a collectible and a tree.**

Two findings worth acting on:

- **`RequiredFlagIds` is binary** — it models "the story reached a point", not "you spent 8 of
  12". A tree needs a *cost* and *prerequisite nodes*. Recommendation: put those on a separate
  progression-node type referencing a form id, **not** on the form — same separation that keeps
  capabilities off cosmetics, for the same reason.
- **The currency question is a trap.** There are already three currency vocabularies in play
  (`GoldenTokens` implemented, `{heart, swirl}` in every draft, region-scoped progression
  currency implied by the reference design) and **one** implementation. `UMelodiaTokenWalletSubsystem`
  is the single authority by Decision 020/029g and the audit called it the cleanest system here;
  the `MelodiaTokenWallet` scaffold is quarantined for trying to be a second. Recommended: one
  collectible type **region-tagged rather than region-typed**, so scoping survives without N
  currencies — and settle `{heart, swirl}` in the same decision, since answering them separately
  guarantees drift.

**The traversal-baseline decision now gates this whole design**, not just the wardrobe: a
forms-only model makes the tree the spine of the game, a baseline-plus model makes it optional
enrichment. Those are different games.

Naming deliberately deferred — naming first is how a system ends up shaped by its metaphor.

## 7h. ~91 tool sources exist only as bytecode — READ THIS ONE

`Docs/Reports/LOST_TOOL_SOURCES_2026-08-14.md`. Found while fixing broken links in the wardrobe
SSOT: two links pointed at tools whose **source no longer exists**, only their `.pyc`.

  `Tools/__pycache__/`          **17** orphaned .pyc, 1 recoverable from git
  `Content/Python/__pycache__/` **75** orphaned .pyc, 0 of 6 sampled recoverable

An orphaned `.pyc` means the script was written and RUN, then deleted without ever being
committed. Most of the `Tools/` set is the **portfolio/stage pipeline** — tier setup, stage
looks, EEVEE batch render, review-queue population, asset passports — and
`MELUSINA_BLENDER_WARDROBE_SSOT.md` still documents it as existing.

**Two distinct causes, and fixing the ignore rule only addresses one:**
`Tools/*` is a blanket ignore with a hand-maintained `!Tools/…` allowlist that nobody updates
(same failure that hid the route levels and the dungeon system). But `Content/Python/` **is**
un-ignored — those 75 were simply never committed. No rule prevented it.

**`Tools/echo_topo.py`** (2026-08-13, 22K) has one commit and matches
`feature/echo-topo-chapter2` — **recoverable, restore before that branch is pruned.** Left alone
because which tip to take it from is an owner call.

**The detail worth pausing on:** `validate_local_doc_links.py` was a doc-link validator, lost to
this rule. I wrote `doc_link_check.py` today because I could not find one — **I rebuilt a tool
that already existed**, and both my new tools are untracked under the same rule right now.

**Do not delete `__pycache__` in those two folders** — it is the only evidence these existed.
`.pyc` is Python 3.13; decompilers lag badly, so do not plan on recovery. `python -m dis` plus
the constant pool will at least reveal what a script targeted.

Recommended fix beyond the one-line carve-out: **invert the `Tools/` rule** — track `Tools/**.py`
and ignore known-noisy patterns instead. An allowlist has now failed ~16 times.

## 7i. Traversal capability wiring — reviewed (another lane, UNCOMMITTED)

A parallel lane wired the traversal gate while this lane was on docs:
`Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalCapabilityProvider.{h,cpp}` (untracked)
plus edits to `MelodiaTraversalComponent`, `MelodiaWardrobeSubsystem`, `MelodiaWardrobeComponent`,
`MelodiaWardrobeGachaSubsystem`, `MelodiaNarrativeTypes.h`. **All uncommitted — I did not touch
any of it**, to avoid the mid-change collision that produced a `cannot lock ref HEAD` failure
earlier today.

**The design is sound and matches the architecture contract**, independently arrived at:

- The **game module owns the registry and the traversal decision**; the registry explicitly
  "never owns progression or movement state". That is the declare-don't-decide rule.
- A **native interface**, deliberately not a Wardrobe dependency — avoids the dependency
  inversion flagged in the C++ audit (`MelodiaWardrobe` already depends on `BS_GodFile`).
- **Multiple providers are rejected** "to avoid split capability truth" — single-authority
  discipline, same reasoning as the wallet.
- `QueryTraversalCapability` **fails closed**: an unrecognised id returns false with
  `OutBlockReason = unknown_capability`.

This also means **the traversal-baseline question has effectively been answered in code** — forms
feed a capability query the traversal component consults. Worth confirming that was intended
rather than incidental, since the progression design in 7g hangs off it.

### One defect worth fixing before it ships

**The capability ids are raw string literals duplicated across two modules:**

```
MelodiaTraversalComponent.cpp:156            TEXT("capability.melodia.glide")
MelodiaWardrobeSubsystem.cpp:334,338,342     TEXT("capability.melodia.glide" / ".dash" / ".swim")
```

Nothing keeps the two sides agreeing. Rename either and `QueryTraversalCapability` falls into its
`unknown_capability` branch, returns false, and **the ability silently stops working** — the block
reason is returned but nothing surfaces it. That is the exact silent-no-op class this project
keeps paying for, and the same shape as the `melodiaNarrativeRecord` reflection lookup and the
`FindFunction("AddEquipmentToInventory")` calls.

Also note only **glide** is queried by the traversal component today; `dash` and `swim` are
mapped on the wardrobe side but have no caller, so they are untested paths.

**Fix (small, decision-free):** declare the ids once as named constants in
`MelodiaTraversalCapabilityProvider.h` — the game module owns the interface, so it should own the
vocabulary — and reference them from both sides. Left to that lane rather than done here because
the files are in flight.

## 7j. The gate tests do not run in CI — ~140 assertions, 0 executed

`Docs/Reports/GATE_TEST_COVERAGE_GAP_2026-08-14.md`. Found sweeping the pure-logic suites for
cross-lane breakage. **The suites are healthy; CI never runs them.**

- `unreal_build.yml:65-68` runs pytest with **`working-directory: Content/Python`** — a
  different directory.
- `echo_gates.yml` runs `Tools/*` gate **scripts**, never `Tools/test_*.py`.

Twelve suites, ~140 assertions, human-invoked only. **`test_t3d_safe_wire.py`'s 41 assertions
are the only thing preventing a silent regression back to the tautological postcondition** that
made two ledger rows meaningless.

**Do not just add `pytest Tools/` — that makes it worse.** The suites are split: 9 script-style
(`main()` + `results.append`), 3 pytest-style. Verified directly:
`python -m pytest Tools/test_t3d_safe_wire.py` → **`collected 0 items — no tests ran`**. Adding
pytest to CI would collect nothing from nine suites and report success — the same
green-light-wired-to-nothing failure hit three times today (the T3D assertion, my own test
harness, and this).

Fix order: **make invocation uniform first** (either wrapper functions so pytest collects the
script suites, or CI calls each explicitly — uniform matters more than which), *then* add the CI
step, and **assert a collected-count floor** so a 0-collection is an error rather than a pass.

**8 of 12 suites are untracked** (`Tools/*` again), plus `validate_mcp_registration.py`. Losing a
test is quieter than losing a tool because nothing stops working. Same carve-out decision as
`wardrobe_draft_lint.py` / `doc_link_check.py`, and the same argument for inverting the rule.

Not a defect, recorded so it does not waste time: `test_mcp_registration.py` throws
`ModuleNotFoundError: No module named 'Tools'` as a plain script but **passes** under pytest.
`test_cute_gn_ornaments.py` needs `bpy` and is Blender-only by design.

**All twelve pass when invoked correctly.** Nothing is failing — it is unguarded.

## 7d. Architecture doc

Full authoring contract, invariants, and the reasoning behind each fail-closed choice:
`Docs/MELODIA_WARDROBE_ARCHITECTURE_2026-08-14.md`. Read that before extending the wardrobe —
it records what breaks if each invariant is violated, and §7 lists what was deliberately NOT built
and why.

## 8. Standing operational facts

- **The self-hosted runner is this machine.** CI `build` fails instantly with *"Unable to build while
  Live Coding is active"* whenever the editor is open. Expected, not a regression.
- **The BuildGraph wrapper is not a reliable full-run executor here** — AutomationTool's
  `LogEventParser` goes 100% CPU on zero new lines. Use a single direct `BuildCookRun` UAT process;
  keep BuildGraph as contract/orchestration only.
- **Last editor crash was a D3D12 descriptor-heap limit during a broad material save**, not C++.
  Avoid large material-save batches.
- `static_gates` = **fail** (two material baseline drifts). Not a completion gate; blocks PR merge
  via `echo_gates.yml`, not `release_tag.yml`.
- Only **2 of 413** stock `TurnBasedJRPGTemplate` assets are tracked. As integration deepens, decide
  whether modified stock assets get tracked **before** editing them.
- `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` **kills the editor** when touched via
  `editor_query run_python`. T3D injection (native C++) is safe there; Python is not.
- Run `bp_live_path.py` step 0 before any injection — duplicate content trees mean injecting into an
  unreachable copy *succeeds silently*.

## 9. Still owed, in priority order

1. **Closed-editor build** for `4af757eb`, `988774d3`, `124a4d21`, `7e6e185a` — all four add
   reflected `UPROPERTY`/`USTRUCT`/`UENUM`/`UFUNCTION`s, so **Live Coding cannot register them**.
   One `Build.bat` pass covers all four.

   **This is now the gating item for the wardrobe lane.** I stopped adding reflected types at
   four commits deliberately: piling on a fifth means a first build surfaces several layers'
   errors at once with no way to attribute them. Everything before `4af757eb` is compiled and
   green. Build first, then extend.
2. **PIE the rhythm highway** — compiled, never observed.
3. **Re-record `inject` / `blueprint_compile`** ledger rows from a fresh T3D probe.
4. **Check `BP_RoguelikeDungeonGenerator` implements `IMelodiaDungeonRecipeConsumer`.**
5. **Grep `MELODIA_A4`** in a PIE log to confirm the Sir ladder break.
6. `.uasset` reference query on `UMelodiaOutfitComponent` — still instantiated at
   `MelodiaCharacterBase.cpp:19` despite being quarantined. **Do not remove on grep evidence alone**;
   Decision 020 exists because content referenced classes a C++ grep called dead.

   **Attempted 2026-08-14 and it does not work — read this before trying again.**
   `project_query find_references` on `/Script/MelodiaCore.MelodiaOutfitComponent` returns
   `{"references":{}}`. That is **not** a valid negative: a control query on
   `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController` returns ~40 depends_on and
   ~45 referenced_by entries, so the action works — it simply does not index native `/Script/`
   classes. `project_query search` for `"MelodiaCharacterBase"` also returns 0, because it matches
   asset names, not class usage.

   **Consequence for Decision 020:** that decision says to resolve these with "Monolith's
   asset-reference query", but that query cannot answer a native-class question. Anyone reading
   D020 will get an empty result and mistake it for proof of deadness — the exact mistake D020 was
   written to prevent. A different method is needed: enumerate Blueprints deriving from
   `AMelodiaCharacterBase` / `AMelodiaSmokeCharacter` (they inherit the component from the
   constructor) and `export_asset_text` each, or use the editor's own Reference Viewer.

   Mitigating context: `BP_Melusina` — the known consumer — was already quarantined in Decision 034,
   and the canonical pawn `BP_MelusinaJRPGCharacter` derives from stock `BP_JRPGCharacterBase`, not
   from `AMelodiaCharacterBase`, so it never had the component.

7. **Corroboration worth keeping:** the same control query shows `/Game/ZenForestTest` (class
   `World`) hard-references `BP_BattleController`. ZenForestTest is a live gameplay map, consistent
   with the owner's statement that it is the authority exploration map — and further confirmation
   that my earlier "art/greybox, not the route" claim was wrong.
7. Rotate the Figma key (public on v2, doc redacted, live key still valid).
