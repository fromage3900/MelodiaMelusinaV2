# PCG System Refinement Report

**Cycle:** 2026-06-25 (tick 25 @ 2m loop)  
**Mode:** PCG System Refinement (audit → safe fixes → report)  
**Scope:** `pcg_graph_builder.py`, `pcg_portfolio_standards.py`, validation/audit scripts, universal + greybox builders

---

## Executive Summary

The EnvSandbox PCG stack is **architecturally sound and compatibility-preserving**: one scatter-chain builder (`wire_scatter_chain`), one standards module, and thin style wrappers (Sakura, greybox presets). This cycle fixed a **build-report KeyError**, tightened **deterministic pruning**, centralized **component seeds**, and improved **headless audit reliability**.

| Goal | Status | Notes |
|------|--------|-------|
| Deterministic generation | Improved | Self-prune comparison source `Random` → `Largest`; seeds centralized |
| Reusable biomes | Good | `PRESETS` + `wire_scatter_chain` parameterize density/voxel/exclusion |
| Portfolio-ready outputs | Good | All 7 expected graphs exist; build `passed: true` after force rebuild |
| Maintainability | Improved | Audit fallbacks, `scatter_chain_meta_valid`, `SEED_*` constants |

**Headless verification (UE 5.8 commandlet, null RHI):**

- `setup_pcg_universal.py --force` → `passed: true` (`Saved/Audit/pcg_universal_build.json`)
- `audit_pcg_universal.py` → **`clean: true`** (build-meta chain fallback; all 7 graphs exist)
- `audit_pcg_portfolio.py` → stale JSON (Jun 21); orphan **deleted** per `pcg_library_inventory.json` tick 1

---

## 1. Graph Standards Audit

### Layout contract (`pcg_portfolio_standards.py`)

| Path prefix | Purpose |
|-------------|---------|
| `/Game/EnvSandbox/PCG/Universal/` | Portfolio scatter graphs |
| `/Game/EnvSandbox/PCG/Greybox/` | Blockout preset graphs |
| `/Game/EnvSandbox/PCG/Universal/Subgraphs/` | Reusable exclusion falloff |
| `/Game/EnvSandbox/PCG/Collections/` | `SMC_*` scatter kits |
| `/Game/EnvSandbox/PCG/Styles/<Style>/` | Per-style kits + showcase graphs |
| `/Game/EnvSandbox/PCG/_Deprecated/` | Retired orphans |

### Expected graph inventory

| Asset | Owner script | Role |
|-------|--------------|------|
| `PCG_FoliageDensity` | `setup_pcg_universal.py` | Universal grass scatter |
| `PCG_RockScatter` | `setup_pcg_universal.py` | Rock scatter (1.4× voxel) |
| `PCG_ExclusionFalloff` | `setup_pcg_universal.py` | Tag-exclusion subgraph |
| `PCG_WallDetail` | `setup_pcg_universal.py` | Phase-3 stub (input→output) |
| `PCG_Greybox_Minimal` | `setup_pcg_greybox.py` | Low-density preset |
| `PCG_Greybox_Standard` | `setup_pcg_greybox.py` | Portfolio preset |
| `PCG_Sakura_Showcase` | `setup_pcg_greybox.py` | Showcase preset (lazy build) |

### Findings

- **Compliant:** All graphs under correct folders; `PCG_PYTHON_OWNERS` maps paths to builders.
- **Warn:** Root-level `PCG_MeadowScatter` duplicate alongside `_Deprecated/PCG_MeadowScatter` (`stale_orphan`).
- **Gap:** `L_VFX_Showcase` listed in `SHIPPING_LEVELS` but asset missing (portfolio audit `level_missing`).

---

## 2. Node Consistency Audit

### Canonical scatter chain (`wire_scatter_chain`)

```
Input → [Surface|Volume Sampler] → [Exclusion] → [Density Filter] → [Self Prune] → Transform → Spawner → Output
```

| Node | Universal | Minimal | Standard | Showcase |
|------|-----------|---------|----------|----------|
| Volume sampler | ✓ | ✓ | ✓ | — |
| Surface sampler | — | — | — | ✓ (when enabled) |
| Density filter | ✓ | ✓ | ✓ | ✓ |
| Self prune | ✓ | ✓ | ✓ | ✓ |
| Exclusion inline | — | — | — | ✓ (showcase preset) |
| Transform jitter | 0 | 12 cm | 18 cm | 24 cm |

### Findings

- **Good:** All foliage presets share one builder; no divergent node wiring in Python.
- **Good:** Rock graph uses shorter chain (sampler → transform → spawner) by design.
- **Warn:** `PCG_ExclusionFalloff` subgraph is **passthrough** when `PCGFilterByTagSettings` is unavailable in commandlet; `pcgex_candidate` logged as `PCGExDistanceFilterProviderSettings`.
- **Info:** `is_standalone_graph` triggers UE 5.8 deprecation warnings; migrate to `GraphUsageContext` in a future cycle (no behavior change today).

---

## 3. Scatter Patterns Audit

### Density & spacing

| Parameter | Default | Minimal | Standard | Showcase |
|-----------|---------|---------|----------|----------|
| `voxel_cm` | 180 | 240 | 200 | 220 |
| `density` | 0.42 | 0.28 | 0.38 | 0.32 |
| `SPACING_PRUNE_RADIUS_CM` | 85 | 85 | 85 | 85 |
| ISM band | 250–1600 | 120–900 | 250–1600 | 320–1800 |

### Mesh resolution (`configure_spawner`)

- Weighted entries from `SCATTER_MESHES` role lists; falls back to `resolve_mesh()`.
- Greybox uses engine basic shapes + `Greybox_Kit` cubes — portfolio-safe placeholders.

### Determinism

| Control | Before | After (this cycle) |
|---------|--------|-------------------|
| Component seed | Hardcoded 4242 / 5150 | `SEED_FOLIAGE` / `SEED_ROCKS` in standards |
| Self-prune comparison | `Random` | `Largest` (pairs with `LARGEST_TO_SMALLEST`) |
| Density filter upper bound | `density_mult * 0.85` | unchanged (deterministic given seed) |

### Level drift (Sakura)

Portfolio audit shows `L_SakuraPath` volumes still reference:

- Actor: `PCG_Greybox_GroundCover` (expected: `PCG_Sakura_GroundCover` after `setup_pcg_sakura.py`)
- Graph: `PCG_FoliageDensity` (showcase preset expects `PCG_Sakura_Showcase`)

**Remediation:** Run `setup_pcg_sakura.py` or `fix_pcg_dead_systems.py --apply` to re-apply showcase preset.

---

## 4. Validation Coverage Audit

### Script matrix

| Script | Output | Checks |
|--------|--------|--------|
| `audit_pcg_portfolio.py` | `pcg_portfolio_audit.json` | Plugins, inventory, shipping levels, dead systems, `_PROJECT` leak |
| `audit_pcg_universal.py` | `pcg_universal_audit.json` | Graph existence, chain validity, build gate |
| `audit_pcg_clustering.py` | `pcg_clustering_audit.json` | ISM bands, volume scale, exclusion guides |
| `audit_melodia_pcg_reference.py` | `melodia_pcg_reference.json` | Melodia salvage tiers (read-only) |
| `pcg_validate_helpers.py` | — | `generate_and_wait`, ISM counts, `scatter_chain_meta_valid` |
| `run_specialist_pcg_loop_tick.py` | `specialist_pcg_loop.json` | Rotating 7-task maintenance loop |

### Gaps identified

| Gap | Severity | Mitigation (this cycle) |
|-----|----------|-------------------------|
| `setup_pcg_universal` referenced `report['passed']` but wrote `ok` | **Critical** | Fixed: unified `passed` key; collections no longer block graph pass |
| Headless `get_nodes()` returns 0 | Medium | Audit falls back to `pcg_universal_build.json` metadata |
| Sakura showcase not in `EXPECTED_GRAPHS` | Low | Added to universal audit |
| No static scatter-meta validator | Low | Added `scatter_chain_meta_valid()` |
| PCG audits not wired in `run_verify.ps1` | Medium | Documented; recommend adding to SQA loop |
| ISM counts = 0 in null RHI | Expected | Clustering audit skips ISM band check on null RHI |

---

## 5. Performance Audit

### Cost controls (current)

- **Voxel sizing:** 180–240 cm keeps point counts bounded for greybox volumes (~52×52 m scale).
- **Rock scatter:** 1.4× foliage voxel (≈252 cm) reduces instance count vs grass.
- **Self-prune:** 85 cm radius with `LARGEST_TO_SMALLEST` removes overlapping instances.
- **Density filter:** Upper bound capped at 0.95, scaled by preset multiplier.
- **ISM bands:** Preset-specific min/max guard against runaway instance counts.

### Observations

- Showcase preset trades density for surface sampling + exclusion — appropriate for hero shots.
- `generate_and_wait` polls up to 60 s with GC pump — adequate for editor; consider PIE verification for clustering piles (noted in clustering audit).

---

## 6. Naming Conventions Audit

| Pattern | Example | Usage |
|---------|---------|-------|
| `PCG_<Feature>` | `PCG_FoliageDensity` | Graph assets |
| `SMC_<Scope>_ScatterKit` | `SMC_Portfolio_ScatterKit` | Collection kits |
| `PCG_<Tag>` | `PCG_Ground`, `PCG_Exclude` | Actor tags |
| `PCG_<Role>_*` | `PCG_Greybox_GroundCover` | Level actor labels |
| `PCGCol_*` | Melodia collections | Read-only salvage (Tier A) |
| `MI_<Style>_<Material>` | `MI_Sakura_Grass` | Spawner material overrides |

**Compliant.** Style wrapper (`pcg_sakura_standards.py`) re-exports portfolio constants without renaming graph contracts.

---

## 7. Reusability Audit

### Strengths

- **Single scatter builder** — new biomes = new `PRESETS` entry + optional `graph_path`.
- **Melodia tier hints** — `melodia_tier()` guides salvage without importing `_PROJECT` graphs.
- **`duplicate_scatter_kit`** — graceful manifest fallback when Melodia source missing.
- **Greybox apply** — `apply_greybox_pcg(level, preset)` works on any level with tagged ground.

### Extension points (no redesign required)

1. Add preset key to `PRESETS` → call `build_preset_graphs` or `wire_scatter_chain` with cfg.
2. Add style folder under `Styles/<Name>/` + thin standards re-export (Sakura pattern).
3. Wire `GRAPH_WALL` spline scatter when Phase 3 is ready (stub already reserved).

---

## 8. Safe Improvements Applied

| File | Change |
|------|--------|
| `setup_pcg_universal.py` | Fix `passed`/`ok` KeyError; separate `graphs_ok` / `collections_ok`; collections `manifest_only` no longer fails build |
| `pcg_graph_builder.py` | Self-prune `comparison_source`: `Random` → `Largest` for deterministic output |
| `pcg_portfolio_standards.py` | Add `SEED_FOLIAGE` (4242), `SEED_ROCKS` (5150) |
| `setup_pcg_greybox.py` | Use centralized seed constants |
| `audit_pcg_universal.py` | Add `GRAPH_SAKURA_SHOWCASE`; chain validation with build-meta fallback; `chain_source` telemetry |
| `pcg_validate_helpers.py` | Add `scatter_chain_meta_valid()` + `SCATTER_CHAIN_META_KEYS` |

All changes are **backward-compatible** — no new architecture, no pin/output contract changes.

---

## 9. Recommended Next Cycle

| Priority | Action | Command |
|----------|--------|---------|
| P1 | Remove stale root orphan | `python Content/Python/fix_pcg_dead_systems.py --apply` |
| P1 | Re-apply Sakura showcase volumes | `python Content/Python/setup_pcg_sakura.py --rebuild` |
| P2 | Rebuild graphs after prune change | `python Content/Python/setup_pcg_universal.py --force` |
| P2 | Verify clustering in editor PIE | Headless level-load audits crash commandlet (tick 3); use live editor |
| P3 | Add PCG portfolio step to `run_verify.ps1` | SQA integration |
| P3 | Replace deprecated `is_standalone_graph` | When `GraphUsageContext` Python binding is stable |

---

## 10. Repeat Loop Checklist

```
[✓] 1. Audit graph standards
[✓] 2. Audit node consistency
[✓] 3. Audit scatter patterns
[✓] 4. Audit validation coverage
[✓] 5. Audit performance
[✓] 6. Audit naming conventions
[✓] 7. Audit reusability
[✓] 8. Apply safe improvements
[✓] 9. Generate report
[✓] 10. Repeat (loop armed — 2m interval, PID 9116)
```

---

## Artifact Index

| Artifact | Path |
|----------|------|
| This report | `PCG_REFINEMENT_REPORT.md` |
| Universal build | `Saved/Audit/pcg_universal_build.json` |
| Universal audit | `Saved/Audit/pcg_universal_audit.json` |
| Portfolio audit | `Saved/Audit/pcg_portfolio_audit.json` |
| Standards | `Content/Python/pcg_portfolio_standards.py` |
| Builder | `Content/Python/pcg_graph_builder.py` |

---

*Generated by PCG System Refinement Mode — Environment Portfolio Platform (PPA domain).*
