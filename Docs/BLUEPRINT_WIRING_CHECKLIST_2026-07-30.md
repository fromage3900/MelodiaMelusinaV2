# Blueprint Wiring Checklist — 2026-07-30

Everything below is editor work. The C++ is built and linked; these are the connections that
activate it. Ordered so each step is testable before the next.

**Nothing here breaks if left undone.** Every system degrades to current behaviour when unwired.

---

## 1. Hair — DONE, no editor work required (resolved 2026-07-31)

**Nothing to do here. Do not re-add any hair correction.**

This step used to say: tick **Force Attach Correction** and set **Fallback Attach Correction →
Rotation → 45°**. Both properties have been **deleted** from `UMelodiaHairComponent`, and following
those instructions is what pivoted the hair the wrong way for three days.

`UMelodiaHairComponent` now sockets the hair to `head_x` and applies the inverse of that bone's
bind-pose component-space transform, read off the skeleton. The hair mesh is authored in character
space, so parenting it to a bone was stacking `head_x`'s bind transform on geometry that already
accounted for it — that was the ~3 ft offset (head height) and the wrong rotation (the bone's axis
convention). The inverse cancels both exactly. Verified correct in PIE.

**Verify:** PIE, look for `MELUSINA_HAIR_SOCKET bone=head_x bind_cs_loc=... bind_cs_rot=...`.
There is no longer any `MELUSINA_HAIR_CORRECTION` line — if you see one, you are on an old build.

---

## 2. Travel — route everything through the subsystem

### 2a. Allowlist the destination

**Asset:** `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig`

- **Travel Level Ids** → add `/Game/EnvSandbox/Environments/L_KaleidoNave`
- Confirm the other route maps are present too

Travel is allowlisted by design — an unlisted ID is refused and logs
`Melodia intent rejected: RequestTravel(...)`.

### 2b. Tag the arrival PlayerStarts

**Asset:** `/Game/EnvSandbox/Environments/L_KaleidoNave`

KaleidoNave has **four** PlayerStarts. Until one is tagged the engine picks arbitrarily.

- Select the PlayerStart you want arrivals at
- Details → **Player Start Tag** → e.g. `Arrive_FromDreamstate`
  (the `Tags` array also works — both are checked)

Repeat per destination that needs a defined arrival point.

### 2c. Replace direct travel nodes

**Assets:** Dreamstate level Blueprint, and any Blueprint calling `Open Level`

Replace `Open Level` with:

```
Get Melodia Travel Subsystem  →  Travel To
    Level Id   = /Game/EnvSandbox/Environments/L_KaleidoNave
    Spawn Tag  = Arrive_FromDreamstate
```

`Travel To` returns a bool. **Branch on it** — false means the ID was not allowlisted and no travel
happened. Do not assume success.

### 2d. Overlap volumes

**Component:** `MelodiaMapTransitionComponent` on any trigger actor

- **Target Map Name** — as before
- **Target Spawn Tag** — new; set it

No node changes needed, the component already routes through the subsystem.

**Verify:** PIE and travel. Expect:
```
MELODIA_TRAVEL_START    level=... spawn_tag=...
MELODIA_TRAVEL_ARRIVED  level=... spawn_tag=... placed=1
```
`placed=0` means no PlayerStart matched the tag — the log names the tag and how many starts exist.

---

## 3. Input contexts — the QOL fix

The rule: **nothing calls `Set Input Mode` or `Show Mouse Cursor` ever again.** Push on open, pop on
close. That is the whole contract.

For each UI below, add to its **construct/open** path:

```
Get Melodia Input Context Subsystem  →  Push Context
    Context = <see table>
    Owner   = Self
→ store the returned handle in a variable
```

and to its **destruct/close** path:

```
Get Melodia Input Context Subsystem  →  Pop Context (handle variable)
```

| Asset | Context |
| --- | --- |
| Active battle UI widget (`/Game/TurnBasedJRPGTemplate/Blueprints/UI/...`) | `Battle` |
| Quill dialogue widget | `Dialogue` |
| `WBP_MainMenu` | `Menu` |
| Settings panel | `Menu` |
| Save/Load screen | `Menu` |
| Pause menu | `Menu` |

**Remove existing `Set Input Mode` / `bShowMouseCursor` nodes from those graphs** as you go — leaving
them in means two things fighting over input, which is the bug this replaces.

### Then consume the permissions

- **Traversal** (jump/glide/move input): gate on `Is Movement Allowed`
- **Interact key and prompts:** gate on `Is Interaction Allowed`
- **Manual save button:** gate on `Is Saving Allowed` — already enforced in C++, but grey the button
  so the player is not offered something that will refuse

**Verify:** open dialogue → cursor appears, movement dead. Close → cursor gone, movement back.
Travel mid-dialogue → arrive with movement working. Any leak logs:
```
MELODIA_INPUT_LEAK context=Dialogue owner=WBP_... was still held at clear
```

---

## 4. Rhythm — make it actually fire

Two wires. Both required; either alone shows nothing.

### 4a. Start a clock at battle start

The stock battle currently starts no clock, so `Has Musical Time` is false and the rhythm layer
correctly stays silent.

In the battle start path:

```
<battle controller actor>  →  Add Component: Melodia Audio Component   (if absent)
→ Start Battle Clock (BPM = 128)
→ Play BGM Quantized     (optional; plays the placeholder 128 BPM track on the bar)
```

128 matches the existing placeholder BGM. This is the Quartz path — no content authoring. Harmonix
replaces it later without touching any call site, which is why the music clock subsystem exists.

### 4b. Call the grader on command confirm

On the skill/attack confirm node, **after** the stock command is issued:

```
Get Melodia JRPG Presentation Rhythm Component  →  Record Input Now
→ On Presentation Rhythm Result  →  drive VFX / UI flourish
```

**Never route the result into damage, turn order, or the result matrix.** Decision 016: expressive
only, upside only, no miss penalty. The battle UI must never display "MISS".

**Verify:** `melodia.Rhythm.Disable 1` in console — the skill must play **identically, at full
value**. If anything changes, the layer has become authority and that is a Decision 016 violation.

---

## 5. Persona loop closer — one intent, one choice

This is the smallest change with the largest result: it closes the loop end to end.

### 5a. Allowlist a stat

**Asset:** `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig`

- **Social Stat Ids** → add e.g. `melodia_harmony`

Name them musically (Harmony, Tempo, Timbre) and fix the IDs now — they are persisted in the save
record, so renaming later orphans existing saves.

### 5b. Author the choice

In a ZenForest NPC's Quill script, on a dialogue choice:

```
melodia:stat:priestess_first_echo:melodia_harmony:1
```

Format is `melodia:stat:<stableIntentId>:<statId>:<delta>`. The stable authored intent ID is
recorded in `ConsumedIntentIds`, so replaying or reloading the same choice cannot double-pay while
a different authored Harmony choice can still progress the stat.

### 5c. Bind Quill to the ZenForest NPCs

`ZenForestTest.umap` has NPCs tagged `MelodiaQuestNPC` but **no Quillscript assets bound** — that is
why quests fire and dialogue does not. Bind a `UQuillscriptAsset` to each NPC's interaction path,
the same way the Morning Sir interaction already does.

**Verify the whole loop once:**
```
talk to NPC → choice raises the stat → stat gates a quest → quest gates a marker
  → marker leads to the encounter → battle → result → flag → autosave
  → full process restart → reload → stat and flag both survived
```
That single pass proves the entire Persona-lite spine.

---

## Order

1 → 2 → 3 → 5 → 4.

Hair first because it is one minute. Travel next because the route is already changed. Input third
because it is the biggest felt improvement. Persona fifth because it closes the loop. Rhythm last
because it is the only one that is pure polish.

## What I can verify afterwards

> **Corrected 2026-07-31.** This section previously said *"Graph topology I cannot read reliably."*
> **That was wrong**, and it is why the five items above were all scoped as hand-wiring.
>
> Monolith returns complete topology. `blueprint_query("get_graph_data")` gives every node with
> every pin, type, default and `connected_to`; `blueprint_query("export_graph")` additionally gives
> a flat de-duplicated edge list of `{from_node, from_pin, to_node, to_pin}`. Both iterate the live
> `UEdGraph`, so they reflect a write immediately.
>
> The mistaken belief traces to `Plugins/Monolith/Docs/MONOLITH_GUIDE.md`, which warns that
> `project_query("get_asset_details")` serves a **stale indexed snapshot**. That warning is real but
> it is about the asset index, not the graph readers.

Verifiable definitively:

- Config/DataAsset values — allowlist entries, social stat IDs, component defaults
  (`get_cdo_properties`, `get_component_details`)
- Actor properties and tags — e.g. did the PlayerStart get the tag (`mesh.get_actor_properties`)
- **Graph topology** — nodes, pins, defaults and every connection (`export_graph`, `get_graph_data`)
- **Whether a graph changed at all** — `get_graph_fingerprint`, a stable structural hash
- **Whether an expected wiring is present, and a forbidden node absent** —
  `assert_graph_matches` with `spec.forbidden_nodes`

Not verifiable by tooling, still human:

- Whether the result *feels* right — the `melodia.Rhythm.Disable 1` A/B in item 4, "cursor appears
  and movement is dead" in item 3. Logs can be collected; the judgement is yours.

### Which items an agent can now do

| Item | Agent-executable? |
| --- | --- |
| 1. Hair flags | Yes — component property write + readback |
| 2a. Travel allowlist / 5a. Social stat ID | Yes — `set_property_at_path` on the config DataAsset |
| 2b. PlayerStart tags | Yes — actor `Tags` array write + readback |
| 2c. Replace `Open Level` nodes | Yes, with the verification loop below |
| 3. Input contexts (×6 widgets) | Yes, but do **one** end-to-end and PIE-verify before batching the rest |
| 4. Rhythm wires | Yes for the wiring; the Decision 016 A/B stays human |
| 5b. Author the Quill intent | **No** — the stat ID is persisted in save records; naming is a design decision |
| 5c. Bind Quill to ZenForest NPCs | **No** — writes content refs into `ZenForestTest.umap`, which Decision 021 says must be cleaned in-editor first, deliberately, not by script |

### The loop to use for any graph edit

```
export_graph            -> keep it: rollback record AND assertion baseline
get_graph_fingerprint   -> before
<mutate>
compile_blueprint       -> not clean? STOP
assert_graph_matches    -> matched:false? STOP
get_graph_fingerprint   -> after; record both
save_asset
```

One asset per transaction. `set_node_property` reconstructs the node it writes, and
`ReconstructNode` drops links on renamed pins **silently** — read `pins_removed` in its response and
assert against the pre-edit export. That is the whole reason the assertion step is not optional.

Prerequisite: the editor must be running and free of modal dialogs (Monolith cannot answer while a
modal blocks the game thread — grep the log for `MODAL_OPEN`).

## 6. Narrative UI and Cosmic Orrery scope — added 2026-08-01

### 6a. Opening slideshow — authored, compile-clean
- Asset: `/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow`
- Keep native bind names unchanged: `SlideArtwork`, `KickerText`, `TitleText`, `BodyText`, `AdvanceButton`, `SkipButton`.
- `T_Melodia_SoftMG_Parchment` is not a generic panel fill; its source art contains large arches. The current lower third correctly uses `T_ParchmentNoise`.
- Fresh Monolith compile: 0 errors, 0 warnings.
- Visual proof: `Saved/MelodiaOpeningSlideshowPreview_Final.png`.

### 6b. Project-owned Quill presentation — required
- Do not point Quill at `WBP_DialogueBubble`; it is a plain `UserWidget`, not `UDialogBox`.
- Create project-owned subclasses/skins for `UDialogBox`, `USelectionBox`, and `UBackgroundBox`.
- Assign them through each Quill asset's `FScriptSettings` or the authored Quill `Use` command.
- Project widgets may call `AddToViewportAtLayer` to avoid the plugin selection/background viewport-condition defect.
- Never advance the interpreter separately from Quill delegates.

### 6c. Shared keybind/focus/feedback layer — required
- Create CommonInput action rows/controller data for Confirm, Back, Navigate, Interact, Menu, Dialogue Advance, and Skip.
- Replace hard-coded key labels with `CommonActionWidget`/project keybind badges.
- Give every menu/dialogue screen an explicit initial focus and navigation graph.
- Route hover/click/back/denied/quest/Harmony/choice presentation through one semantic feedback router using existing sparkle sprites and `A_UI_Bubble` as the initial confirm sound.

### 6d. Native Cosmic Orrery main menu — implementation slice
- Preserve `AOrreryMainMenuGameMode` save/load/travel/opening authority.
- Preserve `DA_OrreryRegistry` destination and unlock authority.
- Reuse `L_WP_CosmicOrrery`, `SM_Terrain_CosmicOrrery`, `MI_NikkiHero_CosmicOrrery`, and existing PCG style assets where suitable.
- Add one presentation-only 3D Orrery actor/menu camera seam. Selection may rotate/illuminate/emit FX; confirm still executes through the existing menu action.
- Port the website's galaxy/nebula/dust/shooting-star/reduced-motion language natively; do not embed a WebBrowser.

### Verification order
1. Compile/save/read back each WBP.
2. Keyboard-only focus traversal, then mouse, then gamepad glyph switching.
3. Verify each click emits one feedback event and one gameplay/menu action.
4. Verify Quill choice broadcasts exactly one original statement.
5. Verify reduced-motion disables ambient motion without changing input or authority.
6. Verify New/Continue/Load still use the canonical slot and existing travel path.

## 6. Narrative UI and Cosmic Orrery scope — added 2026-08-01

### 6a. Opening slideshow — authored, compile-clean
- Asset: `/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow`.
- Keep native bind names unchanged: `SlideArtwork`, `KickerText`, `TitleText`, `BodyText`, `AdvanceButton`, `SkipButton`.
- `T_Melodia_SoftMG_Parchment` is not a generic panel fill; its source art contains large arches. The current lower third correctly uses `T_ParchmentNoise`.
- Fresh Monolith compile: 0 errors, 0 warnings. Proof: `Saved/MelodiaOpeningSlideshowPreview_Final.png`.

### 6b. Project-owned Quill presentation — required
- Do not point Quill at `WBP_DialogueBubble`; it is a plain `UserWidget`, not `UDialogBox`.
- Create project-owned subclasses/skins for `UDialogBox`, `USelectionBox`, and `UBackgroundBox`.
- Assign them through each Quill asset's `FScriptSettings` or authored Quill `Use` command.
- Project widgets may call `AddToViewportAtLayer` to avoid the plugin selection/background viewport-condition defect.
- Never advance the interpreter separately from Quill delegates.

### 6c. Shared keybind/focus/feedback layer — required
- Create CommonInput action rows/controller data for Confirm, Back, Navigate, Interact, Menu, Dialogue Advance, and Skip.
- Replace hard-coded key labels with `CommonActionWidget`/project keybind badges.
- Give every menu/dialogue screen an explicit initial focus and navigation graph.
- Route hover/click/back/denied/quest/Harmony/choice presentation through one semantic feedback router using existing sparkle sprites and `A_UI_Bubble` as the initial confirm sound.

### 6d. Native Cosmic Orrery main menu — implementation slice
- Preserve `AOrreryMainMenuGameMode` save/load/travel/opening authority and `DA_OrreryRegistry` destination/unlock authority.
- Reuse `L_WP_CosmicOrrery`, `SM_Terrain_CosmicOrrery`, `MI_NikkiHero_CosmicOrrery`, and existing PCG style assets where suitable.
- Add one presentation-only 3D Orrery actor/menu camera seam. Selection may rotate/illuminate/emit FX; confirm still executes through the existing menu action.
- Port the website's galaxy/nebula/dust/shooting-star/reduced-motion language natively; do not embed a WebBrowser.

### Verification order
1. Compile/save/read back each WBP.
2. Test keyboard-only focus traversal, then mouse, then gamepad glyph switching.
3. Verify each click emits one feedback event and one gameplay/menu action.
4. Verify Quill choice broadcasts exactly one original statement.
5. Verify reduced-motion disables ambient motion without changing input or authority.
6. Verify New/Continue/Load still use the canonical slot and existing travel path.
