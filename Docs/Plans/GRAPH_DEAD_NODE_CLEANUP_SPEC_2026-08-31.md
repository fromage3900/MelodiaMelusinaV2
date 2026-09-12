# Graph Dead-Node Cleanup Spec — 2026-08-31

**Generated:** 2026-08-31 (overnight daemon)
**Source:** `Saved/Audit/graph_reachability_2026-08-31.md`
**Scope:** Blueprint dead-node cleanup — 2 BPs, 20 dead nodes total
**Mode:** T3D cleanup spec — no direct .uasset writes

---

## Summary

| Blueprint | Dead Node Count | Root Cause |
|---|---|---|
| BP_MelusinaJRPGCharacter | 15 | Orphaned Niagara variable nodes (no exec path from event graph) |
| WBP_MelodiaQuillDialog | 5 | Orphaned Branch/Set/SetText nodes (no exec path) |
| BP_JRPGPlayerController | 1 | Orphaned Add to Viewport node |
| WBP_MelodiaQuillDialog | (above) | (shared with second entry) |

**Total: 21 dead nodes across 3 blueprints**

---

## Target 1: BP_MelusinaJRPGCharacter

**Path:** `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter`

### Dead Nodes

All 15 nodes share the same pattern:
- **Node Type:** `Set Niagara Variable By String (Float)` (K2Node_CallFunction)
- **Target:** Niagara Particle System Component
- **Issue:** No exec path from any event entry → unreachable code

### Cleanup Spec

```json
{
  "target": "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
  "operations": [
    {
      "op": "remove_dead_nodes",
      "pattern": {
        "node_type": "K2Node_CallFunction",
        "target_type": "Niagara Particle System Component",
        "function_name": "Set Niagara Variable By String (Float)"
      },
      "count": 15,
      "scope": "EventGraph",
      "condition": "no_exec_path_from_event_entry"
    }
  ]
}
```

### Owner Notes

- These are Niagara particle system setters that lost their execution chain
- Character BP still functions; these are vestigial from an earlier Niagara setup
- After removal, recompile + fingerprint BP_MelusinaJRPGCharacter to confirm no regressions

---

## Target 2: WBP_MelodiaQuillDialog

**Path:** `/Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog`

### Dead Nodes

| # | Node | Type | Issue |
|---|---|---|---|
| 1 | Branch | K2Node_IfThenElse | No exec path |
| 2 | Set TypewriterIndex | K2Node_VariableSet | No exec path |
| 3 | SetText (Text) | K2Node_CallFunction (Target is Text) | No exec path |
| 4 | Branch | K2Node_IfThenElse | No exec path |
| 5 | SetText (Text) | K2Node_CallFunction | No exec path |

### Cleanup Spec

```json
{
  "target": "/Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog",
  "operations": [
    {
      "op": "remove_dead_nodes",
      "nodes": [
        {"name": "Branch", "type": "K2Node_IfThenElse"},
        {"name": "Set TypewriterIndex", "type": "K2Node_VariableSet"},
        {"name": "SetText (Text)", "type": "K2Node_CallFunction"},
        {"name": "Branch", "type": "K2Node_IfThenElse"},
        {"name": "SetText (Text)", "type": "K2Node_CallFunction"}
      ],
      "scope": "EventGraph",
      "condition": "no_exec_path_from_event_entry"
    }
  ]
}
```

### Owner Notes

- Quill dialog likely migrated to a new event-driven typewriter system
- These dead nodes may have been replaced by the new WBP_MelodiaQuill* widgets (see `quill_ui_widgets_commit_spec`)
- Verify the dialog widget still functions in PIE after cleanup

---

## Target 3: BP_JRPGPlayerController

**Path:** `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController`

### Dead Nodes

| # | Node | Type | Issue |
|---|---|---|---|
| 1 | Add to Viewport | K2Node_CallFunction (Target is User Widget) | No exec path from event entry |

### Cleanup Spec

```json
{
  "target": "/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController",
  "operations": [
    {
      "op": "remove_dead_nodes",
      "nodes": [
        {"name": "Add to Viewport", "type": "K2Node_CallFunction"}
      ],
      "scope": "EventGraph",
      "condition": "no_exec_path_from_event_entry"
    }
  ]
}
```

---

## Fix Sequence (ordered)

1. **BP_MelusinaJRPGCharacter** — remove 15 Niagara dead nodes (highest count, cosmetic only)
2. **WBP_MelodiaQuillDialog** — remove 5 dead nodes (verify new widget system first)
3. **BP_JRPGPlayerController** — remove 1 dead node (lowest risk)
4. **Compile all 3 BPs** — confirm no compile errors
5. **PIE smoke test** — verify game launches, character + Quill dialog functional

## Safety

- Requires live Monolith MCP (localhost:9316) + editor
- Never hand-edit .uasset binary
- Backup: git commit before running T3D operations
- Gate acceptance: ledger row via `Tools/echo_run.py record dead_node_cleanup pass` (owner-only)

## Pre-Commit Hook Notes

- No new files added
- No .gitignore changes
- No CLAUDE.md never-touch paths affected