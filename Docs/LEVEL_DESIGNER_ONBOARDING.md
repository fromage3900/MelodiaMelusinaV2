# Level Designer Onboarding

This is the shortest safe path from checkout to a validated greybox contribution.

## Start

1. Install UE 5.8 and Git LFS.
2. Clone the repository and run `git lfs pull`.
3. Open `BS_GodFile.uproject`.
4. Read [COLLABORATION_WORKFLOW.md](COLLABORATION_WORKFLOW.md).
5. Open `ZenForestTest` for gameplay smoke or `L_Template` for neutral PCG/look-dev work.

## Ownership

- `ZenForestTest` owns the playable Melodia smoke loop.
- `L_Template` owns neutral material, PCG, water, and Niagara proving.
- Greybox Kit assets are reusable blockout tools; do not edit them for one level.
- Hero landmarks, final composition, and Sakura art direction remain human-owned.
- PCG places static support dressing. Niagara owns motion. WaterBody and spline
  systems own water. `BP_InstanceOnSpline` owns authored spline dressing.

## Greybox workflow

Create level-local blockout geometry first. Use approved `SM_Greybox_*` assets,
stable labels, and explicit ownership. Add PCG volumes only over tagged surfaces
such as `PCG_Ground`, with exclusion volumes for paths, ponds, torii, and authored
landmarks. Replace greybox assets through reviewed asset references, not by
rewiring shared kit meshes.

## Five-minute validation

```powershell
python Content/Python/catalog_project_assets.py
python -m unittest discover -s Content/Python/gmm -p "test_*.py" -q
```

With editor access, run the relevant BP, Zen, PCG, and material audit scripts.
Capture a screenshot or report showing the changed level and generated output.
Zero PCG instances means the surface/volume context is unverified, not that the
graph is finished.

## Handoff

Before closing the editor, record the map and assets touched, whether the editor
is closed, the validation command used, and any unresolved warnings. Never have
two contributors writing the same `.umap` or `.uasset` simultaneously. Submit a
branch with the report path and a short visual note.

## Do / Do Not

Do use level-local folders, tags, exclusions, deterministic seeds, and audit
reports. Do keep PCG density conservative until generated counts are proven.

Do not mass-rename or move assets, edit shared Greybox Kit meshes for a scene,
put final hero composition into PCG, commit `Saved/`, or claim visual validation
from a headless structural check alone.
