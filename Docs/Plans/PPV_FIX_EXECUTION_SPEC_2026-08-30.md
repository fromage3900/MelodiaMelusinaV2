# PPV Canonical State — Execution Spec — 2026-08-30

**Source**: `Saved/Audit/ppv_canonical_state_2026-08-31.json`
**Prerequisites**: Live Monolith MCP (`:9316`), editor open, no modal blocking

---

## Current Drift

| Issue | Current | Canonical | Severity |
|---|---|---|---|
| Actor label | `PPV_Dreamprint_Candidate` | `PPV_NikkiDream` | HIGH |
| Grade weight | `0.18` | `0.69` | HIGH |
| Outline weight | `0.57` | `1.0` | HIGH |
| StarryNight MI | `MI_StarryNight_VanGogh` (surface) | `MI_StarryNight_Hero` (post-process) | HIGH |

---

## Fix Sequence (owner or daemon with editor access)

### Option A: Run existing Python harnesses (preferred)

```bash
# From project root — these scripts are idempotent
python Content/Python/finalize_ppv_hero_stack.py
python Content/Python/build_ppv_nikkidream.py
python Content/Python/strip_ppv_color_overrides.py
```

### Option B: Manual via Monolith MCP

```
1. Open PPV_NikkiDream actor in editor
2. Set actor label: PPV_NikkiDream
3. PostProcessVolume settings:
   - blendables[0]: MI_MelodiaInk_PortfolioHero, weight=1.0
   - blendables[1]: MI_MeluColorGrade_PortfolioHero, weight=0.69
   - blendables[2]: MI_StarryNight_Hero, weight=1.0
4. Save actor
```

### Verification

```bash
melodia_ppv_report  # expect canonical stack confirmed
melodia_material_get_compile_stats MI_MelodiaInk_PortfolioHero  # expect 0 errors
melodia_material_get_compile_stats MI_StarryNight_Hero  # expect 0 errors
```

---

## Safety Notes

- ⚠️ Requires live Monolith MCP. If MODAL_OPEN warnings persist, dismiss editor modals first.
- ⚠️ Never hand-edit `.uasset` — always use editor Python or Monolith.
- ⚠️ `finalize_ppv_hero_stack.py` is idempotent — safe to re-run.