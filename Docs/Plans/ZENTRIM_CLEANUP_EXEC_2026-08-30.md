# ZenTrim Cleanup Execution Spec

**Generated:** 2026-08-30 (overnight daemon)
**Source:** `Saved/Audit/zentrim_cleanup_proposal_2026-08-31.json`
**Mode:** Spec only — no `.uasset` hand-edits. Editor Monolith pass required to apply.

---

## Summary

| Category | Count | Action |
|---|---|---|
| Legitimate trimsheet MIs | 12 | None — these are correct |
| Misuse MIs | 2 | Texture swap via editor |
| Scratch quarantine | 2 | Delete or move to quarantine |
| **Total zentrim refs** | **86** | |

---

## Misuse Targets (2 MIs needing texture swap)

### 1. `MI_NikkiHero_SakuraDream`

| Field | Current | Proposed |
|---|---|---|
| **Path** | `Content/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream.uasset` | Same |
| **Current texture** | `/Game/Greybox_Kit/ZenTrim_Base4K_BaseColor` | `KB3D_ATL_BrickStoneCleanA_BaseColor` |
| **Rationale** | SakuraDream hero cloth has no trim UVs — trimsheet causes stretching | KB3D_ATL_* textures are proper tilable PBR with matching Normal/Roughness |
| **Also swap** | | KB3D_ATL_BrickStoneCleanA_Normal, _Roughness, _Metallic, _Height |
| **Tiling check** | Verify `DetailTiling` / `Stack2_Tiling` values are appropriate for fabric (not trim-sheet scale) |
| **Effort** | Low | |

### 2. `MI_NikkiHero_SakuraDream_IntegratedV1`

| Field | Current | Proposed |
|---|---|---|
| **Path** | `Content/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1.uasset` | Same |
| **Current texture** | `/Game/Greybox_Kit/ZenTrim_Base4K_BaseColor` | `KB3D_ATL_BrickStoneCleanB_BaseColor` (different variant to avoid identical look) |
| **Rationale** | IntegratedV1 uses tilable NikkiChain master but retains trimsheet | KB3D tilable for proper chain fabric rendering |
| **Also swap** | | KB3D_ATL_BrickStoneCleanB_Normal, _Roughness, _Metallic, _Height |
| **Tiling check** | Same as above | |
| **Effort** | Low-Medium | |

---

## Scratch Quarantine

| File | Recommendation |
|---|---|
| `Content/EnvSandbox/Materials/_Scratch/MI_Nikki_ZenTrimTest.uasset` | **DELETE** — Scratch test with same misuse pattern. Not shipping. |
| `Content/EnvSandbox/Materials/_Scratch/M_Master_Toon_Universal_Inst2.uasset` | **Quarantine** — References ZenTrim textures via M_Master_Toon_Universal. Either swap to KB3D tilables or leave quarantined under `_Scratch/`. |

---

## Execution Order (Editor Monolith Pass)

```
1. Quarantine scratch files (delete or leave in _Scratch — owner decision)
2. Open MI_NikkiHero_SakuraDream in editor
   → Swap ZenTrim_Base4K_BaseColor → KB3D_ATL_BrickStoneCleanA_BaseColor
   → Swap ZenTrim_Base4K_Normal → KB3D_ATL_BrickStoneCleanA_Normal
   → Swap ZenTrim_Base4K_Roughness → KB3D_ATL_BrickStoneCleanA_Roughness
3. Open MI_NikkiHero_SakuraDream_IntegratedV1 in editor
   → Swap ZenTrim_Base4K_BaseColor → KB3D_ATL_BrickStoneCleanB_BaseColor
   → Same for Normal/Roughness
4. Verify DetailTiling/Stack2_Tiling values appropriate for fabric
5. Run project_state.py staleness check after editor save
```

---

## KB3D_ATL Family Reference

All textures live at: `Content/EnvSandbox/Textures/Atlantis/`

| Variant | BaseColor | Normal | Roughness | Metallic | Height |
|---|---|---|---|---|---|
| BrickStoneCleanA | ✓ | ✓ | ✓ | ✓ | ✓ |
| BrickStoneCleanB | ✓ | ✓ | ✓ | ✓ | ✓ |
| BrickStoneCleanBeigeA | ✓ | ✓ | ✓ | ✓ | ✓ |
| BrickStoneCleanBlueA | ✓ | ✓ | ✓ | ✓ | ✓ |
| BrickStoneCleanBlueB | ✓ | ✓ | ✓ | ✓ | ✓ |
| BrickStoneCleanBlueC | ✓ | ✓ | ✓ | ✓ | ✓ |
| BrickStoneCleanRedB | ✓ | ✓ | ✓ | ✓ | ✓ |
| BrickStoneCleanWhiteA | ✓ | ✓ | ✓ | ✓ | ✓ |

All have complete 5-map PBR sets (BaseColor/Height/Metallic/Normal/Roughness).

---

## Guardrails

- **Never write .uasset directly** — all swaps must go through Editor Monolith MCP or T3D command
- **Never certify gates without ledger** — this is a material fix, no gates affected
- **Propose specs/PRs** — this spec documents intent, execution is owner-driven
- **SPLIT protection not needed** — material swaps are not in never-touch table

## Notes

- The 12 legitimate trimsheet MIs are correctly using ZenTrim textures on trim UV hosts — do NOT modify them
- After texture swaps, the 2 misuse MIs will still reference the `NikkiChain` master material — only their texture parameters change
- If additional SakuraDream variants exist in other paths (e.g., `NikkiIntegrated/Mapped/`), check them for the same misuse pattern