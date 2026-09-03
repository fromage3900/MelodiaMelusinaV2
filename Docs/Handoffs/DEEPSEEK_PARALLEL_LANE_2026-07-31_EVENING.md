# Handoff: Parallel C++ Lane — for DeepSeek

**Read `_AGENT_WORKING_AGREEMENT.md` first. It is binding.** Do the job asked, ship it, stop. Never
add a mechanism that compensates for a problem — fix the cause. A fix request is not a review
request. If genuinely blocked, say so in a sentence and stop rather than guessing.

## Status update — you're unblocked

Your `MelodiaOllamaValidation.cpp` deferred wiring "until after Claude's batch" — that batch is
done. **Build is green** (exploration-gate + cross-module authority locator + pacing subsystem +
`BP_Melusina` quarantine, one pass, 46/3 regression baseline unchanged, zero new failures).

**One thing to know before you touch that file again:** it had a compile error when the shared
build ran — the async HTTP callback lambda used `Message` without capturing it, which doesn't
compile. Fixed with a one-line capture-list addition (by value, not reference — the callback
outlives the function that queued it, so a reference would dangle). Nothing else about your file
was touched; the design (async HTTP replacing the old blocking, shell-injectable `_popen` call) was
already correct. Decision 035 in `_DECISION_LOG.md` has the full note if you want it.

## Your lane — three items, all pure C++, none need the editor open

Pick in any order. All are headless-verifiable (build + the automation suite) — you do not need
Monolith or a running editor for any of these.

### 1. Finish wiring your own Ollama probe

Now that the build's green: wire the call site in `MelodiaNarrativeSubsystem.cpp`'s
`HandleQuillNotification` to actually invoke `MelodiaOllamaValidation::ValidateMessageAsync`, confirm
the `MELODIA_Ollama_Validation` log line fires. **Still logging-only, still non-gating** — Decision
016/009's authority rules don't change: this must never block or alter the intent path, only log
alongside it. If you need a live PIE run to prove the log line fires, note that as a follow-up rather
than blocking on it — the build+compile proof is sufficient to call the wiring itself done.

### 2. Reroute the remaining 6 orphaned `OpenLevel` calls through `IMelodiaTravelProvider`

`_TASK_QUEUE.md`, P1. Sites: `OrreryMainMenuGameMode.cpp:380,388,397,422,449` (five) and
`MelodiaOpeningPortal.cpp:45` (one). All are direct `UGameplayStatics::OpenLevel(...)` calls in
MelodiaCore-native C++ that predate this evening's cross-module authority locator.

**Follow the exact pattern already proven** in
`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSirMelodiousIntroActor.cpp` — search that file for
`UMelodiaAuthorityLocator::Get` to see the shape: resolve the locator, get the
`IMelodiaTravelProvider`, call `TravelTo(LevelId, SpawnTag)`, and **keep the original direct
`OpenLevel` as a fallback** for when no provider is registered or `TravelTo` returns false (not
allowlisted). Never assume `TravelTo` succeeds — a false return means no travel happened.

Do the six sites as separate, reviewable changes if you can (one file at a time is fine — they're
independent), not one giant diff. `OrreryMainMenuGameMode.cpp`'s five sites may share enough context
to do together if they're clearly the same shape; use judgment.

### 3. Migrate remaining scattered pacing floats to `UMelodiaPacingSubsystem`

`_TASK_QUEUE.md`, P2. Candidates: `MelodiaBattleSession`'s `Pacing` category
(`EnemyTelegraphDuration`/`EnemyAttackAnimDuration`/`EnemyPostImpactDuration`), `MelodiaBattleArena`
hitstop/dolly durations, `MelodiaExplorationActors.TravelDuration`.

**Follow the exact pattern already proven** in the same `MelodiaSirMelodiousIntroActor.cpp` — search
for `UMelodiaPacingSubsystem::Get` and `ResolveDuration`. Resolve once at the point the value is
consumed (not per-`Tick()` if the consumer ticks — see `ResolvedDepartureDurationSeconds` for why:
resolved once in `BeginWindowDeparture()`, read every frame in `Tick()`, never re-resolved mid-arc).
**Never overwrite the authored `EditAnywhere` field** — it's the fallback source when
`ResolveDuration` returns false, which is *every* call right now, since no `UMelodiaPacingProfile`
is authored yet. That's expected, not a bug.

## Before you call anything done

1. **Closed-editor build**, zero errors. If the editor's open (someone else needs it for UI/Blueprint
   work), coordinate rather than force it closed — check with the owner or wait.
2. **Regression gate**: `Automation RunTests Melodia` (the full suite, not `.Integration` — that
   filter hides 3 pre-existing, unrelated failures). Expect **46 pass / 3 fail**
   (`Melodia.NPC.InteractionDefaults`, both `Melodia.Roguelike.Functional.*`) — those three are
   known and not yours to fix. Anything beyond those three is yours to explain or fix.
3. One line per item in your report: what changed, build result, test result. Not a design document.

## Not yours

- Anything in `_TASK_QUEUE.md`'s KaleidoNave/Blueprint-wiring rows — Cline's lane.
- UI/widget work — Gemini's lane.
- Persona-lite remaining lanes / quest-authority investigation — Qwen's lane.
- Authoring the `UMelodiaPacingProfile` DataAsset itself — needs the editor (Monolith
  `create_data_asset`), leave it for an editor-session pass, not this headless lane.
- `BP_Melusina` / pawn unification — done this evening (Decision 034), don't re-touch.
