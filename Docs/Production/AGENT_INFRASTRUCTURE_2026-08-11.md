# Agent Infrastructure — 2026-08-11

New tools in `Tools/` that extend the multi-agent ecosystem. All stdlib-only,
all write evidence (no prose claims), all safe to run with the editor open or
closed unless noted.

## Model Router — `Tools/model_router.py`

Policy-based model selection with cost ledger and fallback.

| Command | What it does |
|---|---|
| `python Tools/model_router.py pick <class> [--detail]` | Show the lane order for a task class |
| `python Tools/model_router.py chat <class> --prompt "..." [--json]` | Route + run the call, log usage |
| `python Tools/model_router.py test [--class <class>]` | Health-check each lane candidate |
| `python Tools/model_router.py cost` / `ledger` | Per-model spend, call ledger |

Task classes: `triage audit code author review orchestrator vision`.
Keys: env `OPENROUTER_API_KEY` / `TOKENROUTER_API_KEY`, else read from root
`.mcp.json` at runtime (no key duplication). Ledger: `Saved/router_ledger.jsonl`.

## Playtest Harness — `Tools/playtest_harness.py`

Real-input PIE verification for the `runtime` gate (evidence standard
2026-08-11: probe-only = HOLD; real keyboard input through
`BP_BattleUI::OnKeyDown` required).

| Command | What it does |
|---|---|
| `preflight` | Monolith reachable + exactly one editor process + no compile-error blueprints |
| `check-wiring` | Reflection check of BP_BattleUI for OnKeyDown→RegisterLaneHit / BindRhythmHUD; writes `Saved/Playtest/wiring_report.json`; picks input backend |
| `run --map L_KaleidoNave --backend slate-sendinput --vars EnemyHP:a.b.c` | Start PIE smoke, send real keys, snapshot damage vars, capture clip, write `Saved/Playtest/<marker>_report.json` |
| `ab --map L_KaleidoNave` | Rhythm on/off A/B, compares damage delta, writes `Saved/Playtest/ab_*.json` |
| `record pass|fail --note "..." --session s-xxxx` | Appends the `runtime` row to `Saved/gate_ledger.json` (replaces the deleted `record_gate.py`; same schema) |

Input backends: `slate-sendinput` (real OS keys via SendInput — strongest),
`pie-inject-input` (Monolith `pie_inject_input_action`, Enhanced Input),
`probe` (documented fallback). `--backend auto` picks from `check-wiring`.
Editor + Monolith must be running for `run`/`ab`.

## Video Review Lane — `Tools/video_review_lane.py`

Fresh-eyes regression review of PIE captures using a **free** vision model
(`nvidia/nemotron-nano-12b-v2-vl:free` — paid-model image input returns 402 on
the free-tier key). Accepts frames, video (ffmpeg), or a single image.
Verdict JSON includes per-frame observations + `flagged_frames`.
Example (verified 2026-08-11 against `.kiro_video_review/contact-sheet.jpg` —
flagged T-pose + debug text).

## Project Memory — `Tools/memory_index.py`

Keyword/structural index over `Docs/`, root docs, ledger, playtest reports.
`build` → `Saved/memory_index.json` (2197 files, 2026-08-11);
`search "query"` returns ranked hits with snippets. Rebuild after doc changes.

## Lane Dispatcher — `Tools/lane_dispatcher.py`

Reads the queue authority (`NEXT_ACTIONS.md`), classifies each item
(code/audit/author/orchestrator/vision/review), assigns the best model lane via
the router policy, writes `Saved/dispatch_report.md`. Read-only — never mutates
the queue.

## Notes

- `echo_run.py` / `record_gate.py` are gone from the tree (removed by the
  2026-08-11 reorg); `playtest_harness record` writes the same ledger schema so
  gate evidence stays verifiable. `Saved/Echo/state.txt` still exists.
- API keys remain inline in `.mcp.json`/`.opencode.json` (existing pattern);
  new tools read them at runtime instead of duplicating them.
