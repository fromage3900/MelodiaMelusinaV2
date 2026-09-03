# Environment Build Validation — 2026-08-11

This handoff records the result of implementing the full-workspace environment
plan. It is evidence of setup/tool behavior, not a claim that the gameplay
vertical slice is complete.

## Implemented

- Added the active workspace source-of-truth and drift map:
  `Docs/ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md`.
- Added the Windows runbook:
  `Docs/ENVIRONMENT_RUNBOOK_2026-08-11.md`.
- Added non-destructive setup validation and opt-in bootstrap:
  `deploy/validate_setup.ps1` and `deploy/bootstrap_environment.ps1`.
- Replaced fixed mirror paths in the active environment/portfolio helpers with
  `Config/paths.json`, environment variables, or checkout-relative resolution.
- Repaired collaborator onboarding defaults and validation.
- Aligned ECHO validation, editor HOLD behavior, live-path/static stages, runtime
  tool commands, atomic ledger writes, optional session ids, and playtest ledger
  recording.
- Added ECHO contract tests and included them in the Python test configuration.
- Made world-manifest import canonical-schema aware and opt-in for actor spawning:
  validation is default; `--apply` requires explicit `static_mesh_path` values.
- Made portfolio export return failure when any recorded pipeline step fails,
  even if an old package file exists.
- Made website validation/deployment paths portable, generated the website
  lockfile, fixed the broken deprecated-page links, and removed the fixed
  `G:\EnvironmentPortfolio` site-facts dependency.

## Successful checks

| Check | Result |
|---|---|
| `validate_setup.ps1 -SkipServices -CheckWebsite` | 0 hard issues; 2 warnings for local Python 3.14 vs documented 3.11 and Node 24 vs CI Node 20 |
| Project/engine/plugin discovery | Unreal 5.8, Blender 5.2 path, Git LFS, project plugins found |
| Python suite | 294 passed, including ECHO contract tests |
| Updated Python syntax compilation | Passed |
| ECHO manifest listing/status | Passed; ledger truth remains visible |
| ECHO Quill proposal with `--live-allowlist` | Passed against `DA_MelodiaIntegrationConfig` |
| Website JavaScript lint | Passed in root and `my-site-clean` after local plugin resolution was made explicit |
| Website asset validation | Passed: 0 hard and 0 soft missing assets |
| Website facts validation | Passed with no issues |
| Website JSON/link validation | Passed: 41 pages in `my-site-clean`, 44 pages in the root copy |
| Deployment manifest checker | Ran successfully; current manifest contains no absolute URLs to probe |

## Deliberate blockers still visible

### ECHO/editor gates

The one-editor static chain was run on 2026-08-11 and recorded as
`static_gates=fail`. The failure is not hidden:

- T3D baseline verification reported 12 drifted assets.
- Blueprint sweep reported 10 shadowed events, 304 empty events, 239 dead
  exec findings, and 16 duplicate short names.
- `bp_live_path BP_BattleUI --json` returned both the live canonical asset and
  the `_ThirdParty` copy, so the result is correctly `AMBIGUOUS(2)`.
- The editor-dependent graph/UI gates did not produce a clean chain.

The current runtime row remains `fail`; `save_load`, `repeat_consume`, and
`package_launch` remain open. No runtime campaign was promoted from this setup
work. Real keyboard rhythm input, full-process save/load, repeat-consume, and
packaged launch still require the campaign runbooks and their evidence artifacts.

### Website style gates

- `npm run lint` passes.
- `npm run lint:css` still reports 24 existing duplicate-selector/property
  findings across the layered presentation stylesheets. They were not
  auto-rewritten because merging them could change the visual cascade.
- `npm run lint:tokens` now resolves the token source portably but still reports
  232 existing raw-color findings. The missing external
  `melodia-design-system/tokens.json` is no longer treated as a path failure;
  the tracked `wix/melodia-tokens.css` remains the local fallback.
- Therefore `npm run verify:all` remains blocked by the existing token debt,
  which is intentionally recorded instead of being bypassed.

### Toolchain versions

The machine currently exposes Python 3.14 and Node 24. The runbook and CI
baseline remain Python 3.11 and Node 20. The validator warns rather than
silently treating those versions as equivalent; install the documented
versions before relying on exact CI parity. Ruff is not currently on PATH.

## Next evidence-bearing actions

1. Resolve or quarantine the duplicate Blueprint mirror after owner review;
   never delete it from a sweep verdict alone.
2. Decide which baseline drift is intentional, then update the T3D baseline
   only with a reviewed asset change.
3. Run `Melodia.Wiring` and the four ECHO campaigns in order.
4. Migrate or explicitly approve the layered CSS raw colors and duplicate
   selectors.
5. Install Python 3.11/Node 20/Ruff for CI-parity verification.
