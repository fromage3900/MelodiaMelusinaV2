# L_MelusinaMorning PCG / Massive World — coverage audit + drift close

**Date:** 2026-10-01
**Trigger:** owner report that "landscape aware PCG massive world assets" appeared lost
**Verdict:** No PCG graph, data asset, or biome asset was lost. A real version-control
gap existed and is now closed on the git side. The p4 side still needs an owner submit.

## What was actually missing

Nothing was deleted. The `L_MelusinaMorning` OFPA mirror was only *partly* versioned:

| Population | Count | State before |
|---|---|---|
| External actor files on disk | 258 | — |
| Tracked in git | 199 | versioned |
| **Untracked in git** | **59** | **not in git at all** |
| ├─ of those, p4-opened for add | 43 | staged in Perforce, unsubmitted |
| └─ **of those, never in p4 (`no such file`)** | **16** | **second copy did not exist** |

The 16 are the real exposure. They were reachable from the level on this workstation
and had no copy anywhere else. They now have a git copy (commit `e09cf1c7a`) and are
p4-opened for add in the default changelist, awaiting an owner submit.

## The PCG / Massive World assets themselves — all present

| Asset family | Files | git | p4 depot |
|---|---|---|---|
| `Content/Melodia/PCG/` (Core, MassiveBiome, Meadow, Morning) | 17 | 17 tracked | 17 |
| `Content/Melodia/WorldCompiler/` (`PCG_WorldCompiler_PointField`, DT, `EUW_WorldCompiler`) | 11 | 11 tracked | present |
| `Content/Massive/` (MassiveWorld + MassiveShared, incl. `PCG_Biome*`, `PCG_Cliff*`, `PCG_Lake`, `PCG_River`, `PCG_Slope`, `PCG_Spread`) | 206 | 4 tracked / 202 ignored | 206 |

The Massive World PCG graph set is whole. `Content/Massive` is the one family where
**git holds almost nothing** (4 of 206) and Perforce is the only real copy — that is
the arrangement to watch, not a loss.

## What the untracked actors referenced

ASCII + UTF-16LE token scan of the 59 (UE stores `FString` payloads wide-char, so a
byte-only pass reports false zeroes):

- **4 `PCGComponent` actors** bound to `/Game/Melodia/WorldCompiler/PCG_WorldCompiler_PointField`
  (`0/NS/…`, `1/U8/…`, `B/MY/…` — the last two are the ~1.1 MB ones)
- **1 landscape-material actor** → `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CliffGrass`
- remainder: Niagara / VFX / mesh / brush actors (`NS_Morning_PetalDrift`,
  `NS_Morning_PollenSparkle`, `NS_Morning_GlitterGlint`, `NS_Morning_PondMist`,
  `NS_Morning_WindFront`, Brushify cliff slabs)

Already-tracked actors confirm the intended wiring is intact and referenced
`PCG_Melodia_MassiveBiome`, `PCG_Biome_RockScatter`, `DA_Melodia_RockScatter`,
`PCG_Meadow_RainbowBloom`, `BP_Morning_GoldenSpiral`, `PCG_VegetationTransform`.

## Why it looked like PCG was lost

The level file itself is 14 KB and holds no PCG strings — every component lives in an
external actor. With 59 of 258 actors untracked, opening the level on a fresh machine
(or after any `git clean`) silently dropped the PCG point-field components and the
landscape material actor. That reads exactly as "the PCG work disappeared."

## Actions taken

1. `e09cf1c7a` — 59 external actors committed to git (3.45 MB, LFS pointers verified
   on the three ~1.1 MB files; set-equality guard confirmed zero files outside the
   intended tree).
2. 16 previously-invisible actors confirmed p4-opened for add in the default changelist.
3. No graph, data asset, level, config, or protected file was modified. No p4 submit.

## Owner decisions still open

- **p4 submit.** The 16 at-risk actors and the wider 184-file opened set sit in pending
  changelists. None were submitted. This is the only remaining action that closes the
  "only one copy" risk on the Perforce side.
- **`Content/Massive` (202 files) is Perforce-only.** It is not in git and cannot be
  until someone decides it belongs in the git-tracked set; adding it is a large LFS
  decision, not a cleanup.
- **L_MelusinaMorning has no landscape floor** (per the World Compiler contract). The
  "landscape aware" placement runs `terrain.kind: ground_probe` against the
  `SM_PM3D_Sphere3D*` islands. If a new landscape is wanted, that is a separate owner
  decision — do not infer one from this audit.
