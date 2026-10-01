# UE Tools — Blueprint Issues and BP Path Problems

## Purpose
Track all issues, workarounds, and open problems related to blueprint inspection tools (`ue_bp_*`) and blueprint/asset path handling.

---

## Issue 1: `ue_bp_summary` / `ue_bp_inspect` — Missing 'path' Parameter

**Symptom:**
Calls to `ue_bp_summary` and `ue_bp_inspect` with a `blueprint_path` parameter return:
```
{"success": false, "error": "Missing 'path' parameter"}
```

**What was tried:**
- `/Game/FullSample/Blueprints/Characters/DA_TestKnight_Sword.DA_TestKnight_Sword`
- `/Game/FullSample/Blueprints/Characters/DA_TestKnight_Sword`
- `/Game/FullSample/Blueprints/Characters/Enemies/ACFMeleeEnemyBP.ACFMeleeEnemyBP`
- `/Game/FullSample/Blueprints/Items/Weapons/ACFSwordBP.ACFSwordBP`
- With and without the `.uasset` extension

**Result:** All failed with the same error. The parameter name expected by the bridge server may be `path` instead of `blueprint_path`, or the tool schema is mismatched.

**Impact:** Cannot inspect blueprint internals (graphs, variables, components, functions) programmatically.

**Workaround:** Use `ue_console` with Python (`py ...`) to query blueprint data via the Python API instead.

**Status:** **OPEN**

---

## Issue 2: `ue_asset_open` Game Thread Timeouts

**Symptom:**
After opening one asset successfully, subsequent `ue_asset_open` calls time out:
```
{"status": "error", "success": false, "error": "Game thread timeout — operation took too long"}
```
or:
```
Bridge timeout after 15000ms
```

**What was tried:**
- Open `/Game/FullSample/Blueprints/Characters/DA_TestKnight_Sword.DA_TestKnight_Sword` → succeeded once
- Open `/Game/FullSample/Blueprints/Characters/Enemies/ACFMeleeEnemyBP.ACFMeleeEnemyBP` → timed out
- Open `/Game/FullSample/Blueprints/Items/Weapons/ACFSwordBP.ACFSwordBP` → timed out
- Retry the same first asset → also timed out

**Impact:** Cannot reliably open multiple assets in sequence for inspection or comparison.

**Workaround:** Space out calls; use Python console commands to read asset metadata instead of opening the editor view.

**Status:** **OPEN**

---

## Issue 3: `ue_selection_get` Timeout After Asset Open

**Symptom:**
After `ue_asset_open` succeeds, `ue_selection_get` also times out with:
```
Game thread timeout — operation took too long
```

**Impact:** Cannot read what the editor has selected after opening an asset.

**Workaround:** None known.

**Status:** **OPEN**

---

## Issue 4: `ue_bp_summary` / `ue_bp_inspect` / `ue_da_reflect` / `ue_dt_list` Bridge Timeouts

**Symptom:**
All blueprint/data asset inspection tools time out:
```
Bridge timeout after 15000ms
```

**What was tried:**
- `ue_bp_summary` on multiple blueprints
- `ue_bp_inspect` on multiple blueprints
- `ue_da_reflect` on DA_TestKnight_Sword
- `ue_dt_list` on DA_TestKnight_Sword

**Impact:** Zero ability to inspect blueprint or data asset internals through the bridge.

**Workaround:** Use `ue_console` with Python to reflect classes and read properties.

**Status:** **OPEN**

---

## Issue 5: `ue_console` Python Commands Return Empty Output

**Symptom:**
Some `ue_console` Python commands execute but return empty output even when they should print:
```
py import unreal; ar = unreal.AssetRegistryHelpers.get_asset_registry(); assets = ar.get_assets_by_path(...); [print(a.asset_name) for a in assets[:30]]
```
→ output: `""`

**What was tried:**
- Different import styles
- Different path formats (project content dir, `/Game/...`, etc.)
- Simpler print statements (`py print("Python works")`) → also empty

**Impact:** Python console as a diagnostic fallback is unreliable for reading data back.

**Note:** The Python code may actually be running but stdout is not captured by the bridge response.

**Workaround:** Write Python results to a file on disk, then read the file.

**Status:** **OPEN**

---

## Issue 6: Asset Path Format Ambiguity

**Symptom:**
Uncertainty about the exact path format expected by different tools.

**Known formats in use:**
- `/Game/FullSample/Blueprints/Characters/DA_TestKnight_Sword.DA_TestKnight_Sword` (with class suffix) — works for `ue_asset_list`, `ue_asset_open` (sometimes)
- `/Game/FullSample/Blueprints/Characters/DA_TestKnight_Sword` (without suffix) — unknown if any tool prefers this

**Impact:** Trial-and-error required for every new tool call.

**Workaround:** Use `ue_asset_list` to get exact paths, then reuse those verbatim.

**Status:** **OPEN — needs documentation**

---

## Issue 7: `ue_bp_compile` — Untested

**Symptom:**
Not yet tested. Given the parameter-name issues with `ue_bp_summary` and `ue_bp_inspect`, `ue_bp_compile` likely has the same schema mismatch.

**Status:** **UNTESTED — likely broken**

---

## Summary Table

| Tool | Status | Issue | Workaround |
|---|---|---|---|
| `ue_bp_summary` | **BROKEN** | Missing 'path' param / timeout | Python console |
| `ue_bp_inspect` | **BROKEN** | Missing 'path' param / timeout | Python console |
| `ue_bp_list_graphs` | **UNTESTED** | Likely same param issue | — |
| `ue_bp_get_components` | **UNTESTED** | Likely same param issue | — |
| `ue_bp_get_variables` | **UNTESTED** | Likely same param issue | — |
| `ue_bp_compile` | **UNTESTED** | Likely same param issue | — |
| `ue_da_reflect` | **BROKEN** | Timeout | Python console |
| `ue_dt_list` | **BROKEN** | Timeout | Python console |
| `ue_asset_open` | **FLAKY** | Works once, then timeouts | Space out calls; use Python |
| `ue_selection_get` | **FLAKY** | Timeout after asset open | Wait longer; retry |
| `ue_console` (Python) | **PARTIAL** | Empty stdout | Write to file |
| `ue_asset_list` | **WORKING** | — | — |
| `ue_project_info` | **WORKING** | — | — |
| `ue_ping` | **WORKING** | — | — |
| `ue_level_screenshot` | **UNTESTED** | Likely works | — |
| `ue_level_spawn` | **UNTESTED** | Likely works | — |

---

## Recommended Next Steps

1. **Fix `ue_bp_*` parameter schema** — The bridge server likely expects `path` instead of `blueprint_path`, or the JSON schema is mismatched.
2. **Fix Python stdout capture** — Ensure `ue_console` Python output is forwarded back through the bridge response.
3. **Add retry/backoff for game-thread operations** — `ue_asset_open` and `ue_selection_get` need resilience.
4. **Document exact path formats** — Each tool should clearly state what path format it expects.
5. **Test all tools end-to-end** — Run a verification suite that exercises every tool against known assets.

---

## Notes
- These issues were discovered while attempting to create a new ACF test knight with a one-handed sword (2026-05-28).
- The workaround pattern is: use `ue_asset_list` to discover assets, then use `ue_console` with Python for any deeper inspection.