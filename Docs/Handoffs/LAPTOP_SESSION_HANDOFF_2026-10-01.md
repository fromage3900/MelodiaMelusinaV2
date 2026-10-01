# Laptop handoff — 2026-10-01 closeout

For the desktop peer agent and for the next laptop session. Read
`AGENT_START_HERE.md` first; this file only covers what changed today.

Branch: **`collab/laptop/session-2026-10-01`** (additive, 6 commits on
`35ea2666`). `main` and `origin/main` are **byte-identical to before this
session** — verified, not assumed.

**Start here, then §5b.** The animatic is the only item with a clock on it.

---

## 1. What was recovered

Three lanes existed only in the working tree. None was reachable from the
object store, and the branch's remote is `gone`.

| Commit | Lane | What |
|---|---|---|
| `c0063d1c` | **ANMN301 animatic — DUE Fri Oct 9** | v04 MP4 (19.6 MB), v04 VSE blend, build/fix/burn scripts, beat board, storyboard, copernicus textures, panels_final/ — 165 files |
| `d92c46f1` | **Brutalist GN** | `brutalist_city.py`, `brutalist_roofs.py`, `brutalist_uv.py`, `higgsas_pipeline.py`, health scripts, 7.9 MB showcase — 3154 insertions |
| `68c73b8f` | **Humber toon spine** | workflow + manifest v1 + schema |
| `f287c08e` | **Office props (this session's build)** | `GN_OFFICE_DeskCluster`, coverage manifest, health + stage scripts |

Superseded animatic artifacts deliberately left untracked: v01–v03 blends,
`proxy_v01`, `proxy_v01_posed`, `v04.blend1`. They are on disk and in the backup.

**77 files an earlier session had left staged** (75 `Saved/Audit/` brooch PNGs +
2 brooch-lab files) were unstaged, not committed. The pre-commit hook correctly
blocks `Saved/` build artifacts; they remain untracked and were never mine.

## 2. Cold backup

`P:\_laptop_safety\2026-10-01\` — **238 files, 97.3 MB**, outside the repo so no
git command can reach it. `BACKUP_MANIFEST.json` records HEAD, both main refs,
all 4 stash entries, and every path with an md5 of its first 8 MB.

Written by `Tools/repo_safety_backup.py` (committed in `f287c08e`), which
refuses to overwrite an existing destination. Stashes were **recorded, never
touched** — all 4 still present.

## 3. Open: `.gitignore` needs owner review — READ THIS

`.gitignore` is on the pre-commit never-touch table, and the working-tree version
carries **53 deleted lines** that predate this session. The deletions strip:

- the `!Content/EnvSandbox/Materials/` unignore chain that keeps **authored
  material masters** addable (its own comment records that a cross-line merge
  once dropped `M_Master_Nikki` and the blanket ignore then prevented restoring it)
- the reviewed `Content/TurnBasedJRPGTemplate/Blueprints/{Controllers,Projectiles,
  Units}` battle-guard `.uasset` exceptions
- `!Tools/setup_accessory_studio.py`, `!Tools/melodia_studio_census.py`,
  `!Tools/guard_protected_assets.py`, `!Tools/git_ok.py` and others

This session added exactly **one** line to that file:
`!Tools/office_prop_coverage.py`. It is **not committed** — committing the file
would delete those protections along with it.

**Action needed:** decide whether those 53 deletions are intended. If they are,
commit `.gitignore` alone with `SKIP_PROTECTION=1` and a message that says so.
If not, restore the deleted rules. Until then `Tools/office_prop_coverage.py`
and `Tools/repo_safety_backup.py` stay untracked-but-not-ignored — a `git add -A`
would sweep them in *with* the deletions.

## 4. Open: addon sync (Blender was open)

`blender.exe` PID 18036 was running at closeout, so the one-way install was
**not** run. Close Blender, then:

```
python deploy/_sync_addon_to_blender_5_2.py
blender -b --factory-startup --python Tools/melodia_studio_census.py -- --json Saved/Audit/census_2026-10-01b.json
```

`only_live` was measured **empty**, so this is a safe one-way install, not a case
where `sync()` would `rmtree` unreferenced live files.

The live addon is 3 files behind the checkout and is missing
`core.link_sockets`' self-link rejection.

Expected census delta: `603 -> 604`, `baseline new: 1`
(`GN_OFFICE_DeskCluster`). Then re-cut the baseline in the same change
(studio freeze rule 3) with `Tools/verify_full_registry.py`, after preserving
the old file to `Saved/Audit/registry_baseline_pre_officeprops_2026-10-01.json`.

## 5. Verified this session

| Gate | Result |
|---|---|
| `_melodia_health_office_props.py` | **PASS problems=0** — 189 nodes, 294v, all 6 toggles remove geometry, width lands on 1.400 m |
| `_melodia_health_brutalist_office.py` | PASS problems=0 |
| `_melodia_health_brutalist_cubicles.py` | PASS problems=0 |
| `_melodia_preset_audit.py` | 0 shadowed keys, 0 brand orphans, 3 packs 5/5 |
| `Tools/verify_brutalist_materials.py` | MATGATE PASS 11/11 |
| `Tools/melodia_studio_census.py` | PASS 603, 0 lost, 0 new (pre-sync) |
| `main` / `origin/main` | unchanged, verified by hash |
| 4 stashes | intact |

## 5b. ANMN301 animatic — NOT submittable (detail in its own doc)

Full write-up: **`Docs/Production/ANMN301_ANIMATIC_READINESS_2026-10-01.md`**
Commit: `6abfbc38`

Container is exact — 1920x1080, 24 fps, 1560 frames, 65.000 s, h264, silent,
correct title card, 19 numbered panels, VSE coverage 1560/1560.

The character does not read in panels 11/12/16/17. Root cause is **not** framing:

    ARM2 VERDICT BONES_DO_NOTHING

The bone matrix rotates; `EXPORT_Body` does not move a vertex. Skin is intact
(164/164 groups, 55852 weighted verts, 0 empty). `EXPORT_Body` xspan 0.46 vs
zspan 2.0 is not a human shape, and the stage blend has 212 objects / zero
armatures / no `EXPORT_*` meshes — the character exists only via the runtime
append in `animatic_fix.py`.

Fastest settle: open live Blender (PID 18036, MCP 127.0.0.1:9876), load
`proxy/SHOREWAKE_proxy_v02_storyboard.blend`, select `EXPORT_Body`, pose
`c_arm_fk_l`. Four headless probes did not answer this; ten seconds of viewport
will.

Also open: the committed MP4 (19.6 MB, `c0063d1c`) and the working-tree MP4
(24.5 MB) are different files. Both pass spec. Owner decides which to keep.

## 6. Not done, in priority order

0. **ANMN301 character readability** (§5b) — hard deadline **Fri Oct 9, 5 PM**.
   The 19.6 vs 24.5 MB MP4 choice rides on this.
1. `.gitignore` review (§3) — **blocking**, and it can bite via `git add -A`
2. addon sync + baseline re-cut (§4)
3. `git push` — **not performed.** No push was authorised
4. Wave 1 remainder: `TaskChair`, `MonitorBank`, `ShelfUnit`, `StorageStack`,
   `BreakroomCounter`, `ServiceUnit`, `Panel`. Blinds have **no owner** —
   `venetian_kit.py` is an 82-line loggia archetype, not blinds
5. Wave 3: 8 interior materials (carpet, laminate, drop ceiling, troffer,
   powder coat, screen emissive, polypropylene, whiteboard gloss)
6. Wave 4 shotlist S01–S05 — stager exists for the desk only

## 7. Scratch left untracked on purpose

`brave_dump.html`, `search_japan.json`, `search_korea_cn_tibet.json`,
`search_pass2.json`, `met_objects.json`, `millinery_glossary.txt`,
`easterling.txt` (0 bytes), `AGENTS.md.bak*`, `4thtimestillnobones.fbx` (4.2 MB),
`tmp/`. All in the cold backup. Move to a dated archive or leave — your call.