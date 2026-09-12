# Decisions

## 2026-06-30

- The actual Sakura level art pass is human-owned. Agents may support it with generic tools, captures, manifests, and audits, but must not edit scene composition or hero asset placement.
- The universal material/look-dev platform is the primary automation focus.
- `M_Master_Toon_Universal`, `M_Master_Toon_Landscape_HeightBlend`, and `M_Water_Master_Grand_v6` are the current reusable environment pillars.
- Material metadata should be generated as a thin manifest rather than inferred repeatedly by every downstream system.
## 2026-07-02

- Website handoff is a generated contract: run `python Content/Python/package_to_website_handoff.py` after `portfolio_aggregator.py` to update `_github_deploy/generated/*_config.json` from `Saved/Portfolio/portfolio_package.json`.
- `_github_deploy/` remains the active deploy lane for Unreal package configs until `my-site-clean/` is explicitly promoted.
