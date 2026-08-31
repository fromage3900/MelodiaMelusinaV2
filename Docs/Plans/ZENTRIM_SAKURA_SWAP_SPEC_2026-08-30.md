# ZenTrim Sakura Texture Swap Spec — 2026-08-30

**Source:** `Saved/Audit/zentrim_cleanup_proposal_2026-08-31.json`
**Modified files:** 3 `.uasset` files (daemon guardrail — spec only, no writes)

---

## Summary

Two hero cloth MIs use trimsheet textures that cause stretching (hero cloth has no trim UVs). Third file is a copernicus dress bake thickness map.

---

## Block 1 — SakuraDream MIs (Texture Swap Required)

| Target | Current Texture | Proposed Replacement | Rationale |
|---|---|---|---|
| `Content/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream.uasset` | `/Game/Greybox_Kit/ZenTrim_Base4K_BaseColor` | `KB3D_ATL_BrickStoneCleanA_BaseColor` | Trimsheet stretches on hero cloth (no trim UVs); KB3D tilable is correct |
| `Content/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1.uasset` | `/Game/Greybox_Kit/ZenTrim_Base4K_BaseColor` | `KB3D_ATL_BrickStoneCleanB_BaseColor` (different variant) | IntegratedV1 uses NikkiChain master but retains trimsheet; swap to KB3D tilable |

**Owner verification needed:**
- Confirm KB3D_ATL_BrickStoneCleanA_Normal and _Roughness also assigned if needed
- Confirm KB3D_ATL_BrickStoneCleanB_Normal and _Roughness also assigned if needed
- Visual check in-editor after swap

---

## Block 2 — Copernicus Dress Bake (Commit Only)

| Field | Value |
|---|---|
| File | `Content/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_DressShorewake_Thickness_SBS.uasset` |
| Change | Modified (4 insertions, 4 deletions in .uasset) |
| Origin | Commit `31b06169` (copernicus petal Cop arrow + VAT) |
| Action | Texture rebake — thickness map updated |
| Risk | LOW — automated copernicus output |

---

## Proposed Commit Grouping

**Batch 1 — PBR script (no .uasset):**
```bash
git add Content/Python/create_pbr_instances.py
git commit -m "chore: add PBR MI creation script for 12 orphaned texture sets"
```

**Batch 2 — Copernicus rebake:**
```bash
git add Content/Melodia/Characters/Melusina/Textures/Clothes/T_MelusinaC_DressShorewake_Thickness_SBS.uasset
git commit -m "fix(copernicus): rebake Shorewake dress thickness map"
```

**Batch 3 — Sakura swaps (after owner verification):**
```bash
git add Content/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream.uasset \
        Content/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1.uasset
git commit -m "fix(materials): swap ZenTrim trimsheet to KB3D tilable on SakuraDream MIs"
```

---

## Risk Assessment

| Item | Risk | Notes |
|---|---|---|
| PBR script commit | LOW | Non-destructive, editor-only utility |
| Copernicus rebake | LOW | Automated output from verified pipeline |
| Sakura texture swap | MEDIUM | Requires owner visual verification in-editor |

---

## Guardrails

- Daemon never writes `.uasset` directly
- Sakura swap requires owner sign-off (texture assignment)
- Pre-commit hook: `.uasset` files are allowed under `Content/` (not `Intermediate/`/`Saved/`)