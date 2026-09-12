# Oceanology Enable State — 2026-08-27

Status: **GATE E CORE PASS** (updated end of session). Plugin loads natively on UE 5.8 and the
Oceanology ocean actor survives PIE → save → close → reopen → PIE in the isolated Sea Above
prototype map. See "Gate E verdict" at the bottom.

## Working-tree state (uncommitted, owner-intended)

- `BS_GodFile.uproject` — single hunk vs HEAD: `Oceanology_Plugin` `Enabled: false → true`
  plus the Fab MarketplaceURL. No other plugin flips.
- `Plugins/Oceanology_Plugin/` — untracked, full package (Source/, Binaries/, Content/,
  Intermediate/). NextGen line, `.uplugin` VersionName `1.1.0` "OCEANOLOGY NEXT-GEN", 2 modules
  (Runtime + UncookedOnly editor), Win64.

## Binary vs descriptor mismatch (the load blocker)

| Check | Value | Verdict |
|---|---|---|
| Local engine `Build.version` changelist | `55116800` (UE 5.8.0 promoted) | — |
| Engine `UnrealEditor.modules` BuildId | `55116800` | — |
| In-tree plugin DLLs BuildId | `55116800` | **match — binaries are 5.8-built** |
| In-tree `.uplugin` `EngineVersion` | `5.5.0` | **stale metadata — triggers compatibility modal** |

Editor boot evidence (2026-08-27 17:09 session, `Saved/Logs/BS_GodFile.log`):

```
LogPluginManager: Warning: Plugin 'Oceanology_Plugin' requires engine version '5.5.0' and
  may not be compatible with the current engine version '5.8.0-55116800+++UE5+Release-5.8'
Message dialog closed, result: No, title: 'Oceanology_Plugin' is Incompatible ...
LogPluginManager: Display: Skipping load of 'Oceanology_Plugin'.
```

The plugin is **not loaded** in the running editor; the editor itself is healthy.

## Archive verdict — do NOT stage `OceanologyLegacy-UE5.8-package-20260825`

`G:\BS_GodFile_Archive\20260827\OceanologyLegacy-UE5.8-package-20260825\` is, despite its
name, the **legacy line**: `.uplugin` VersionName `5.7.0`, `EngineVersion: 5.4.0`, binaries
BuildId `33043543` (not this engine). The in-tree NextGen package is strictly newer and
BuildId-matched. The archive stays archival.

## Load options (owner decision)

1. **Descriptor metadata correction (recommended):** with the editor closed, update
   `EngineVersion` `5.5.0 → 5.8.0` in `Plugins/Oceanology_Plugin/Oceanology_Plugin.uplugin`.
   This is a metadata correction of a package whose binaries already match the engine
   BuildId — not a build-failure mask. Requires owner approval per the 08-25 plan's
   descriptor-edit prohibition.
2. **Load-anyway modal:** answer "Yes" at the next boot. No file change, but the modal
   returns every boot and wedges headless automation.
3. **Full rebuild from Source/** (closed editor, rule 15/21): fallback if option 1 fails
   to load natively for any binary reason.

## Gate E sequence after native load confirmed

Per `Docs/WorldGen/PROCEDURAL_ENVIRONMENT_BUILD_PLAN_GAEA2UNREAL_OCEANOLOGY_2026-08-25.md`
recovery gate §4–5 and `Docs/Handoffs/OCEANOLOGY_WATER_COEXISTENCE_2026-08-15.md`:

1. Read-only asset-registry inventory (registered classes, water materials, WP behavior)
   → `Saved/Audit/`.
2. Isolated-map water actor placement only (Sea Above prototype or Liquid Cathedral).
3. Spikes #1–#3 from the coexistence contract (query entry point, MI param capture via
   reflection, caustics dedup).
4. PIE → **save → close → reopen** rerun before Gate E is claimable.

## Boundaries unchanged

- Oceanology = hero-surface simulation authority in its regions only.
- `UMelodiaWaterInteractionSubsystem` keeps gameplay-water authority; adapter C++ is a
  separate later spike, not part of this enable.
- Single-writer contracts on FLIP particles, `MS_Water_*` audio, and MPC palette stand.

---

## Gate E verdict — 2026-08-27 (end of session)

**PASS (core).** Evidence trail (all in Saved/Logs/BS_GodFile.log unless noted):

1. Native load: Mounting Project plugin Oceanology_Plugin + both modules InternalLoadLibrary
   succeeded; session shader compile errors = 0 (shader guard fix holds).
2. Native actor: AOceanologyInfiniteOcean (/Script/Oceanology_Plugin.OceanologyInfiniteOcean)
   spawned via Python into LV_SeaAbove_Prototype as SeaAbove_OceanologyOcean_Test.
   Note: the BP wrapper BP_OceanologyInfiniteOcean is deprecated; spawn the native class.
3. Isolation matrix (Monolith PIE):
   - empty template map + ocean → PIE PASS (Server logged in, stable)
   - SeaAbove map alone → PIE PASS
   - SeaAbove map + ocean → PIE PASS (60+ s stable; the one earlier crash was a transient race
     against first-boot 4K texture compilation of plugin content, not reproducible after warm-up)
4. save_map → MAP_SAVED True; editor closed cleanly; uproject Enabled: true SURVIVED clean
   shutdown (the earlier reverts were UE crash-recovery auto-disabling recently-enabled plugins
   after crashes — do not confuse with owner intent).
5. Reopen: actor OceanologyInfiniteOcean_0 present in the reloaded map; second PIE PASS.

Caveats / remaining:
- Spikes #1–#3 (surface-query entry point, MI parameter capture, caustics dedup) still open —
  required before the adapter C++ spike.
- Plugin example BPs fail to compile on 5.8 (BP_ThirdPersonCharacter swim nodes,
  wave-manipulator examples) — plugin-content debt, not on our path; do not fix by editing
  plugin assets without owner approval.
- One missing plugin content object observed: M_UnderOcean_PostProcess_Vo... (underwater PP
  material) — verify against the purchased NextGen package completeness later.
- Crash reporter is now configured to retain reports locally
  (Engine/Programs/CrashReportClient/Saved/Config/Windows/Engine.ini, upload disabled).
- Uncommitted: uproject enable flip + .uplugin EngineVersion correction + shader guard fix.
  Commit decision with owner (plugin dir is untracked).
