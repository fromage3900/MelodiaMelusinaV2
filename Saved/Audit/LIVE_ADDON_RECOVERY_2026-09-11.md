# Live addon recovery — 2026-09-11

## What was about to be destroyed

`deploy/sync_surreal_to_live.ps1` (via `deploy/_sync_addon_to_blender_5_2.py`) was
about to be run to install `surreal_arch` into the Blender 5.2 live addons folder.
Its `--check` reported:

```
Live byte check: 242/255 match
MISSING live files (5):  surreal_arch/trimsheet_magic.py, melodia_gn/{core_forms_port,greybox_port,music_port,nikki_decor}.py
STALE live files (8):    surreal_arch/{melodia_gn_route,quality_props,zen_kit}.py, melodia_gn/{core,melodia_house,presets,stack,__init__}.py
LIVE ADDON SYNC: OUT OF DATE
```

Following that verdict would have been wrong. `sync()` is implemented as
`shutil.rmtree(live_package)` followed by `shutil.copytree(source)` — a full
replace. The live install held **17 files that exist only there**, so the sync
would have deleted every one, permanently.

**Root cause of the misleading verdict:** `--check` compares checkout -> live only.
It lists `MISSING live files` (in the source, absent live) and `STALE live files`
(bytes differ), and has no notion of **live-only** files. When the live install is
*ahead* of the checkout it still prints `OUT OF DATE`, and the implied action is
destructive. The tool cannot distinguish "the live copy is behind" from "the
checkout has lost files the live copy still has".

**Found before running anything.** No sync was executed.

## What the checkout had lost

`deploy/surreal_arch/melodia_gn/__pycache__/` contained compiled bytecode for
modules whose `.py` source no longer exists in the checkout. A `.pyc` with no
matching `.py` in its own package directory is proof the source was there and was
removed afterwards.

17 lost module sources:

| module | recoverable from the live install? |
|---|---|
| `barrel_vault_kit.py` | yes |
| `curved_wall.py` | yes |
| `dreamy_gothic_arch.py` | yes |
| `garment_material_id.py` | yes |
| `garment_smart_bevel.py` | yes |
| `garment_trim_uv.py` | yes |
| `garment_vertex_ao.py` | yes |
| `gold_light_strip.py` | yes |
| `music_euro_remainder.py` | yes |
| `musical_mesh_variants.py` | yes |
| `nikki_advanced_decorations.py` | yes |
| `nikki_musical_decorations.py` | yes |
| `ornament_strip.py` | yes |
| `rose_window.py` | yes |
| `ue_proxy_kit.py` | yes |
| `castle_kit_kit.py` | **no — bytecode only** |
| `zen_kit_kit.py` | **no — bytecode only** |

The last two have differently-named siblings present in the checkout
(`castle_kit.py`, `zen_kit.py`), so they are most likely renames rather than
unique work. Unverified.

Two further live-only files that were never in the checkout:
`Docs/ADDON_AUTHORITY_2026-09-03.md` (the authority doc that the
`melodia-studio-addon-convergence` skill has been telling agents to "promote" from
the docs branch — it was in the live install the whole time) and
`melodia_gn/build_and_verify_dreamy.py`.

The live `melodia_gn/__init__.py` imports 15 of these modules by name, i.e. they
are live functionality, not dead files. The checkout's `__init__.py` does not
import them.

The 17-source loss is the signature of a destructive git operation run over an
untracked/uncommitted tree — the hazard documented in `AGENTS.md` ("NEVER RUN
THESE") — or of a partial cross-workstation copy. Cause undetermined.

## Actions taken

1. **Backed up** all 17 live-only files with md5s and a MANIFEST — twice:
   * `Saved/Recovery/live_addon_only_20260911/files/` + `MANIFEST.txt`
   * `Saved/Audit/live_addon_recovery_20260911/` (copy, md5-verified)
2. **Restored** all 17 into the checkout at `deploy/surreal_arch/`. Additive only;
   md5-identical to the live install; HEAD unchanged; nothing committed.
   These are untracked but **not gitignored**, so `git add` protects them.
3. **Did not** run the sync. **Did not** modify the restored files.
4. Recorded the sync tool's blind spot in the `melodia-studio-addon-convergence`
   skill.

## Open decisions (owner input required)

### 1. Id collision — `MEL_nikki_star_pendant`, `MEL_nikki_heart_filigree`

Both ids are claimed by two different modules:

* `melodia_gn/nikki_musical_decorations.py` (recovered; the older authority, and the
  module that produced the Melusina study's original decor trees)
* `melodia_gn/nikki_decor.py` (new; registered in the tracked baseline)

`register_builder` is last-wins, so whichever module imports last silently owns the
id. The collision is latent today because no tree imports both — but it becomes real
the moment the recovered imports are restored.

Note the older module's own defects, independent of the collision. Measured headless
(`Saved/Audit/nikki_decor/check_recovered.log`), empty base mesh in, builder output out:

| builder | Resample Curve input linked? | evaluated verts | verdict |
|---|---|---|---|
| `build_nikki_heart_filigree` | **no** (`Count` linked, `Curve` never linked) | **0** | dead — produces nothing from any guide |
| `build_nikki_star_pendant` | yes | **153,664** | broken — uses `Star_Pendant_Template` as its own guide *and* its own instance, so it instances the star's bevelled tube on itself |
| `build_nikki_wall_beads` | n/a (no guide input at all) | 336 | works, but hardcodes spacing/count instead of taking a guide |

All three hardcode scene objects through `Object Info` with `Object.default_value`
and leave `transform_space` at `ORIGINAL`, so they carry the same host-transform
displacement defect: on `ROOF_Roof_Main` at (0,15,2) they land 4-6 m off the
building.

Correction to an earlier assumption: `MEL_nikki_wall_beads` scales a radius-1.0 bead
by `Bead Radius` (0.03), which is correct — so the study's 2 m wall beads were
**not** this module's fault. They came from a later hand-edit of
`Wall_Bead_String_GN` that set `Scale Instances = 1.0` while keeping `Bead Radius`
as an unwired 0.03.

Options: keep the new implementations and rename the older registrations to
`MEL_nikki_legacy_*` (non-destructive; their functions and trees stay intact) — or
drop the new ones and let the older module own the ids.

### 2. Restore the 15 dropped imports?

The checkout's `melodia_gn/__init__.py` does not import the recovered modules. Their
~30 builders are therefore absent from the checkout registry. Restoring the 15
import lines is a coupled change: it activates those builders, which will show as
`new` in the census against `Tools/registry_baseline.json` and must be resolved
together with decision 1.

## Commands, for whoever acts next

```bash
# diff the two trees in BOTH directions before any sync (the check does not do this)
python - <<'PY'
import os
LIVE = os.path.expandvars(r"%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch")
SRC  = r"P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch"
def s(root):
    o=set()
    for dp,dn,fn in os.walk(root):
        dn[:]=[d for d in dn if d!="__pycache__"]
        o|={os.path.relpath(os.path.join(dp,f),root).replace("\\","/") for f in fn if f.endswith(".py")}
    return o
print("live-only (would be DELETED):", sorted(s(LIVE)-s(SRC)))
PY

# only when live-only is empty:
powershell -File P:/MelodiaMelusinaV2-Laptop/deploy/sync_surreal_to_live.ps1
```

To protect the recovered sources from a future clean or revert (owner action — no
agent is permitted to stage or commit):

```bash
cd P:/MelodiaMelusinaV2-Laptop
git add deploy/surreal_arch/melodia_gn/{barrel_vault_kit,curved_wall,dreamy_gothic_arch,\
garment_material_id,garment_smart_bevel,garment_trim_uv,garment_vertex_ao,gold_light_strip,\
music_euro_remainder,musical_mesh_variants,nikki_advanced_decorations,nikki_musical_decorations,\
ornament_strip,rose_window,ue_proxy_kit,build_and_verify_dreamy}.py \
        deploy/surreal_arch/Docs/ADDON_AUTHORITY_2026-09-03.md
```
