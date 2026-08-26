# Material Organization Plan — 2026-08-25

Lane: `audit` (disk-only). No editor launches, no `.uasset` writes, no Monolith calls.
Evidence: `Saved/Audit/material_org_baseline.json` (generated this date by PowerShell census of
`*.uasset` under `/Game/EnvSandbox/Materials`, `/Game/Melodia/_PROJECT/04_Materials`;
`/Game/ZenForestTest_MusicalGlam` does not exist on disk).

---

## Current State Summary

Total assets scanned: **2093** across the two existing roots.

| Root | Notes |
|---|---|
| `/Game/EnvSandbox/Materials/` | Primary material spine (masters, functions, instances, landscape, Niagara, candidates, plus undocumented extra folders) |
| `/Game/Melodia/_PROJECT/04_Materials/` | Legacy/mirror material + texture library (MooaToon, Textures, Landscape, Masters, PostProcess) |
| `/Game/ZenForestTest_MusicalGlam/` | **MISSING on disk** — glam-pass pattern not yet instantiated |

Counts by class guess (name-prefix heuristic):

| Class guess | Count |
|---|---|
| MaterialInstanceConstant (MI_*/`*_Inst*`) | ~800 |
| Material (M_*) | ~330 |
| Texture2D / ToonProfile (T_*/TP_*/unprefixed texture packs) | ~900 |
| MaterialFunction (MF_*) | small handful (Functions dirs: 75+5 assets incl. textures; MF_ prefixed only a few — most Functions-dir contents are unprefixed) |
| Other (LI_Probe_None, _TMP probes) | few |

**Duplicates: 299 distinct basenames appear in 2+ locations** (~700 files involved). Worst offenders are texture packs mirrored wholesale (`Textures\Spokes` vs `Textures\sbs_-_gradient_texture_pack...512x512\Spokes`, etc.) and master-level mirrors:

- `M_Master_SDF_Toon` ×3 — Masters\SDF, SDF root area copies, `_Archive\Instances_SDF_Default`
- `M_Master_SDF_Toon_Inst` ×3
- `M_Master_Nikki_Landscape` in Masters AND `_Scratch`
- `M_Master_Toon_Universal_Inst`/`Inst1` duplicated into `_Scratch`
- `M_Master_Toon_Universal_BACKUP_20260702` still live under `_Scratch`
- `M_Master_Simple_Universal` in Masters AND `_Archive` root
- PostProcess Candidates duplicated between `Materials\PostProcess\Candidates` and `_Archive\Candidates_Archive`

**Orphans (MI naming implies a missing master): 1** strict hit — but note the strict rule only
catches `M_X_Inst` forms. The looser signal is large: **126 masters have zero same-stem child
candidates** (`*_Inst*`/`MI_*<stem>*` anywhere in the scan), including several canonical-looking
names (e.g. `M_CathedralFloor_Textured` has MI children only via the Melodia mirror;
`M_SpeedTreeMaster`, `M_SpaceParallax_Test`, most `M_SDF_*` masters rely on family-prefix
instances that don't embed their stem).

Top 5 findings:

1. **299 duplicate basenames**, dominated by wholesale texture-pack mirrors inside `04_Materials\Textures` (Spokes/512x512 packs exist twice; `Textures\Textures` vs `Tileables` overlap heavily).
2. **126 masters with zero instance-child candidates** — either dead or instances named without the parent stem; both cases block any automated parenting audit.
3. **Master mirrors outside `Masters/`:** `_Scratch` and `_Archive` hold editable-looking copies of the four canonical masters' siblings (`M_Master_Nikki_Landscape`, `M_Master_Toon_Universal_Inst*`, `M_Water_Master_Grand_v6_Inst`). Same hazard class as the quarantined `BP_BattleUI` duplicate.
4. **Undocumented top-level folders** in EnvSandbox\Materials beyond the spec set: `Impressionist\`, `Instances\Atlantis` (83), `Instances\Environment\RetroTextures` (117), `Instances\Kenney\`, `PostProcess\`, `RenderStudio\`, `SDF\`, `Space\`, `ToonProfiles\`, `_Archive\`, `_Scratch\`. The taxonomy below must absorb or quarantine these.
5. **Version-stack drift in Water:** `M_Water_Master_Grand_v6/v7/v9/v10_Substrate/v10_Upgrade` all live simultaneously with per-version instance trees (`v7/v9/v10`) — only v6 is referenced as owner in `material_family_manifest.py`.

Drift watchlist reference: `Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md` contains **no** material
node-drift rows (it covers pillar ownership only), so the known node-count drift is cited against
the **P0 gate `static_gates` (OPEN per `PROJECT.md` / AGENTS.md 2026-08-24 authority)**:

- `M_Master_Simple_Universal`: node count drifted 25 → 26 (unauthorized +1 node).
- `M_Master_Toon_Landscape_HeightBlend`: 290 → 304 (+14 nodes).
- Both masters sit behind the `static_gates` P0 gate; until that ledger row is recorded PASS,
  treat every non-canonical master copy (backups, `_Scratch`, `_Archive\Masters_BACKUP_20260821`)
  as potentially divergent from the live graph.

---

## Target Taxonomy

Consistent with existing patterns (`Masters/`, `Functions/`, `Instances/<Family>/`).
ZenForestTest_MusicalGlam stays isolated at project root when it appears — never merged into
EnvSandbox (glam-pass pattern: parallel content root, own Materials tree).

```
/Game/EnvSandbox/Materials/
    Masters/                  # M_* only. One canonical name per master. No _Inst/_MI here.
        SDF/                  # keep — established subfamily
    Functions/                # MF_* only; move stray textures to Textures/
    Instances/<Family>/       # MI_* only, grouped by family stem:
        Universal/            #   MI_* defaulting to M_Master_Toon_Universal
        Landscape/
        Water/                #   collapse v7/v9/v10 into Water/Legacy_v7 etc.; active = Water/
        Nikki/ NikkiHero/ Melusina/ Showcase/ Zen/ Baroque/ Environment/ ...
    Landscape/                # landscape-layer materials & probes (keep)
    Niagara/                  # keep
    PostProcess/              # promote from undocumented folder; Candidates/ and Profiles/ subdirs stay
    ToonProfiles/             # TP_* (keep)
    Textures/                 # T_* and pack textures referenced by materials (single copy)
    Candidates/               # evaluation-stage assets awaiting promotion/deletion decision
    _Archive/                 # read-only quarantine; nothing references it
    _Scratch/                 # disposable; scheduled for emptying

/Game/Melodia/_PROJECT/04_Materials/     # legacy mirror — freeze; migrate unique masters
    # (Cathedral/, MooaToon/, Glitter/, ...) into EnvSandbox taxonomy, then delete duplicates.

/Game/ZenForestTest_MusicalGlam/         # ISOLATED glam-pass root (when created):
    Materials/Masters/ Functions/ Instances/Glam/   # same shape, zero cross-references into EnvSandbox
```

Rules:
1. Exactly one disk location per basename project-wide (redirectors allowed only via editor tooling, never hand-copied).
2. `Masters/` must contain zero `MaterialInstanceConstant` assets (today it holds `MI_IridescentRock`, `MI_SakuraLandscape`, `M_Master_*_Inst*`).
3. Every MI lives under `Instances/<ParentStem>/`.
4. Version stacks get one ACTIVE name; older versions move to `Masters/Archive_v<N>/` pending deletion sign-off.
5. ZenForestTest_MusicalGlam is never scanned by EnvSandbox audits; its own baseline JSON lands in its own Saved/Audit.

---

## Drift Watchlist

| Item | Signal | Status source |
|---|---|---|
| `M_Master_Simple_Universal` node drift | 25 → 26 nodes | `static_gates` P0 gate OPEN (PROJECT.md); ORCHESTRA_CONVERGENCE has no material rows |
| `M_Master_Toon_Landscape_HeightBlend` node drift | 290 → 304 nodes | same |
| Quarantine backups of HeightBlend (×8 dated 20260728–29 in `_Archive\Masters_BACKUP_20260821`) | potential divergent graphs vs live | verify before any delete |
| `M_Master_SDF_Toon` ×3 locations | which copy do `SDF/Instances/*` parents resolve to? | needs redirector check in-editor (out of lane scope) |
| Water master version stack (v6..v10) | manifest pins v6 as owner; v10 instances exist | reconcile owner pointer in `material_family_manifest.py` |
| 126 masters with zero child candidates | dead-master candidates list | confirm with `bp_live_path`-style reachability before deletion (ORPHAN means prove it, not delete it) |

Watchlist maintenance: re-run the census script after each migration batch; diff
`duplicates.count` and `masters_zero_child_candidates.count` against this baseline.

---

## Migration Skeleton — `organize_material_folders_v2.py`

Follows the metadata-only pattern of `organize_masters.py`: touches asset metadata
(Group / SortPriority / folder moves via `EditorAssetLibrary`), never graph topology,
never parameter values. Dry-run by default. Batched saves.

```python
"""organize_material_folders_v2.py — metadata-only material folder reorganization.

Run in-editor (Monolith editor_query run_python). Dry-run default:
  run_python organize_material_folders_v2.py            # prints plan only
  run_python "... --apply"                              # executes + saves in batches
"""
from __future__ import annotations
import json

# ---- single source of truth: the plan emitted by the disk census -------------
# Load Saved/Audit/material_org_baseline.json (or an embedded MOVES table).
# Each move: {asset: "/Game/...", from: ..., to: ..., reason: "duplicate|misplaced|version_stack"}

DRY_RUN = "--apply" not in ARGV  # pseudo; parse sys.argv in real impl
BATCH_SIZE = 20                  # save every N moves; verify dirty list per batch (rule 9)

def build_moves(baseline: dict) -> list[dict]:
    moves = []
    for dup in baseline["duplicates"]["entries"]:
        keep = pick_canonical(dup["locations"])      # prefer Masters/, then non-_Archive/_Scratch
        for loc in dup["locations"]:
            if loc != keep:
                moves.append({"from": loc, "to": "_Archive/Dupes/" + basename(loc),
                              "reason": f"duplicate of {keep}"})
    for mi in baseline["misplaced_instances"]:        # MI_* outside Instances/<Family>/
        moves.append({"from": mi["path"], "to": target_family_dir(mi), "reason": "instance_misplaced"})
    return moves

def apply_batch(batch: list[dict]) -> dict:
    results = []
    for mv in batch:
        if not unreal.EditorAssetLibrary.does_asset_exist(mv["from"]):
            results.append({**mv, "error": "asset_missing"}); continue
        if DRY_RUN:
            results.append({**mv, "action": "would_move"}); continue
        ok = unreal.EditorAssetLibrary.rename_asset(mv["from"], mv["to"])
        results.append({**mv, "moved": bool(ok)})
    return {"moved": sum(1 for r in results if r.get("moved")),
            "errors": [r for r in results if r.get("error")]}

def main() -> int:
    moves = build_moves(load_baseline())
    report = []
    for i in range(0, len(moves), BATCH_SIZE):
        report.append(apply_batch(moves[i:i+BATCH_SIZE]))
        if not DRY_RUN:
            save_dirty_packages()          # EditorAssetLibrary.save_directory or per-dirty list
            assert_no_fixup_redirectors(report[-1])
    print("ORGANIZE_MATERIAL_V2_RESULT", json.dumps(
        {"dry_run": DRY_RUN, "total_moves": len(moves), "batches": report}))
    return 0
```

Safety rails inherited from the working agreement:
- Never `delete_asset`; duplicates move to `_Archive/Dupes/`, deletion is a separate signed-off pass.
- Never rename an asset whose path another open package references without letting UE emit fixups (rename_asset handles redirectors; hand file-moves do not — hence editor-side execution, not filesystem).
- Verify by re-reading after every batch (`does_asset_exist(new)` true, old path false-or-redirector).
- One editor instance; check port 9316 listener before running.
- After full migration, regenerate the disk census and require: duplicates == 0 outside `_Archive`, `Masters/` free of MI_*.

---

*Deliverable pair:* `Saved/Audit/material_org_baseline.json` (census) + this plan. Next lane
(`mcp`, one editor) may execute the skeleton's dry-run to produce the concrete MOVES table.
