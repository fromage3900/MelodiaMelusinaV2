# WBP Binding Matrix — 2026-08-14

Scope: `Imports/UI/Specs/` (11 widget specs) cross-referenced against the Blueprint-facing C++
surface in `Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/`,
`Plugins/MelodiaCore/Source/MelodiaCore/` (Token Wallet, Token Catalog, Rhythm HUD, Battle
Session, Save Game, Opening Flow, Roguelike Run, Opening State/Resonance/Dissonance), and
`Source/BS_GodFile/MelodiaIntegration/`. This is a **read-only static-analysis pass** — no
`.uasset` was opened, so "consumes" below means "a spec document or a C++ header/.cpp textually
references the symbol," not "the widget graph in the editor actually calls it." Where that
distinction matters it is called out explicitly.

## Summary

Across the 11 specs and the mechanics called out for today's additions, the matrix below classifies
**23 mechanic rows**: **13 BOUND** (spec explicitly documents the binding to an existing,
correctly-scoped BlueprintCallable/Pure/Assignable symbol), **6 BINDABLE BUT UNBOUND** (the
BP-callable surface exists but no spec or widget references it, or the surface is real but wired to
the wrong/quarantined authority), and **4 NO BACKING FUNCTION** (a spec asks for behavior with no
C++ symbol anywhere in the repo). The four NO BACKING FUNCTION items are all inside `WBP_BlessingBurden`
(the offered-pair getter and `CommitDoorwayChoice`) and `WBP_IntensityWarning` (the reduced-distortion
and reduced-flashing flags, and the first-Rupture gate) — i.e., exactly the items the specs
themselves already flagged as "F1/F2 needed." Today's three new mechanics (`MelodiaTokenCatalog`,
wardrobe gating queries, wallet grant/spend) are all real BlueprintCallable/Pure symbols but **none
of the 11 specs reference any of them** — they are BINDABLE BUT UNBOUND, the highest-risk category
for "wired to nothing" because they compiled today and have no consumer at all, authored or planned.

## Matrix

| Mechanic | C++ symbol + file:line | Consuming widget/spec | Classification |
|---|---|---|---|
| Boss name/toughness | `UMelodiaBattleSession::ActiveEnemyId` (`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.h:209`), `UMelodiaRhythmHUDWidget::SetEnemyBreakGauge` (`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmHUDWidget.h:92`) | `Imports/UI/Specs/WBP_Battle_Command.md:36` | BOUND |
| Enemy vitals / intent / BPM | `SetEnemyVitals` (`MelodiaRhythmHUDWidget.h:76`), `ActiveEnemyIntentName/Damage/BPM` (`MelodiaBattleSession.h:212-219`) | `WBP_Battle_Command.md:37` | BOUND |
| Skill orb (SP) | `SetSkillPoints` (`MelodiaRhythmHUDWidget.h:84`) | `WBP_Battle_Command.md:38` | BOUND |
| Command row (basic/skill/ult/flee + gates) | `SubmitBasicCommand/SubmitSkillCommand/SubmitUltimateCommand/SubmitFleeCommand` + `CanSubmit*Command` (`MelodiaBattleSession.h:82-108`) | `WBP_Battle_Command.md:39` | BOUND |
| ULT gauge | `SetUltimateGauge` (`MelodiaRhythmHUDWidget.h:88`) | `WBP_Battle_Command.md:40`, `WBP_UltCutIn.md` | BOUND |
| Phase banner | `OnBattlePhaseChanged` (`MelodiaBattleSession.h:131`) → `SetBattlePhaseBanner` (`MelodiaRhythmHUDWidget.h:104`) | `WBP_Battle_Command.md:41` | BOUND |
| Battle results (rank/judgments/damage/combo/score) | `GetLastEncounterResult`/`GetLastBattleResults` (`MelodiaBattleSession.h:144,172`), `SessionMaxCombo`/`SessionScore` (`MelodiaBattleSession.h:161-165`) | `WBP_Battle_Results.md` | BOUND |
| Party vitals / SP / zone caption / mini staff | `SetPartyVitals`/`SetSkillPoints` (`MelodiaRhythmHUDWidget.h:80,84`) | `WBP_FieldHUD.md` | BOUND |
| Continue / gate on save | `UMelodiaSaveGameSubsystem::HasSaveGame()` (`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGameSubsystem.h:74`) → `LoadGame()` (`:71`) | `WBP_MainMenu.md` "Continue" row | BOUND — but see caveat below |
| New Game | `UMelodiaOpeningFlowSubsystem::ResetOpening()` (`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOpeningFlowSubsystem.h:70`) | `WBP_MainMenu.md` "New Game" row | BOUND |
| Latest-save card | `GetSaveSlotSummary(0)` (`MelodiaSaveGameSubsystem.h:97`) | `WBP_MainMenu.md` "Latest-save card" row | BOUND — same caveat |
| Save/load slot list + save/load actions | `GetAllSaveSlotSummaries`, `SaveToSlot`, `LoadFromSlot`, `HasSaveInSlot`, `DeleteSlot`, `OnSaveCompleted`, `OnLoadCompleted` (`MelodiaSaveGameSubsystem.h:79-117`) | `WBP_SaveLoad.md` | BOUND — same caveat |
| ULT gauge / fire / cut-in | `SetUltimateGauge` (`MelodiaRhythmHUDWidget.h:88`), `SubmitUltimateCommand` (`MelodiaBattleSession.h:104`), `TriggerSparkleBurst`/`DoPulse` (`MelodiaRhythmHUDWidget.h:72,68`) | `WBP_UltCutIn.md` | BOUND |
| **Offered {BlessingId,BurdenId} pair getter** | none found | `WBP_BlessingBurden.md:36` (tagged "F1 needed" in the spec itself) | **NO BACKING FUNCTION** |
| **`CommitDoorwayChoice(BlessingId, BurdenId)`** | none found; nearest live analog is `UMelodiaRoguelikeRunSubsystem::CommitReward(int32 CandidateIndex)` (`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeRunSubsystem.h:103`), which is index-based reward selection, not a blessing/burden pair with replay recording | `WBP_BlessingBurden.md:37` (tagged "F1 needed") | **NO BACKING FUNCTION** |
| Seed strip (RunSeed/DoorwayID/DissonanceTier) | `RunSeed` exists as `UMelodiaRoguelikeRunSubsystem::RunSeed` (`MelodiaRoguelikeRunSubsystem.h:175`, BlueprintReadOnly via `MelodiaRoguelikeAuthorityTypes.h:78`). `DoorwayID` does not exist anywhere in the repo. `DissonanceTier` exists as `UMelodiaDissonanceComponent::Tier` (`MelodiaOpeningStateComponent.h:60`) but on a different subsystem than the roguelike run authority the spec calls for | `WBP_BlessingBurden.md:38` (tagged "F1 needed") | **NO BACKING FUNCTION** (partial: `RunSeed` alone is bindable, but the combined readout the spec asks for is not) |
| Dissonance tier getter | `UMelodiaDissonanceComponent::Tier` (BlueprintReadOnly, `MelodiaOpeningStateComponent.h:59-60`) — an `ActorComponent`, **not** the `UMelodiaDissonanceSubsystem` the spec names (that class does not exist anywhere in the repo) | `WBP_DissonanceBanner.md:36` (tagged "F3 needed") | BINDABLE BUT UNBOUND (wrong-authority mismatch — see note) |
| Live dissonance update delegate | `UMelodiaDissonanceComponent::OnTierChanged` (`FMelodiaDissonanceTierChanged`, `MelodiaOpeningStateComponent.h:66-67`) — named differently from the spec's `OnDissonanceChanged`, and again lives on a component, not a subsystem | `WBP_DissonanceBanner.md:37` (tagged "F3 needed") | BINDABLE BUT UNBOUND |
| **Motion tier chips / reduced-distortion flag / reduced-flashing flag / first-Rupture gate** | `EMelodiaMotionTier` + `GetMotionTier`/`SetMotionTier` exist (`MelodiaRhythmHUDWidget.h:17-23`, `MelodiaSaveGameSubsystem.h:107-111`); grep for `ReducedDistortion`, `FlashIntensity`, `ReduceFlashing`, `ReduceDistortion`, `AcknowledgeIntensity`, `IntensityWarning` returns **zero matches** anywhere in the repo | `WBP_IntensityWarning.md:36-39` (tagged "F2 needed") | **NO BACKING FUNCTION** (motion tier alone is bindable; the two flags and the transition gate are not) |
| Resonance bond state stepper | `UMelodiaResonanceBondComponent::BondState`/`OnBondStateChanged`/`SetBondState` (`MelodiaOpeningStateComponent.h:39-46`) | `WBP_ResonanceBond.md:36` (tagged "F4 needed") | BINDABLE BUT UNBOUND |
| Bond meter potency (0–1) | none found — `UMelodiaResonanceBondComponent` has no float potency property, only the 4-state `BondState` enum | `WBP_ResonanceBond.md:37` (tagged "F4 needed") | **NO BACKING FUNCTION** |
| Perfect/Break flourish trigger hook | none found on `UMelodiaResonanceBondComponent`; `TriggerSparkleBurst`/`DoPulse` exist generically on the HUD widget (`MelodiaRhythmHUDWidget.h:68-74`) but nothing routes a Perfect/Break combat event into the bond component | `WBP_ResonanceBond.md:38` (tagged "F4 needed") | **NO BACKING FUNCTION** |
| `UMelodiaTokenCatalog::ResolveCost/GetTokenByVariant/GetTokensForElement` | `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenCatalog.h:89,96,106` (all BlueprintPure/Callable) | none — not referenced in any of the 11 specs | BINDABLE BUT UNBOUND |
| Wardrobe gating: `IsFormUnlocked`, `GetEquippedFormId`, `GetActiveCapabilities`, `IsCapabilityActive` | `Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeSubsystem.h:86,90,101,105` | none — no wardrobe/gating WBP spec exists in `Imports/UI/Specs/` at all | BINDABLE BUT UNBOUND |
| Wallet: `TryGrantShards`, `TrySpendShards`, `GetShards`, `OnWalletChanged` | `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenWalletSubsystem.h:71,83,86,111` | none — no wallet/shop WBP spec exists in `Imports/UI/Specs/` | BINDABLE BUT UNBOUND |
| Rhythm highway tuning (`HighwayApproachHeight`, `HighwayLaneRowWidth`, `HighwayHitLineFromBottom`, `HighwayNoteSize`) | `MelodiaRhythmHUDWidget.h:155-168` (all BlueprintReadWrite) | `SetNoteHighwayActive` is called out generically in code but no spec names these four tuning properties individually; `note_highway_dim` appears in `WBP_Battle_Command.md` layout tree only as a visual region, with no binding row | BINDABLE BUT UNBOUND |

## NO BACKING FUNCTION — what actually blocks runtime integration

These are spec-requested behaviors with **no C++ symbol anywhere in the repo** to bind to (not
"exists elsewhere," not "wrong name" — genuinely absent):

1. **Offered {BlessingId, BurdenId} pair getter** (`WBP_BlessingBurden.md:36`, gap F1). No function
   or property returning a pending blessing/burden pair exists on any subsystem, including
   `UMelodiaRoguelikeRunSubsystem`.
2. **`CommitDoorwayChoice(BlessingId, BurdenId)`** (`WBP_BlessingBurden.md:37`, gap F1). The closest
   analog, `UMelodiaRoguelikeRunSubsystem::CommitReward(int32 CandidateIndex)`
   (`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeRunSubsystem.h:102-103`), takes an index
   into a reward list, not a blessing+burden ID pair, and there is no same-seed replay recording tied
   to it.
3. **`DoorwayID` readout** (`WBP_BlessingBurden.md:38`, gap F1). Zero matches for `DoorwayID`
   anywhere in the repo (`RunSeed` alone exists on `UMelodiaRoguelikeRunSubsystem`, but the spec asks
   for the combined `RunSeed`+`DoorwayID`+`DissonanceTier` triplet from one authority).
4. **Reduced-distortion flag, reduced-flashing flag, first-Rupture gate**
   (`WBP_IntensityWarning.md:36-39`, gap F2). Zero matches for `ReducedDistortion`, `FlashIntensity`,
   `ReduceFlashing`, `ReduceDistortion`, `AcknowledgeIntensity`, or `IntensityWarning` in any `.h`/`.cpp`
   in the repo. Only the motion-tier enum/getter/setter exist; the two boolean flags and the
   transition-blocking gate the modal is supposed to enforce do not.
5. **Bond meter potency (0–1)** and **Perfect/Break flourish trigger hook**
   (`WBP_ResonanceBond.md:37-38`, gap F4). `UMelodiaResonanceBondComponent` only exposes the 4-state
   `BondState` enum — no continuous potency value, no flourish-trigger UFUNCTION or delegate tied to
   combat Perfect/Break events.

Additionally flagged as an **authority mismatch** rather than pure absence: `WBP_DissonanceBanner.md`
(gap F3) asks for `UMelodiaDissonanceSubsystem` — that class does not exist. The nearest real
symbol, `UMelodiaDissonanceComponent::Tier` / `OnTierChanged`
(`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOpeningStateComponent.h:54-71`), is a
per-actor `ActorComponent`, not a globally-queryable subsystem, so a HUD banner cannot bind to it
without first locating the actor instance that owns the component — worth surfacing to design/eng
before anyone tries to wire this spec as written.

## Not verified — and why

- **Actual UMG graph bindings.** Every "BOUND" row above is BOUND on the strength of the *spec
  document* stating the binding and the *C++ symbol* existing with a matching signature — not on
  inspection of the compiled `.uasset` Widget Blueprint graph, which this task is barred from
  opening. A spec can claim "ready" and the WBP could still not exist on disk or not have the graph
  wired. Treat every BOUND classification as "verified reachable from the authored plan," not
  "verified reachable at runtime."
- **`WBP_MainMenu` / `WBP_SaveLoad` / `WBP_MenuButton`.** Both specs state `Status: greenfield (no
  WBP on disk)`. I did not search `Content/` for `.uasset` files of these names (out of scope/binary),
  so I cannot confirm whether they have since been authored. The BOUND classification for their C++
  bindings reflects only that the *subsystem* side is real and ready, per the spec's own "ALL READY"
  table — reachability still depends on the WBP existing, which is unverified.
  - Correction while writing this: the same greenfield caveat also applies to the "BOUND — but see
    caveat below" rows for Continue/Latest-save card/SaveLoad; downgrade your confidence accordingly
    if `WBP_MainMenu`/`WBP_SaveLoad` are confirmed absent from `Content/`.
- **`UMelodiaSaveGameSubsystem` quarantine status.** Its `UCLASS(NotBlueprintable, ...)` specifier
  and an in-header comment (`MelodiaSaveGameSubsystem.h:48-50`) mark it as a second, non-shipping save
  authority per an earlier project decision, while `CLAUDE.md`'s "Gameplay authority correction"
  section says the JRPG template — not MelodiaCore — owns save/battle/turn authority. I have not
  reconciled which save subsystem `WBP_SaveLoad`/`WBP_MainMenu` are actually meant to target at
  runtime; if the JRPG template's save system is authoritative, every "BOUND" row citing
  `UMelodiaSaveGameSubsystem` may in fact be wired to a dead parallel system. Flagging rather than
  guessing.
- **Whether any Blueprint (not spec) widget references the three "today" mechanics.** I grepped
  `.h`/`.cpp` only; Blueprint graphs that call `IsFormUnlocked`, `TryGrantShards`, etc. from inside a
  `.uasset` are invisible to text search and cannot be ruled out — but no spec, no C++ caller, and no
  doc reference to them exists either, which is the basis for the BINDABLE BUT UNBOUND call.
- **`.claude/worktrees/magical-williamson-a3534a/`** contains a parallel/duplicate copy of much of
  `Plugins/MelodiaCore/Source/MelodiaCore/`. All grep/citation work above used the primary tree only;
  the worktree copy was excluded as it is not the shipping source tree, but its existence means a
  second, possibly-diverged copy of the roguelike/dissonance code is present in the repo and was not
  audited.
