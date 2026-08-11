# Portfolio Ship Checklist

**Status:** In Progress — delegated to AI agents (per Decision 008, 2026-07-29)  
**User supplies:** Hero renders, material previews, and final website push assets  
**AI agent tasks:** Pipeline fixes, capture automation, website handoff  
**Render supply now delegated to BLACKBOXAI agent lane.**  
User provides final composed renders → agent runs pipeline → validates → deploys to GitHub Pages.

---

## Pipeline Fixes (AI Agent Delegated)

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Fix portfolio level path in `generate_portfolio.py` | **Done** | Already fixed — `LEVEL` corrected to `/Game/EnvSandbox/Environments/Sakura/L_SakuraPath` |
| 1.2 | Fix material preview exporter (`NameError` + wrong filter) | **Done** | Already fixed — `import datetime` present, asset filter uses `MaterialInterface` class check |
| 1.3 | Verify render capture works (PSO fix + CineCamera) | **Available** | Start editor with `-unattended`, run `trigger_build`, test capture on known material |
| 1.4 | Run full portfolio pipeline end-to-end | **Available** | `generate_portfolio.py` → `portfolio_aggregator.py` → `package_to_website_handoff.py` |
| 1.5 | Ship website (ingest → validate → deploy) | **Blocked** | Waiting on user-supplied hero renders for website push |

---

## Portfolio Package Sections — Target State

| Section | Current | Target | Notes |
|---|---|---|---|
| `scene` | 🔴 null | ✅ real metadata | Unblocked by 1.1 |
| `assets` | 🔴 `[]` | ✅ populated | Unblocked by 1.1 |
| `materials` | 🔴 `[]` | ✅ 30+ instances | Unblocked by 1.2 |
| `renders` | 🟡 partial | ✅ hero + breakdown + materials + pcg | User supplies hero renders |
| `pcg` | ✅ full | ✅ full | Already working |
| `stats` | 🔴 null | 🟡 documented gap | Stats exporter parked (P3) |
| `metadata` | ✅ full | ✅ full | Already working |

---

## Deliverables

- [ ] Live website with hero renders for 4 WP levels
- [ ] Material preview gallery (30+ instances)
- [ ] PCG system breakdown (53+ graphs, 6 Escher generators, cathedral grammar)
- [ ] Scene metadata for loaded level
- [ ] Stats section (documented as known gap — no exporter exists)

---

## Known Gaps (Documented, Not Blocking)

- Stats exporter missing — schema slot ready, no producer
- Some render captures may be placeholder until CineCamera is tagged
- PCG crash graphs (4) quarantined — not blocking portfolio
- Material system review (7 fixes) parked — post-ship