# Git history landmines — 2026-09-02

**Inventory only.** These paths/objects are forever-cost while reachable from
`main`. Removing them from history requires owner-approved `git filter-repo` /
LFS prune under the destructive-operation gate in
[`GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md).

Forward policy: do not re-add equivalents. Do **not** agent-edit `.gitignore` /
`.gitattributes` without `SKIP_PROTECTION=1` + owner instruction.

## Still in the `HEAD` tree

| Hazard | Evidence | Risk |
| --- | --- | --- |
| `Plugins/PCGExtendedToolkit/.git_disabled/**` | ~94 tracked paths including `objects/pack/*.pack` (multi-MB raw packs) | Nested-git dump; pack blobs bypass normal LFS discipline |
| `_QuarantineAssets_*` / `_Quarantine_InvalidCookAssets_*` | ~70 tracked paths; LFS pointers still billed | Duplicate/shadowed assets kept "safe" but still cost storage |
| `CompatibilityLabs/**` backups & vocoder WAVs | Still LFS-tracked | Backup-in-Git anti-pattern |
| Root / experiment FBX & shirt textures | Present in LFS pointer set (`4thtimestillnobones.fbx`, shirt PNGs, etc.) | Scratch names on `main` |

## Large blobs in the object graph (>2 MB samples)

From `git rev-list --objects --all` (see
`Saved/Audit/git_large_blobs_2026-09-02.txt`):

| Approx size | Path |
| --- | --- |
| 20.1 MB | `86419_Zbrush_Orb_Brushes_pack_for_Blender_3D/textures/OrbSlash4.psd` |
| 19.0 MB | `TDImportCache/hairhairhairt.tdc` |
| 18.5 MB | Orb slash clean PSD |
| 16.0 MB | `Content/Python/quantum/qsharp_project/build_diag.txt` |
| 9.8 MB | `…/SK_MelusinaHair.uasset.boneless_20260730.bak` |
| 9.0 MB | `Plugins/Monolith/Tools/MonolithQuery/ThirdParty/sqlite3.c` |
| 5.2 MB | `Plugins/PCGExtendedToolkit/.git_disabled/objects/pack/pack-cdab8a….pack` |
| 6.1 MB | `Plugins/VRM4U/ThirdParty/assimp/bin/x64/assimp-vc141-mt.dll` |

Several of these are **not** LFS pointers historically — they inflate Git object
storage even when absent from a sparse working tree.

## Root-cause commit

`13717fb3` — *MelodiaMelusina V2: Electric Boogaloo* — ~8k-file foundation dump.
Expected for V2 cutover; still the origin of nested `.git_disabled` packs and
much of the LFS bill.

## Forward-only mitigations (allowed without rewrite)

1. Stop new commits under quarantine / CompatibilityLabs / scratch FBX roots
   ([`GIT_LFS_FORWARD_DISCIPLINE_2026-09-02.md`](GIT_LFS_FORWARD_DISCIPLINE_2026-09-02.md)).
2. Cold-archive superseded portfolio blends
   ([`LFS_COLD_ARCHIVE.md`](LFS_COLD_ARCHIVE.md)).
3. Prefer Perforce (or filesystem backup) for lock-sensitive creative assets.
4. Intake scripts / pre-commit already block many junk paths — keep using them;
   do not weaken them to "fix" landmines.

## Explicitly out of scope until owner orders

- `git filter-repo` / BFG / history rewrite
- `git lfs prune` / aggressive `git gc --prune`
- Remote branch deletion that might drop the last ref to an OID
- Deleting quarantine trees from `main` without a proven external backup

## Related

- [`GIT_HEALTH_2026-09-02.md`](GIT_HEALTH_2026-09-02.md)
- [`Reports/LFS_HEALTH_2026-08-13.md`](Reports/LFS_HEALTH_2026-08-13.md)
- [`Reports/GIT_LEFTOVERS_TRIAGE_2026-08-11.md`](Reports/GIT_LEFTOVERS_TRIAGE_2026-08-11.md)
