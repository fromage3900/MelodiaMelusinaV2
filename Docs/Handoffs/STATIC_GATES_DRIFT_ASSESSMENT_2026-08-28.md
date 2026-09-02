# Static Gates Baseline Drift Assessment — 2026-08-28

## Summary

The `static_gates` gate has been FAIL since 2026-08-14 (last recorded: `static_gates: fail (2026-08-14)`).
The Blueprint fingerprint baseline (`bp_fingerprints.json`) was captured on 2026-08-11 — 17 days and
227 commits ago, 77 of which touch `Content/` or `Source/`. The baseline covers 279 Blueprint assets
across `/Game/TurnBasedJRPGTemplate`, `/Game/MelodiaIntegration`, and `/Game/Melodia`.

**Drift risk: HIGH.** At least 10 commits since Aug 11 directly modified Blueprint graphs, UI widget
blueprints, or integration-config assets that are in the 279-entry baseline scan scope. The
`verify_baseline` gate (material sha256) and `bp_regression_checker` (topology fingerprints) will
almost certainly report mismatches. The `bp_sweep` and `bp_live_path` gates are more likely to pass
clean — they check shipped-defect classes and reachability, not byte-exact fingerprints — but the
quarantine relocation (`eb6ff433`) and HUD centralization (`e1b62b28`) could surface new findings.

**Recommendation: re-baseline after verifying no real defects, static gates before PIE gates.**

---

## 1. Baseline Structure

### bp_fingerprints.json (156 KB, 279 entries)

Each entry records a topology-mode fingerprint for one Blueprint graph:

| Field | Description |
|---|---|
| `asset_path` | `/Game/...` package path |
| `graph_name` | EventGraph or named graph |
| `mode` | `topology` (node/connection/histogram shape) |
| `node_count` | Total nodes in the graph |
| `connection_count` | Total pin-to-pin connections |
| `fingerprint` | SHA-1-style hash of the graph topology |
| `node_class_histogram` | Per-K2Node-class counts (e.g. `K2Node_CallFunction: 16`) |

Scan scope: `/Game/TurnBasedJRPGTemplate`, `/Game/MelodiaIntegration`, `/Game/Melodia` (Blueprint,
WidgetBlueprint, and AnimBlueprint classes).

### verify_baseline.py

Despite the name, `verify_baseline.py` checks the **material catalog** (`material_catalog.json`
sha256 hashes), not `bp_fingerprints.json`. It re-exports material T3D text from the live editor
and compares sha256 against committed baselines, with a canonicalization step that sorts sibling
objects to suppress false drift from exporter reordering.

### bp_regression_checker.py — the actual fingerprint gate

`bp_regression_checker.py` is the tool that fingerprints Blueprint graphs against
`bp_fingerprints.json`. It scans the three content roots via `project_query:find_by_type`, fetches
each graph fingerprint via `blueprint_query:get_graph_fingerprint`, and calls
`compare_fingerprints()` which reports `[NEW]`, `[CHANGED]`, and `[MISSING]` entries.

**The static gate chain's `verify_baseline` step runs `verify_baseline.py` (material catalog),
not `bp_regression_checker.py` (Blueprint fingerprints).** Blueprint fingerprint drift is checked by
the `fingerprint` stage under `runtime_gates` (`EDITOR_ONLY["fingerprint"]`), not the static chain.

This is an important distinction: the static chain's failure modes are material drift and UI lint,
not Blueprint topology drift.

---

## 2. Static Gate Chain (5 tools)

From `echo_run.py` STATIC dict, in execution order:

| # | Gate | Tool | What it checks | Fail mode |
|---|---|---|---|---|
| 1 | `graph_reachability` | `Tools/graph_reachability.py --all-melodia --ci` | Dead exec islands inside graphs | Exit code ≠ 0 |
| 2 | `bp_live_path` | `Tools/bp_live_path.py <asset> --json` for each configured target | Assets reachable from entry points | Exit code ≠ 0 |
| 3 | `bp_sweep` | `Tools/bp_sweep.py --limit 200` | 5 defect classes: SHADOWED, EMPTY, DEAD, DUPES, unreadable | SHADOWED/DUPES/unreadable > 0 |
| 4 | `ui_lint` | `Tools/ui_lint.py --all-melodia` | Font/colour/padding consistency | Exit code ≠ 0 |
| 5 | `verify_baseline` | `Docs/T3D_Baseline/verify_baseline.py` | Material catalog sha256 match | Any DRIFT or FAIL |

**Note:** `bp_sweep` only fails on SHADOWED, DUPES, or unreadable > 0. EMPTY and DEAD are reported
but do not fail the gate (stock template has ~167 empty stubs and ~54 dead PEN nodes — these are
noise, not shipped defects).

**`bp_live_path` targets** (from echo_run.py env `MELODIA_ECHO_LIVE_PATH_ASSETS`):
- `BP_BattleUI`
- `BP_MelodiaJRPGGameMode`

---

## 3. Git Activity Since Aug 11 (Drift Risk Analysis)

### Aggregate counts
- **227 total commits** since 2026-08-11
- **77 commits** touching `Content/` or `Source/`
- **27 commits** touching `.uasset` files under `Content/`
- **19 commits** touching `Source/` (C++ — affects CDO properties, not graph topology directly)
- **64 commits** touching `Tools/` (no fingerprint baseline impact)

### High-risk commits (likely to cause fingerprint mismatches or sweep findings)

| Commit | Description | Risk |
|---|---|---|
| `e1b62b28` | `feat(hud): centralize battle rhythm widget ownership` | **HIGH** — changes BP_BattleUI graph; may affect live_path and sweep |
| `538b3358` | `ui_wbp_finalization_20260828` | **HIGH** — UI WBP changes in baseline scan scope |
| `d242f74d` | `feat(quill): track dialogue WBPs, fix selection/background viewport guard` | **HIGH** — new WBPs added to scan scope; will appear as [NEW] |
| `e1d1b4cd` | `fix(ui): restore Quill dialogue visibility via parent Play call` | **MEDIUM** — modifies existing WBP graphs |
| `bc880736` | `feat(p0): extend narrative allowlist and repair the Quill trigger` | **MEDIUM** — modifies integration config / Quill BP |
| `694b7250` | `feat(integration): FGameplayTag migration, P0 content, CPU traces` | **HIGH** — FGameplayTag migration touches many BP graphs |
| `bea0133c` | `fix(melodia): reparent player controller onto stock JRPG base` | **HIGH** — changes player controller BP graph hierarchy |
| `f78f00f8` | `feat(p0): integrate P0 playthrough, wardrobe equip, choral sheep` | **MEDIUM** — new gameplay BPs added |
| `1a28a4ac` | `feat(p0): close battle_integration_map + hud_single_writer` | **MEDIUM** — HUD widget consolidation |
| `eb6ff433` | `quarantine: relocate 33-asset Content_MelodiaIntegration mirror` | **HIGH** — removes 33 assets from scan scope; will appear as [MISSING] |

### Medium-risk commits
- `4b6c990c` — QSC authoring defect corrections (may touch .qsc-compiled .uasset)
- `3912f570` — P0-NARR-01 quest completion notification (narrative BP changes)
- `1fad1269` — ChoralSheep 12 pitch-class coat pipeline (new BPs)
- `78b912a8` — Melusina idle canonical v22 ARP, pawn SoT BP_MelusinaJRPGCharacter

### Low-risk commits (docs, tools, worldgen, specs)
- ~150 commits touching only `Docs/`, `Tools/`, `specs/`, `deploy/`, `.jcode/`, `.claude/`

---

## 4. Drift Risk Assessment

### Will the static gates pass after the rebuild?

**Likely NO for verify_baseline; PROBABLY YES for bp_sweep/bp_live_path/graph_reachability/ui_lint.**

#### verify_baseline (material catalog) — HIGH RISK FAIL
The material catalog was last baselined alongside the BP fingerprints on Aug 11. Multiple commits
since then touched materials:
- `3c30ff5c` — finalize universal landscape master (triproplanar + PBR defaults)
- `94c253b3` — MF_NikkiDream pin fallbacks + MF pin inspector
- `7d0d8133` — sync subagent material edits (landscape SakuraGarden, Toon Landscape HeightBlend)
- `54c4064d` — enable triplanar blend on M_Master_Toon_Landscape_HeightBlend

These material edits will cause sha256 mismatches in `verify_baseline.py`. The tool has a
reorder-only canonicalization check that suppresses false drift from exporter sibling ordering,
but genuine material edits will report as DRIFT.

#### bp_sweep (defect classes) — MODERATE RISK
The quarantine of 33 duplicate assets (`eb6ff433`) was specifically done to clear 16 duplicate short
names and 10 shadowed events. After the rebuild, the quarantine assets should no longer be in the
scan scope, so DUPES and SHADOWED counts should be clean. However, the HUD centralization
(`e1b62b28`) and new WBPs (`d242f74d`, `538b3358`) could introduce new duplicate short names or
shadowed events if not carefully authored.

#### bp_live_path — LOW RISK
The configured targets (`BP_BattleUI`, `BP_MelodiaJRPGGameMode`) are core integration assets that
have been actively maintained. The reparenting of the player controller (`bea0133c`) could affect
reachability, but the targets are explicitly wired and should remain LIVE.

#### graph_reachability — LOW-MODERATE RISK
New BPs from the FGameplayTag migration and P0 content integration could have dead exec islands if
not fully wired. This is the kind of defect graph_reachability catches. However, scoped runs of
bp_sweep have been clean since the three-editor incident.

#### ui_lint — MODERATE RISK
UI WBPs were actively changed (`d242f74d`, `538b3358`, `e1d1b4cd`). If the UI style audit catches
font/colour/padding inconsistencies introduced by these changes, it will fail.

### Blueprint fingerprint drift (runtime_gates, not static_gates)
`bp_regression_checker.py` is run under `runtime_gates` as the `fingerprint` stage, not under
`static_gates`. It will almost certainly report [NEW] entries (new WBPs), [CHANGED] entries (HUD
centralization, FGameplayTag migration, reparenting), and [MISSING] entries (quarantined assets).
This is expected and is the primary driver for re-baselining.

---

## 5. What to Do If the Static Gates Fail

### Decision tree

```
static_gates FAIL
  ├─ verify_baseline (material drift)?
  │    ├─ Count drifted materials
  │    ├─ For each drifted material:
  │    │    ├─ Is it reorder-only? → false positive, ignore
  │    │    ├─ Is it an intentional material edit since Aug 11?
  3    │    │    ├─ YES → accept drift, re-baseline with --update
  │    │    └─ NO → investigate; could be an unintended material change
  │    └─ Run: python Docs/T3D_Baseline/verify_baseline.py --diff
  │    └─ Re-baseline: python Docs/T3D_Baseline/verify_baseline.py --update
  │
  ├─ bp_sweep (SHADOWED/DUPES/unreadable > 0)?
  │    ├─ SHADOWED > 0 → a parent event is being overridden; fix the BP or quarantine the duplicate
  │    ├─ DUPES > 0 → duplicate short names; rename or quarantine
  │    ├─ unreadable > 0 → corrupt/unloadable asset; fix or remove
  │    └─ EMPTY/DEAD > 0 → reported but does NOT fail the gate; informational only
  │
  ├─ bp_live_path (ORPHAN/AMBIGUOUS)?
  │    ├─ ORPHAN → asset not reachable from entry points; wire it or remove it
  │    └─ AMBIGUOUS(n) → multiple construction paths; disambiguate or document
  │
  ├─ graph_reachability (dead exec islands)?
  │    └─ Dead islands inside a graph → prune dead nodes or wire them
  │
  └─ ui_lint (font/colour/padding mismatch)?
       └─ Identify the offending widget(s); align to the token set
```

### Re-baseline procedure

1. **Verify the editor is up and Monolith answers on 9316:**
   ```bash
   python Tools/echo_run.py status
   ```

2. **Run the static gate chain and capture the output:**
   ```bash
   python Tools/echo_run.py run static_gates 2>&1 | tee Saved/Logs/static_gates_2026-08-28.log
   ```

3. **For each failure, triage using the decision tree above.**

4. **If the failures are all expected drift (intentional content changes), re-baseline:**
   ```bash
   # Material catalog
   python Docs/T3D_Baseline/verify_baseline.py --update

   # Blueprint fingerprints
   python Tools/bp_regression_checker.py --update
   ```

5. **Re-run the static gate chain to confirm PASS:**
   ```bash
   python Tools/echo_run.py run static_gates
   ```

6. **Record the gate result in the ledger:**
   ```bash
   python Tools/echo_run.py record static_gates pass --note "re-baselined 2026-08-28 after 17 days of P0 content changes"
   ```

7. **Commit the updated baselines:**
   ```bash
   git add Docs/T3D_Baseline/bp_fingerprints.json Docs/T3D_Baseline/material_catalog.json
   git commit -m "fix(baseline): re-baseline fingerprints + materials after P0 content integration"
   ```

### If real defects are found (not just drift)

If `bp_sweep` reports SHADOWED or DUPES that are not explained by the quarantine or known changes:
1. Do NOT re-baseline — that would bake the defect into the baseline.
2. Fix the defect (rename, reparent, or quarantine the offending asset).
3. Re-run the gate to confirm the fix.
4. Then re-baseline the fingerprints.

---

## 6. Recommended Gate Execution Sequence

### Static gates FIRST, then PIE gates

**Rationale:** The static gate chain is fast, non-destructive, and catches structural defects
before investing in a PIE run. PIE gates require the editor to load the full map, which takes
significantly longer and can hang if there are broken assets. Running static gates first ensures:

1. No dead exec islands or unreachable assets waste a PIE session
2. Material drift is documented before runtime evidence is collected
3. Defect classes (SHADOWED/DUPES) are caught and fixed before they cause runtime crashes

### Recommended order

```
1. python Tools/echo_run.py status
   → Confirm editor is reachable on 9316

2. python Tools/echo_run.py run static_gates
   → graph_reachability → bp_live_path → bp_sweep → ui_lint → verify_baseline
   → If FAIL: triage per §5, re-baseline or fix, re-run

3. python Tools/echo_run.py run runtime_gates
   → pie_smoke → regression → fingerprint (bp_regression_checker)
   → The fingerprint stage is where Blueprint topology drift is reported
   → If [NEW]/[CHANGED]/[MISSING]: re-baseline bp_fingerprints.json

4. python Tools/echo_run.py record static_gates pass --note "..."
5. python Tools/echo_run.py record runtime_gates pass --note "..."
```

### Why not PIE first?

- PIE loads the full map and can crash on broken assets — static gates catch those first
- The editor is currently building; static gates can run as soon as Monolith answers, while PIE
  needs the full map loaded
- Re-baselining fingerprints is cheaper than re-running PIE
- The Echo pipeline manifest specifies `static_gates` before `runtime_gates` in the stage ordering

---

## 7. Key Findings

1. **The static_gates gate has been FAIL for 14 days** (last recorded 2026-08-14). No PASS exists
   in the ledger for this gate since the Aug 11 baseline was captured.

2. **77 of 227 commits since Aug 11 touch Content/ or Source/.** The P0 content integration
   (FGameplayTag migration, Quill dialogue WBPs, HUD centralization, wardrobe equip, choral sheep,
   narrative allowlist) represents significant structural change to the Blueprint graph topology.

3. **The `verify_baseline` gate checks material catalog sha256, not Blueprint fingerprints.**
   Blueprint topology drift is checked by `bp_regression_checker.py` under `runtime_gates`, not
   under `static_gates`. The static chain's failure modes are material drift, UI lint, sweep
   defects, and reachability — not topology fingerprint mismatch.

4. **The quarantine (`eb6ff433`) removed 33 assets from the scan scope.** These will appear as
   [MISSING] in `bp_regression_checker` but should NOT cause `bp_sweep` failures (the quarantine
   was specifically to clear 16 duplicate short names + 10 shadowed events).

5. **`bp_sweep` only fails on SHADOWED/DUPES/unreadable.** EMPTY and DEAD counts are informational
   and do not fail the gate (stock template noise: ~167 empty stubs, ~54 dead PEN nodes).

6. **The editor is currently building.** All five static gates require Monolith on port 9316.
   No gate can run until the build completes and Monolith answers.

---

## 8. Action Items

| Priority | Action | Owner | Blocked by |
|---|---|---|---|
| P0 | Wait for editor build to complete, confirm Monolith on 9316 | editor session | Build finishes |
| P0 | Run `echo_run.py run static_gates` and capture output | audit lane | Editor up |
| P0 | Triage any FAIL per the decision tree in §5 | audit lane | Gate output |
| P1 | Re-baseline `bp_fingerprints.json` and `material_catalog.json` if drift is expected | audit lane | Clean gate run (or explained failures) |
| P1 | Re-run static gates to confirm PASS after re-baseline | audit lane | Re-baseline complete |
| P1 | Record `static_gates pass` in the ledger | audit lane | Confirmed PASS |
| P2 | Run `runtime_gates` (pie_smoke, regression, fingerprint) after static gates pass | playtest lane | Static gates PASS |
| P2 | Record `runtime_gates` result in the ledger | playtest lane | Runtime gates complete |

---

## Appendix: Gate Ledger History (static_gates)

| Date | Status | Notes |
|---|---|---|
| 2026-08-07 | pass | (implied — graph_reachability pass recorded) |
| 2026-08-11 | fail | First recorded static_gates fail |
| 2026-08-14 | fail | Last recorded static_gates fail (current state) |
| 2026-08-28 | — | Not yet run (editor building) |

---

*Authored: 2026-08-28 (audit lane). Editor build in progress; assessment based on baseline file
structure, tool source, echo pipeline manifest, and git log analysis.*
