# Parallel agent lanes — core gameplay loop closeout (2026-08-08, updated 2026-08-09)

> **Superseded for new spawns (2026-08-12 evening):** use
> [`PARALLEL_LANES_2026-08-12.md`](PARALLEL_LANES_2026-08-12.md) +
> [`PARALLEL_SESSIONS_2026-08-12.md`](PARALLEL_SESSIONS_2026-08-12.md).
> Rhythm + Quill are **OWNER LOCKED WORKED** — do not start A1 “observe rhythm” from this file.

## The rule that makes this safe

**The Unreal editor is an exclusive resource. Exactly one lane may hold it at a time.**

On 2026-08-08 three editor instances ran concurrently on this project (PIDs 13900, 17404,
40804, launched within 33 seconds). The result was five crash reports in one hour, assets
changing under an agent mid-edit, and 39 unsaved packages lost to a forced kill. Decision
025 already forbids two MCP surfaces against one graph; this is the same hazard one level
up. (One dead hidden editor instance was killed again 2026-08-09 — check
`Get-Process UnrealEditor` before every editor session.)

## Lane contract (2026-08-09 — Melodia Echo)

Work allocation stays here; authority does not. Per `Docs/ECHO_PIPELINE_2026-08-09.md`,
every lane's deliverable is a **spec + claimed gate**, and nothing is done until the gate
records a ledger row:

1. Author the change as a spec (`.qsc` / T3D / JSON) or a named change.
2. `python Tools/echo_run.py validate-spec <file>` — contract + allowlist check.
3. Run the chain (`echo_run.py run static_gates` with the editor up).
4. `python Tools/echo_run.py record <gate-id> pass|fail --note "..."`.
5. Only then claim the lane done in `_TASK_QUEUE.md`.

A lane handoff may name the gate id it expects to record — that is the new handoff shape.
An agent that reports "done" without a ledger row has reported prose.

Lanes below are grouped by the resource they contend for. Everything in groups B, C and D
can run fully parallel with each other **and** with the one active group-A lane.

| Group | Resource | Concurrency |
|---|---|---|
| **A** | UE editor + Monolith 9316 | **ONE lane at a time. Serialize.** |
| **B** | Blender | parallel; one Blender instance per lane is fine |
| **C** | TouchDesigner | one lane (single TD instance) |
| **D** | Text / spec / no tool | fully parallel, any number |

Before starting a group-A lane, confirm no other agent holds the editor:
`Get-Process UnrealEditor` should show exactly one PID, and port 9316 exactly one listener.

---

## GROUP A — UE editor (serialize these)

### A1. Observe the rhythm loop in PIE
The whole battle chain is verified CONNECTED and has never been seen to PLAY. This blocks
almost everything else, so run it first.

Confirm: beat advances (`UMelodiaMusicClockSubsystem::OnMelodiaBeat`), grade moves
(`UMelodiaRhythmCombatSubsystem::RegisterLaneHit`), `ShowRhythmGrade` renders to
`RhythmGradeText`, lanes light on Q/W/O/P press and **unlight on release** (the OnKeyUp fix
landed today — verify it visibly). A/B damage with rhythm on vs `melodia.Rhythm.Disable 1`
per Decision 024 — **not** full-Perfect vs full-Miss, since Decision 016 sets no miss
penalty and that comparison shows no delta by design. Re-toggle the TouchDesigner Embody
`.tox` first if audio matters.
Record two damage numbers. That is the deliverable.

### A2. Resolve the duplicate content trees
Two ambiguity traps in the battle chain:
- `BP_BattleUI` exists at `/Game/TurnBasedJRPGTemplate/...` (LIVE) and
  `/Game/_ThirdParty/TurnBasedJRPGTemplate/...` (orphan island with its own BP_BattleController)
- `Content/MelodiaIntegration/Content_MelodiaIntegration/` — 33 assets, a stale mirror of
  the live tree, untracked in git, dating to 2026-07-26. It still contains a copy of
  `BP_MelodiaBattleUI` carrying the ten shadowed events that were fixed in the live copy.

Verify each with `python Tools/bp_live_path.py <asset>` first. `ORPHAN` means *prove it
before deleting*, never *safe to delete* — the tool cannot see `TSoftObjectPtr` (Decision
049) or `.umap` actor references (Decisions 020/029d/037a). The mirror is untracked, so
deletion is unrecoverable. **Get owner sign-off before deleting anything.**

### A3. Apply the UI token pass
`python Tools/ui_style_audit.py` inventories 137 widget blueprints / 898 styled widgets and
found 59 distinct font face/size pairs and 90 raw colours collapsing to 46 tokens. Apply
the consolidation with `ui_query.batch_style` / `set_font` / `set_brush`.
Start with the near-miss clusters, which are pure win: six near-identical darks around
`#110C14`, three greys around `#D1D1D1`. Two cyans sit at HDR gain 214x and 255x —
`hdr(0,235,255)` and `hdr(0,214,158)` — decide whether that is intentional glow before
touching them.
Depends on: D1 (token spec) if you want a designed palette rather than the audited one.

### A4. Wire the Sir rescue trigger
Everything downstream of `NotifySirRescued()` is complete and correct: phase transition →
`OnPhaseChanged` → `MelodiaJRPGPartyBootstrapSubsystem::HandleOpeningPhaseChanged` → adds
`BP_SirMelodiousPlayerUnit` via the stock `AddPlayerUnit` contract → and
`SetSirMelodiousExplorationUnlocked(true)`, which also unlocks the flight pawn.

The only caller is dungeon-run completion, and no map places `AMelodiaDungeonRunCoordinator`,
so it never fires in the slice. Hook it to the MorningIntro Quill flag
`melodia:flag:melodia_smoke_complete` instead. **Check the precondition first**: the
transition is strict and returns false unless Phase is already `FirstDungeonUnlocked`.
Needs C++ in MelodiaCore + game module → closed-editor rebuild. Batch with A5.

### A5. Damage progression smoothing
Owner reports damage progression needs to be smoother. **Do not guess at the curve** —
get the recorded contact sheet first. Relevant seams: `CalculateDamage` and `DealDamage`
(functions on `BP_BattleController`), and the rhythm scalar arriving via
`GetPendingDamageMultiplier()` polled at damage-notify time.
Do not add a compensating multiplier to cancel out a bad curve — fix the curve.
Batch any C++ with A4 into one rebuild window.

### A6. Skybound Refrain conditional bonus
From `_VERTICAL_SLICE_SCOPE.md` co-op gates: wire Skybound Refrain's bonus when Resonance
is present on the target. `BP_MelusinaPetalCadence`, `BP_SirSkyboundRefrain` and
`BP_Resonance` all exist and are mapped. Then PIE-test: Petal Cadence → Resonance applied
→ Skybound Refrain → bonus damage → turn release, and Sir without Resonance for the
normal-damage control.

---

## GROUP B — Blender (parallel)

> Blender 5.2 only. 5.1 is not installed — that directory is empty. Docs targeting 5.1
> describe steps that cannot run.

### B1. Instrument meshes
Author the instrument set the rhythm/battle presentation needs. Deliver as FBX into
`Exports/`, then hand to a group-A lane for import — **do not import yourself**, an FBX
import dialog is modal and will block the editor's game thread for whoever holds it.
That exact modal cost this project a forced editor kill today.

### B2. Sir Melodious battle mesh + portrait
Open gate in `_VERTICAL_SLICE_SCOPE.md`: "Author Sir's battle mesh, portrait, and
`skillAnimation` entry for Skybound Refrain." The rigged mesh exists at
`Content/Melodia/Characters/SirMelodious/Rigged/SK_SirMelodious_Rigged`. Needed: the
battle-ready variant, a portrait, and the animation entry.

### B3. Melusina combat body
Open gate: "Verify Melusina's full body is visible in combat (not just hair)." The hair
fix landed 2026-07-31 and is verified (`MELUSINA_HAIR_SOCKET`) — **do not re-apply the hair
correction properties**. This is about the body mesh visibility during battle, which the
combat Blueprint hides/redirects.
Long-term item, out of scope for this lane: re-export hair against the body armature with
matching bone names (body 465 bones, hair 148, currently zero shared names, which is why
Copy Pose From Mesh cannot work).

---

## GROUP C — TouchDesigner (one lane)

### C1. TD integration + Envoy persistence
Project at `_TouchDesigner/grandmaster_melodia/`, exported to diffable `.tdn`:
`networks/osc.tdn` (14 ops), `audio.tdn` (35), `postfx.tdn` (35), `project1_full.tdn`.

The Embody `.tox` and Envoy must be re-toggled after every TD restart before the 9870
surface or the TD→UE audio leg works. **Make that state persistent or self-restoring**, or
state plainly that TD cannot do it. Then give a verification procedure that proves data is
actually flowing rather than that the ops exist and look connected — "it looks wired" is
this project's most expensive failure mode.

UE side sends BPM via `UMelodiaAudioReactivePresentationSubsystem` (`LastKnownBPM`,
default 120) until Harmonix publishes real tempo. OSC server: `Content/Python/osc_server.py`.
Validator: `deploy/touchdesigner_validator.py`.
The `.toe` is irreplaceable — call out any destructive step with a backup instruction first.

---

## GROUP D — text / spec / no tool contention (fully parallel)

### D1. UI token spec
Turn the audit output (`Saved/Dashboards/ui_style.txt` and `ui_tokens.json`) into a designed
palette and type scale, rather than merely deduplicating what exists. 59 font pairs is drift,
not a scale — propose 5-7 sizes with intent. Deliver concrete values: hex, sizes, weights,
brush margins, padding, animation durations in seconds.
Constraints: lane readability during play beats prettiness; the four lanes must be
distinguishable without relying on hue alone; stock UMG brushes and the Kenney/Soft-MG kit
only. Feeds A3.

### D2. Grief hook — story finalization
Finalize the grief throughline as Quillscript. The narrative spine is
`MelodiaNarrativeSubsystem` driving `AQuillscriptInterpreter` / `UQuillscriptAsset`, with
dialogue rewards, social stats (Harmony/Tempo/Timbre) and bonds already wired.
The compiled MorningIntro script is the departure authority:
`melodia:battle:melodia_smoke_encounter` → typed result →
`melodia:flag:melodia_smoke_complete` → `$ End`.
Intent verbs available: battle, quest, flag, travel, reward, stat, item.
**Any new id must be allowlisted** in `DA_MelodiaIntegrationConfig` or it is silently
rejected — `QuestIds`, `DialogueRewardIds`, `NarrativeFlagIds`, `SocialStatIds`. An
unallowlisted id fails closed with no error, which is how two of three authored quests
became unreachable once already.
Deliver script text plus the exact allowlist entries required.

### D3. Niagara + MPC rhythm FX spec
`MPC_Melodia_Palette` already publishes, every tick: `GlobalReactivity`, `Bass`, `Mid`,
`Treble`, `BeatPhase`, `BeatPulse`, `RhythmPulse`. `BeatPulse` = sin²(BeatPhase·π), the
music's pulse. `RhythmPulse` = the player's hit, set by `PulseImpact(Strength)` on lane
press and decaying linearly at 3.5/sec, so a 1.0 hit is gone in ~285 ms. Design the
envelope around that tail; the decay is fixed in C++.
**Open question to answer, not assume:** `PulseImpact` takes no lane index, so per-lane FX
either needs a Blueprint-pushed user parameter or a C++ signature change. Say which.
Presentation only — nothing may affect gameplay state, damage, timing or input.
Budget for 4 hits/second sustained; give particle counts and what to cut first.

### D4. Roguelike reintroduction plan
The dungeon system is whole, not gutted: quarantine is 13 headers carrying
`UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)`. `UMelodiaRoguelikeRunSubsystem` has
run lifecycle, structured + endless modes, seeded stage recipes, Dissonance, Heart/Swirl
tokens, archetypes, and `ExportSnapshot`/`ImportSnapshot`. Blessings/burdens exist as
`EMelodiaRunRewardType` (SongPower / Recovery / SkillPointRegen / DissonantBargain with
`DissonanceCost`).
The gap: `MelodiaDungeonRunCoordinator` listens to `UMelodiaBattleSession` (MelodiaCore's
own), but the game uses the stock TurnBasedJRPG controller. Four seams to spec —
run→battle via `StartTaggedJRPGBattle`, battle→run via `RecordEncounterResult`,
rewards→damage (reuse the proven `GetPendingDamageMultiplier` seam), and a reward-choice UI.
Reintroducing this **reverses Decision 016 and the "Explicitly deferred" line in
`_VERTICAL_SLICE_SCOPE.md`** — the plan must include the decision-log entry, not assume it.
Gate on A1 passing first: all four seams terminate in the stock battle loop.

### D5. Save chain spec
Foundation gates, all currently open: canonical `BP_JRPGSaveGame` slot created and loaded
across a full process restart; one narrative flag and one reward restoring without
duplication; loading the JRPG slot with Quill unavailable while preserving JRPG-owned
state; routing a missing script/checkpoint to an authored safe location without erasing
valid state; interpreter invalidation during terminal-result broadcast retaining a
recoverable pending result; manual saving stays unavailable during a narrative battle.
Schema is at **v3** — treat any schema change as out of scope and say so if one is implied.

### D6. Packaged launch triage
"Package the proven three-map route" is done (`Saved/StagedBuilds_20260730/`, 2.1 GB,
`Success - 0 error(s)`). **Launching it outside the editor is still open.** Diagnose from
the packaged logs; do not re-package first. Cook exit 25 was previously traced to
`PCGEx_PathTesselate.uasset` (invalid name at index 411, Decision 022) — check whether that
class of fault recurs.

---

## Standing rules for every lane

- **Monolith only** for Blueprint graph work. `ueblueprintmcp` is deliberately disabled
  (Decision 027) and needs a closed-editor build; it was found running today and should not
  be. Never two MCP surfaces against one graph (Decision 025).
- **Verify by re-reading.** `success: true` means nothing threw. `save_asset` returned
  inconclusive at least once today.
- **A fingerprint covers one graph.** Ask which *other* graph encodes the same fact — the
  `OnKeyDown`/`OnKeyUp` split cost a full session.
- **Semantic identity, never node instance names** (Decision 024). Address by id, verify by
  `custom_name` / `function` / class before mutating.
- **Search both forms.** `UnitHasEnoughMP` vs `Unit Has Enough MP` — a substring search on
  the identifier form missed a live macro instance and produced a confidently wrong triage.
- **`MODAL_OPEN` in the log** means a modal dialog is blocking the game thread, not that
  the editor has hung. Killing it there costs every unsaved package for nothing.
- **A doc's date is when it was written, not when it was last true.** Run
  `python Tools/project_state.py --view staleness`; 3 of 4 tracked docs are currently
  behind their subject.
