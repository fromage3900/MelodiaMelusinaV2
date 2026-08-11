# Mobile scan → ZBrush → UE + Rokoko / Live Link (Melusina)

**Date:** 2026-08-11  
**Authority sculpt path:** ZBrush (always).  
**Scan front-end:** Polycam primary, Kiri Engine secondary.  
**Mocap:** Rokoko Studio + Live Link preview; FBX → `SK_MocapSource` → `RTG_Mocap_to_Melusina` for game clips.  
**Companions:** [`SCULPT_ASSET_INTAKE_2026-08-11.md`](SCULPT_ASSET_INTAKE_2026-08-11.md), [`ROKOKO_MELUSINA_MOCAP.md`](ROKOKO_MELUSINA_MOCAP.md), [`LIVEOPS_GIT_SOP_2026-08-11.md`](LIVEOPS_GIT_SOP_2026-08-11.md)

## Locked choices

| Job | Tool | Notes |
|-----|------|-------|
| Quick scan | **Polycam** | LiDAR / prop / room → OBJ/GLB out |
| Detail photogrammetry | **Kiri Engine** | Denser capture when worth the wait |
| Sculpt authority | **ZBrush** | Dynamesh / ZRemesher / your brush packs (local, not git) |
| Suit / gloves / face capture | **Rokoko Studio** | Character profile from `SK_MocapSource` FBX |
| Live preview | Epic **Live Link** + Rokoko Studio Live | Drive **source** mesh only |
| Game anim | FBX inbox → retarget | Never bake shipping clips straight onto `SK_Melusina` via Live Link |

Blender Live Link port **9876** is mesh/env sync — leave it alone for mocap.

```text
Phone Polycam / Kiri
        │
        ▼
     ZBrush  ──►  Imports/Sculpt/Inbox/*_vNN.fbx
                        │
                        ▼
              sculpt_intake_check.py → one UE import → Universal MI → one LFS commit

Rokoko Studio
   ├─ Live Link preview → SK_MocapSource / Newton (rehearsal)
   └─ FBX → Imports/Mocap/Rokoko/Inbox
              → import_rokoko_mocap.py
              → A_Src_Rokoko_<Take>
              → RTG_Mocap_to_Melusina
              → A_Mocap_Rokoko_<Take> on Melusina
```

## Phone / on-the-go

- **Capture** on phone (Polycam/Kiri); **sculpt** in ZBrush on desktop (or when docked).
- **Steer** MelodiaMelusinaV2 from Cursor iOS: docs, intake checks, PR review — not LFS mesh pushes.
- Sync finished FBX via iCloud/Dropbox into the Windows tree’s `Imports/Sculpt/Inbox` or `Imports/Mocap/Rokoko/Inbox`, then run the check/import on the UE box.

## Sculpt drop (after ZBrush)

1. Export versioned FBX: `SM_<Role>_<Name>_v01.fbx` or `SK_Melusina_<Part>_v01.fbx`.
2. Drop in `Imports/Sculpt/Inbox/` (+ optional `.sculpt.json` from `specs/sculpt/sidecar.example.json`).
3. `python Tools/sculpt_intake_check.py --limit-mb 50`
4. One editor import to a **new** `/Game/...` path (never overwrite an existing `.uasset`).
5. Assign `M_Master_Toon_Universal` for environment props; one LFS commit.

## Rokoko recording (Melusina)

1. One-time: `Tools/setup_rokoko_livelink_plugins.ps1` + Rokoko Studio Live for UE 5.8 (see Rokoko doc).
2. Export `SK_MocapSource` → `Imports/Mocap/Rokoko/CharacterRef/` → Rokoko character profile.
3. Record take → FBX → `Imports/Mocap/Rokoko/Inbox/`.
4. Editor: `import import_rokoko_mocap as r; r.main(import_only=False)`.
5. Verify `A_Mocap_Rokoko_*` on Melusina. Prefer bake+retarget for shipping; Live Link is rehearsal.

If neck/spine warps: finish Melusina neck hierarchy fix before stocking a large library.

## LFS / Echo

- Mesh/mocap FBX stay in `Imports/` (gitignored binaries) until intentional publish.
- Finished `.uasset` anims/meshes: one concern per commit; collab branches ≤50 MB unless `feature/sculpt-*` / `MELODIA_LFS_LIMIT_MB=512`.
- Capture does not close Echo `runtime` — still needs playable ledger evidence.
- `docs50` / `slice50` are the real ≤50 MB packs — do **not** treat old `lightweight` (~1.9 GB) as a phone/collab slice (Grok collab research 2026-08-11).

## Windows PC checklist (cloud cannot do this)

No private Cursor worker is attached to the foundation cloud agent. Run these on the UE workstation:

1. `git lfs pull --include="Content/EnvSandbox/**,Content/TurnBasedJRPGTemplate/**"` — EnvSandbox is often **0 files** in cloud; Universal PCG/`M_Master_Toon_Universal` need that pull before prop MI assign or `placement50` measure.
2. `python Tools/sculpt_intake_check.py --limit-mb 50` then one editor import to a **new** path.
3. Rokoko: `Tools\setup_rokoko_livelink_plugins.ps1` once → CharacterRef FBX → Inbox takes → `import_rokoko_mocap.main()`.
4. Gameplay: wire stock `BP_BattleUI` / `BP_BattleController` (keep authority); Melodia overlays only — [`Reports/JRPG_BP_REPLACEMENT_PRIORITY_2026-08-11.md`](Reports/JRPG_BP_REPLACEMENT_PRIORITY_2026-08-11.md).

Research digest (four read-only agents, **no research branch**): [`Reports/GROK_RESEARCH_FOLDIN_2026-08-11.md`](Reports/GROK_RESEARCH_FOLDIN_2026-08-11.md).
