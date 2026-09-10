# Smartsuit (Rokoko Studio Live) UE 5.8 port — 2026-09-09

## Done
- Set `EngineVersion` to `5.8.0` in `Plugins/Smartsuit/Smartsuit.uplugin`
- UHT: `BitmaskEnum` → `/Script/Smartsuit.EPlaybackChange` in `RokokoStudioCommandAPI.h`
- UE_LOG format sanitizer: `{0}` → `%s` in `VirtualProductionSource.cpp`
- `RunUAT BuildPlugin` **UnrealEditor Win64 Development** → SUCCESS
- Installed binaries:
  - `Plugins/Smartsuit/Binaries/Win64/UnrealEditor-Smartsuit.dll`
  - `Plugins/Smartsuit/Binaries/Win64/UnrealEditor-SmartsuitEditor.dll`

## Still open (shipping / packaged game only)
`UnrealGame` Win64 Development fails:
- `AnimNode_RokokoFacePose.cpp` / `SmartsuitPoseNode.cpp`: `NewObject` overload + missing `USkeletalMeshComponent` include
- Not required for editor Live Link preview

## Load
Restart Unreal Editor (or disable/enable Smartsuit) so modules load. Confirm Edit → Plugins → Rokoko Studio Live / Smartsuit, and Window → Virtual Production → Live Link.
