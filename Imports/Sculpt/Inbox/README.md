# Sculpt Inbox

Drop finished (or checkpoint) mesh exports here — **not** into `Content/` and **not** over an existing `.uasset` path.

## Naming

```text
SM_<Role>_<Name>_vNN.fbx          static mesh / prop / ornament
SK_<Character>_<Part>_vNN.fbx     skeletal (character / wardrobe)
T_<Name>_vNN.png                  texture companion (optional)
<meta>.sculpt.json                sidecar (optional but preferred)
```

Examples: `SM_Orn_RoseWindow_8Petal_v01.fbx`, `SK_Melusina_Coat_v03.fbx`

## Rules (AGENTS / live-ops)

1. Iterate in Blender / ZBrush. Export **once** when ready — each FBX version costs full LFS size.
2. Never import FBX onto a path that already has a `.uasset` (creates a redirector; hours of pain).
3. One concern per commit when promoting to Content (`feature/sculpt-…` or binary-only branch).
4. Run offline check before asking for UE import:

```bash
python Tools/sculpt_intake_check.py
python Tools/sculpt_intake_check.py --limit-mb 50
```

5. After a successful UE import, move the FBX to `Imports/Sculpt/Archive/` (local; not required in git).

See `Docs/SCULPT_ASSET_INTAKE_2026-08-11.md`.
