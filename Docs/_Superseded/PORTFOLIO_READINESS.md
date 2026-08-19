# Portfolio Readiness - Platform Infrastructure

This checklist tracks reusable platform readiness. Sakura scene art readiness is intentionally excluded because final Sakura composition and hero art are human-owned.

## Platform Readiness Checklist

| Item | Status | Evidence / Next Action |
|---|---|---|
| Root project entry point | Done | `README.md` created for platform-level pitch. |
| Documentation index | Done | `DOC_INDEX.md` created. |
| Current state truth table | Done | `CURRENT_STATE.md` created. |
| Agent operating model | Done | `AGENT_OPERATING_MODEL.md` created. |
| Generic environment pipeline | Done | `UNIVERSAL_ENVIRONMENT_PIPELINE.md` created. |
| Material look-dev pipeline | Done | `MATERIAL_LOOKDEV_PIPELINE.md` created. |
| Material family manifest producer | Done | `Content/Python/material_family_manifest_full.py`. |
| Material metadata consumed by aggregator | Partial | Producer writes `MaterialPreviews/previews_manifest.json`, which the existing aggregator can consume. |
| Generic preview images | Partial | Metadata exists; actual captures depend on `L_Template` capture runs. |
| Website/Figma handoff map | Partial | Design system exists; package-to-website adapter still planned. |
| Recursive production loops | Partial | Existing loops documented; new producer role defined. |

## Readiness Definition

The generic platform is portfolio-ready when:

- Material family metadata is generated without opening Sakura.
- `portfolio_package.json.materials[]` is populated from generic material manifests.
- `L_Template` captures can prove universal, landscape, water, and trimsheet systems.
- Agents can run docs/audit/capture/report loops without modifying scene art.
- Website/Figma/ArtStation handoff has stable field mappings.

## Next Highest-Leverage Platform Actions

1. Run `python Content/Python/material_family_manifest_full.py`.
2. Run `python Content/Python/portfolio_aggregator.py`.
3. Verify `Saved/Portfolio/portfolio_package.json` contains `materials[]`.
4. Add package-to-website metadata adapter.
5. Add a generic `L_Template` capture report for material grids.
