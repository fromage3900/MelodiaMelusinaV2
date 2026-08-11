# Current System Map — Portfolio Generation Pipeline

> Read-only audit snapshot. Captured 2026-06-25 from `G:/EnvironmentPortfolio/BS_GodFile`.
> No code was modified to produce this document.
> Companion docs: [PORTFOLIO_PIPELINE_AUDIT.md](PORTFOLIO_PIPELINE_AUDIT.md), [NEXT_HIGHEST_LEVERAGE_TASK.md](NEXT_HIGHEST_LEVERAGE_TASK.md).

## 1. The intended loop

```
Unreal Scene (L_SakuraPath)
  → exporters write JSON/PNG fragments  (Saved/Portfolio/**)
  → portfolio_aggregator compiles       → Saved/Portfolio/portfolio_package.json
  → Figma plugin maps the package       → breakdown pages  (← NOT wired today)
```

The first three arrows exist in code. The fourth (package → Figma) is documented intent only.

## 2. Component inventory

All code lives in `Content/Python/`. Status legend: ✅ production-ready · 🟡 partial / works-with-caveats · 🔴 broken or orphaned · ⬜ specified but not implemented.

### Producers (exporters)

| Component | File | Writes | Status | Notes |
|---|---|---|---|---|
| Scene metadata (primary) | `scene_metadata_exporter.py` | `Saved/Portfolio/Metadata/scene_metadata.json` | 🟡 | Correct shape, but last run wrote **all nulls** (level never loaded). Uses deprecated `EditorLevelLibrary.get_editor_world()`. |
| Scene metadata (legacy) | `capture_scene_metadata.py` | `Saved/Portfolio/SceneMetadata/scene_metadata.json` | 🔴 | **Duplicate** scanner, different schema (`world`/`actors`/`class`) and path. Uses the *modern* `UnrealEditorSubsystem` API. Aggregator only falls back to it. |
| Viewport renders | `render_exporter.py` | `Renders/Hero/`, `Renders/Breakdown/` | 🟡 | Hero capture works (2 PNGs on disk). Breakdown needs a tagged CineCamera. Level slug uses the same deprecated API. |
| Render orchestrator | `capture_portfolio_renders.py` | (calls compiler) | 🟡 | Viewport step works; Monolith material-grid / overlay / trim steps **gracefully skip** when Monolith is down (default). |
| Render-plate compiler | `compile_render_plates.py` | `Renders/renders_manifest.json` | ✅ | Disk scan + Figma presentation blocks. Always writes valid manifest. (Minor: surfaced 1 of 2 hero PNGs in last run — verify.) |
| Material previews | `capture_material_previews.py` | `MaterialPreviews/previews_manifest.json` | 🔴 | **Orphaned** (not called by any orchestrator) **and broken**: `main()` references `datetime` without importing it (NameError); asset filter `endswith(".mat"/".material")` matches no UE asset path → 0 results even if run. Dir does not exist on disk. |
| Stats manifest | — | `Stats/portfolio_stats_manifest.json` | ⬜ | **No exporter exists.** Schema slot + aggregator mapper are ready and waiting. |
| PCG build | `audit_pcg_universal.py` et al. | `Saved/Audit/pcg_universal_build.json` | ✅ | Present (1.6 KB). This is the *only* fully-populated package section today. |

### Infrastructure

| Component | File | Role | Status |
|---|---|---|---|
| Filesystem layout | `portfolio_output_layout.py` | Canonical paths, `ensure_portfolio_layout()`, `organize_portfolio_outputs()` (moves stray PNGs into Hero/Breakdown/Materials/Trims) | ✅ |
| Schema / contract | `portfolio_schema.json` | v1.0 sections + `source_fragments` + `field_mappings` + `legacy_aliases` | ✅ |
| Aggregator (compiler) | `portfolio_aggregator.py` | Read-only fragment → `portfolio_package.json`. Provenance, soft validation, always writes valid output, fallback package on error | ✅ **(strongest component)** |
| Entry point | `generate_portfolio.py` | In-editor + headless-Cmd launcher; loads level, runs steps, writes `Saved/Audit/generate_portfolio.json` | 🟡 — see §4 |
| Monolith client | `monolith_mcp_client.py` | JSON-RPC to Monolith MCP (port 9316) for grid/overlay captures | ✅ |
| Editor hook | `init_unreal.py` | Startup wiring | ✅ |

### Downstream presentation (separate repo: `C:/Users/froma/Downloads/melodia-design-system/`)

| Component | Status | Notes |
|---|---|---|
| `DESIGN-SYSTEM.md`, `tokens.json` | ✅ | Mature design system (note: file is `DESIGN-SYSTEM.md`, hyphenated — not `DESIGN_SYSTEM.md`). |
| `melodia-figma-plugin/code.js` | 🟡 | Real plugin, but token data is **hardcoded** ("mirrors tokens.json"). It does **not** read `portfolio_package.json`. |
| `wix/*.html` embeds, PSD heroes | ✅ | Presentation assets, manually driven. |

## 3. Output state — what's actually in `portfolio_package.json`

Last generated 2026-06-25T08:32 UTC. The package is **schema-valid with all 7 top-level keys**, but only 2 of 7 sections carry real data:

| Section | Populated? | Why |
|---|---|---|
| `scene` | 🔴 null | `scene_name`/`level_path`/`engine` all null — source `scene_metadata.json` is all-null. |
| `assets` | 🔴 `[]` | `static_mesh_actors` empty in source (no level loaded). |
| `materials` | 🔴 `[]` | `previews_manifest.json` missing (exporter orphaned). |
| `renders` | 🟡 partial | `hero` = 1 plate ✅; `breakdown`/`materials`/`pcg` groups empty (need Monolith/CineCamera). |
| `pcg` | ✅ full | Mapped from existing `pcg_universal_build.json`. |
| `stats` | 🔴 null | No stats exporter exists. |
| `metadata` | ✅ full | Provenance + 9 validation warnings. |

**Plain reading:** the plumbing runs end-to-end and never crashes, but the package is *data-starved*. The structural pipeline is done; the capture stage is not delivering real data.

## 4. The root cause of the empty `scene`/`assets`

`generate_portfolio.py:30` hardcodes:

```python
LEVEL = "/Game/EnvSandbox/Levels/L_SakuraPath"
```

The level does **not** live there. On disk it is:

```
Content/EnvSandbox/Environments/Sakura/L_SakuraPath.umap
→ /Game/EnvSandbox/Environments/Sakura/L_SakuraPath
```

So `_load_portfolio_level()` calls `does_asset_exist(".../Levels/L_SakuraPath...")` → **False** → logs "level not found, using current editor level" → no level is loaded → every exporter scans an empty world → null scene, empty assets, null engine version, and a render with a `"level"` placeholder slug. One stale constant starves the spine of the portfolio.

## 5. Data-flow diagram (as-built)

```
generate_portfolio.py  (in-editor OR headless UnrealEditor-Cmd)
  │
  ├─ ensure_portfolio_layout()                         ✅ dirs created
  ├─ _load_portfolio_level()  ──[stale path → no load]🔴
  ├─ scene_metadata_exporter ─► Metadata/scene_metadata.json   (null data)
  ├─ capture_portfolio_renders
  │     ├─ render_exporter ─► Renders/Hero/*.png        ✅ hero
  │     └─ Monolith grid/overlay/trim ─► (skipped, Monolith off)
  ├─ compile_render_plates ─► Renders/renders_manifest.json     ✅
  └─ portfolio_aggregator ─► Saved/Portfolio/portfolio_package.json  ✅ valid, mostly null

   [ NOT WIRED ]  capture_material_previews ─► MaterialPreviews/previews_manifest.json
   [ MISSING   ]  stats exporter           ─► Stats/portfolio_stats_manifest.json
   [ NOT WIRED ]  portfolio_package.json   ─► melodia-figma-plugin (reads hardcoded tokens)
```

## 6. Relationship to existing project docs

This map does not replace the team's existing docs; it reconciles them against on-disk reality:

- `PORTFOLIO_PIPELINE.md` / `DATA_FLOW.md` describe the **aspirational** end state (Houdini→UE→Figma→ArtStation, full Monolith capture suite, stats manifest, ArtStation zip). Much of that is spec, not yet built.
- `UNREAL_CAPTURE_GAPS.md`, `FIGMA_LAYOUT_GAPS.md`, `UNMAPPED_DATA_POINTS.md` catalogue *future* capability gaps. They are downstream of the current blocker and should not be prioritized until the package carries real data.
- `SYSTEM_MAP.md` is a higher-level project map; this `CURRENT_SYSTEM_MAP.md` is scoped specifically to the portfolio-generation loop.
