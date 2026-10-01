---
name: configure-dialogue
description: Full workflow for creating ACF dialogue assets, configuring voices (ElevenLabs TTS), wiring character data assets, and setting up participants. Covers spec-based graph creation, voice config duplication, participant mapping, and runtime verification.
globs: []
alwaysApply: false
---

# Configure Dialogue in ACF Ultimate

This skill covers end-to-end dialogue configuration in the Ascent Combat Framework (ACF) using the Ascent Dialogue System (ADS). It covers **three orthogonal paths** that converge at runtime:

```
Voice Config (DA_VoicesConfig)  ←  maps Character.* tag to ElevenLabs voice
Dialogue Graph (ADS asset)      ←  nodes + edges + participant tags + text
Character Data Asset            ←  ACFDialogueFragment with participant tag + dialogue ref
```

At runtime: Character `ACFDialogueFragment` → ADS asset selects a node → node's `Participant` tag → Voice Config → ElevenLabs voice ID → TTS audio plays.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Voice Config | `UACFVoicesConfig` (DataAsset) | `/Game/Integrations/ATSIntegrations/Dialogue/DA_VoicesConfig` | Maps `Character.*` tags to ElevenLabs voice IDs |
| Dialogue Graph | `UADSDialogue` / `UADSWorldDialogue` | Your content folder | Nodes (lines/responses) + edges + participant bindings |
| Character Data Asset | `UACFCharacterDataAsset` | Your content folder | Holds `ACFDialogueFragment` linking character to dialogue |

> **Never edit sample assets.** Duplicate `DA_VoicesConfig` and sample dialogue assets into your own content folder.

---

## 2 — Duplicate the Voice Config

1. Content Browser → `/Game/Integrations/ATSIntegrations/Dialogue/DA_VoicesConfig`
2. **Duplicate** (Ctrl+D) → save as `Content/YourGame/Dialogue/DA_VoicesConfig`
3. Edit → Project Settings → Plugins → Ascent Dialogue Settings → Voice Generation:
   - **TTS Voice Gen Key** — paste your ElevenLabs API key
   - **Voice Config Data Asset** — assign **your duplicated** `DA_VoicesConfig`
4. Open **your copy** → Details → **Refresh Voices** (fetches ElevenLabs voices)
5. Under **Voice Configs**, add one entry per speaking character:
   - Key: `Character.*` GameplayTag (e.g. `Character.Shopkeeper`)
   - Value → **Selected Voice Name** from dropdown (or **Manual Voice ID**)
6. Save the asset

Every dialogue node that needs TTS audio will look up its `Participant` tag against this map.

---

## 3 — Create a Dialogue Graph (via spec)

Use `ue_dialogue_validate_spec` first to validate, then `ue_dialogue_create_graph` to write.

### Required fields

| Field | Description |
|---|---|
| `asset_path` | Full path, e.g. `/Game/YourGame/Dialogues/DA_ShopkeeperDialogue` |
| `dialogue_class` | `ADSDialogue` (non-world) or `ADSWorldDialogue` (world-space) |
| `dialogue_tag` | Registered GameplayTag for this dialogue (e.g. `Dialogue.Shopkeeper`) |
| `default_participant_tag` | Fallback speaker tag, e.g. `Character.Shopkeeper` |
| `participants` | Array of `{id, gameplay_tag, display_name?, description?, voice_id?, voice_name?}` |
| `nodes` | Array of `{id, kind: "start"|"line"|"response", participant_id, text, position?}` |
| `edges` | Array of `{from: node_id, to: node_id}` |

### Participant rules

- Each `participant_id` must reference a character in your game (usually matching the `Character.*` tag)
- The `gameplay_tag` on each participant maps to the Voice Config's key for TTS
- `start` kind nodes are entry points — they have no incoming edge and exactly one outgoing edge
- `response` kind nodes are player choices (not speaker lines) — they branch, not monologue

### Example spec

```json
{
  "asset_path": "/Game/MyGame/Dialogues/DA_GuardDialogue",
  "dialogue_class": "ADSDialogue",
  "dialogue_tag": "Dialogue.Greeting",
  "default_participant_tag": "Character.Guard",
  "participants": [
    { "id": "guard", "gameplay_tag": "Character.Guard", "display_name": "Guard" },
    { "id": "player", "gameplay_tag": "Character.Player", "display_name": "You" }
  ],
  "nodes": [
    { "id": "start", "kind": "start", "participant_id": "guard", "text": "" },
    { "id": "greeting", "kind": "line", "participant_id": "guard",
      "text": "Halt! Who goes there?", "position": { "x": -400, "y": 0 } },
    { "id": "friendly", "kind": "response", "participant_id": "player",
      "text": "A friend. Let me pass.", "position": { "x": -400, "y": 200 } },
    { "id": "hostile", "kind": "response", "participant_id": "player",
      "text": "None of your business.", "position": { "x": -400, "y": 400 } }
  ],
  "edges": [
    { "from": "start", "to": "greeting" },
    { "from": "greeting", "to": "friendly" },
    { "from": "greeting", "to": "hostile" }
  ]
}
```

### Workflow

1. Build spec with `nodes`, `edges`, `participants`
2. Call `ue_dialogue_validate_spec(spec)` — fix any errors/warnings
3. Call `ue_dialogue_create_graph` with the validated spec

### Audio generation

After the graph is created, configure audio:

1. `ue_dialogue_voice_suggest` to preview voices per participant
2. `ue_dialogue_generate_audio` with `approved: true` after user confirms voice choices

---

## 4 — Wire to a Character Data Asset

The character (NPC or player) must carry an `ACFDialogueFragment` on their `UACFCharacterDataAsset`:

- Open the character's Data Asset (e.g. `DA_NPC_Shopkeeper`)
- Scroll to **Fragments** → **+** → pick `ACFDialogueFragment`
- Set:
  - **Participant Tag** — same `Character.*` tag used in Voice Config AND on dialogue nodes (e.g. `Character.Shopkeeper`)
  - **Dialogues** — reference your dialogue asset(s)
  - **Default Camera Config** — optional (camera framing during dialogue)

The `UACFCharacterInitializerComponent` on the character Blueprint applies this fragment at `BeginPlay`.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `Character.*` tag exists in Project Settings → GameplayTags
- [ ] Voice Config DA has an entry for every `Character.*` tag that speaks
- [ ] Project Settings → Ascent Dialogue Settings → Voice Config DA points to **your duplicated copy**
- [ ] Each dialogue node's `Participant` matches a key in Voice Config
- [ ] Character Data Asset has `ACFDialogueFragment` with matching `Participant Tag`
- [ ] `ue_dialogue_validate_spec` passes for the dialogue graph
- [ ] ElevenLabs TTS Voice Gen Key is set in Project Settings

**Common failures:**

| Symptom | Fix |
|---|---|
| "No voice config" warning | Add the participant's `Character.*` tag to your Voice Config DA |
| Wrong voice plays | Check `Participant` tag on the node matches Voice Config key exactly (case-sensitive) |
| Dialogue doesn't start | Confirm the Character Data Asset has `ACFDialogueFragment` with the dialogue asset assigned |
| TTS generation does nothing | Verify TTS Voice Gen Key in Project Settings; click **Refresh Voices** on your Voice Config |
| Node text empty | Fill the `text` field in the spec before creating the graph |