# Portfolio Pipeline Audit — Architecture Review

> Read-only audit. 2026-06-25. Scope: the `Unreal → portfolio_package.json → Figma` loop.
> Companion docs: [CURRENT_SYSTEM_MAP.md](CURRENT_SYSTEM_MAP.md), [NEXT_HIGHEST_LEVERAGE_TASK.md](NEXT_HIGHEST_LEVERAGE_TASK.md).

## Executive summary

The pipeline is **architecturally sound and over-built downstream, under-fed upstream.** The aggregator, schema, layout manager, and render-plate compiler are production quality — they always produce a valid `portfolio_package.json` and never crash. But five of seven package sections are null/empty because the **capture stage isn't delivering real data.** The dominant cause is a single stale level-path constant, compounded by one orphaned exporter and two genuinely-missing producers.

This is good news: the expensive, hard-to-get-right part (the deterministic compiler + contract) is done. The remaining work is small, surgical, and mostly about *feeding* the existing machine — not rebuilding it.

## 1. Exporter architecture

**Pattern (good):** thin exporters each write one read-only JSON/PNG fragment; a separate compiler assembles them. Clean separation of concerns, idempotent, resilient to partial failure. This is the right shape for a TD pipeline.

**Risks:**

| # | Risk | Evidence | Severity |
|---|---|---|---|
| E1 | **Silent null capture** — exporters happily emit all-null fragments and the run still reports success. A "green" pipeline can yield an empty portfolio. | `generate_portfolio.py` exit 0 whenever `portfolio_package.json` exists, regardless of content; last package is 5/7 empty. | **High** |
| E2 | **Stale hardcoded level path** | `generate_portfolio.py:30` points at `/Game/EnvSandbox/Levels/...`; level is at `/Game/EnvSandbox/Environments/Sakura/...`. | **High** (root cause) |
| E3 | **Deprecated UE 5.8 API** — `EditorLevelLibrary.get_editor_world()` used in `scene_metadata_exporter.py` and `render_exporter.py`; the legacy script already moved to `UnrealEditorSubsystem`. | Two scanners, two API generations. | Medium |
| E4 | **Orphaned + broken material exporter** | `capture_material_previews.py` not wired; `main()` missing `datetime` import; asset filter matches nothing. | Medium |
| E5 | **Default headless run disables Monolith** | launcher adds `-DisablePlugins=Monolith` unless `PORTFOLIO_CAPTURE_MONOLITH=1`. So `materials`/`breakdown` render groups can never populate in the default path. | Medium |

## 2. Schema architecture

**Strengths:** `portfolio_schema.json` is a real single-source contract — section requirements, `source_fragments` (which file owns which section), explicit `field_mappings` (rename tables), and `legacy_aliases` for read-time normalization. The aggregator is fully schema-driven. Field mappings are correct (verified: `scene_name ← level_name`, etc. — the null output is bad source data, not a mapping bug).

**Risk — contract drift (S1, Medium):** the aggregator embeds a second copy of the schema as `_FALLBACK_SCHEMA` (`portfolio_aggregator.py:38-81`). Two copies of the contract will drift. The fallback is a reasonable safety net but should be kept obviously in sync (or generated from the JSON).

**Risk — schema demands data no producer emits (S2, Low/structural):** `materials.required_fields` wants `material_type`, `shader_family`, `output_maps`; `stats` wants `triangle_count`, `draw_calls`. No exporter produces these. The schema is ahead of the producers — fine as a target, but it guarantees perpetual validation warnings until producers catch up.

## 3. Aggregator architecture

**This is the best-engineered part of the system.** Read-only, deterministic (`sort_keys=True`), provenance tracking, soft validation (never raises), guaranteed 7-key output shape, and a fallback package if assembly throws. It correctly maps every section and faithfully reports what's missing via `validation_warnings`.

**Observation — maturity inversion (A1):** the compiler is more sophisticated than the exporters feeding it. The team built downstream rigor before upstream reliability. Nothing to fix in the aggregator; the lesson is to point effort upstream.

**Minor (A2):** the aggregator treats a present-but-null field as "missing required field" (e.g. `scene.scene_name`). Correct behavior, but it means *fixing the source* (not the aggregator) is always the right move — reinforcing that this is a data problem.

## 4. Design-system integration

**The biggest missing contract (D1, High for the stated goal).** The pipeline's terminal artifact is `portfolio_package.json`, but **nothing consumes it.** The Figma plugin (`melodia-figma-plugin/code.js`) renders from hardcoded token data, and the Wix embeds are hand-authored. The "→ Figma mapping → portfolio output" arrow in the goal is documentation, not wiring. Until something reads the package, improving the package has no visible downstream effect.

Note also the design system lives in a **separate, un-versioned-with-the-project folder** (`Downloads/melodia-design-system/`), disconnected from the UE repo. There is no defined hand-off path or schema mapping between `portfolio_package.json` and the Figma component inputs.

## 5. Duplication

| Dup | Detail | Recommendation |
|---|---|---|
| Two scene scanners | `scene_metadata_exporter.py` (Metadata/, modern shape, deprecated world API) vs `capture_scene_metadata.py` (SceneMetadata/, legacy shape, modern world API) | Pick the primary (`scene_metadata_exporter.py`), port the modern `UnrealEditorSubsystem` call into it, delete or archive the legacy one. Not urgent — aggregator's fallback prevents breakage. |
| Two output dirs | `Metadata/` vs `SceneMetadata/` for the same concept | Collapses naturally when the duplicate scanner is retired. |
| Design-system doc naming | Project references `DESIGN_SYSTEM.md`; actual file is `DESIGN-SYSTEM.md` in Downloads | Cosmetic; standardize the reference. |

## 6. Bottlenecks

The entire "usable portfolio" outcome is bottlenecked on **one thing: the capture stage producing a non-empty level scan.** Everything downstream of that (layout, compiler, schema, package shape) already works. Optimizing the aggregator or extending the schema yields nothing until the scene loads.

## 7. Unnecessary complexity

- The Monolith material-grid / overlay / trim capture paths (`capture_portfolio_renders.py`) are elaborate, unverified, and skip by default. They are downstream sophistication built before the basic viewport+scene capture was proven reliable. Keep, but don't invest further until the spine works.
- The gap-analysis docs (`UNREAL_CAPTURE_GAPS`, `FIGMA_LAYOUT_GAPS`, `UNMAPPED_DATA_POINTS`) enumerate advanced features (G-buffer passes, LOD metrics, UDS params, audio-reactivity bands) that are far ahead of a pipeline that currently can't name its own level. Useful backlog; wrong priority for now.

## 8. Missing contracts (summary)

1. **Capture-succeeded assertion** — no check that the level loaded / the scan is non-empty before declaring success. (Causes E1.)
2. **`portfolio_package.json` → Figma ingestion** — no consumer reads the package. (D1.)
3. **Stats producer** — schema slot exists, no exporter. (S2.)
4. **Material previews producer** — exists but orphaned and broken. (E4.)

## 9. Verdict

Do **not** redesign anything. The architecture is correct and the compiler is excellent. The work is to *feed* the existing machine and to *connect* its output. The smallest change that turns the all-null package into a genuinely usable one is identified in [NEXT_HIGHEST_LEVERAGE_TASK.md](NEXT_HIGHEST_LEVERAGE_TASK.md).
