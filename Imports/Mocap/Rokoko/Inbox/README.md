# Rokoko Inbox

Drop Rokoko Studio FBX takes here — not onto `SK_Melusina` directly.

## Naming

```text
IdleTest.fbx   →  A_Src_Rokoko_IdleTest  →  A_Mocap_Rokoko_IdleTest
WalkLoop.fbx   →  A_Src_Rokoko_WalkLoop  →  A_Mocap_Rokoko_WalkLoop
```

Prefer combat-aligned stems when you can: `Idle`, `Walk`, `Run`, `Dodge`, `Stab`, `HitReact`, `Victory`.

## Import (editor open)

```python
import import_rokoko_mocap as r
r.main(import_only=False)  # import + retarget
# or: r.main(import_only=True) then Tools/run_headless_mocap_retarget.ps1
```

Bone profile must match `Imports/Mocap/Rokoko/CharacterRef/` (`SK_MocapSource` export).  
Full SOP: `Docs/ROKOKO_MELUSINA_MOCAP.md` · combined phone pipeline: `Docs/MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md`.
