# Monolith Commands — Prepared for Item 2b and Item 3

**Prepared by:** Cline (2026-07-31)
**Execute from:** Rider or any tool with Monolith JSON-RPC access
**Protocol:** JSON-RPC POST to `http://127.0.0.1:9316/mcp`

---

## Item 2b: Tag PlayerStarts in KaleidoNave

**Tag value:** `melodia traversal` (owner-provided)
**Target:** `/Game/EnvSandbox/Environments/L_KaleidoNave`

### Step 1: Inventory PlayerStarts

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mesh_query",
    "arguments": {
      "action": "get_level_actors",
      "level_path": "/Game/EnvSandbox/Environments/L_KaleidoNave",
      "class_filter": "PlayerStart"
    }
  },
  "id": 1
}
```

Expected: 2 PlayerStarts — `NaveStart` (persistent level, loc `[200,0,760]`) and `Dreamstate_PlayerStart` (merged Dreamstate sublevel, loc `[9,10,741]`).

### Step 2: Tag Dreamstate_PlayerStart

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mesh_query",
    "arguments": {
      "action": "set_actor_properties",
      "actor_path": "/Game/EnvSandbox/Environments/L_KaleidoNave.Dreamstate_PlayerStart",
      "properties": {
        "PlayerStartTag": "melodia traversal"
      }
    }
  },
  "id": 2
}
```

### Step 3: Verify by readback

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mesh_query",
    "arguments": {
      "action": "get_actor_properties",
      "actor_path": "/Game/EnvSandbox/Environments/L_KaleidoNave.Dreamstate_PlayerStart",
      "property_names": ["PlayerStartTag", "Tags"]
    }
  },
  "id": 3
}
```

Expected: `PlayerStartTag = "melodia traversal"` or `Tags` contains `"melodia traversal"`.

---

## Item 3: Replace OpenLevel nodes with TravelTo

**Target:** `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance`
**Nodes to replace:** `K2Node_CallFunction_10`, `K2Node_CallFunction_30`, `K2Node_CallFunction_46`, `K2Node_CallFunction_52`

### Verification Loop (MANDATORY — Decision 024)

For each node, follow this exact sequence:

```
export_graph            → save this. Rollback record AND assertion baseline.
get_graph_fingerprint   → before
<mutate: replace OpenLevel with TravelTo>
compile_blueprint       → not clean? STOP. Report, don't retry blind.
assert_graph_matches    → spec.forbidden_nodes: [{class: K2Node_CallFunction, function: OpenLevel}]
                       → matched:false? STOP.
get_graph_fingerprint   → after; record both
save_asset
```

### Step 1: Export graph (baseline)

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "blueprint_query",
    "arguments": {
      "action": "export_graph",
      "blueprint_path": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
      "graph_name": "EventGraph"
    }
  },
  "id": 4
}
```

**Save the response.** This is the rollback record and assertion baseline.

### Step 2: Get fingerprint (before)

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "blueprint_query",
    "arguments": {
      "action": "get_graph_fingerprint",
      "blueprint_path": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
      "graph_name": "EventGraph"
    }
  },
  "id": 5
}
```

**Record the hash.** Expected: `ce961a1949d25073f257e8a114703ea97fd23f71` (or similar).

### Step 3: Replace OpenLevel with TravelTo (one node at a time)

For each of the 4 nodes (`_10`, `_30`, `_46`, `_52`):

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "blueprint_query",
    "arguments": {
      "action": "set_node_property",
      "blueprint_path": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
      "graph_name": "EventGraph",
      "node_id": "K2Node_CallFunction_52",
      "property": "FunctionReference",
      "value": {
        "MemberName": "TravelTo",
        "MemberGuid": "",
        "BlueprintGuid": "/Game/Source/BS_GodFile/MelodiaIntegration/MelodiaTravelSubsystem.MelodiaTravelSubsystem"
      }
    }
  },
  "id": 6
}
```

**Note:** The exact mutation depends on the node structure from the export. The `FunctionReference` must point to `UMelodiaTravelSubsystem::TravelTo`. The `LevelId` pin should be wired to the appropriate map path, and the `SpawnTag` pin should be wired to `"melodia traversal"` (or the appropriate tag for that travel leg).

**After each mutation:**

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "blueprint_query",
    "arguments": {
      "action": "compile_blueprint",
      "blueprint_path": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance"
    }
  },
  "id": 7
}
```

**If not clean:** STOP. Report the error. Do not retry blind.

### Step 4: Assert no OpenLevel nodes remain

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "blueprint_query",
    "arguments": {
      "action": "assert_graph_matches",
      "blueprint_path": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
      "graph_name": "EventGraph",
      "spec": {
        "forbidden_nodes": [
          {
            "class": "K2Node_CallFunction",
            "function": "OpenLevel"
          }
        ]
      }
    }
  },
  "id": 8
}
```

**Expected:** `matched: true` (no OpenLevel nodes remain).

**If `matched: false`:** STOP. Report the missing connections. Do not proceed.

### Step 5: Get fingerprint (after)

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "blueprint_query",
    "arguments": {
      "action": "get_graph_fingerprint",
      "blueprint_path": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
      "graph_name": "EventGraph"
    }
  },
  "id": 9
}
```

**Record the hash.** It should differ from the "before" hash.

### Step 6: Save asset

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "blueprint_query",
    "arguments": {
      "action": "save_asset",
      "asset_path": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance"
    }
  },
  "id": 10
}
```

---

## Verification After All Changes

### PIE Test

1. Load `/Game/EnvSandbox/Environments/L_KaleidoNave`
2. PIE
3. Check log for:
   ```
   MELODIA_TRAVEL_START    level=... spawn_tag=melodia traversal
   MELODIA_TRAVEL_ARRIVED  level=... spawn_tag=melodia traversal placed=1
   ```
4. `placed=0` means no PlayerStart matched the tag — the log names the tag and how many starts exist.

### Fingerprint Stability Gate (Decision 024)

Before relying on `assert_graph_matches`, prove the fingerprint is byte-stable:

1. Call `get_graph_fingerprint` twice on an untouched graph
2. Call it once after a no-op `save_asset`
3. Require byte-identical output across all three calls

If the fingerprint is not stable, stop and report — do not proceed to graph surgery on an unproven tool.

---

## Standing Constraints

- **Commit via `BS_GodFile/.git`** — recovered 2026-08-05; latest local commit `ec20b015`; checkpoint `6154cc1e` captures recovered history.
- **Verification loop is mandatory** — `compile_blueprint` or `assert_graph_matches` failure = hard stop
- **Fix causes, don't add compensating mechanisms**
- **Do not touch hair** — `UMelodiaHairComponent` is correct and PIE-verified
- **L_SakuraPath is human-owned**
- **One asset per transaction** — don't touch a second Blueprint before the first is asserted clean

---

## Report Back

One line each: what you fixed, what you deferred and why. Not what you considered, not a design doc — the working agreement means brief and factual.