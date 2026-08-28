# Oceanology Plugin .uplugin Fix Status & Native-Load Confirmation Checklist — 2026-08-28

**Lane:** `asset_qa` (read-only documentation; no editor, no C++, no asset writes)
**Scope:** Confirm the Oceanology plugin descriptor fix is correct and produce the exact
verification procedure for the next editor boot after the rebuild.

---

## 1. Current state — descriptor vs engine vs project

### 1.1 EngineVersion in the .uplugin

| Field | Value | Source line |
|---|---|---|
| `EngineVersion` | **`5.8.0`** | `Oceanology_Plugin.uplugin` line 13 |
| `Version` | 1 | line 3 |
| `VersionName` | `1.1.0` | line 4 |
| `FriendlyName` | `OCEANOLOGY NEXT-GEN` | line 5 |
| `Installed` | `true` | line 15 |

**Verdict: corrected.** The descriptor previously declared `EngineVersion: 5.5.0`
(captured in `OCEANOLOGY_ENABLE_STATE_2026-08-27.md` §"Binary vs descriptor mismatch").
It now declares `5.8.0`, matching `BS_GodFile.uproject` → `EngineAssociation: "5.8"`.

The stale `5.5.0` was the sole load blocker: UE 5.8.0 raised a compatibility modal on boot
and the plugin was skipped (`LogPluginManager: Skipping load of 'Oceanology_Plugin'`).
The modal is gone by design once the descriptor matches the engine.

### 1.2 BuildId match — plugin binaries vs engine

| Check | BuildId | Verdict |
|---|---|---|
| Local engine `Build.version` changelist | `55116800` (UE 5.8.0 promoted) | — |
| Engine `UnrealEditor.modules` | `55116800` | — |
| In-tree plugin DLLs (`Binaries/Win64/`) | `55116800` | **match — binaries are 5.8-built** |

Source: `OCEANOLOGY_ENABLE_STATE_2026-08-27.md` §"Binary vs descriptor mismatch".

**Verdict: binaries already match the engine.** The only stale artifact was the descriptor
metadata (`EngineVersion: 5.5.0`), which is now corrected to `5.8.0`. No binary rebuild is
required for the *load* to succeed — the binaries were already 5.8-compiled. The pending
editor rebuild is for the new `MelodiaShader` module (AGENTS.md rules 15/21), not for
Oceanology. After that rebuild the Oceanology binaries remain BuildId-matched because the
rebuild targets the game project module, not the plugin's prebuilt DLLs.

> **Caveat:** if the rebuild regenerates plugin binaries (e.g., a full project rebuild touches
> all `Binaries/Win64/*.dll`), confirm BuildId is still `55116800` afterward. If it drifts,
> the plugin must be rebuilt from `Source/` to match.

### 1.3 Plugin enabled in the .uproject

`BS_GodFile.uproject` lines 271–274:

```json
{
    "Name": "Oceanology_Plugin",
    "Enabled": true,
    "MarketplaceURL": "com.epicgames.launcher://ue/Fab/product/4e59bf12-d0c8-46f4-b5f9-37d48d0b6e63"
}
```

**Verdict: enabled.** `Enabled: true` is present and correct.

Per the 08-27 enable-state doc, the `.uproject` had a single uncommitted hunk vs HEAD:
`Oceanology_Plugin` `Enabled: false → true` plus the Fab MarketplaceURL. No other plugin
flips. The 08-27 Gate E core pass confirmed that `Enabled: true` survived a clean editor
shutdown (earlier reverts were UE crash-recovery auto-disabling, not owner intent).

---

## 2. Why it was broken — the load chain

```
.uplugin EngineVersion 5.5.0  ← stale metadata (binaries are 5.8)
  → UE 5.8.0 compatibility modal: "may not be compatible with current engine version"
  → Modal answered "No" (or auto-dismissed in headless)
  → LogPluginManager: Skipping load of 'Oceanology_Plugin'
  → Plugin never mounted; AOceanologyInfiniteOcean not registered; no spawn possible
```

The fix: edit `EngineVersion: 5.5.0 → 5.8.0` in the `.uplugin` descriptor. This is a
metadata correction of a package whose binaries already match the engine BuildId —
**not** a build-failure mask.

---

## 3. Pre-rebuild state summary

| Item | State | Needs action? |
|---|---|---|
| `.uplugin` EngineVersion | `5.8.0` ✅ | No — corrected 08-27 |
| Plugin binary BuildId | `55116800` (matches engine) ✅ | No — unless rebuild drifts it |
| `.uproject` Enabled flag | `true` ✅ | No |
| `.uplugin` Modules | 2: `Oceanology_Plugin` (Runtime, PostConfigInit) + `Oceanology_PluginEditor` (UncookedOnly, PostEngineInit), both Win64 | No |
| `.uplugin` sub-plugins | Niagara (enabled), AudioModulation (enabled) | No |
| Native load confirmed post-rebuild | **Not yet** | **Yes — see §4** |

---

## 4. Checklist — confirming native load after the editor rebuild

This is the exact procedure to run **after** the closed-editor `Build.bat` rebuild completes
and the editor is relaunched. Every item must pass; any failure stops and escalates.

### 4.1 Pre-boot file checks (editor closed)

- [ ] **C1.** `Oceanology_Plugin.uplugin` line 13 reads `"EngineVersion": "5.8.0"` (no
      regression from the rebuild or a git operation).
- [ ] **C2.** `BS_GodFile.uproject` `Oceanology_Plugin` entry has `"Enabled": true`.
- [ ] **C3.** Plugin binary BuildId still `55116800` — verify with:
      ```bash
      # From the project root, editor closed:
      python -c "
      import struct, pathlib
      # UE DLLs embed BuildId in the version resource; check the .modules sidecar
      # or use the Build.version changelist from the engine as the reference.
      # Simplest: confirm the .uplugin + .uproject are correct (C1/C2) and let
      # the boot log confirm the load.
      print('BuildId check is log-confirmed at boot (C4-C6).')
      "
      ```
      If the rebuild touched `Plugins/Oceanology_Plugin/Binaries/Win64/*.dll`, confirm
      the `.modules` BuildId matches `55116800` before booting. If it drifted, do a full
      closed-editor rebuild from `Source/` (AGENTS.md rules 15/21).

### 4.2 Boot log — native load (editor launching)

- [ ] **C4.** Launch the editor on `BS_GodFile.uproject`.
- [ ] **C5.** No compatibility modal appears for `Oceanology_Plugin`. If a modal **does**
      appear, the `.uplugin` fix did not stick or the binary BuildId drifted — do **not**
      answer "Yes" to load-anyway; stop and re-verify C1–C3, then rebuild from `Source/`
      if C3 failed.
- [ ] **C6.** `Saved/Logs/BS_GodFile.log` contains:
      - `LogPluginManager: Mounting Project plugin Oceanology_Plugin`
      - Both modules report `InternalLoadLibrary` succeeded:
        `Oceanology_Plugin` (Runtime) **and** `Oceanology_PluginEditor` (UncookedOnly)
      - **No** `Skipping load of 'Oceanology_Plugin'` line
      - **No** `Warning: Plugin 'Oceanology_Plugin' requires engine version` line

### 4.3 Class registration (editor live)

- [ ] **C7.** `AOceanologyInfiniteOcean` (`/Script/Oceanology_Plugin.OceanologyInfiniteOcean`)
      is registered and spawnable — confirm via Monolith or Python:
      ```python
      # Monolith or py-unreal after boot:
      import unreal
      factory = unreal.SystemLibrary.load_class(
          "/Script/Oceanology_Plugin.OceanologyInfiniteOcean"
      )
      assert factory is not None, "Oceanology class not registered — plugin did not load"
      ```
- [ ] **C8.** Run `melodia_system_health` (MCP) — Oceanology plugin appears in the loaded
      plugin list with no errors.

### 4.4 PIE stability — isolated map (editor live)

- [ ] **C9.** Open `LV_SeaAbove_Prototype` (or an empty template map).
- [ ] **C10.** Spawn `AOceanologyInfiniteOcean` via the native class (not the deprecated
      `BP_OceanologyInfiniteOcean` wrapper) → actor present in the outliner.
- [ ] **C11.** Enter PIE → Server logs in, 60+ seconds stable, no crash. (The 08-27
      transient race on first-boot 4K texture compile was non-reproducible after warm-up;
      if it recurs, warm shaders then re-PIE.)
- [ ] **C12.** `save_map` succeeds → `MAP_SAVED: True`. Close editor cleanly.
- [ ] **C13.** Reopen the project → `.uproject` still shows `Oceanology_Plugin: Enabled: true`
      (not auto-reverted by crash recovery). Actor `OceanologyInfiniteOcean_0` present in
      the reloaded map.
- [ ] **C14.** Second PIE → stable, ocean actor renders.

### 4.5 Post-confirmation

- [ ] **C15.** Record the pass in `Saved/gate_ledger.json` or the appropriate gate doc.
- [ ] **C16.** Commit the `.uplugin` EngineVersion correction and the `.uproject` enable
      flip if not already committed (owner decision — plugin dir may be untracked).

---

## 5. Fallback if native load fails

If the modal still appears after the rebuild **despite** C1–C3 passing, the descriptor
fix is insufficient and the fallback is a **full closed-editor rebuild from `Source/`**
per AGENTS.md rules 15/21:

```bash
# Editor closed:
cd C:\EnvironmentPortfolio\BS_GodFile
.\Build.bat  # or the project's established build command
```

Then re-run C4–C14.

The 08-27 Gate E core pass already demonstrated that the descriptor fix alone is
sufficient (native load, actor spawn, PIE stability, save/close/reopen survival) — the
fallback exists for the edge case where the rebuild perturbs the binary BuildId.

---

## 6. Sources

| File | What it provided |
|---|---|
| `Plugins/Oceanology_Plugin/Oceanology_Plugin.uplugin` | EngineVersion (5.8.0), VersionName (1.1.0), Modules (2, Win64), sub-plugins (Niagara, AudioModulation) |
| `BS_GodFile.uproject` | `Oceanology_Plugin: Enabled: true` (lines 271–274), EngineAssociation "5.8" |
| `Docs/Handoffs/OCEANOLOGY_ENABLE_STATE_2026-08-27.md` | BuildId match evidence (55116800), load-blocker root cause, Gate E core pass verdict, fallback policy |
| `Docs/Handoffs/UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28.md` | §5.1 plugin-load verification steps, post-install checklist, risk register, execution order |

---

## 7. One-line status

> **Descriptor fixed (`5.5.0 → 5.8.0`), binaries BuildId-matched (`55116800`), `.uproject`
> enabled (`true`). Native load confirmed on 08-27 (Gate E core pass); re-confirm with
> checklist §4 after the editor rebuild.**
