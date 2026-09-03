# PBR_GAPFILL_COMMIT_SPEC_2026-08-31.md

## MI_PBR_GapFill_12 — Task Spec

### Source
- `Content/Python/create_pbr_instances.py` (untracked, 211 lines)
- `Saved/Audit/material_catalog_consolidated_2026-08-31.json`

### Scope
12 complete PBR texture sets with zero material instances — needs git commit + MI creation

| # | Stem | Has Albedo | Has Normal | Has Roughness | Has Metallic |
|---|------|------------|------------|---------------|--------------|
| 1 | T_FloralBrickGrayScale | ✓ | ✓ | ✓ | ✓ |
| 2 | ZenTrim_Base4K | ✓ | ✓ | ✓ | ✓ |
| 3 | ZenTrim_ColourShift | ✓ | ✓ | ✓ | ✓ |
| 4 | ZenTrim_CrackedTohell | ✓ | ✓ | ✓ | ✓ |
| 5 | ZenTrim_FlowersLIttleBit | ✓ | ✓ | ✓ | ✓ |
| 6 | ZenTrim_FlowersLOTS | ✓ | ✓ | ✓ | ✓ |
| 7 | ZenTrim_FlowersMid | ✓ | ✓ | ✓ | ✓ |
| 8 | ZenTrim_Wet | ✓ | ✓ | ✓ | ✓ |
| 9 | basetrim | ✓ | ✓ | ✓ | ✓ |
| 10 | concretetrim | ✓ | ✓ | ✓ | ✓ |
| 11 | landscape_grass | ✓ | ✓ | ✓ | ✓ |
| 12 | landscapegrayscale | ✓ | ✓ | ✓ | ✓ |

### Parent Material
`Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`

### Naming Convention
`MI_PBR_<Stem>` (PascalCase, e.g., `MI_PBR_FloralBrickGrayScale`)

### Target Folder
`Content/EnvSandbox/Materials/Instances/Environment/Stylized/`

### Git Actions
1. `git add Content/Python/create_pbr_instances.py` (untracked)
2. Create 12 MIs in editor (script or manual)
3. `git add Content/EnvSandbox/Materials/Instances/Environment/Stylized/MI_PBR_*.uasset`
4. Commit with message: `chore(material): add 12 PBR gap-fill MIs for complete texture sets`

### Lane
`audit` (qwen3:8b or nemotron-free)

### Priority
2

### Notes
- Daemon may commit the Python script (untracked file) — no .uasset writes by daemon
- MI creation requires editor Monolith pass
- Once script is committed, daemon can run it to verify texture discovery
