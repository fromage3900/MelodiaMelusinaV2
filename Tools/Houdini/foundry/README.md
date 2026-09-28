# Tools/Houdini/foundry — Houdini Foundry contract gate

| | |
|---|---|
| **Purpose** | Offline gate around the existing Hython families: validate recipes, plan deterministic outputs/tiles, re-derive bake-manifest hashes, probe hython with a hard timeout. |
| **Authority** | Contract tooling only. It never cooks, never imports `hou` or `unreal`, never writes MPCs. Cooking stays with the owning Hython family under `Tools/Houdini/*` or an HDA under `hda/`. |
| **Inputs** | `recipes/houdini_foundry/*.json` (`melodia.houdini_foundry_recipe.v1` / `..._bake_request.v1`), `specs/houdini_foundry/*`. |
| **Outputs** | Plans on stdout / `--out`; `probe --out` evidence JSON. Bake tools write `Saved/HoudiniFoundry/<recipe_id>_<seed>/bake_manifest.json`. |
| **Dependencies** | stdlib only; reuses `Content/Python/resonant_world_generator.stable_int` (seeds) and `Tools/universe_foundry.content_hash` (recipe hash). |
| **Evidence** | `Saved/Audit/houdini_foundry/<recipe_id>/` (small, tracked with `git add -f`). |
| **Status** | SOURCE ONLY — unit-tested offline (`test_houdini_foundry.py`); no Houdini/UE execution has run through it. |
| **At college** | Gate 0: `probe`. Every gate: `validate` before cook, `verify` after cook. |

```powershell
python Tools/Houdini/foundry/houdini_foundry.py probe --out Saved/Audit/houdini_foundry/probe_2026-09-24.json
python Tools/Houdini/foundry/houdini_foundry.py validate recipes/houdini_foundry/*.json
python Tools/Houdini/foundry/houdini_foundry.py plan recipes/houdini_foundry/field_atlas_sea_above_test_tile.v1.json
python Tools/Houdini/foundry/houdini_foundry.py verify Saved/HoudiniFoundry/<recipe_id>_<seed>/bake_manifest.json
python Tools/Houdini/foundry/test_houdini_foundry.py
```

**`Tools/*` is gitignored with per-file allowlisting** (`.gitignore` line ~250, a protected file). New files here are silently unstaged unless added with `git add -f <path>`. Always `git status --ignored Tools/Houdini` before closing a gate.
