# 12 — Shared UE integration procedure (Gates 1, 2C, 4, 6, 7, 9)

| | |
|---|---|
| **Purpose** | One procedure for every Houdini product that enters UE, so no product is "imported" without save/reload proof. |
| **Authority** | UE is the runtime/world authority. One editor, one writer: Monolith `127.0.0.1:9316` is the preferred tool surface. `ueblueprintmcp` stays **off**; never run two surfaces against one graph. `MelodiaIntegrationMap` is additive-only. Owner-authored levels (`L_SakuraPath`, `L_MelusinaMorning`) are ask-first. `LV_SeaAbove_Prototype` `00_CANON/*` is read-only. |
| **Status** | STAGED. |

## Preconditions (every time)

1. No `deploy/SURREAL_*_LOOP_STOP` / `deploy/AGENT_LOOP_STOP_*` if the target is under `/Game/EnvSandbox/`. Otherwise use `/Game/Melodia/HoudiniFoundry/`.
2. The product's `bake_manifest.json` verifies (`houdini_foundry.py verify`).
3. The editor is open on the target map. Do not `load_level` away from `MelodiaIntegrationMap` right after PIE stop, because async teardown crashes the editor.
4. `scene_context_cycle.begin()` before the first spatial mutation.

## Procedure

| Step | Action | Record in manifest `ue` block / evidence |
|---|---|---|
| 1 | Snapshot before: target folder asset list + map actor list (`scene_context_cycle`) | `before.json` |
| 2 | Import / Houdini Engine cook + bake into the recipe's `ue_target.asset_path_prefix` | `baked_asset_paths`, import settings |
| 3 | Bind to **one existing consumer** (mesh placement, MI texture param, Niagara user param, PCG sampler). There are no new masters, graphs, systems or MPC writes | consumer asset path + parameter name |
| 4 | Visual check: Brennan looks at the viewport or a capture | capture path in `Saved/Audit/Screens/` |
| 5 | Save (clear LFS read-only flags first; unattended save) | `saved: true` |
| 6 | Close map → reopen → recount assets/actors → re-check the binding | `reloaded_equal: true` + `after.json` |
| 7 | `scene_context_cycle.end()` → `scene_context_diff.json` | diff path |
| 8 | Houdini Engine hygiene: no cooked Houdini Asset Actor left driving content (bake, then delete or keep un-cooked with a clear label) | note |
| 9 | Fill `engine_version`, `houdini_engine_plugin_version`; set manifest `status` | manifest |

## Proof labels

- Houdini output + `verify` only → **SOURCE/TOOL PROVEN**.
- Steps 1–7 done with evidence → **LIVE PROVEN (scoped)** for that product on that map.
- Packaged build / full route → **not claimed** by any FoundryDay gate.

Only a `CURRENT_STATE.md` edit promotes a label, and it links the evidence.
