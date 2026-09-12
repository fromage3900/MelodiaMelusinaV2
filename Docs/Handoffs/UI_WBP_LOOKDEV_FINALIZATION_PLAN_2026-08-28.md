# UI/WBP Lookdev and Final Polish Plan — 2026-08-28

**Authority:** `_AGENT_WORKING_AGREEMENT.md`,
`Docs/Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md`,
`Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`, and
`Docs/ORCHESTRA_CONTRACT_2026-08-20.md`.

**Visual SSOT:** `melodia-design-system/tokens.json` through
`UMelodiaDesignTokens` / `DA_MelodiaDesignTokens`.

**Tonight's outcome:** finish the existing live UI surfaces for the First Dream P0 loop, prove
their runtime identity and content bindings, and capture evidence. This plan does not create a new
HUD, quest UI authority, progression system, or gameplay path.

## 1. Locked product route

The UI must support one integrated route:

```text
Quill dialogue/choice
  -> allowlisted Smoke encounter
  -> stock JRPG command UI + Melodia rhythm presentation
  -> typed victory / defeat / fled / unavailable result
  -> Quill resumes exactly once
  -> quest + reward + completion flag
  -> wardrobe Glide and music-world-key payoffs
  -> canonical save / restart / restored presentation
```

QuillScript remains narrative authority. The TurnBased JRPG template remains battle, result,
inventory, and save authority. `UMelodiaUIBridgeSubsystem` is the only Melodia battle-presentation
writer. Widgets display state; they do not mutate quests, rewards, combat, wardrobe, or saves.

## 2. Current baseline — do not redo

- `WBP_MelodiaQuillDialog` now calls native `Parent: Play`; the owner confirmed the dialogue on
  screen. Do not rebuild or replace this chain.
- `WBP_MelodiaQuillSelection` and `WBP_MelodiaQuillBackground` already fall through to native Play.
- The five canonical narrative assets are assigned to the tracked Quill WBP chain.
- The Smoke encounter now proves all four terminal outcomes and exactly-once Quill restoration.
- Victory proved the ordered authored transaction:
  `melodia:quest:melodia_q_echo_01` -> `melodia:reward:melodia_smoke_reward` ->
  `melodia:flag:melodia_smoke_complete:true`.
- The battle runtime uses stock `BP_BattleUI`; Melodia presentation ownership remains
  `UMelodiaUIBridgeSubsystem`.
- `hud_single_writer` has live identity evidence but remains ledger-open. Treat it as open until
  the final viewport capture and ledger row exist.

## 3. Final WBP system

### 3.1 Quill narrative surface — tracked, final chain

| Asset | Final responsibility | Tonight's acceptance |
|---|---|---|
| `WBP_MelodiaQuillDialog` | Speaker, body, portrait, advance affordance | Parent Play remains first; readable over all five scenes; no raw white/black/default font |
| `WBP_MelodiaQuillSelection` | Choice prompt container | Correct choice-entry class; focus visible; keyboard/gamepad selection readable |
| `WBP_MelodiaQuillChoiceEntry` | One choice row | 52 px minimum target; selected/hover/disabled states use semantic tokens |
| `WBP_MelodiaQuillBackground` | Optional narrative backdrop | No duplicate viewport add; absence of authored `Bg(...)` is not treated as a widget defect |

Lookdev direction: ivory editorial surface, midnight-plum text, champagne-gold rules and focus,
lavender/sakura secondary accents, and restrained astral-night treatment for battle/world-music
moments. Gold/astral glow is reserved for one focal element per surface.

### 3.2 Battle surface — one writer

- Stock `BP_BattleUI` keeps command input, party/targeting, and JRPG state.
- `UMelodiaUIBridgeSubsystem` owns Melodia rhythm/results presentation.
- `WBP_MelodiaRhythmHighway` must visibly show the live Q/W/O/P bindings; D/F/J/K copy is rejected.
- The rhythm surface must show timing feedback without obscuring stock Attack/Skill/Item/Flee
  decisions.
- Victory, defeat, fled, and unavailable must each reach a typed result presentation without a
  second result widget or duplicate transition.
- The unused `melodiaBattleUI` / `MelodiaUI` variables are not used as proof. Their retirement is a
  separate explicit owner decision, not a prerequisite for styling.

### 3.3 Quest and P0 content projection

No generic quest framework is added. The UI projects the canonical narrative record and typed
results already owned by Narrative/JRPG.

| P0 beat | UI obligation | Authority/proof |
|---|---|---|
| Morning / five Quill scenes | Dialogue, portrait, background, choices remain readable and focused | Quill WBP chain + scene assignments |
| Smoke encounter | Battle HUD appears once; stock commands remain usable | `hud_single_writer` |
| Rhythm judgment | Miss and stronger grade are legible; grade changes JRPG result degree | `rhythm_owner`, `rhythm_grade_to_result` |
| Four battle outcomes | One terminal presentation, then Quill resumes/aborts once | `battle_integration_map` |
| Echo quest completion | Quest/reward/flag feedback follows acknowledged commit order; never pre-announces success | `melodia_q_echo_01`, `melodia_smoke_reward`, `melodia_smoke_complete` |
| Resonant outfit / Glide | Preview/equip state, capability gained, and blocked-route affordance agree | `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook` |
| Piano world key | Phrase feedback resolves into one visible route-open state | `music_world_key` |
| Save / Continue | Restored outfit, materials, quest/world state, and UI agree after process restart | canonical JRPG save + Narrative record |

The deferred nine-item economy/song/HUD/dungeon/enemy/quest expansion in
`Docs/P0_TASK_LEDGER.json` stays post-P0 and is not integrated tonight.

## 4. Tonight's execution order

### Gate A — safe editor baseline

1. Confirm exactly one `UnrealEditor` process and one listener on port 9316.
2. Read dirty packages and errored Blueprints. Do not save unrelated Melusina, landscape, PPV,
   Houdini, companion, or worldgen work already present in the worktree.
3. Confirm a current closed-editor build contains the Quill/UI bridge changes. Header or reflected
   property changes require a full build; Live Coding is not accepted for them.
4. Run the scoped `ui_style_audit.py` inventory once the editor answers. Save the JSON action list
   under `Saved/Dashboards/`; do not treat an empty/failed report as evidence.

### Gate B — Quill WBP polish, one asset per transaction

Order: Dialog -> Selection -> ChoiceEntry -> Background.

For each asset:

```text
export_graph + widget-tree read -> stable fingerprints -> mutate via Monolith
-> compile clean -> assert_graph_matches -> fingerprint after
-> save -> re-read live values and dirty-package state
```

Apply only token-backed typography, colors, spacing, focus, brush assignment, and layout fixes.
Do not clean cosmetic dead nodes during this pass unless they directly block the requested surface.

### Gate C — battle/rhythm/results polish

1. Start battle from the live Smoke Quill interpreter; idle PIE is invalid.
2. Identify the actual viewport instances and record stock UI, rhythm HUD, and results widget paths.
3. Prove `UMelodiaUIBridgeSubsystem` is the sole Melodia widget creator/writer.
4. Correct Q/W/O/P legends and final token styling on the actual rhythm surface.
5. Drive real key input for one miss and one stronger grade.
6. Capture the four terminal outcomes and exactly-once Quill continuation.

### Gate D — quest, wardrobe, and music integration

1. Run the current canonical narrative route and confirm quest/reward/flag presentation occurs only
   after the acknowledged transaction.
2. Equip the locked Glide outfit through `UMelodiaWardrobeSubsystem`; prove presentation and
   capability change together.
3. Cross the visible Glide route and capture its UI/animation/VFX response.
4. Complete the existing Piano phrase; prove one typed world result and one visible route change.
5. Save canonically, exit the process, restart, Continue, and verify all projected UI state.

### Gate E — final lookdev proof

Capture live PIE `HighResShot` frames plus machine-readable state reads for:

- each Quill surface and at least one choice state;
- stock battle command UI with one Melodia rhythm surface;
- miss and stronger-grade feedback;
- victory, defeat, fled, and unavailable;
- committed quest/reward/flag feedback;
- outfit before/after, Glide route payoff, and Piano route payoff;
- post-restart restored state.

Run the scoped UI token audit again. No raw `#FFFFFF`, `#000000`, `#FFF2E5`, default-font widgets,
wrong key legends, duplicate viewport writers, or unbound live-result surface may remain on the
captured route.

## 5. Completion contract

Tonight is complete only when:

1. All touched WBPs compile clean, graph assertions match, and live rereads confirm saved values.
2. The active route uses the four tracked Quill WBPs and the one battle-presentation writer.
3. Updated quest/P0 content is visible through canonical authority, not a UI-side mutation path.
4. Evidence envelopes exist beside captures and identify the build, map, widget instances, typed
   results, quest transaction, wardrobe capability, world result, and restart state.
5. `static_gates`, `rhythm_owner`, `hud_single_writer`, `rhythm_grade_to_result`,
   `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, and `music_world_key` are recorded only from
   evidence that actually satisfies their contracts.

If a compile is not clean, a graph assertion is false, the editor has two instances, or an
unrelated dirty package would be saved, stop that transaction and preserve the evidence. Do not
add a compensating widget, flag, alternate quest path, or second UI writer.

## 6. Execution record — 2026-08-28

### Completed

- Confirmed one live editor/Monolith surface before mutation.
- Initial safety read reported zero dirty packages and zero errored Blueprints.
- Captured the scoped Quill style inventory at
  `Saved/Dashboards/ui_tokens_20260828.json`.
- `WBP_MelodiaQuillBackground`: replaced the raw-white image tint with semantic ivory; compile
  clean, exact graph assertion matched, fingerprint remained
  `6b29f79a10156ff757f63351fc8b2b1c3ba349a4`.
- `WBP_MelodiaQuillChoiceEntry`: applied semantic ivory/plum colors, transparent token-derived
  shadow/background values, and the 18 pt body scale; compile clean, exact graph assertion matched,
  fingerprint remained `f0d10909a9fdacd5c4a77824b7145cb427003482`.
- `WBP_MelodiaQuillSelection`: applied semantic ivory/plum colors and the 20 pt prompt scale;
  compile clean, exact graph assertion matched, fingerprint remained
  `6b29f79a10156ff757f63351fc8b2b1c3ba349a4`.
- `WBP_MelodiaQuillDialog`: applied the planned ivory/plum/gold palette and token type sizes; compile
  completed with zero errors and zero warnings, and the topology fingerprint remained
  `d8eae2b348ea8bd02bf2b8b924095bb36eb1a067`.

### HOLD

`WBP_MelodiaQuillDialog` did not clear the mandatory assertion gate. The live graph export contains
`K2Node_CallParentFunction_99` (`Parent: Play`) and the unchanged fingerprint still reports one
`K2Node_CallParentFunction`, but `assert_graph_matches` could not resolve the node's semantic key and
returned `matched:false`. Per the working agreement, no second assertion/fix attempt was made.

Battle/rhythm/results, quest feedback, wardrobe/Glide, Piano world-key, live screenshots, restart
proof, and ledger promotion therefore remain unexecuted. No gate is claimed closed by this pass.

At stop, the editor reported one unrelated dirty external actor under
`/Game/__ExternalActors__/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype/`; it was not
saved or included in this work.
