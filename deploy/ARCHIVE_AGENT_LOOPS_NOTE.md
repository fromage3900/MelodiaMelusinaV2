# STOP — agent overnight loops are not the school verify path

Use the fixed smoke queue instead of free-form Cursor/agent slice loops:

```powershell
cd C:\EnvironmentPortfolio\BS_GodFile\deploy
.\run_blender_smoke_queue.ps1
.\verify_melodia_studio.ps1
```

Do not treat `G:\EnvironmentPortfolio` mirrors as SSOT. Edit and sync from:

`C:\EnvironmentPortfolio\BS_GodFile\deploy\`

Existing `SURREAL_*_LOOP_STOP` files remain in force for overnight agent slices.
