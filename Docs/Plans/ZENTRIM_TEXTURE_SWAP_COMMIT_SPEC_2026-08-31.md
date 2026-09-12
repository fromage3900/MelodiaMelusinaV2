# ZENTRIM_TEXTURE_SWAP_COMMIT_SPEC_2026-08-31.md

## MI_ZenTrim_Swap_ShadowDream — Task Spec

### Source
- `Saved/Audit/zentrim_cleanup_proposal_2026-08-31.json`
- `Saved/Audit/zentrim_misuse_2026-08-30.json`

### Scope
2 modified MIs need texture swap + 1 untracked texture commit

### Target 1: MI_NikkiHero_SakuraDream
- **Path**: `Content/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream.uasset`
- **Current**: `/Game/Greybox_Kit/ZenTrim_Base4K_BaseColor` (trimsheet, wrong)
- **Proposed**: `KB3D_ATL_BrickStoneCleanA_BaseColor` (proper tilable PBR)
- **Reason**: SakuraDream hero cloth has no trim UVs → trimsheet causes stretching
- **ShadowDream**: blue #8AA0D6 s0.55 (preserved from current material settings)
- **Action**: Editor texture swap + commit

### Target 2: MI_NikkiHero_SakuraDream_IntegratedV1
- **Path**: `Content/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1.uasset`
- **Current**: `/Game/Greybox_Kit/ZenTrim_Base4K_BaseColor` (trimsheet, wrong)
- **Proposed**: `KB3D_ATL_BrickStoneCleanA_BaseColor` (proper tilable PBR)
- **Reason**: Same as above — hero cloth, no trim UVs
- **ShadowDream**: blue #8AA0D6 s0.55
- **Action**: Editor texture swap + commit

### Target 3: T_MelusinaC_DressShorewake_Thickness_SBS
- **Path**: `Content/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_DressShorewake_Thickness_SBS.uasset`
- **Status**: Untracked (new)
- **Action**: `git add` + commit
- **Note**: Melusina DressShorewake SBS thickness map

### Git Commit Sequence
```
git add Content/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream.uasset
git add Content/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1.uasset
git add Content/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_DressShorewake_Thickness_SBS.uasset
git commit -m "fix(material): swap ZenTrim misuse to KB3D_ATL on SakuraDream MIs, add DressShorewake thickness"
```

### Pre-commit Hook
- 3 modified files + 1 untracked — all under Saved/Audit or Content/
- Should pass pre-commit (Saved/Audit/*.{json,md} already allowed)

### Lane
`audit` (qwen3:8b or nemotron-free)

### Priority
1 (highest — clears modified files that could block other commits)

### Notes
- Daemon may commit the untracked texture file directly
- Texture swap on existing MIs requires editor action
- If daemon cannot swap, owner must run editor Monolith pass
