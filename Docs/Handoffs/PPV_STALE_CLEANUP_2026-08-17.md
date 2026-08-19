# Handoff: Stale PPV Cleanup — L_SakuraPath and L_Template (2026-08-17)

**Status**: Documentation added. Manual Unreal Editor action required.

> **UPDATE 2026-08-18** — **L_SakuraPath no longer exists** (Sakura folder under
> `EnvSandbox/Environments/` is empty; only `L_Render_SakuraDream` remains under
> `_PROJECT/Levels/RenderTests/`). Its stale-volume action item is obsolete.
> **The dreamprint ink layer was never attached anywhere** (last setup run was
> 2026-08-01, before the ink existed); `setup_nikki_render_post_process.py` was
> re-run 2026-08-18 and all 9 remaining levels now carry the full stack —
> outline + grade + **ink** (`nikki_post_process_audit.json`, ok=true).

## Overview

Per [`PPV_STORYBOOK_OUTLINE_INTEGRATION_2026-08-01.md`], two levels contain stale post-process volumes from the pre-dreamprint era that must be cleaned up before the dreamprint PPV replacement is fully authoritative.

## L_SakuraPath — Stale Unlabeled Volume

| Actor | Priority | Blendables |
|---|---|---|
| `PPV_NikkiDream` | 10.0 | `MI_PP_StorybookOutline`, `M_PP_MeluColorGrade` (current) |
| `PostProcessVolume` (unlabeled) | 0.0 | `M_PP_ToonOutline`, `M_PP_StorybookVines_Inst` — **quarantined** |

**Issue**: Weighted blendables accumulate across overlapping volumes. The old outline (`M_PP_ToonOutline`/`M_PP_StorybookVines_Inst`, priority 0.0) is stacked on top of the new `PPV_NikkiDream` blendables, causing duplicate edge-detection and visual artifacts.

**Fix**: Delete or disable the unlabeled `PostProcessVolume` actor in L_SakuraPath.

**Owner Decision**: Per `CLAUDE.md` standing rule, L_SakuraPath art direction is owner‑owned. This is not an agent-driven change, but must be executed before dreamprint promotion.

## L_Template — Stale Volume + Missing PPV_NikkiDream

| Actor | Priority | Blendables |
|---|---|---|
| `PostProcessVolume` (unlabeled) | 0.0 | `M_PP_ToonOutline`, `M_PP_StorybookVines_Inst` — **quarantined** |
| `PPV_NikkiDream` | *absent* | — |

**Issue**: L_Template carries the same stale unlabeled volume as L_SakuraPath, **and** has no `PPV_NikkiDream` actor. Every level copied from L_Template inherits the stale volume without the corresponding grade/color pipeline.

**Fix**:
1. Delete or disable the unlabeled `PostProcessVolume` actor in L_Template.
2. Ensure L_Template has a `PPV_NikkiDream` volume. 

**Note**: L_Template is now included in [`setup_nikki_render_post_process.py`]'s `LEVELS` tuple (added 2026-08-17). The next script run (`python setup_nikki_render_post_process.py --force`) will spawn a `PPV_NikkiDream` actor if none exists, and apply the canonical blendable stack (`M_PP_StorybookOutline` weight 1.0, `M_PP_MeluColorGrade` weight 0.69).

## Dreamprint PPV Replacement Context

The dreamprint system is the **official replacement for the NikkiDream PPV pipeline**. It adds:

- `MPC_MelodiaInk` + `InkReact` scalar parameter (meta-sound driven ink liveliness)
- Profile-based MI switching via `ApplyProfile()` (ProfileIndex 0/1/2 → GameplayStandard/Narrative/PortfolioHero)
- `InkMasterWeight` control per profile
- A/B verification via `setup_dreamprint_ab.py`

The old NikkiDream PPV components (`M_PP_StorybookOutline`, `M_PP_MeluColorGrade`) remain in the scene but are now managed **alongside** the dreamprint ink layer. The stale old-outline volumes **must** be cleaned up to prevent blendable stacking conflicts.

## Action Items

- [ ] Delete/disable unlabeled `PostProcessVolume` in L_SakuraPath
- [ ] Delete/disable unlabeled `PostProcessVolume` in L_Template
- [ ] Run `python setup_nikki_render_post_process.py --force` to ensure L_Template gets `PPV_NikkiDream`
- [ ] Re-run `audit_nikki_render_post_process.py` to verify all levels
- [ ] Commit cleanup changes (when outside read-only mode)