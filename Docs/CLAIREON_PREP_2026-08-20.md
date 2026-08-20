# Claireon Prep Checklist

Status: Plugin added to .uproject, launch config created, deps identified.

## What's Done
- [x] Added Claireon + 12 missing engine plugins to `BS_GodFile.uproject` (now 68 plugins total)
- [x] Created `.claireon/launch_editor.json` (proxy-mode editor launch config)
- [x] Created `Scripts/LaunchEditor.ps1` (build + launch UE5.8 editor with `-StartMCPServer`)
- [x] Computed deterministic port: **64998** (SHA-256 of `C:\EnvironmentPortfolio\BS_GodFile`, folded into 49152-65535)

## What Still Needs Manual Action

### 1. Register Claireon in your MCP client config
Your `C:/Users/froma/.mcp.json` currently has: blender, it-is-unreal, monolith. Add:

```json
"claireon": {
  "type": "http",
  "url": "http://127.0.0.1:64998/mcp"
}
```

### 2. Build the editor
Run from project root:
```powershell
# Option A: Use UBT directly
"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe" BS_GodFileEditor Win64 Development -Project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject"

# Option B: Use the Claireon utility script
& "C:\EnvironmentPortfolio\BS_GodFile\Plugins\Claireon\Scripts\Utilities\Invoke-EditorBuild.ps1"
```

### 3. Launch with Claireon enabled
Either:
- Launch editor with `-StartMCPServer` flag (auto-starts MCP on load)
- Or click the **Claireon** toolbar button in-editor to open the panel

The server writes its live port/PID to `Saved/Claireon/MCPServer.json` on startup.

### 4. Proxy mode (optional, for crash survival)
```powershell
& "C:\EnvironmentPortfolio\BS_GodFile\Plugins\Claireon\Scripts\Utilities\Start-MCPProxy.ps1"
```
This spawns the always-on proxy (registration port 43017) and binds port 64998 for this worktree. Claude Code stays connected across editor restarts/crashes.

## CONFLICT WARNING: UEBlueprintMCP
`.uproject` has `UEBlueprintMCP` enabled. Per project history (OPENCODE_TECHNICAL_OBSERVATIONS.md), this plugin was **permanently disabled** due to security concerns — it exposes ~60 tools via an unauthenticated TCP socket (port 55558). Claireon's `python_execute` is the same execution surface.

**Recommendation:** Disable UEBlueprintMCP in `.uproject` when running Claireon. Two unrestricted Python execution surfaces on the same project is an unnecessary attack surface.

## Required Dependencies (all engine-bundled, now in .uproject)
| Plugin | Source |
|--------|--------|
| Claireon | Plugins/Claireon/ (source-only checkout) |
| GameplayAbilities | Engine/Plugins/Runtime/GameplayAbilities |
| Chooser | Engine/Plugins/Chooser |
| Metasound | Engine/Plugins/Experimental/MetasoundExperimental |
| ModularGameplay | Engine/Plugins/Runtime/ModularGameplay |
| ModelViewViewModel | Engine/Plugins/Editor/ModelViewViewModelPreview |
| MotionWarping | Engine/Plugins/Animation/MotionWarping |
| Niagara | Engine/Plugins/Experimental/ChaosNiagara (+ others) |
| NNERuntimeORT | Engine/Plugins/NNE/NNERuntimeORT |
| PCG | Engine/Plugins/Experimental/PCGBiomeCore |
| PropertyBindingUtils | Engine/Plugins/Runtime/PropertyBindingUtils |
| SQLiteCore | Engine/Plugins/Runtime/Database/SQLiteCore |
| StateTree | Engine/Plugins/Runtime/GameplayStateTree |

## Files Created/Modified
| Path | Action |
|------|--------|
| `BS_GodFile.uproject` | Modified — added 13 plugins |
| `.claireon/launch_editor.json` | Created — proxy launch config |
| `Scripts/LaunchEditor.ps1` | Created — editor build+launch script |
