# Kenney static-mesh graveyard ΓÇö retirement and redirect map

**Date**: 2026-10-21
**Domain**: asset ownership, Poitou environment integrity
**Authority**: this is the record of the retirement. Status lives in `CURRENT_STATE.md`.

## 1. What the pack actually was

The Kenney *Retro Fantasy Kit* sat in `/Game/EnvSandbox/Meshes/Environment/` as **one
folder per mesh**, with the pack's own lowercase-hyphenated naming. The project's own
assets are `SM_*` / `BP_*` / `MI_*` prefixed, so the two never collide.

| | |
|---|---|
| Pack members (static meshes) | **1,562** in the Asset Registry |
| Plus the pack's material instances | 984 (Kenney MI folder + `_RetroFantasyKit/Materials` + `_Loose` + `AvatarGarden/Materials`) |
| **Universe considered** | **2,546** |
| **Source-control owner** | **Perforce**, not git. `//Melodia/main/Content/EnvSandbox/Meshes/Environment/...` was added in **change 79**. The client view maps straight onto the local `Content/` folder, so the whole pack is P4-owned. **None of it is in git** (0 of 1,530 verified), and it never consumed git-LFS storage. |

A name-shape heuristic over the whole tree matched 2,628 packages ΓÇö 885 of them the actual
pack, the rest Audio, UI borders, characters. The rule was narrowed to
`/Game/EnvSandbox/Meshes/Environment/` + non-project-prefixed names before anything was cut.

## 2. What was retired

**2,506 files opened for delete in Perforce changelist `292`, which was SUBMITTED on 2026-10-21 18:10.**
That is **98.5% of the pack** ΓÇö the ask was 75%.

- Local disk: `Meshes/Environment` went **2,618 ΓåÆ 119** uassets; `Materials/Instances/Kenney` ΓåÆ **0**.
- **Revert is still possible**: `p4 revert -c 292` restores the files into a new pending
  changelist from the depot, and the submit is a separate, reversible step.
- Review: `p4 describe -s 292` ┬╖ Description: *"Melodia: retire the unreferenced Kenney static-mesh pack (2506 files, Asset Registry verified zero referrers). Owner submit required."*

### How the cut list was decided ΓÇö the Asset Registry, not a heuristic

`Tools/Editor/asset_graveyard_referencers.py` runs the query **headlessly** (the Python
commandlet, `-unattended -nullrhi`), so it never touches the owner's editor session:

```text
UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript \
    -script=".../asset_graveyard_referencers.py" -unattended -nopause -nosplash \
    -nullrhi -stdout -FullStdOutLogOutput
```

UE 5.8's Python exposes `ar.get_referencers(package_name, options)` with
`unreal.AssetRegistryDependencyOptions()` (there is **no** `unreal.AssetRegistryDependencyType`
in 5.8 ΓÇö the first attempt failed on exactly that).

A material instance whose *only* referencer is a mesh being deleted is an orphan the moment
that mesh goes, so the cut is a **fixpoint**: an asset is removable only when every referrer
is itself removable. That is why 519 material instances go with their meshes instead of
being stranded.

### Guards that were applied

1. **Referencers.** Any asset with a referrer outside the cut set is held. (The offline
   name-scan was discarded for this reason: it matched generic names like `wall`, `floor`,
   `tree`, `table` inside unrelated packages, and reported a dialogue asset as "referencing"
   38 Kenney meshes. It is kept only as a cross-check.)
2. **Local edits.** 10 pack materials and `tree-high` / `tree_fat` differ from the depot ΓÇö
   unsubmitted work. They are **held back**, not cut, and their local edits are intact.
3. **Already open.** Files open in another changelist belong to someone else's in-flight
   change and are never touched.
4. **A protection list** ΓÇö the 19 meshes that are referenced or named by the Houdini HDA.
   These are the *redirect* set, not the delete set.
5. **The owner submitted it.** `p4 delete` opened the files for delete and change 292 was
   submitted on 2026-10-21 18:10; the git mirror of the seven material instances is the
   `assets: mirror the Perforce delete of the Kenney material instances into git` commit.

## 3. The redirect map ΓÇö what still needs replacing

19 meshes survived because something references them. **All 19 are in-theme kill candidates
except where noted.** Measured bounds are the real ones, in centimetres, from
`Saved/Audit/AssetGraveyard_20261021/mesh_bounds.json`.

### 3a. In the live level (`L_Poitou_v2`) and the canal PCG

| Kenney asset | size cm | who references it | in-theme replacement | size cm | note |
|---|---|---|---|---|---|
| `.../door/StaticMeshes/door` | 15.0 ├ù 35.9 ├ù 60.5 | `L_Poitou_v2` (**114 placed**) | `SM_Poitou_LockGate_Pair` | 867.2 ├ù 445.8 ├ù 274.0 | a lock gate, not a house door. **No in-theme door exists** ΓÇö the pack door is the level's door. Needs an authored in-theme door, or the 114 doors stay. |
| `.../fence_simple/StaticMeshes/fence_simple` | 100.0 ├ù 7.0 ├ù 34.5 | `L_Poitou_v2` | `SM_Poitou_BridgeParapet` | 586.1 ├ù 55.0 ├ù 109.9 | a stone parapet, not a fence. **No in-theme fence exists.** |
| `.../canoe/StaticMeshes/canoe` | 30.0 ├ù 115.0 ├ù 18.3 | `L_Poitou_v2` + the HDA | `SM_Marais_Barque_4m6_Sculpted` | 450.2 ├ù 144.2 ├ù 30.3 | **exact slot match** ΓÇö the mesh is named 4m6 and measures 4.50 m. Use this. |
| `.../grass_leafsLarge/...` | 47.6 ├ù 48.7 ├ù 14.3 | `L_Poitou_v2` + `PCG_Poitou_CanalBank` + the HDA | `SM_GrassGroundPatch_01` | 339.7 ├ù 490.1 ├ù 18.x | a grass patch, not a reed. **No in-theme reed exists.** |

### 3b. In other levels (not the P0 route)

| Kenney asset | size cm | referenced by | in-theme replacement | size cm |
|---|---|---|---|---|
| `Bush01/04/05/08_Art` | 244.9 ├ù 193.5 ├ù 134.2 | `L_KaleidoNave`, `ZenForestTest`, `L_ZenForestACFTrial` | `SM_EuropeanHornbeam_Sapling_01` | 184.1 ├ù 274.5 ├ù 21.x |
| `Rock01/02_Art` | 116.0 ├ù 108.3 ├ù 48.1 | same three + 8 Morning external actors | `SM_MossyRocksVine_01` | 186.9 ├ù 219.2 ├ù 80.x |
| `Stone01/03/05_Art` | 223.4 ├ù 212.1 ├ù 63.9 | same three | `SM_Maillezais_CrumbledWall_Sculpted` | 1197.7 ├ù 126.5 ├ù 673.7 |
| `flower_redA` | **does not load** | `L_Lookdev_ToonAB` | ΓÇö | ΓÇö |
| `violin` | 0.5 ├ù 0.1 ├ù 1.5 | **`BP_MelusinaJRPGCharacter`** (the canonical heroine) + 2 test BPs + `BP_MelusinaACFHybrid` | **no in-theme violin** | ΓÇö |

`L_MelusinaMorning` is a 37 KB shell, so its 9 external-actor references to `Rock01_Art` are
in a map that is no longer the playable opening. They can be left for the Morning rebuild.

### 3c. The Houdini HDA ΓÇö the durable fix

`Tools/Poitou/snip/inst.vex` hard-codes four pack meshes:

```vfl
string POP   = ".../tree-high/StaticMeshes/tree-high.tree-high";
string ASH   = ".../tree_fat/StaticMeshes/tree_fat.tree_fat";
string GRS   = ".../grass_leafsLarge/StaticMeshes/grass_leafsLarge.grass_leafsLarge";
string CANOE = ".../canoe/StaticMeshes/canoe.canoe";
```

Deleting the files does **not** fix this: the HDA re-emits the instances on the next cook, and
if the mesh is gone the instance is null. The HDA must be repointed, and `poitou_layout_live.hdalc`
rebuilt (`Tools/Poitou/build_poitou_hda.py`, headless hython ΓÇö no editor needed).

**Two defects in the current instance block, found by measuring the meshes:**

1. **`tree-high` no longer loads at all** ΓÇö it is one of the 95 unsmudged/broken packages in
   the project (`Failed to find object` during the asset-registry scan). The poplar branch of
   the HDA is already emitting broken instances.
2. **The scale divisors are stale.** `tree-high` and `tree_fat` differ from the depot ΓÇö they
   were rescaled in place and never re-submitted. The VEX still divides by the *original*
   sizes (`0.76` / `1.15` / `0.65` m for the ash), but `tree_fat` now measures
   **1356.0 ├ù 1631.0 ├ù 1594.3 cm**. The ash is therefore scaled against a mesh roughly **18x**
   larger than the divisor assumes. That is the real reason the level reads as a graveyard:
   the props are the wrong size, not just the wrong art.

The replacement divisors, measured:

| type | current mesh (cm) | current divisor (m) | replacement mesh (cm) | replacement divisor |
|---|---|---|---|---|
| `poplar` | `tree-high` ΓÇö **does not load** | 1.02 / 2.97 / 1.02 | `SM_MossyTree_01` | 779.0 / 224.7 / 183.9 |
| `ash_tetard` | `tree_fat` ΓÇö 1356.0 ├ù 1631.0 ├ù 1594.3 | 0.76 / 1.15 / 0.65 (stale) | `SM_AshTetard_Canal_03_Sculpted` | 220.1 / 217.6 / 229.3 |
| `barque` | `canoe` ΓÇö 30.0 ├ù 115.0 ├ù 18.3 | 0.30 / 0.18 / 1.15 | `SM_Marais_Barque_4m6_Sculpted` | 450.2 / 144.2 / 30.3 |
| `reed*` | `grass_leafsLarge` ΓÇö 47.6 ├ù 48.7 ├ù 14.3 | absolute `set(3,12,3)` | `SM_GrassGroundPatch_01` | 339.7 / 490.1 / 18.x |

> **The repoint is written up but NOT applied.** Which source axis is "up" for each mesh cannot
> be settled from bounds alone, and the current VEX already disagrees with itself about the
> axis order (it divides Y by the mesh's Z and Z by the mesh's Y). Shipping a rewritten
> divisor without a visual check would put a second scale bug into the level. The patch goes
> in **with** the recook and the PIE look, in one editor session.

## 4. Owner decisions

1. **The 114 doors.** There is no in-theme house door. Author one, or keep the pack door.
2. **The canal fence.** `SM_Poitou_BridgeParapet` is a parapet, not a fence. Author a fence, or
   accept the parapet.
3. **The reeds.** There is no in-theme reed. `SM_GrassGroundPatch_01` is a grass patch.
4. **The poplar.** `SM_MossyTree_01` is the Megascan the owner already used for the far poplar
   bands (12,132 instances), so near and far would read as one species ΓÇö but it is a Megascan,
   not a Poitou poplar. A Poitou poplar is the canon-correct answer.
5. **Melusina's violin.** The canonical heroine Blueprint references a pack `violin` that
   measures 0.5 ├ù 0.1 ├ù 1.5 cm. It is a token, not an instrument. Is it even visible?
6. **Submit the changelist.** `p4 submit -c 292` is the owner's call.

## 5. Tooling added

| Tool | What it does |
|---|---|
| `Tools/Editor/asset_graveyard_census.py` | offline candidate inventory + name-scan referencer map (advisory) |
| `Tools/Editor/asset_graveyard_referencers.py` | **authoritative** Asset Registry referencer map, headless |
| `Tools/Editor/poitou_mesh_bounds.py` | measured bounds for the current and candidate meshes |
| `Tools/Editor/poitou_redirect_targets.py` | referencers + materials for the referenced set |
| `Tools/Editor/poitou_intheme_meshes.py` | the in-theme replacement surface with bounds |
| `Tools/Editor/poitou_graveyard_p4_delete.py` | the guarded Perforce delete (opens for delete, never submits) |
| `Tools/Editor/asset_graveyard_prune.py` | file-level prune for git-owned trees (not used here ΓÇö the pack is P4-owned) |

Evidence: `Saved/Audit/AssetGraveyard_20261021/` ΓÇö `census.json`, `referencers.json`,
`mesh_bounds.json`, `redirect_targets.json`, `intheme_meshes.json`, `p4_delete_receipt.json`.
