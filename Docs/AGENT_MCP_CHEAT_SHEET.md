# Agent MCP Cheat Sheet — BS_GodFile Melodia Integration

> **Purpose:** One-page reference so any agent can use Monolith/MCP on this project without re-discovering paths, constraints, and safe patterns every session.
> **Last updated:** 2026-08-18
> **Monolith port:** 127.0.0.1:9316 (fixed by config)

---

## 1. Health Check (run first)

```bash
# One-liner: is Monolith alive and is the editor the only instance?
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:9316/').read().decode())"
Get-Process UnrealEditor | Select-Object Id, StartTime
```

Monolith silent? Check for `MODAL_OPEN` in the editor log before killing — it may be an FBX import dialog, not a hang.

---

## 2. Key Asset Paths (canonical)

| Role | Path |
|---|---|
| Integration GameMode (now configured for HUD) | `/Game/Melodia/_PROJECT/BP_MelodiaGameMode` |
| Integration PlayerController | `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGController_Config` |
| Integration Pawn (explore) | `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` |
| Integration Map | `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` |
| Battle presentation unit | `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` |
| Explore character | `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` |
| Battle HUD widget | `/Game/Melodia/UI/WBP_Battle_Rhythm` |
| Battle results widget | `/Game/Melodia/UI/WBP_Battle_Results` |
| Rhythm highway widget | `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway` |
| Quill dialog | `/Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog` |
| Allowlist config | `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig` |
| SaveGame | `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGSaveGame` |

---

## 3. Essential Monolith Commands

### Editor state
```json
{ "action": "get_td_status" }
{ "action": "list_dirty_packages" }
{ "action": "list_errored_blueprints" }
```

### Blueprint inspection (safe — C++ path, no Python glue)
```json
{ "action": "get_cdo_properties", "params": { "asset_path": "<path>" } }
{ "action": "get_components", "params": { "asset_path": "<path>" } }
{ "action": "get_graph_data", "params": { "asset_path": "<path>" } }
{ "action": "get_variables", "params": { "asset_path": "<path>" } }
{ "action": "get_blueprint_info", "params": { "asset_path": "<path>" } }
```

### Blueprint mutation
```json
{ "action": "set_cdo_property", "params": { "asset_path": "<path>", "property_name": "<name>", "value": "<value>" } }
{ "action": "set_component_property", "params": { "asset_path": "<path>", "component_name": "<name>", "property_name": "<name>", "value": "<value>" } }
{ "action": "add_component", "params": { "asset_path": "<path>", "component_name": "<name>", "component_class": "<class>" } }
{ "action": "remove_component", "params": { "asset_path": "<path>", "component_name": "<name>" } }
{ "action": "compile_blueprint", "params": { "asset_path": "<path>" } }
```

### Widget/UMG
```json
{ "action": "get_widget_tree", "params": { "asset_path": "<path>" } }
{ "action": "add_widget", "params": { "asset_path": "<path>", "widget_class": "Image", "widget_name": "<name>", "parent_name": "<parent>", "anchor_preset": "stretch_fill" } }
{ "action": "set_brush", "params": { "asset_path": "<path>", "widget_name": "<name>", "property_name": "Brush", "texture_path": "<texture>" } }
{ "action": "compile_widget", "params": { "asset_path": "<path>" } }
{ "action": "create_widget_blueprint", "params": { "save_path": "<path>", "parent_class": "UserWidget", "root_widget": "CanvasPanel" } }
```

### Save
```json
{ "action": "save_packages", "params": { "packages": ["<path1>", "<path2>"] } }
```
> ⚠️ `save_packages` on `.umap` can crash Monolith. For maps, use native Ctrl+S in-editor instead.

---

## 4. Echo Pipeline Commands

```bash
# Check gate status
python Tools/echo_run.py status

# Validate a spec
python Tools/echo_run.py validate-spec <path>

# Run static gates
python Tools/echo_run.py run static_gates

# Record a gate result
python Tools/echo_run.py record <gate-id> pass|fail
```

Gate ledger: `Saved/gate_ledger.json`
State output: `Saved/Echo/state.txt`

---

## 5. Safe Working Rules (non-negotiable)

1. **One editor instance only.** Check `Get-Process UnrealEditor` before any editor work.
2. **Never `git clean -fd` or `git checkout -- .`** — untracked Content/ would be permanently erased.
3. **Never call `load_blueprint_class()` / `get_default_object()` from Python on anything under `Content/TurnBasedJRPGTemplate/Blueprints/Skills/`** — fatal editor crash due to `D_DamageType` enum glue failure.
4. **Use Monolith `blueprint_query` for CDO reads/writes** — it's C++ safe; Python is not for skill BPs.
5. **Verify by re-reading** — `success: true` only means nothing threw. Confirm with `list_dirty_packages`.
6. **A file existing is not a file compiling** — build before trusting code another lane left behind.
7. **Search both name forms** — `UnitHasEnoughMP` vs `Unit Has Enough MP`.
8. **Parallelise research, never the editor** — read-only explorers can run concurrently; all editor work serialises through one holder.
9. **Static graph inspection is not runtime proof** — a green compile does not mean a node is reachable.
10. **Do not write a PID into a doc** — PIDs go stale the moment the editor restarts.

---

## 6. Common Patterns

### Find a skeletal mesh asset
```json
{ "action": "search", "params": { "query": "SK_Melusina", "type": "SkeletalMesh" } }
```

### Check if a Blueprint has errors
```json
{ "action": "get_op_errors", "params": { "op_path": "<path>", "recurse": true } }
```

### Get level actors
```json
{ "action": "get_level_actors", "params": { "level_path": "<map_path>" } }
```

### Spawn an actor in PIE (for testing)
```json
{ "action": "spawn_actor", "params": { "class_path": "<bp_path>", "location": {"x":0,"y":0,"z":0} } }
```

---

## 7. Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---|---|---|
| Monolith silent / request hangs | Modal dialog open in editor (FBX import, etc.) | Check editor for dialog; don't kill |
| `save_packages` crash on `.umap` | Monolith bug with map saving | Use Ctrl+S in editor |
| Asset "disappears" | In-session `delete_asset` hiding it | Force rescan: `ar.scan_paths_synchronous([folder], force_rescan=True)` |
| `get_cdo_properties` shows `None` for components | Monolith can't resolve Blueprint-instanced component pointers | Use `get_components` instead |
| Melusina naked in combat | `MelusinaPresentationMesh` using body-only mesh | Set to `SK_Melusina` (full character) |
| Rhythm HUD not showing | GameMode has wrong HUD class | Set `BP_MelodiaGameMode.HUDWidgetClass = WBP_Battle_Rhythm` |
| Anim instance crash at `NativeUpdateAnimation` | `UMelodiaLocomotionAnimInstance` null traversal interface | Already fixed in current source (line 36 constructor pattern) |

---

## 8. Figma Token Assets (for UI)

| Token | Path |
|---|---|
| Parchment panel | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_SoftMG_ParchmentPanel` |
| Dark board | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Tokens_DarkBoard` |
| Container | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Container` |
| Card | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Card` |
| Corner baroque | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Style_CornerBaroque` |
| Divider scroll | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Style_DividerScroll` |
| Color: gold 100 | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Foundations_Gold_color_gold_100` |
| Color: ivory 100 | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Foundations_Ivory_color_ivory_100` |
| Color: plum 500 | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Foundations_Plum_color_plum_500` |
| Surface: base | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Foundations_Semantic_color_surface_base` |
| Surface: raised | `/Game/Melodia/UI/Textures/Figma/T_Melodia_Figma_Foundations_Semantic_color_surface_raised` |

---

## 9. Notification Contract (for QuillScript / Narrative)

The subsystem recognizes only these seven verbs:

```
melodia:battle:<EncounterId>
melodia:quest:<QuestId>
melodia:flag:<FlagId>:<true|false>
melodia:travel:<LevelId>
melodia:reward:<RewardId>
melodia:stat:<IntentId>:<StatId>:<Delta>
melodia:item:give:<ItemId>:<Count>
```

`melodia:stat:` is idempotent per `<IntentId>` (recorded in `FMelodiaNarrativeRecord::ConsumedIntentIds`).
`melodia:item:` is a **logging stub** — validates and logs, but does not grant items.

---

## 10. Gate Status (as of 2026-08-18)

| Gate | State |
|---|---|
| `runtime` | pass (2026-08-13, owner-verified real input) |
| `save_load` | pass (2026-08-14) |
| `package_launch` | pass (2026-08-14) |
| `repeat_consume` | **OPEN** — last completion gate |
| `static_gates` | fail (2026-08-14) — non-blocking for release |

Run `python Tools/echo_run.py status` for live state.
