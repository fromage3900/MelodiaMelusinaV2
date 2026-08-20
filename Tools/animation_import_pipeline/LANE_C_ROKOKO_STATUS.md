# Lane C: Rokoko Mocap Pipeline — Status Assessment

**Date:** 2026-08-08
**Author:** Agent assessment

---

## What's Ready

### Scripts (fully authored, on disk)

| Script | Path | Status |
|--------|------|--------|
| `import_rokoko_mocap.py` | `Content/Python/import_rokoko_mocap.py` | Complete — imports Inbox FBX onto `SK_MocapSource`, batch-retargets to Melusina via `IKRetargetBatchOperation` |
| `headless_retarget_mocap.py` | `Content/Python/headless_retarget_mocap.py` | Complete — runs with editor closed, rebinds skeleton via C++ helper `MelodiaAssetRepairLibrary.set_skeletal_mesh_skeleton`, writes `retarget_report.json` |
| `setup_rokoko_livelink_plugins.ps1` | `Tools/setup_rokoko_livelink_plugins.ps1` | Complete — one-time Epic Live Link plugin enable |
| `run_headless_mocap_retarget.ps1` | `Tools/run_headless_mocap_retarget.ps1` | Complete — wrapper launching `UnrealEditor-Cmd.exe` with `-run=pythonscript` |

### Docs (pipeline architecture)

- `Docs/ROKOKO_MELUSINA_MOCAP.md` — Full pipeline spec (import → retarget → game anims), folder map, naming conventions, one-time setup, Live Link optional path.

### Assets in CompatibilityLabs snapshot (NOT in live project)

All four pipeline assets exist in `CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/`:

| Asset | Snapshot path |
|-------|---------------|
| `SK_MocapSource` | `Snapshot_2026-08-06/Content_Melodia/Mocap/Source/SK_MocapSource.uasset` |
| `SK_MocapSource_Skeleton` | `Snapshot_2026-08-06/Content_Melodia/Mocap/Source/SK_MocapSource_Skeleton.uasset` |
| `IK_MocapSource` | `Snapshot_2026-08-06/Content_Melodia/Mocap/Source/IK_MocapSource.uasset` |
| `RTG_Mocap_to_Melusina` | `Snapshot_2026-08-06/Content_Melodia/Mocap/RTG_Mocap_to_Melusina.uasset` |

### Retarget directory (snapshot only)

`Snapshot_2026-08-06/Content_Melodia/Mocap/Retarget/` also contains `IK_Melusina_Body_Current.uasset` and `RTG_Mocap_to_Melusina_Current.uasset` — these look like re-targeter variants.

---

## What's Blocked

### BLOCKER 1 — Mocap content tree is absent from the live project

The entire `/Game/Melodia/Mocap/` directory tree does **not exist** under `Content/Melodia/`:

| Expected path | Exists? |
|---------------|---------|
| `Content/Melodia/Mocap/Source/SK_MocapSource` | ❌ |
| `Content/Melodia/Mocap/Source/IK_MocapSource` | ❌ |
| `Content/Melodia/Mocap/RTG_Mocap_to_Melusina` | ❌ |
| `Content/Melodia/Mocap/Source/Anims/` | ❌ |
| `Content/Melodia/Characters/Melusina/Animations/Mocap/` | ❌ |

All pipeline assets are **only** in `CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/`. They must be restored to the active content tree before any script can run.

### BLOCKER 2 — `Imports/Mocap/Rokoko/Inbox/` does not exist

The drop folder for Rokoko FBX exports (referenced by `import_rokoko_mocap.py` line 30 as `C:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\Rokoko\Inbox`) is **entirely absent**. No `Imports/Mocap/` directory exists anywhere in the project. No FBX files exist.

### BLOCKER 3 — Missing neck hierarchy fix doc

`Docs/MELUSINA_NECK_RIG_HIERARCHY_BUG_2026-07-11.md` — referenced by `ROKOKO_MELUSINA_MOCAP.md` line 112 as a prerequisite gate before recording a large Rokoko library — **does not exist**. This means the ARP skeleton rewire has not been documented or committed.

### BLOCKER 4 — Python scripts reference G: drive hardcoded paths

`import_rokoko_mocap.py` uses:
- `INBOX = r"C:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\Rokoko\Inbox"`
- `REPORT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Melodia\rokoko_import_report.json"`

`headless_retarget_mocap.py` uses:
- `REPORT = r'C:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia/retarget_report.json'`

These will break if the project is relocated. Consider making them relative.

### BLOCKER 5 — No source animations exist

`Content/Melodia/Mocap/Source/Anims/` does not exist. There are no `A_Src_Rokoko_*` animations to retarget. Even if the pipeline assets are restored, the retarget step can only run after Rokoko FBX captures are dropped in the Inbox and imported.

---

## Steps to Unblock

### 1. Restore Mocap content tree from snapshot

Copy the four source assets from the CompatibilityLabs snapshot into the live content directory:

```powershell
# Ensure target directories exist
$mocapSource = "Content/Melodia/Mocap/Source"
$mocapRetarget = "Content/Melodia/Mocap"
New-Item -ItemType Directory -Path $mocapSource -Force | Out-Null

# Copy source assets
Copy-Item -Path "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/SK_MocapSource.uasset" `
          -Destination "Content/Melodia/Mocap/Source/SK_MocapSource.uasset" -Force
Copy-Item -Path "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/SK_MocapSource_Skeleton.uasset" `
          -Destination "Content/Melodia/Mocap/Source/SK_MocapSource_Skeleton.uasset" -Force
Copy-Item -Path "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/IK_MocapSource.uasset" `
          -Destination "Content/Melodia/Mocap/Source/IK_MocapSource.uasset" -Force
Copy-Item -Path "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/RTG_Mocap_to_Melusina.uasset" `
          -Destination "Content/Melodia/Mocap/RTG_Mocap_to_Melusina.uasset" -Force
```

Also create the output directory that `import_rokoko_mocap.py` expects:

```powershell
New-Item -ItemType Directory -Path "Content/Melodia/Characters/Melusina/Animations/Mocap" -Force | Out-Null
```

### 2. Create Imports/Mocap/Rokoko/Inbox/ directory

```powershell
New-Item -ItemType Directory -Path "Imports/Mocap/Rokoko/Inbox" -Force | Out-Null
New-Item -ItemType Directory -Path "Imports/Mocap/Rokoko/CharacterRef" -Force | Out-Null
```

### 3. Author the neck hierarchy fix doc

`Docs/MELUSINA_NECK_RIG_HIERARCHY_BUG_2026-07-11.md` must be created documenting:
- The ARP skeleton rewire needed for Melusina's spine/neck
- Which bones need re-parenting
- Whether existing retarget chains in `RTG_Mocap_to_Melusina` need updating
- Whether any existing clips will break after the skeleton change

Until this doc is written and the skeleton fix is applied, recording a large Rokoko library risks having to re-retarget everything after the skeleton swap.

### 4. (Optional) Make Python paths relative

Change hardcoded `C:\EnvironmentPortfolio\BS_GodFile\` paths in both Python scripts to resolve from project root (`os.getcwd()` or `unreal.SystemLibrary.get_project_directory()`).

### 5. First test take

Once assets are restored:
1. Record a short take in Rokoko Studio
2. Export FBX to `Imports/Mocap/Rokoko/Inbox/IdleTest.fbx`
3. In editor, run `import_rokoko_mocap.main(import_only=False)`
4. Verify `A_Mocap_Rokoko_IdleTest` on `SK_Melusina` for spine/neck quality

---

## Commands to Run Once Unblocked

### Restore pipeline assets (PowerShell from repo root)
```powershell
New-Item -ItemType Directory -Path "Content/Melodia/Mocap/Source" -Force | Out-Null
New-Item -ItemType Directory -Path "Content/Melodia/Mocap/Source/Anims" -Force | Out-Null
New-Item -ItemType Directory -Path "Content/Melodia/Characters/Melusina/Animations/Mocap" -Force | Out-Null
Copy-Item -Path "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/SK_MocapSource.uasset" -Destination "Content/Melodia/Mocap/Source/SK_MocapSource.uasset" -Force
Copy-Item -Path "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/SK_MocapSource_Skeleton.uasset" -Destination "Content/Melodia/Mocap/Source/SK_MocapSource_Skeleton.uasset" -Force
Copy-Item -Path "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/IK_MocapSource.uasset" -Destination "Content/Melodia/Mocap/Source/IK_MocapSource.uasset" -Force
Copy-Item -Path "CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/RTG_Mocap_to_Melusina.uasset" -Destination "Content/Melodia/Mocap/RTG_Mocap_to_Melusina.uasset" -Force
```

### Create Inbox directories
```powershell
New-Item -ItemType Directory -Path "Imports/Mocap/Rokoko/Inbox" -Force | Out-Null
New-Item -ItemType Directory -Path "Imports/Mocap/Rokoko/CharacterRef" -Force | Out-Null
```

### Enable Live Link plugins (one-time)
```powershell
powershell -ExecutionPolicy Bypass -File Tools\setup_rokoko_livelink_plugins.ps1
```

### Import + retarget a take (editor open)
```python
import import_rokoko_mocap as m
m.main(import_only=False)
```

### Headless retarget of all source clips (editor closed)
```powershell
powershell -ExecutionPolicy Bypass -File Tools\run_headless_mocap_retarget.ps1
```

---

## Summary Table

| Component | Status | Location |
|-----------|--------|----------|
| Pipeline docs | ✅ Complete | `Docs/ROKOKO_MELUSINA_MOCAP.md` |
| Import script | ✅ Complete | `Content/Python/import_rokoko_mocap.py` |
| Headless retarget script | ✅ Complete | `Content/Python/headless_retarget_mocap.py` |
| Plugin setup script | ✅ Complete | `Tools/setup_rokoko_livelink_plugins.ps1` |
| Headless wrapper script | ✅ Complete | `Tools/run_headless_mocap_retarget.ps1` |
| SK_MocapSource | ❌ Snapshot only | `CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/` |
| SK_MocapSource_Skeleton | ❌ Snapshot only | `CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/` |
| IK_MocapSource | ❌ Snapshot only | `CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/Source/` |
| RTG_Mocap_to_Melusina | ❌ Snapshot only | `CompatibilityLabs/Snapshot_2026-08-06/Content_Melodia/Mocap/` |
| Inbox directory | ❌ Missing | `Imports/Mocap/Rokoko/Inbox/` |
| Neck hierarchy fix doc | ❌ Missing | `Docs/MELUSINA_NECK_RIG_HIERARCHY_BUG_2026-07-11.md` |
| Source animations | ❌ None | `Content/Melodia/Mocap/Source/Anims/` |
| Rokoko FBX files | ❌ None | `Imports/Mocap/Rokoko/Inbox/` |
