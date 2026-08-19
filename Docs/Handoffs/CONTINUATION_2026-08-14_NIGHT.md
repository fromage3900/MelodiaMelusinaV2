# Continuation handoff — cold start for a fresh session (2026-08-14 night)

Written so a new session resumes without re-deriving anything. Read this, then
`_TASK_QUEUE.md`. Branch `feature/repo-lockin-20260813`, all Claude-lane work pushed.

**Loop contract:** 15-minute loop, prioritising long-term C++ stability, Melodia wardrobe,
and Chapter 1. Commits/pushes approved when healthy. Codex + GPT drive editor/Monolith;
this lane is **back end only** — C++, Python, docs, ledger. Never the editor, never
Monolith writes, never another lane's uncommitted files.

---

## 1. The one blocking action

**A closed-editor build is owed and now covers four things:**

| Commit | Why it needs a real build |
|---|---|
| `1fdb5286` | `UMelodiaTokenCatalog` — a new `UCLASS`; Live Coding cannot register it |
| `7bc11139` | New `UFUNCTION` (`PurchaseCosmeticWithShards`) + inline `FName` constants |

```
"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development -Project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" -NoUBA -MaxParallelActions=4 -Wait -NoProfiling
```

~30s warm. Check `MelodiaCore.dll` timestamp moves past 19:30. **Everything before
`1fdb5286` is compiled and green.**

## 2. The finding that matters most tonight

`Docs/Reports/WBP_BINDING_MATRIX_2026-08-14.md` — **13 bound, 6 bindable-but-unbound,
4 no-backing-function.**

**All three mechanics built today are BINDABLE BUT UNBOUND.** `UMelodiaTokenCatalog`,
the wardrobe gating queries, and the wallet shard API all compile with clean BP surfaces
and **no spec in `Imports/UI/Specs/` references any of them — there is no wardrobe, shop
or wallet WBP spec at all.**

That is this project's signature defect at the UI layer: a mechanic that is *callable*
and never *called*. The C++ is not the gap; the widget spec is.

**4 with no backing function** (all self-flagged F1/F2/F4 in their specs):
- `WBP_BlessingBurden` — no offered-pair getter, no `CommitDoorwayChoice`, `DoorwayID`
  appears nowhere in the repo
- `WBP_IntensityWarning` — no reduced-distortion flag, reduced-flashing flag, or
  first-Rupture gate (zero-hit grep)
- `WBP_ResonanceBond` — no bond-meter potency float, no Perfect/Break flourish hook

**Unresolved authority conflict flagged, not guessed:** the menu specs target
`UMelodiaSaveGameSubsystem`, which is `NotBlueprintable` and marked in its own header as a
**quarantined second save authority**, while `CLAUDE.md` names the JRPG template as save
authority. Do not wire menus to it until that is settled.

## 3. What landed this session (Claude lane)

**Compiled and verified earlier today:** rhythm highway lane fix (four columns, not one
strip), wardrobe use-after-free, equipment `StockItemClass` seam, Resonant Forms + gating
queries, styling model, and two UHT errors in the traversal capability registry that had
**never compiled**.

**Pushed, awaiting the build:** `MelodiaTokenCatalog`, `PurchaseCosmeticWithShards`,
capability-id constants.

**Burden recovery (`e8b40004`) — the owner was right, a converter lost it.**
`extend_roguelike_blessings.py` omitted `curse`/`curse_effect` when copying room mods, which
is why 26 blessings had 0 burdens. 21 authored pairs were in `DT_MelodySlime_RoomMods.json`
the whole time. Recovered to `DT_Burdens.json` via
`Tools/extract_burdens_from_roommods.py`: **21 rows, 17 gameplay-ready, 4 flagged**. No
magnitude was guessed. The four flagged are the ones a guess would have corrupted —
including `ModMelodious`, whose "curse" *reduces damage taken* and is therefore a benefit.

**`Tools/*` ignore inverted** — 61 carve-outs replaced; 233 files now tracked. That rule had
silently lost ~91 tool sources.

## 4. Answers to the open questions

**Persona-lite loop — what remains.** The loop itself is closed: all four gates PASS.
What is missing is *felt* quality, not mechanism — the rhythm highway has been compiled
since 13:51 and **has never once been looked at in PIE**. `HighwayApproachHeight` is the
pacing dial. `MELODIA_RHYTHM session=` has never appeared in any log; its absence is the
single most informative thing to check.

**Missing JRPG cores.** None missing — the stock template is the mechanical authority and
is complete. The gaps are *bridges*, not cores: `StockEquipmentPaths` is a hardcoded 3-entry
map in a `.cpp` so every new item needs a rebuild; `FindFunction("AddEquipmentToInventory")`
and `("WearEquipmentOnUnit")` are string-reflection calls with **no else branch**, so a
renamed BP function disables equipping silently; and `UnitId == TEXT("melusina")` is
hardcoded, so no other party member can equip anything.

**Making the C++ stable and easier to understand.** Four recurring hazards, in order of
how often they have actually bitten:

1. **`GetNarrativeRecord()` returns by value.** Caused a use-after-free and a per-slot
   full-record copy. Anything calling it in a loop is suspect — fetch once, bind to a named
   `const&`.
2. **String-keyed lookups with no failure branch.** The `melodiaNarrativeRecord` reflection
   lookup (3 call sites), the two equipment `FindFunction` calls, and the capability ids
   (fixed tonight). The fix pattern is always the same: declare the name once in the module
   that owns the concept, and make the miss loud.
3. **One vocabulary, many copies.** `EMelodiaSpellElement` now correctly spans skills, wallet
   shards and cosmetic styling — that is the model. Every drift bug this session came from a
   second copy of a list.
4. **Quarantined-but-live classes.** 13 classes carry `QUARANTINED LANE` guards that block
   *new* Blueprints but leave every `BlueprintCallable` reachable from existing graphs. Dead
   C++ with a live BP surface is the worst combination for cleanup.

## 5. Immediate next actions

1. **Build** (§1) — blocks everything.
2. **Author a wardrobe/wallet WBP spec** in `Imports/UI/Specs/` so today's mechanics stop
   being unreachable. This is the highest-value item in §2 and it is *spec* work, not C++.
3. **PIE one encounter** — observe the highway; capture `MELODIA_RHYTHM session=`,
   `MELODIA_A4`, `MELODIA_TOKENS`.
4. **`package_launch` montage repoint** — `AM_Melusina_Spell_Shoot`/`_Sword_Attack` point at
   `Animations/Quaternius_Retargeted/CAS_Q_Armature_*`; assets are at
   `Animations/QuaterniusRetargeted/A_Q_Melusina_*`. **A repoint, not a re-retarget.**
5. Re-record `inject`/`blueprint_compile` — they read PASS but cite the tautological run.

## 6. Owner decisions still open

- **Rarity ladder** — `Refined`/`Couture` (23 of 40 drafts) vs the generic enum. Neither side
  has authority; the drafts are LLM output.
- **Burden currency** — recommend `TrySpendShards` on the one Melody Token wallet.
  `HeartMelodyTokens` lives on the quarantined run subsystem and would be a second authority.
- **The 4 flagged burdens** — magnitudes must be authored, not inferred.
- **Save authority for menus** (§2).

## 7. Standing hazards

`Content/TurnBasedJRPGTemplate/Blueprints/Skills/` kills the editor via
`editor_query run_python` (T3D native injection is safe there). `bp_live_path.py` step 0
before any injection — duplicate content trees mean injecting into an unreachable copy
*succeeds silently*. `.gitignore` and `Config/*.ini` are protected. **A gate closes only when
`record_gate.py` writes a row backed by a real run.**
