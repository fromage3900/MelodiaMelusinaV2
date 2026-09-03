# Tomorrow Prep — living doc

**Updated:** 2026-09-03 (hourly prep pass) · Updated in place — do not fork dated copies.
Scope: world building · reusable chapter structure · packaged builds · Shorewake testing.

---

## Reconciliation — where docs and filesystem disagree

**`CURRENT_STATE.md` is STALE on packaging.** It still lists (lines 41-42):

| | CURRENT_STATE.md | Ledger (latest row) | Filesystem |
|---|---|---|---|
| `package_build` | FAIL 2026-08-14 | **pass** 2026-08-14 | — |
| `package_launch` | FAIL 2026-08-14 | **pass** 2026-09-03 02:32 | `BS_GodFile.exe` exists on G: |

**Trust the ledger + filesystem.** Cook #3 exited 0 and the packaged build boots and loads
`L_MelodiaMainMenu` (0 fatals). `CURRENT_STATE.md` line 120 ("itch.io upload — once
package_launch passes") is now unblocked. That file needs an owner edit; this pass is not
permitted to write it.

All 11 P0 gates pass on latest-row-per-gate. Offline 12/12, MCP regression 38/38.

---

## Ready to go

| Item | Evidence |
|---|---|
| Packaged Win64 build boots outside editor | `G:\melodia_packages\P0_Closeout_20260902\Windows\BS_GodFile.exe`; its log shows `Mounted IoStore … LoadMap L_MelodiaMainMenu … 0.348976s`, 0 fatals |
| Cymatics + optical-LOD contract on ALL 10 masters | 14/14 scalars verified live on each; re-verify anytime with `Content/Python/wire_cymatics_masters.py` (idempotent) |
| Shorewake equips | `grant → equip → GetEquipped(SKIRT) == Cos_ShorewakeDress`. Catalog record added (SKIRT/RARE → `SK_ShorewakeDress_Melusina465`) |
| Faraway Mother level populated | 9 actors; ornaments now genuinely height-aware (terrain Z 24-60, per-ornament offsets) |
| Height-aware raycast fixed | `faraway_mother_prototype_build.py` — real trace, ignores haze box/PPV/sibling ornaments, raises instead of falling back |
| Git working tree | Clean at last check; 8 commits landed tonight; bundle `BS_GodFile-allrefs-20260903-0145.bundle` verified complete |

---

## Blocked

| Blocker | Smallest next action |
|---|---|
| **Repo cannot push at all.** 3 LFS pointers in history have no binary in `.git/lfs/objects`: `Blue_Nebula_8`, `Purple_Nebula_7`, `Purple_Nebula_6` (`bfeca0bc`, `6e669910`, `b5bd919a`). GitHub rejects with `GH008` after uploading 11 GB. | Source those 3 textures OR excise them from history. Owner decision — not a 2 a.m. fix. |
| Packaged route can't run — 3 assets exist on disk but were not cooked: `DA_MelodiaIntegrationConfig`, `DA_MelodiaPersonaContent`, `128BPMarpeggiomelody_beatgrid` | Add `+DirectoriesToAlwaysCook` for `/Game/MelodiaIntegration/Config` and `/MIDI` (established pattern, 3 existing entries), then re-cook (~15 min warm). `DefaultGame.ini` is never-touch → needs owner sign-off. |
| Shorewake renders grey | All 48 `SW_Dress_P*` MIs bind 0 texture params; the `T_MelusinaC_DressShorewake_*` suite is on disk unused. Bind them. |
| `LV_FarawayMother_Prototype` renders black | Level has ZERO light/sky actors. Add a lighting rig before any capture. |
| 3 masters referenced by MI specs don't exist | `M_Master_Melusina_Costume`, `M_Master_FarawayMother_Fabric`, `M_Master_Starskiff_Rigid` — build them, or repoint the specs at `M_Master_Toon_Universal`. |
| Melusina T-poses in `LV_FarawayMother_Prototype` | No anim class driving her in that level. |

---

## Landmines — these silently no-op or mislead

1. **`Bass` / `GlobalReactivity` = `BattleIntensity`** — exactly 0 outside battle. Not audio bass.
2. **`Treble` == `BeatPulse` == `BeatIntensity`** — one float under three names, 0 with no music clock.
   *(The un-cooked beat-grid MIDI above is one reason a packaged run has no clock.)*
3. **`GlobalEmissiveBoost` / `GlobalSparkleIntensity` / `TimeOfDayWarmth` have NO writer** anywhere
   in `Source/` — permanently frozen at MPC defaults. Wired-looking, inert.
4. **Two `MPC_Melodia_Palette` assets.** Canonical `/Game/Melodia/_PROJECT/04_Materials/` (47 scalars).
   `/Game/_PROJECT/04_Materials/` is DEAD (Aug-11, 17 scalars) — `MF_MeluSparkle` and
   `MF_MeluPaletteColors` still point at it with empty `ParameterName`.
5. **Setting a CollectionParameter name on a material instance is a silent no-op.**
   `klein_veil_import.py` skips unknown scalars without complaining.
6. **`DA_MelodiaCosmeticCatalog` is on the PLUGIN mount** `/MelodiaWardrobe/Catalog/`, not `/Game/`.
   Catalog-first, fails closed (`unknown_id`). `EditorAssetLibrary.save_asset` returns False on it —
   use `EditorLoadingAndSavingUtils.save_packages`.
7. **`MPD_Default.uasset` is quarantined inside the UE_5.8 engine install** to make the cook pass.
   An engine update or verify-install restores it and packaging breaks again.
8. **Never add `DirectoriesToNeverCook` for an enabled plugin path** — causes
   "registered … for two different domains" ensure, which fails the cook on the error tally.
   Proven twice (PCGExtendedToolkit, MeshPartition).
9. **Master `.uasset` files are frequently read-only on disk** — saves fail and pop a modal that
   blocks Monolith entirely (`MODAL_OPEN`). `chmod u+w` first.
10. **A second editor writes `Saved/Logs/BS_GodFile_2.log`**, not `BS_GodFile.log`.
11. **Editor crashed twice tonight**, both during heavy master-material save bursts.

---

## Chapter reusability — 6-phase loop vs disk

| Phase | Asset | On disk |
|---|---|---|
| 1 Sanctuary | `L_MelusinaMorning` | ✅ |
| 2 Overworld / music-key | `LV_SeaAbove_Prototype`, `APCGHeroMusicGraphHost` | ✅ both |
| 3 Battle arena | `L_KaleidoNave` | ✅ |
| 4 Reward | idempotent intent-ID path | ✅ (gate `repeat_consume`) |
| 5 Traversal upgrade | `IMelodiaTraversalCapabilityProvider` | ✅ — but only `glide`/`dash`/`swim` exist; `SeaAboveResonance` in the Shorewake manifest is NOT in `Source/` |
| 6 Checkpoint / menu | `BP_JRPGSaveGame`, `L_MelodiaMainMenu` | ✅ both |

Every phase has real assets. The gap is **wiring and lighting**, not missing content.

---

## Suggested order for tomorrow

1. **Lighting rig for `LV_FarawayMother_Prototype`** (~20 min) — nothing can be judged until this exists.
2. **Bind the 48 Shorewake MI texture sets** (~45 min) — turns a grey garment into a real lookdev subject.
3. **`AlwaysCook` + re-cook** (~30 min, mostly unattended) — makes the packaged route actually playable.
4. **Decide the 3 missing masters** (~30 min) — build or repoint.
5. **The 3 missing LFS objects** (owner decision) — until then nothing leaves the machine except G: bundles.
6. **Retire the dead `MPC_Melodia_Palette` copy** (~15 min) — repoint the 2 material functions, set their `ParameterName`.

Not urgent: the ~144 orphaned PBR stems (that count is self-flagged stale-high; re-run
`Tools/pbr_full_scan.py` for a real number before spending time on it).
