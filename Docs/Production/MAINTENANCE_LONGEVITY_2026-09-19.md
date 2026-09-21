# Maintenance & longevity changes — 2026-09-19

Follow-on to the 2026-09-18 deep review. Records what was implemented, what was
deliberately deferred (and why), and how to run the new tooling. Every change was
verified with a live run; the log path is cited.

## Implemented (all verified)

### P0.3 — sync data-safety (`deploy/_sync_addon_to_blender_5_2.py`)
The installer did one-way `rmtree`+`copytree` and `--check` compared
checkout→live only, so a **live-only file was silently deleted** (freeze doc §3.2).
Added:
- `live_only_files()` — files under the managed packages present live but absent
  from the checkout.
- `--check` now prints a `LIVE-ONLY files (N)` section.
- `sync()` **refuses by default** and lists the files; `--force` overrides.
- A best-effort warning when `blender.exe` is running (freeze ritual: sync with
  Blender closed).
*Verified:* `--check` reported a live-only file; `sync` refused (exit non-zero);
after cleanup, `284/284 match / OK`.

### P0.4 — one-writer enforcement (`deploy/_melodia_preflight.py`, new)
Three concurrent Blender processes crashed gate D on 2026-09-18; it passed with
fewer. The preflight answers "is it safe to start a gate?" and refuses otherwise.
*Verified:* default → BLOCKED (exit 3) with 1 interactive session live;
`--allow-interactive` / `--allow-any` → OK; `--json` emits the process list.

### P0.5 — line-ending governance (`deploy/_melodia_eol.py`, new)
`.gitattributes` mandates `*.py/*.json/*.md = eol=lf`, but CRLF files caused a
~5000-line churn on `Tools/registry_baseline.json` and made `git status` show
EOL-only "modified" files. The tool parses the policy and rewrites only
violations.
*Verified:* found 13 violations; `--fix` normalized 10 (deploy/Docs/baseline);
`deploy` and `Docs` now report **EOL CLEAN**. The 3 remaining are another lane's.

### P0.2 — C1 check-flow bug (`deploy/_melodia_health_c1_monolith_ui.py`)
The C1 health script called `register_overhaul()` without `monolith.register()`,
so the monolith's own panels were never registered and the escape-hatch drawer
assertion could only fail for the wrong reason. Fixed to mirror Blender's real
enable order.
*Verified:* C1 retired **33** monolith panels (was 1); the legacy-drawer checks
now PASS; failures dropped **2 → 1**, and the single remaining failure is the
genuine owner decision (`SURREAL_ARCH_PT_plan_edit_floating`). Log:
`Saved/Audit/health_c1_monolith_ui_2026-09-19.log`.

### P0.1 (visibility half) — dropped-link recorder
`core.link_sockets` / `link_float_to_vector` swallowed every failure as a WARN,
so 19 trees miswire silently while the gate stays green. Added a recorder
(`_LINK_FAILURES`, `link_failures()`, `reset_link_failures()`, `LINK_STRICT`) and
a dedicated audit `deploy/_melodia_health_gn_links.py` that prefers the checkout.
*Verified:* `builders=593 built=593 build_errors=0`, `trees_with_dropped_links=19`
(10 None-socket, 7 End-Location, 7 type-mismatch). Log:
`Saved/Audit/health_gn_links_2026-09-19.log`.

### P1.9 — stale-lock sweep (`deploy/_melodia_lock_sweep.py`, new)
A stale `.git/index.lock` blocked staging on 2026-09-18; the repo also carries 14
orphan `index.stash.*.lock` files. The tool reports/removes only provably-stale
locks and **never** while a `git.exe` is live; `--force-remove` is the explicit
override.
*Verified:* reported 14 stale locks; correctly refused to delete while a git
process appeared present.

## Deferred (evidence-based, not skipped)

These touch files an **active concurrent lane** is editing right now, so acting
would collide or capture half-finished work:

| Item | File(s) | Why deferred |
|---|---|---|
| P0.1 tree fixes (19 pairs) | `melodia_gn/*` builders | `__init__/note_school/paris_wall_detail/time` are being edited by the PARIS/GN lane |
| P1.7 gate `--quick` | `Tools/verify_addon.py` | contested — the PARIS lane bumped `RECORDED_EMPTIES 137→138` there |
| P2.10 gate progress logging | `Tools/verify_addon.py` | same file |
| P2.14 `__init__.py` count comment | `melodia_gn/__init__.py` | contested |
| P2.13 `Tools/*` ignore policy | `.gitignore` | protected file (pre-commit hook rule 6) |
| C1 `plan_edit_floating` | `integration.py` / `branding.py` | **owner design decision** (retire vs keep) |

The recorder from P0.1 is the prerequisite for those tree fixes: once the PARIS
lane lands, run `_melodia_health_gn_links.py`, fix the 19 trees, then flip
`core.LINK_STRICT` and wire `link_failures()` into `verify_addon.py` as a gate.

## Not needed

- **P1.8 (.gitattributes)**: the policy is already explicit (`*.py/*.json/*.md
  text eol=lf`, `*.ps1/*.ini text eol=crlf`). The gap was enforcement, now
  covered by `_melodia_eol.py`.

## How to run

```
python deploy/_melodia_preflight.py --allow-interactive     # one-writer check
python deploy/_melodia_eol.py [--fix] [--path deploy]       # EOL governance
python deploy/_melodia_lock_sweep.py [--fix]                # stale git locks
python deploy/_sync_addon_to_blender_5_2.py [--check|--force]
# inside Blender 5.2:
#   --background --factory-startup --python deploy/_melodia_health_gn_links.py
#   --background --factory-startup --python deploy/_melodia_health_c1_monolith_ui.py
```

## Environment note (concurrency is real)

This session saw a second lane commit (`d637bad4`, `f26b0e82`) and edit
`Tools/verify_addon.py` + `Tools/registry_baseline.json` + several `melodia_gn`
files **while work was in progress**. Any further change in those paths should
re-run `git status` immediately before staging and stage named files only.
