# Project Scope, T3D Pipeline & 0.1% Workflow Plan — 2026-08-06 (evening)

**Written:** 2026-08-06, editor closed for rebuild
**Lens:** persona-lite loop · T3D pipeline health · workflow leverage
**Ground truth:** owner PIE-tests continuously; all "unproven" gate labels in this project mean
*not recorded against the checklist*, **not** *not observed*. That distinction drives §2.

---

## 1. Where the project actually is

### Landed today (verified)

| Change | Evidence |
|---|---|
| **QuillScript UI renders** | Owner-confirmed in PIE. Root cause was the default-slot wrapper canvas, not bindings. |
| Travel allowlist repaired — `L_MelusinaMorning` + `L_Melodia_Dreamstate` added | Independent re-export of `DA_MelodiaIntegrationConfig`; disk 12:57 |
| `WBP_MelodiaQuillDialog` / `…Selection` wrappers → stretch-fill, offsets zeroed | Tree readback; disk 13:00 |
| `WBP_MelodiaQuillChoiceEntry` rebuilt — 3 malformed duplicate `FiligreeDivider`s removed (2 had no slot at all), root `CanvasPanel` → `SizeBox` (Height/MinDesiredHeight 52) | Tree readback; disk 13:05 |
| `BP_ActionsUI` → uniform row (160×48, 16px gaps, matched anchors/alignment) | Tree readback; disk 13:02 |
| KaleidoNave encounter — **direct-match path available** | Bridge matches the **raw ID** via `ActorHasTag` (`MelodiaExternalJRPGBridgeSubsystem.cpp:83`); exactly 1 actor tagged `melodia_smoke_encounter`; stock contract resolves. The `Encounter_<EnemyId>` docstring was stale. |
| PIE smoke on `L_KaleidoNave` | 0 crashes, 188 frames, clean teardown; `ok=false` only from 3 pre-existing `ABP_Melusina_WaterHair` errors |
| Tools pipeline repaired | `bp_regression_checker.py` now uses the `/mcp` JSON-RPC envelope; shared `Tools/mcp_client.py`; `Tools/rebuild_all_dashboards.py` (7 dashboards, Saved + wix mirror) |
| `melodia_ci.yml` removed | Could not pass — Monolith binaries gitignored, no UE 5.8 on `windows-latest`. Snapshot kept at `CompatibilityLabs/Snapshot_2026-08-06/` |

### Blocking, in priority order

1. **SECURITY — `.mcp.json` API keys are in git history** (deepseek-v4 + kimi-k3). File is now untracked, but history cannot be safely scrubbed on this repo. **Rotation is owner-only and cannot be delegated.**
2. **Live Coding is broken** — 5 consecutive identical failures ("Creating patch" → window destroyed). The Monolith enum-pin fix (`PC_Enum` → `PC_Byte`, 3 files) cannot bake through it. **The in-progress rebuild is what clears this.**
3. **Save leg has two hard defects** (both named with file:line in §4).

---

## 2. The 0.1% workflow question — answered against this project

This project already has more MCP surface than almost any solo UE effort in existence
(Monolith ~1328 tools, plus `it-is-unreal`, `ueblueprintmcp`, Ollama, Figma, Blender 5.2).
**More tooling is not the lever.** Three specific gaps are, and all three were demonstrated today.

### Lever 1 — Capture, not testing. (Highest leverage in the project.)

Every gate in `_VERTICAL_SLICE_SCOPE.md` is unchecked while the owner has been PIE-testing
continuously. The loss is not observation; it is that observations never become recorded gate
results, so each session's agents re-derive state from prose that lags reality — which is
exactly how the "docs claim proof that doesn't exist" pathology arises in both directions.

**Build:** `Tools/record_gate.py <gate-id> pass|fail --note "..." [--log <excerpt>]`
Appends a dated, timestamped row to the scope doc's gate table and to a machine-readable
`Saved/gate_ledger.json`. One command, run right after the owner sees a thing work.

This is a ~1 hour build and it is worth more than any new MCP server. It converts the owner's
continuous testing — currently the project's most valuable and least captured asset — into
durable state that every agent reads instead of guessing.

### Lever 2 — Structural linting for UMG.

Today's entire regression was **two mechanically-detectable defect classes**:
- CanvasPanel wrappers left at UMG's default `100×30` slot (Quill Dialog, Selection ×2, ActionsBackground)
- A zero-desired-size root (`CanvasPanel`) on a widget added into a `VerticalBox` (ChoiceEntry)
- plus duplicate widget names and orphaned widgets with no slot (ChoiceEntry ×3)

No compile, fingerprint, or export gate can see any of these. All are trivially visible in
`ui_query get_widget_tree` output.

**Build:** `Tools/ui_lint.py` — flags default-`100×30` slots, duplicate names in one tree,
widgets with no slot, `CanvasPanel`/`Overlay` roots on widgets instantiated into list containers,
zero-width/height images, and `BindWidgetOptional` names present in C++ but absent from the tree.
Reference geometry = `WBP_MainMenu` (root canvas; full-screen elements `min(0,0)/max(1,1)` zero
offsets; positioned elements on a real edge/corner).

This would have found 100% of today's UI defects in seconds, with no editor walkthrough.

### Lever 3 — Reachability linting for Blueprint graphs.

`BP_BattleController` carries **5 dead injected islands (~21 nodes)**, every one with an
unconnected `execute`. Two are headed by `UToolMenus::Get` — an **editor-only class in a runtime
graph**, which is a packaging hazard independent of the rhythm work. The same `UToolMenus::Get`
pattern also appears in `BP_MelodiaJRPGGameInstance` (§4). This is a *class* of artifact, not
two isolated mistakes.

**Build:** `Tools/graph_reachability.py` — walk exec edges backwards from every event entry;
report any exec-capable node with no path to an entry, and any node whose `function_class` is an
editor-only module (`ToolMenus`, `UnrealEd`, `LevelEditor`, …).

### Deliberately *not* recommended

- **More MCP servers.** StraySpark/Autonomix/etc. offer `describe_graph` and T3D injection —
  Monolith already has both (`export_graph`, `build_blueprint_from_spec`). Adding a fourth
  authority over graph mutation contradicts Decision 025 for no new capability.
- **Rebuilding CI now.** It needs a self-hosted runner with UE 5.8 + committed Monolith binaries.
  Until that exists, CI is theatre. The three linters above are the real gate and they run locally.
- **`bRelaxedAllowlistInEditor = true`** (new in `MelodiaIntegrationConfig.h`). Flagging as a
  concern, not blocking: it converts a **loud editor failure into a silent shipping-only failure**.
  The travel allowlist bug I fixed today was loud precisely because there was no bypass. Suggest
  defaulting it `false`, or adding a packaged-build assertion that fails on any
  `DiscoveredUnregisteredIds` entry.

---

## 3. T3D pipeline — verdict and the one missing gate

**The speed claim is real.** One transaction replaces 10–30 node-by-node round-trips, and
`export_asset_text` is the best forensic instrument in the project — the 23-widget live catalog
and today's diagnosis both came from it.

**The correctness debt is also real, and specific.** `build_blueprint_from_spec` wires only the
**injected subgraph's internal** exec pins. Connecting to stock nodes' `then`/`execute` requires a
second manual `connect_pins` pass. That pass was documented as owed and never run — producing the
5 dead islands above, which compile clean and report green on every existing gate.

**Verdict: keep T3D injection, gate it.** The injector must not report success unless every
injected exec-capable node has a path to an event entry, or is explicitly declared pure/data-only.
That is Lever 3 wired into `t3d_blueprint_injector.py` as a post-condition. Without it, T3D
injection is a fast way to manufacture invisible dead code.

**Catalog discipline:** live re-export shows **4/23 migrated** (3 of those font-only via
`F_Melodia_UI`; only `BP_ExploreUI` has a Melodia texture). 22/23 widgets drifted 2×–4× —
owner-confirmed **intentional** Figma-sourced authoring, not regression. Consequence stands: any
bulk operation must target `Saved/T3D/live_catalog/`, never the stale `full_catalog/`.

---

## 4. Scope going forward — the loop, in order

| Leg | State | Next action |
|---|---|---|
| **Rebuild** | In progress | Bakes the enum-pin fix; clears the Live Coding deadlock |
| **Dialogue** | **Working** (owner-confirmed PIE) | Record the gate (Lever 1) |
| **Travel** | Allowlist repaired | One PIE walk: New Game → departure → Dreamstate |
| **Battle** | Encounter direct-match verified; ActionsUI row fixed | 2 rhythm seams remain (below) |
| **Save** | **Two hard defects** | Highest-value remaining work (below) |

### Save leg — the two blocking defects

1. **`BP_MelodiaJRPGGameInstance::OnNewGameStarted` no longer creates the save object.**
   Its exec runs only `RegisterSkill` ×3 and terminates. The stock
   `CreateSaveGameObject → Set jRPGSaveGame_0` chain is now reachable **only** via
   `Array_Add (AddInteractions) → UToolMenus::Get → CreateSaveGameObject`. Consequence: on a cold
   session the first save finds `jRPGSaveGame_0` null → `SyncNarrativeRecordToSave(null)` returns
   false → `SaveGameToSlot(null)` returns false → **no file is written at all.**
   *Fix:* reconnect `OnNewGameStarted` into the stock create chain; delete the stray
   `UToolMenus::Get`.

2. **Slot names do not intersect.** Writers use `"0"/"1"/"2"` (`BP_SavePointBase`, int index) and
   `"MelodiaJRPGSlot0"` (`CreateCanonicalJRPGSlot`, which resets the record first). Readers use
   `"MelodiaJRPGSlot0"` (`WBP_MainMenu`) and `"MelusinaSlot0"` (`WBP_SaveLoadPanel`) — the latter
   is **written by nothing**. *Fix:* unify on one slot string.

Supporting findings: `ConsumedRewardIds` (`MelodiaNarrativeTypes.h:76-77`) is `SaveGame`-flagged and
genuinely persistable — idempotence fails because of 1 and 2, not because the guard is in-memory.
`Btn_Continue`/`Btn_LoadGame` re-enable themselves on `Construct` whenever the slot file exists
(the `False` pin is unwired), so the "deliberately disabled" gate self-defeats once saving works.

### Battle leg — the two rhythm seams

`ShowBattleUI` already creates `WBP_MelodiaRhythmHighway`, adds it to viewport, and pushes the
battle input context; `HideBattleUI` pops it. Remaining:
- **§3a** skill-select → `StartSession(SkillId)`. Seam: cut `UseMP.then → UseSkill.execute` in
  `BP_BattleController` and branch on `sessionId > 0`.
- **§3b** `SubmitRatedInput → HasPendingRequest → ConsumePendingRequest` → stock resolver via the
  `DealDamage.damageMultiplier` pin (two live call sites, both currently at default `1.0`).

Known blockers before §3a/§3b can be *completed* (not started): `OnRhythmComplete` does not exist;
no rhythm Input Action; no `Rhythm` value in `EMelodiaInputContext` (C++ enum → needs the rebuild);
no mapping from stock skill BPs to the 8 snake_case rhythm SkillIds; nothing reads `PatternAsset`
or the chart fields, so the MIDI (imported at `/Game/MelodiaIntegration/MIDI/`, zero referencers)
cannot yet generate a note chart.

### Recommended order

1. Finish the rebuild; confirm the enum-pin fix baked.
2. Fix the two save defects — they are small, precisely located, and gate the whole downstream half.
3. Build `record_gate.py`; back-fill every gate the owner has already observed.
4. Build `ui_lint.py` + `graph_reachability.py`; run both across Melodia + TurnBasedJRPGTemplate.
5. Delete the 5 dead islands in `BP_BattleController` (blocked today only by a `batch_execute`
   param-shape error; the two `UToolMenus::Get` nodes are the packaging-relevant ones).
6. Only then the rhythm seams — they need the rebuild *and* several pieces that don't exist yet.

---

## 5. Owner-only items

1. **Rotate both `.mcp.json` API keys.** Cannot be delegated; keys are in git history permanently.
2. **CI decision:** self-hosted runner with UE 5.8 + committed Monolith binaries, or stay off CI
   and rely on the local linters.
3. **Record the 08-04 battle-widget reparent as intentional** in `_DECISION_LOG.md`, so the 22/23
   widget drift stays classified as authored Figma work rather than regression.
