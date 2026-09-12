# Art Spine Cleanup — 2026-08-13

`python Tools/art_gates.py --strict` fails `spine_hygiene` with 13 files: 11 WIP master
variants and 2 misplaced `MI_` instances, all inside `Content/EnvSandbox/Materials/Masters/`.
These are `.uasset` files — per `CLAUDE.md`, moving or deleting them is a Red action and
needs owner sign-off, so nothing below has been touched. This is a listing for the owner to
approve a disposition on, in one pass.

**Canonical pair — do not touch:** `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.uasset`
and `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend.uasset` (the
un-suffixed names). Everything else in the table is a variant, backup, or misplaced instance
of one of these two.

| Path | Size | Appears to be | Recommended disposition |
|---|---|---|---|
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_ACTIVE_QUARANTINE_20260729_1139.uasset` | 251,079 B | A quarantined-in-place snapshot of the landscape master from 2026-07-29, timestamped mid-day (11:39) — named as the state that was actively broken/under investigation that day. | Archive to `Docs/_Superseded` equivalent art location (e.g. `Content/_Archive/Materials/`) or delete once owner confirms the live master is stable past that date. |
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_AUTHORED_RESTORED_20260729.uasset` | 186,798 B | A restored-from-authored-state snapshot from the same repair day. | Archive — likely superseded by the current canonical master; keep only if owner wants a restore point. |
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_BACKUP_20260728.uasset` | 169,882 B | Pre-repair backup, one day before the 20260729 repair cluster. | Archive — oldest of the landscape backups; safe to demote once repair is confirmed durable. |
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_LIVE_RENDER_REPAIR_20260729.uasset` | 250,744 B | Mid-repair checkpoint from the same day, largest of the "LIVE" variants. | Archive — part of the same repair sequence as ACTIVE_QUARANTINE/AUTHORED_RESTORED. |
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_LIVING_STORYBOOK_PRETRIPLANAR_20260729.uasset` | 240,148 B | Checkpoint before triplanar work landed, "Living Storybook" naming suggests a Sakura/storybook-look experiment branch. | Archive — pre-triplanar state, keep only if triplanar work needs a rollback point. |
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_LIVING_STORYBOOK_WORK_20260729.uasset` | 240,100 B | In-progress "Living Storybook" work variant, adjacent to PRETRIPLANAR above. | Archive with the PRETRIPLANAR sibling — same experiment. |
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_SAFE_FALLBACK_20260729.uasset` | 32,928 B | A minimal fallback variant (much smaller graph than the others — likely a stripped-down safe version kept during the repair). | Keep or archive per owner call — a genuine fallback may be worth retaining outside the spine as an emergency asset; do not delete without checking if anything still references it. |
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_TRIPLANAR_WORK_20260729.uasset` | 240,058 B | In-progress triplanar-projection work variant. | Archive — check first whether triplanar work has since landed in the canonical master; if not yet merged, flag to owner before archiving. |
| `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_BACKUP_20260728.uasset` | 593,228 B | Pre-repair backup of the Universal master (the larger of the two canonical masters), same date as the landscape backup. | Archive — largest file in the set; confirm it is superseded by the current `M_Master_Toon_Universal.uasset` before deleting. |
| `Content/EnvSandbox/Materials/Masters/M_SpaceParallax_Test.uasset` | 17,435 B | An unrelated one-off test material (parallax space effect), not a Toon-spine variant at all — just parked in the wrong folder. | Move out of Masters/ into a scratch/test location, or delete if the experiment is abandoned. |
| `Content/EnvSandbox/Materials/ToonProfiles/TP_Test.uasset` | 3,706 B | A test toon profile, smallest file in the set. | Delete if it was a throwaway test; archive if it documents a profile shape worth keeping as reference. |
| `Content/EnvSandbox/Materials/Masters/MI_IridescentRock.uasset` | 24,800 B | A material *instance* (not a master) misplaced in `Masters/` — also flagged separately by the `naming` gate for using `MI_` in a folder that requires `M_`. | Move to `Content/EnvSandbox/Materials/Instances/` (or wherever the project's instance folder is) — this is a relocation, not a deletion candidate. |
| `Content/EnvSandbox/Materials/Masters/MI_SakuraLandscape.uasset` | 35,831 B | Same issue as above — a Sakura-landscape instance sitting in the Masters/ spine folder. | Move to `Materials/Instances/`. Note `L_SakuraPath` content is human-owned per `CLAUDE.md` — do not alter the instance's parameters while relocating, path-only move. |

## Notes for the owner's pass
- All 9 of the `_BACKUP_`/`_ACTIVE_QUARANTINE_`/`_AUTHORED_RESTORED_`/`_LIVE_RENDER_REPAIR_`/`_LIVING_STORYBOOK_`/`_SAFE_FALLBACK_`/`_TRIPLANAR_WORK_` landscape-master variants share two dates (2026-07-28 and 2026-07-29) and read as a single repair session's checkpoint trail plus one Universal-master backup from the same window. If that repair is confirmed durable in the current canonical masters, all 9 are archive/delete candidates as a batch.
- `M_SpaceParallax_Test.uasset` and `TP_Test.uasset` are not part of the repair trail — they are unrelated test assets that landed in the spine folder and should be triaged independently.
- The two `MI_` files are relocations, not deletions — fixing their location alone clears their `naming` gate failure without any content risk.
- Nothing in this document has been moved, deleted, or otherwise modified. `python Tools/art_gates.py --strict` still reports the same 13-file `spine_hygiene` failure after this pass.
