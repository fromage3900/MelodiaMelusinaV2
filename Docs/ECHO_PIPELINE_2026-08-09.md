# Melodia Echo — One Pipeline, One Truth, Gated Agents

**Written:** 2026-08-09
**Status:** live — manifest `specs/echo_pipeline.json`, runner `Tools/echo_run.py`
**Model:** HoYoverse's in-house "Echo" AI platform — AI agents generate game
content inside the production pipeline, and nothing they produce is believed
until a quality gate scores it. This project already had the gates; Echo is the
orchestration that ties them into one runnable chain with one evidence ledger.

---

## 1. The problem this closes

The integration layer was not "not working" for lack of tooling. The wiring
contract, fingerprints, reachability lint, UI lint, PIE smoke, regression suite,
and gate ledger all exist. What was missing:

1. **No single runnable workflow.** Tools live in `Tools/` and `Docs/`; which one
   to run, in what order, with what expectation, was prose. Prose drifts — the
   staleness radar currently flags 4/4 tracked docs behind their subject.
2. **No single truth.** State was distributed across `CURRENT_STATE.md`,
   `_SESSION_HANDOFF.md`, `_TASK_QUEUE.md`, `_ROADBLOCKS`, and 14 documented
   contradictions. Every agent session re-derived state from prose that lagged
   the game.
3. **No ledger discipline.** `Saved/gate_ledger.json` exists, but nothing
   enforced "no claim without a row". The 2026-08-06 lesson — owner PIE-tests
   continuously, observations never become recorded gate results — is exactly
   the Echo-shaped hole.

## 2. What Echo (HoYoverse) is, and what we take

Echo is HoYoverse's proprietary in-house AI platform: AI agents author content
(dialogue, levels, scenes, props) inside the game's production pipeline, and the
pipeline gates that output before it ships — dramatically cutting production
hours while keeping a human review loop. Three transferable properties, none of
which need a big platform:

| Echo property | Melodia equivalent |
|---|---|
| Agents are content producers, not authorities | Agents author specs (`.qsc`, T3D, JSON); the game's existing authorities (stock JRPG, Quill, allowlist) decide validity |
| Generated content is gated before it ships | The `author → spec_validate → inject → compile → static → runtime → record → promote` chain |
| One evidence record per claim | `Saved/gate_ledger.json` — a claim without a ledger row is not a claim |

Deliberately NOT taken: a new platform, a new agent framework, or more MCP
servers. This project's own 2026-08-06 plan said it and it is still true: more
tooling is not the lever.

## 3. The pipeline

Declared in `specs/echo_pipeline.json` (the manifest is the authority — this doc
explains it, never overrides it):

```
author  →  spec_validate  →  inject  →  compile  →  static_gates  →  runtime_gates  →  record  →  promote
(agent)    (echo_run)       (T3D)      (0 err)     (reachability,   (PIE smoke,      (ledger  (commit +
                       one asset/txn            live-path, ui_lint,  regression,      row)    baseline)
                                                 sweep, baseline)    wiring suite)
```

- **author** — an agent or the owner produces a spec (`.qsc`, T3D pattern,
  JSON data) plus the one gate it claims. Nothing else about the beat is assumed.
- **spec_validate** — `echo_run.py validate-spec <file>` checks JSON, QSC, or T3D
  proposals against the 7-verb contract, integer arity, duplicate consume-once
  identities, and the allowlist authority (`DA_MelodiaIntegrationConfig`).
  Supply `--live-allowlist` with a live editor or `--allowlist-file` with an
  exported JSON snapshot; a proposal containing intents cannot pass without one.
- **inject / compile** — one asset per transaction, pre-flight passes, compile
  must read 0 errors from the nested result (the old `ok:true-with-errors`
  false positive is fixed and must stay fixed).
- **static_gates** — graph reachability, live-path (LIVE not ORPHAN), UI lint,
  project sweep, T3D baseline. All are editor-gated; a non-answering editor
  yields HOLD, never a pass. `bp_live_path` checks the assets listed in
  `MELODIA_ECHO_LIVE_PATH_ASSETS` or its safe defaults.
- **runtime_gates** — PIE smoke, regression suite, the `Melodia.Wiring` suite
  (`Automation RunTests Melodia`), and the campaign scripts
  (`Docs/ECHO/` campaigns, §6).
- **record** — `echo_run.py record <gate-id> pass|fail --note "..."` appends a
  dated ledger row. This is the tail of every stage.
- **promote** — fingerprints/baselines updated if they moved, plain
  `git add`/`commit`. The promotion rule from the wiring contract holds: a
  committed export is an output, never an input.

### Running it

```text
python Tools/echo_run.py list              # stages + tools
python Tools/echo_run.py status            # ledger-backed completion gates
python Tools/echo_run.py run static_gates  # editor must answer 9316
python Tools/echo_run.py run runtime_gates # pie/regression/fingerprint tools
python Tools/echo_run.py run --all         # static chain; runtime is separate
python Tools/echo_run.py run pie_smoke     # one editor gate on KaleidoNave
python Tools/echo_run.py validate-spec specs/toon_profiles/tp_melusina.json
python Tools/echo_run.py validate-spec Content/MelodiaIntegration/Narrative/MelodiaQuillSmoke.qsc --live-allowlist
python Tools/echo_run.py record package_launch pass --note "..."
```

`run` commands never write a ledger row automatically. Review the output and
campaign artifacts first, then use `record` for the exact gate observed. A
missing editor returns `HOLD` with a non-zero exit code; it is not a pass.

## 4. One truth: the control panel

`Tools/project_state.py` is now the derived-state authority:

- `--view integration` — the four completion gates (runtime, save/load,
  repeat-consume, package launch) backed by the ledger, plus scope-checkbox
  progress. Output also lands at `Saved/Echo/state.txt`.
- `--view staleness` — docs that are older than the code they describe are
  UNVERIFIED, not wrong. Currently 4/4 tracked docs are behind their subject.
- Windows-safe: stdout reconfigured to UTF-8 (previously crashed on `→` under
  the cp1252 console).

**Consequence:** no prose doc is believed over this panel. `DOC_INDEX.md`,
`_SESSION_HANDOFF.md` and `CURRENT_STATE.md` remain as history and context; the
ledger and the panel are the truth.

**Latest-row-wins:** `Saved/gate_ledger.json` is append-only. A gate's standing is
always its **last** row chronologically — older rows are history, including older
FAILs superseded by a pass and older passes bounded to a stale baseline. Citing a
non-last row as current standing is a stale-info defect. Read standing via
`python Tools/echo_run.py status` or `python Tools/project_state.py --view
session_start`, never by sampling mid-file.

## 5. Agent contract (how lanes fold in)

The multi-agent lane system (`_TASK_QUEUE.md`, `PARALLEL_LANES_2026-08-08.md`)
stays as the *work allocation*; it stops being the *authority*. Every lane's
deliverable is now:

1. A spec (or a change) —
2. validated by `validate-spec` —
3. gated by the chain —
4. recorded in the ledger —
5. then, and only then, claimable as done.

An agent that reports "done" without a ledger row has reported prose. Lane
handoffs may name the gate id they expect to record — that is the new handoff
shape.

## 6. Campaigns (the runtime proof work, §spine)

Completion = the four gates recorded pass in the ledger:

| Campaign | Gate id | Evidence |
|---|---|---|
| Rhythm→damage delta in PIE | `runtime` | Perfect vs Miss produce different damage numbers; `MELODIA_RHYTHM session=` line present |
| Save round trip + repeat consume | `save_load`, `repeat_consume` | canonical slot across full process restart; stat idempotent per IntentId; no duplicate reward |
| Development package launch | `package_launch` | `BS_GodFile.exe` walks Morning → Dreamstate → KaleidoNave outside the editor |
| Result matrix | `runtime` | Victory/Defeat/Fled/unavailable each resumes/aborts Quill exactly once |

Each campaign owns a short runbook under `Docs/ECHO/campaign_*.md` and records
its own ledger row. Static graph presence is never a runtime claim.

## 7. What this doc is not

Not a framework, not a new platform, not a replacement for
`_AGENT_WORKING_AGREEMENT.md` (which still outranks everything here). It is the
unification of tooling that already exists around one manifest, one runner, one
ledger. If a stage here ever needs a compensating mechanism to pass, the stage
is wrong — delete the cause, not the gate.
