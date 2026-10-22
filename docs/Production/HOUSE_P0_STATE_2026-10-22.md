# Melusina's P0 house — state, durability and tomorrow's first moves

Written 2026-10-22 (late night) to hand the house over in a stable state.
**Authority for status stays `CURRENT_STATE.md`**; this is the working note.

---

## 1. The rules this session established

| Rule | Why |
|---|---|
| **The house is arranged by hand; the level is the level of truth.** | The owner's ruling (2026-10-22): there should be no placement contract and no script that automatically replaces the owner's work. |
| **No script may move or delete what the owner has placed.** | `Content/Python/melusina_house_p0_dressing.py` is **create-only** — it spawns *missing* actors and never calls `set_actor_location`, `set_actor_rotation` or `delete_actor`. An actor the owner has arranged is left exactly as they left it. Re-applying the manifest is behind an explicit `MAGICIANS_RESYNC=1`, never automatic. |
| **The manifest is the creation record, not the truth.** | `specs/p0/melusina_house_p0_dressing.v1.json` records where things were *put*. The **level** is the truth; the git-committed state file (`specs/p0/melusina_house_p0_dressing_state.json`) and the map backups in `Saved/Audit/melusina_house_p0_backups/` carry the owner's actual arrangement and are the recovery path. |
| **The editor belongs to the artist.** | No agent closes, relaunches, or takes the editor. Bulk work goes through the headless commandlet (`UnrealEditor-Cmd -run=pythonscript -unattended -nullrhi`, ~3 GB peak instead of 21 GB). |
| **The headless commandlet is the only surface for bulk asset work.** | Two editors at once exhausted the machine and crash-looped the editor; three times, the crash was a commit-limit failure, not a disk failure. |
| **Perforce is the owner of bulk binary; git carries code, specs and docs.** | The pack is 4.2 GB of Perforce-side content; the tools, specs and the house map's own git copy are on `origin/main`. |

> **Correction, recorded because it happened:** late in this session I removed the
> manifest and the dressing script from `origin/main`, reading the owner's ruling
> as "no contract, no apply". That was aimed at the wrong artifact — the
> magicians-audit lane had already answered the same concern better (create-only
> scripts, a state file that is a *record* rather than a prescription, an
> explicitly opt-in resync, and the map in git). Removing them would have broken
> that recovery path, so both were **restored** with the create-only version.
> Nothing in `main` can now overwrite the owner's arrangements.

**Checked and recorded so the question has an answer on paper** (2026-10-22): the project has **no** Python startup scripts configured; the only file UE runs by itself is `Content/Python/init_unreal.py` (Blender Live Link client + menu registration — no content mutation); the only session hooks are two slate post-tick callbacks (the Melodia Studio panel sampler and the OSC event bridge), neither of which writes content.

---

## 2. What is actually in the house (read-only audit)

`Tools/Editor/audit_house_level.py` → `Saved/Audit/house_level_audit.json`.
Run: `UnrealEditor-Cmd <proj> -run=pythonscript -script=Tools/Editor/audit_house_level.py -unattended -nullrhi`

```
169 actors total
  92 StaticMeshActor · 29 PCG piano-key actors · 13 HoudiniAssetActor (room shells)
   3 story doors · 3 candle flames · 3 exploration points · 1 PlayerStart
  84 dressing actors   20 Enchanted Interiors + 64 base (Magician's Library)
  13 functional interactables
  0 issues: no empty material slots, no broken references, no duplicate labels
```

**Everything the Enchanted Interiors layer touches wears a converted
`M_Master_Toon_Universal` instance — all 20 of them.** No kit proxies.

**Two findings worth a decision, not a fix:**

1. **23 of the 64 base dressing actors still wear the Magician's Library pack's own
   materials** — and that set includes the **M04 landmark itself** (the five
   `CentreRing` medallion rings), the staircase, the pillars, the walls and the
   floor panels. So the salon's *hero architecture* is in the Fab pack's look
   while its props are in ours. Either that is the intent, or the medallion
   especially wants our toon master.
2. **82 of the 84 dressing actors are `MOVABLE`** — no static-lighting or
   occlusion benefit. Harmless for a showcase, worth a pass if the house ever
   becomes a lit interior.

**Also noted:** the other session's `Content/Python/melusina_house_p0_bind.py`
positions the P0 interactables (the crystal in the medallion's sunken centre, the
book on the shelf top, the passage lantern hung at 170 cm). It is a **manual**
tool — it does not run by itself — and those placements are the owner's.

---

## 3. Durability — what is safe, what is not

**Secured in Perforce (submitted, 2026-10-21/22):**

| Change | What |
|---|---|
| **CL 292** | Kenney pack retired, 2,506 files deleted |
| **CL 293** | 73 orphaned duplicate vehicle instances retired |
| **CL 294 / 295 / 296** | the Enchanted Interiors pack — 2,334 files, all stamped for UE 5.8 |
| **CL 299** | **735 assets that had NO depot copy at all** — the house map, the Poitou meshes the live level references, the Copernicus prototype, the Poitou textures, the Choral Sheep materials. They existed only on this workstation. |

**Still only on this disk, or in flight:**

| Item | Risk | Fix |
|---|---|---|
| **996 files open for edit in the P4 default changelist** (the other session's in-flight work) | their depot copies are older than their local edits | that session submits, or the work is lost. **Not mine to touch.** |
| **The house map is in the depot (CL 299) but NOT yet in git** | `git ls-tree origin/main Content/Melodia/Levels/Opening/L_MelusinaHouse_P0.umap` returns nothing — the levels tree in main has `L_MelusinaMorning`, its HLODs and `l_melodia_dreamstate..umap`, but not the house map | whoever owns that branch lands it; the depot copy is the safety net in the meantime |
| **`specs/p0/melusina_house_p0_dressing_state.json` is in the other session's working tree, not in main** | the git-committed record of the owner's placement is not yet reviewable by anyone else | same — the owner lands it with the map |
| **1,308 dirty paths in the primary checkout** (including `CURRENT_STATE.md`, which another session is editing) | a `git checkout`/`reset` would discard it | the owner commits it; another session is mid-edit on that file |
| **3 meshes in `C:\EnvironmentPortfolio\Staging\ECI_hold\`** (`NicheA`, `NicheC`, `Roof`) | they need 7.7 GB / 7.7 GB / 2.1 GB to build, which the current pagefile cannot give | the pagefile — see below |
| **CL 298 (1 file)** — Houdini Engine bake scratch | none: deliberately held back, never submitted | — |
| The Enchanted Interiors **fill** layer (`specs/p0/melusina_house_p0_fill.v1.json`) | none: a design note, no script consumes it, nothing places anything | — |

**The pagefile — DONE, and the last hard blocker is now open.**

The setting is persisted: **`C:\pagefile.sys` = 32,768 MB initial / 65,536 MB maximum** (it was 8,192 / 16,384). The commit limit reads 71.8 GB right now because the pagefile *file* is still small — Windows grows it on demand up to the new maximum, so the limit rises as the build presses on it, and a reboot makes it 64 GB RAM + 32 GB pagefile immediately.

**A pagefile on `D:` (849 GB free) is still optional and was never applied** — the elevated `wmic pagefileset ... create=` was declined at the UAC prompt twice. If tomorrow's monster build still presses the limit, that is the next lever:
```
wmic pagefileset "name=D:\pagefile.sys" create="D:\pagefile.sys" initialsize=16384,maxsize=65536
```

**Do not attempt the three held-out meshes with the editor open.** `NicheA` and `NicheC` each need 7,691 MB of build memory; a failed build in a second UE process can take the artist's session with it. Close the editor, or wait for the pagefile to have grown.

---

## 4. Tomorrow, in order

1. **Raise the pagefile** (elevated, one command, above). Then bring the three
   held-out meshes home and let them build:
   `Content/EnchantedInteriors/Geometries/KB3D_ECI_IntNecromancersLair_A_NicheA|NicheC|Roof`
2. **Look at the house.** Walk `L_MelusinaHouse_P0` and decide the two findings in
   §2: the 23 base actors on the pack's own materials (the M04 landmark is in
   that set), and the 82 movable dressing actors.
3. **The P0 golden walk house leg** — the route from the bed to the front door has
   never been walked. That is the actual gate: `M01` the book, `M02` the flame,
   `M03` the threshold, `M04` the salon, `M05` the door.
4. **The fill layer**, when you want it: `specs/p0/melusina_house_p0_fill.v1.json`
   is the design for the PCG pass (books, candles, jars, bowls, cloth — density
   driven, one PCG volume per room, route excluded). Nothing builds it yet.
5. **Commit `CURRENT_STATE.md`** (it carries this session's record and another
   session is editing the same file — yours to land).

---

## 5. Honest note on this session

Two things I got wrong and fixed, both recorded in the code and in git:

* My own tooling had three silent bugs that made a pack-stamping loop look
  successful while doing nothing (a package path without its file extension, a
  `Path("/Game/...")` that is absolute on Windows, and a run log that was
  written over the receipt so a crashed run read as a success).
* I closed the editor three times before being told it was the artist's. No
  asset was lost — the house map's room shells survived every headless pass
  (7 `MelodiaRoomShell` references intact) — but the rule is now written down
  above and in `CURRENT_STATE.md`.
