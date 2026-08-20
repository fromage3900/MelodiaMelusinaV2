# Handoff — Electric Dreams closeout + editor restart (2026-08-13 ~14:10 ET)

**Pick up:** [`_SESSION_HANDOFF.md`](../../_SESSION_HANDOFF.md) (13:30 lock-in) ·
[`_TASK_QUEUE.md`](../../_TASK_QUEUE.md) (latest queue) ·
[`Saved/Audit/stale_ref_closeout_2026-08-13.md`](../../Saved/Audit/stale_ref_closeout_2026-08-13.md) (evidence).

**Context: the editor is being restarted + rebuilt by the owner right now.** The next
session should not trust any PID found in docs — run `Get-Process UnrealEditor` and use
what it returns. Port 9316 is fixed by config; the starting editor owns it.

## What just landed (this lane, committed)

| Commit | What |
|---|---|
| `db56f084` (on `feature/repo-lockin-20260813`) | **ED stale-ref closure.** `Tools/copy_ed_closures_20260813.py` copied **37 Asmbly external-actor packages** (`Content\__ExternalActors__\Asmbly\*`), `Content\Textures\EnvRnd\t_softsquare_01_m.uasset` and `Content\volume.uasset` from the G: superset; byte-verified per file. Queue row `Stale-ref closeout verify` → **DONE**. (Commit also carries unpushed S3-lane queue rows already in the worktree.) |

**Branch state:** 11 commits ahead of `origin/main`, **NOT PUSHED** (GitHub 443 issues;
the queue's `Push feature/repo-lockin-20260813` row is the sync lane's job). Nothing in
the working tree is mine beyond the committed files — the other modified/untracked paths
(`Content/Python/*`, `deploy/*`, `BS_Melusina_Locomotion.uasset`, `Exports/*`, ...) belong
to other lanes; do not commit or revert them.

## Why the copy happened (one paragraph)

The owner imported Electric Dreams as building blocks, not the full map. After the import,
273 stale `/Game/` references remained on C: (packages referenced by resident assets,
present only on G:). Of those, 37 were Asmbly external actors needed by the 37 assembly
umaps already on C:. Copied those + 2 tiny packages referenced by resident Megascans
decals / AudioModulation buses. **Result: 234 stale refs, all deliberate skips** — 220 ED
world actors ("not the full map"), 7 datalayers, 5 ED demo blueprints, `l_melodia_dreamstate`
(owner decision pending), 1 dirtmask (ED-world-only). The copied actors introduced **zero**
new missing refs (drop was exactly 39 = 37 + 2).

## Verified before the restart (live registry, old editor PID)

- **37/37 Asmbly external actors** visible in the asset registry after a full `/Game` force
  rescan; `Asmbl_CliffWall_00` package loads clean (external actors register under their
  owning WorldPartition map — expected pattern, not a defect).
- `t_softsquare_01_m`, `volume`, `fx_amb_quad_global_lp` all present.
- Game-loop maps 0 real missing (re-checked this session): `L_KaleidoNave`,
  `L_MelusinaMorning`, `L_MelodiaMainMenu`, `L_FallenMoon`.
- ED audio (`/Game/Audio/Aud_Source/fx_Amb_Quad|Spot|Prop`, 28 files) already landed in the
  owner's import — script reported SKIP-EXISTS 28/28; 555 files under `Content\Audio`.

After the restart the fresh editor will re-scan `/Game` on startup; expect the registry to
see all of the above without any action. Optional re-proof: re-run
`python Saved/scan_stale_strings_20260812.py` (expect 234) and one registry check.

## Owner's scenery pass — what's available now

Dress `L_MelusinaMorning` / `L_FallenMoon` with:
- **Assemblies:** `Content\Asmbly\Asmbl_*.umap` (37; cliff walls, grounds, plants, rocks,
  riverbed embankments, foliage PL_*) + their actors now resident.
- **Audio ambience:** `fx_Amb_Quad` (3 riverbed/canopy loops), `fx_Amb_Spot` (15 close loops:
  foliage rustle, puddles, water trickle), `fx_Prop` in `Content\Audio\Aud_Source\`.
- Map ambience onto the existing Melodia audio stack (SCL_Ambience → SUBMIX_Ambience →
  `BP_MelodiaAmbient_GlobalWeather`); no new C++ needed.

## Final thoughts — ED, native water, long-term integration

**ED integration, where it stands.** Done: assemblies + ambience audio are building blocks on
C:, closure verified, licensing clean (Epic official sample). Skipped deliberately: 220 world
actors (661.9 MB), Soundscape palettes (191 files), demo `mx_Music`, datalayers. All recorded
in `Saved/Audit/stale_ref_closeout_2026-08-13.md`. If a future scene wants the ED world's
look wholesale, that is a fresh, owner-approve-again import — not a gap in this one. Wildlife
birdsong palettes (`amb_ss_*`) were part of the skipped Soundscape system; if birdsong is
wanted later, prefer the project's own ambience stack (`A_Ambience_Melusina_98bpm` +
`BP_MelodiaAmbient_GlobalWeather`) over resurrecting the plugin-format system.

**Native UE water.** The project already has a deep, source-integrated native-water story —
V10 (`Docs/WATER_V10_FINALIZATION_STATUS_2026-08-09.md`): `MI_WaterV10_NativeDefault` +
`DA_WaterV10_Default` profiles with `ShallowWaterSimComponent`/`WaveFoamSimComponent`
resolved, `.uproject` enables Water + WaterAdvanced + WaterExtras + MeshPartitionWater +
PCGWaterInterop, and `ApplyProjectWaterDefaults` auto-assigns V10 surface/underwater
materials + the ripple bridge whenever a native Water Body registers. The ED assemblies we
copied include exactly the river-carve pieces (`PL_MediumRiverbedEmbankment_01`,
`PL_SmallRiverbedEmbankment_01/02`, `PL_DriedRapid_01`, `ground_riverBend*`, waterfall
cliffs) — so river scenery in Morning/Fallen Moon = drop `WaterBodyRiver`/`WaterBodyCustom`
into those carved channels and the project defaults do the material wiring. Keep full-sim
bodies rare (ShallowWater/WaveFoam cost); reserve `BP_MelodiaWaterSimulationZone` + FLIP2D
pools for water the player actually touches/enters (`NS_WaterV10_FLIP2D_Pool/Splash`,
contact channel already exclusive). Audio: ED's `fx_amb_quad_riverbed_*` loops ARE usable
river ambience under SCL_Ambience→SUBMIX_Ambience, alongside the existing
`MS_Water_*` metasounds (SurfaceEntry/Impact/Reemergence/SurfaceMovement/UnderwaterBubble).
After any water dressing, re-run `Content/Python/verify_water_v10_profile.py` and the
`L_WaterV10_NativeValidation` map to keep the water gate visibly green.

**Long-term project integration.** Order matters: the three gates (`save_load`,
`repeat_consume`, `package_launch`) close **before** the Perforce move (queue row). C: is now
~20,440 assets and fully self-sufficient for the loop (all copied pieces resident, no G:
dependency at cook time) — keep it that way: future imports must stay selective and
plan-driven like this one (manifest → copy → rescan prove-closure), because G: remains the
superset backup. Watch: LFS lock discipline (0 locks held on 2,224 lockable files), the
duplicate-tree cleanup (two `BP_BattleUI` + 33-asset mirror, owner sign-off required), and
the art-gates baseline (120 duplicate short names) — all are pre-existing, none introduced
this session. Rhythm stays fully classical (no quantum in gameplay per AGENTS.md).

## After the scenery pass (do not start before)

Remaining completion gates — **`runtime` is CLOSED, do not reopen or re-prove**:
1. **`save_load`** — canonical `BP_JRPGSaveGame` slot across a full process restart.
2. **`repeat_consume`** — flag + reward restore without duplication;
   `melodia:stat:` idempotent per IntentId.
3. **`package_launch`** — Development build launches and plays the route outside the editor.

Evidence standard still applies: a gate closes only with a `record_gate.py <id> pass` ledger
row + committed harness + real-input frames where applicable.

## Never again / still in force

- `git clean -fd` / `git checkout -- .` are catastrophic on this repo (bulk `Content/`
  untracked). Never run them.
- One editor only. No Python loading of skill Blueprints (`D_DamageType` death).
- Locks: rhythm + Quill hold. `l_melodia_dreamstate..umap` untouched pending owner call.
- New content touched this session is untracked by design — do not `git add` `Content/` bulk.
