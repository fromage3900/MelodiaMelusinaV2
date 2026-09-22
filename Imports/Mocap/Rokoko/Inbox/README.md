# Rokoko Inbox

Drop Rokoko Studio FBX exports here — not onto `SK_Melusina` directly.

## Before you record (once)

Two things make or break a take:

1. **Locomotion filter ON** (filter panel on the clip) — Studio reconstructs
   world travel from foot contacts. Without it the character jogs in place.
2. **Export checkbox: "Extract Root Motion"** (added in Studio 2.3.2) — puts
   that travel onto a root bone in the FBX. Without it the export is useless
   for locomotion — the 2025-12-15 camera-suite takes had translation stripped
   from every bone and had to be abandoned for root motion.

Trial note: Vision processing on the Pro trial is capped at **30 s/month** —
keep clips short (2–4 s per take is plenty for locomotion loops).

## Naming

```text
A_Rokoko_RunCycle.fbx     →  run the gate  →  retarget lane
A_Rokoko_WalkLoop.fbx     →  run the gate  →  retarget lane
```

Prefer combat-aligned stems when you can: `Idle`, `Walk`, `Run`, `Sprint`,
`Dodge`, `Stab`, `HitReact`, `Victory`.

## The gate (run on every export)

```powershell
& "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup `
  -P Tools/mocap/rokoko_intake_gate.py -- "Imports/Mocap/Rokoko/Inbox"
```

Writes `intake_report_<timestamp>.json` into the Inbox. Verdicts:

| Verdict | Meaning | Action |
|---|---|---|
| `ROOTED` | take travels (>0.5 m/s sustained, >1 m path) | clear for retarget |
| `IN_PLACE` | stripped export | re-export with Root Motion ON |
| `NO_HIP` / `NO_ANIMATION` | couldn't measure | inspect manually |

A real run cycles ~1.1 s per step; the report's `one_step_period_s` should be
in that ballpark — a sanity check that you got the take you think you got.

## After the gate passes

Import (editor open):

```python
import import_rokoko_mocap as r
r.main(import_only=False)  # import + retarget
# or: r.main(import_only=True) then Tools/run_headless_mocap_retarget.ps1
```

Bone profile must match `Imports/Mocap/Rokoko/CharacterRef/` (`SK_MocapSource` export).
Full SOP: `Docs/ROKOKO_MELUSINA_MOCAP.md`.
