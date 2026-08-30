# PPV Drift T3D Fix Spec — 2026-08-31

**Generated:** 2026-08-31 (overnight daemon)
**Source:** `Saved/Audit/ppv_canonical_state_2026-08-31.json`
**Scope:** Post-Process Volume (PPV) drift corrections — 4 fixes
**Mode:** T3D injection spec — no direct .uasset writes

---

## Canonical PPV Stack

| Blendable | Canonical Weight | Domain |
|---|---|---|
| MI_MelodiaInk_PortfolioHero | 1.0 | post_process |
| MI_MeluColorGrade_PortfolioHero | 0.69 | post_process |
| MI_StarryNight_Hero | 1.0 | post_process |

**Actor Label:** `PPV_NikkiDream`

---

## Drift Findings

### 1. Label Mismatch (HIGH severity)

| Field | Current | Canonical |
|---|---|---|
| Actor Label | `PPV_Dreamprint_Candidate` | `PPV_NikkiDream` |

### 2. Weight Drifts

| Slot | Current | Canonical | Delta |
|---|---|---|---|
| grade (MI_MeluColorGrade_PortfolioHero) | 0.18 | 0.69 | -0.51 |
| outline (MI_MelodiaInk_PortfolioHero) | 0.57 | 1.0 | -0.43 |

### 3. Surface Domain Drop

| Asset | Current Domain | Required Domain | Fix |
|---|---|---|---|
| MI_StarryNight_VanGogh | MD_SURFACE | MD_POST_PROCESS | Replace with MI_StarryNight_Hero |

---

## T3D Injection Spec

Apply via `python Tools/t3d_inject.py` or live Monolith editor:

```json
{
  "target": "/Game/EnvSandbox/Blueprints/PPV_NikkiDream",
  "operations": [
    {
      "op": "set_property",
      "property": "ActorLabel",
      "value": "PPV_NikkiDream"
    },
    {
      "op": "set_blendable_weight",
      "blendable": "MI_MeluColorGrade_PortfolioHero",
      "weight": 0.69
    },
    {
      "op": "set_blendable_weight",
      "blendable": "MI_MelodiaInk_PortfolioHero",
      "weight": 1.0
    },
    {
      "op": "replace_blendable",
      "old": "MI_StarryNight_VanGogh",
      "new": "MI_StarryNight_Hero",
      "weight": 1.0
    }
  ]
}
```

## Fix Sequence (ordered)

1. **Rename PPV actor label** → `PPV_NikkiDream`
2. **Set grade weight** → `0.69`
3. **Set outline weight** → `1.0`
4. **Replace MI_StarryNight_VanGogh** → `MI_StarryNight_Hero` (post-process domain)
5. **Verify compile** via `melodia_material_get_compile_stats`

## Safety

- Requires live Monolith MCP (localhost:9316) + editor
- Never hand-edit .uasset binary
- Gate acceptance: ledger row via `Tools/echo_run.py record ppv_drift_fix pass` (owner-only)
- Math harness: 32/32 pass (unaffected — this is a content ops task)

## Pre-Commit Hook Notes

- No new files added
- No .gitignore changes
- No CLAUDE.md never-touch paths affected