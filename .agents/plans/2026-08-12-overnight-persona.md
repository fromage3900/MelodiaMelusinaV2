# Overnight Plan — Core Persona Gameplay Loop + Architecture Sweep (2026-08-12)

## Goal
Run an unattended overnight loop that proves the core persona gameplay loop on C: `C:\EnvironmentPortfolio\BS_GodFile` with Melusina visible and HUD readable, and deliver a grounded architecture + deep-research package by morning — all without touching `G:` DDC or pushing to `origin`.

*User asked for: every item listed (persona design, architecture sweep, loop tuning) + specifically `PAUSE → Save → Quit → Reload` with HUD screenshots of Melusina working.*

## Success Criteria
* **Loop is running detached at bedtime:** `Tools/overnight_persona_pie_loop.py --loop --interval 600` capturing to `Saved/PersonaLoop_Tonight/` and `/tmp/persona_loop.log` — survives UE restart, auto-skips when `9316 False`, captures when `True`.
* **Screenshots by morning:** at least 3 iterations × 5 tasks = 15 capture dirs, each with `*.png` (Melusina mesh + `WBP_MainMenu`/`BP_BattleUI` HUD at 100% alpha) and `_SUMMARY.json` with `frames>0, elapsed>0`.
* **Pause→Save→Quit→Reload proven:** one full `Automation RunTests Melodia` or PIE sequence: `MelodiaIntegrationMap` → `Pause` → `Save` → `Quit` → `Reload` → HUD still readable, `melodiaNarrativeRecord` intact, no duplicate `ConsumedIntentIds`.
* **Static gates stay green:** `f1948852` on `C:` (already committed), `v2` push pending on network, no `Content/` push to `origin`.
* **Architecture package:** `Docs/Reports/jcode_swarm_recipe_a.md`, `..._b_mpa.md`, `..._b_ppa.md` + `bp_sweep`/`graph_reachability`/`ui_style_audit` reports exist and are `PASS`.

## Context And Current Facts
* **C: checkout:** `C:\EnvironmentPortfolio\BS_GodFile` (`/mnt/c/...`), `HEAD f1948852` `[ahead 3]` of `origin/v2` — commit on `C:` is `MUSE lane Done` + P0 claim, `git push v2` fails `Failed to connect to github.com:443` (PowerShell `Test-Connection` blank, browser works — `gh` credential path blocked, not auth).
* **UE:** was stuck `35%` on `G:\UE_DDC` (warnings `very slow 0.00 MiB/s`), fixed by `User env UE-LocalDataCachePath=C:\UE_DDC` + `C:\UE_DDC` created + killed stale `96228`/`59492` + `40188/48572` proxies → now single `UnrealEditor 53144 Unreal Editor - BS_GodFile`, `zenserver 95804`, **shaders compiling → working** per user, but `127.0.0.1:9316` still `False` (`curl Connection refused`) as of 00:41 poll — Zen/Shaders still initializing.
* **Monolith:** `Plugins/Monolith/Binaries/monolith_proxy.exe` exists `True`, `.mcp.json` has `monolith` → `http://localhost:9316/mcp` ✓, `oe` `blender`/`envoy`/`cascadeur` etc. — will bind after shaders finish.
* **Foundation Gate P0:** `Identify instantiated stock battle widget package at runtime` claimed `In Progress | Muse` — static evidence: `BP_BattleUI.uasset` `652K 2026-08-08` vs `_ThirdParty 472K 2026-07-15` + 10+ C++ refs to `/Game/TurnBasedJRPGTemplate/...`, but per `Docs/2026-07-29_PROJECT_HANDOFF.md:22` not runtime proof — needs one PIE capture. Other `P0`s `Available`: save/load canonical, flag/reward restore, travel, etc.
* **Loop already built:** `Tools/overnight_persona_pie_loop.py` `4.9K` `compile:0`, `wait_for_monolith` 30s, 4 tasks (widget, persona exploration, battle parity, save/load), `--once` dry-run → `Monolith not ready — skipping` (correct), detached `--loop --interval 600` running as `froma 8` in sandbox (`bwrap --die-with-parent` — ends when this chat ends). Needs `setsid -f` outside sandbox or `muse cron` for true overnight.
* **Previous swarm:** `jcode v0.75.3` installed at `C:\Users\froma\AppData\Local\jcode\bin`, persistent User PATH already set but fresh PowerShell needed `$env:PATH` prepend; `openai` OAuth hit `usage_limit_reached`, `gemini` → `This client is no longer supported... migrate to Antigravity`, user chose bypass swarm for now.

## Constraints And Non-goals
* **One editor only** (`AGENTS.md:7`) — already enforced after killing `59492/57464` orphans; do not launch second UE.
* **No `G:` DDC, no `Content/_PROJECT/` edits, no bulk `.uasset` churn, no `origin` push** — `v2` only when network returns.
* **Quantum only as async ranking** (`AGENTS.md: Quantum usage`) — not for hit detection.
* **Non-goals tonight:** no `wix/` redesign, no `MaterialMaster` regenerate, no phone gateway `v2`, no publishing to Gumroad.

## Key Decisions
* **Loop stays on `C:\UE_DDC` (Decision: C over G)** — 13s `G:` DDC speed test + `0.07 MB/s` write caused 35% stall; `C:` is NVMe `1866 MB/s` read.
* **Extend loop to 6 tasks (Decision: add Quill + PauseSaveQuitReload)** — current 4 → add `QuillSmoke` (`MelodiaQuillSmoke.qsc` 42 statements) + `PauseSaveQuitReload` (HUD + Melusina). Rejected: keep 4 only — user explicitly asked `every single thing` + that sequence.
* **Validation is PIE + PNG + _SUMMARY.json (Decision: runtime over static)** — `bp_regression_checker` fingerprint is `exact_match` but the 2026-08-06 defect class `shadowed events` proved fingerprint can pass while runtime fails; need `poll_pie_smoke` + frame counts.
* **Overnight persistence via `muse cron` + detached `setsid -f` outside sandbox (Decision: cron over sandbox `setsid`)** — sandbox `setsid` dies with session (`bwrap --die-with-parent`); `muse cron "*/10 * * * *"` survives 7 days.

## Recommended Approach
1. **Finish tonight's loop enhancement** — expand `overnight_persona_pie_loop.py` `PIE_TASKS` to 6-7 entries: (a) `widget_runtime P0` (`BP_BattleUI` active vs `_ThirdParty`), (b) `persona_exploration` (social stats), (c) `battle_parity` (`BattleTestMap`), (d) `save_load` canonical, **(e) `QuillSmoke` (`MelodiaQuillSmoke.qsc` 42 statements) via `HandleQuillNotification` allowlist ves + `melodia:flag/reward/stat`**, **(f) `PauseSaveQuitReload` (Pause → Save `melodiaNarrativeRecord` → Quit → Reload → HUD `WBP_BattleUI`/`WBP_MainMenu` at 100% alpha)** with `sample_vars` for `Melusina` visibility, and **(g) `QuillResume` (typed battle result → Quill resumes once)**. All via `PieSmokeRunner` `capture_pie_movement_clip` + `poll_pie_smoke` → `*.png` + `_SUMMARY.json`.

2. **Text Injection Pipeline (T3D Wiring) deep research** — `AGENTS.md: T3D Wiring Pipeline` `Spec → Inject → Compile → Fingerprint → Regression → Promote` + Echo orchestration `specs/echo_pipeline.json` (`author → spec_validate → inject → compile → static_gates → runtime_gates → record → promote`) via `Tools/echo_run.py` (`list`, `status`, `validate-spec`, `record`). Inventory `t3d_blueprint_injector.py` (`inject_into`), `bp_regression_checker.py` (`fetch_fingerprint`, `compare_fingerprints`, baseline `Docs/T3D_Baseline/bp_fingerprints.json`), `t3d_material_curve_injector.py`, `nl_to_blueprint.py`, `continuous_loop.py` (auto-detect → T3D fix → verify). Check `specs/toon_profiles/tp_melusina.json` + `specs/niagara_mpc_bindings.json` as declarative spec examples. Write `Docs/Reports/arch_sweep_2026-08-12.md` § T3D.

3. **Echo Testing Pipeline deep research** — `Tools/echo_run.py` `static_gates` / `runtime_gates`, `Tools/project_state.py --view integration/staleness` → `Saved/Echo/state.txt`, ledger `Saved/gate_ledger.json` + `Saved/Echo/state.txt` (gate `runtime` OPEN until `record_gate.py <id> pass`). Verify `Docs/ECHO_PIPELINE_2026-08-09.md`, `Docs/ECHO/campaign_01_rhythm_damage_delta.md` (5 evidence standards: ledger row, real `OnKeyDown` input not probe `register_lane_hit`, frames + JSON report, committed harness, `bExecutionDrivingHighway` ownership). Map `Tools/bp_live_path.py` (`LIVE/ORPHAN`), `bp_sweep.py` (5 defect classes: shadowed events / empty-bodied / dead islands / unreachable / duplicate short names), `ui_style_audit.py`, `t3d_dashboard.py`, `graph_reachability.py` vs `bp_live_path`. Write `Docs/Reports/echo_pipeline_2026-08-12.md`.

4. **Subagents + Local Models — full lane inventory for tonight's parallel work** — **jcode swarm (light-swarm ≤6):** coordinator → `PGA`/`MPA`/`PPA`/`WIA`/`SQA`/`WEB`/`MUSE` per `.jcode/swarm-prompt.md` + `config.example.toml` (`swarm=true`, `concurrency_cap=6`), coordinator bootstrap `coordinator-bootstrap.md` Recipe A (WEB+SQA) / B (MPA+PPA). **Muse Code:** `Meta Muse Spark` via `muse` (WSL `muse-bin-0.1.0-R708.1`, auth `~/.config/muse/auth.json`), skills `plan`/`grill`/`git`/`import`, `muse exec --trust-workspace` + `muse cron`. **OpenCode in Rider:** `Ctrl+\` OpenCode terminal, `opencode.jsonc` (Monolith/Blender MCP). **Local models:** `ollama` `qwen3:8b` + `deepseek-r1` + `ollama-mcp` (`_ollama_experiments/scripts/qwen_daemon.py` 4 tasks), `deepseek-v4` + `kimi-k3` via `openrouter/tokenrouter` (keys in `.mcp.json`). **Music/UE:** `ollama` quorum for quantum pattern ranking (approved `AGENTS.md: Quantum usage` — ranking room seeds / rhythm density, not hit detection). Plan tonight's parallel: Muse Code → P0 PIE loop + `MelodiaIntegration` bridge, Ollama Qwen → orphan script audits, DeepSeek → travel/pacing, all via `Monolith` `blueprint_query` (never Python glue on `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` per fatal `D_DamageType` bug).

5. **Architecture sweep before sleep (read-only, parallel)** — run `bp_sweep.py`, `graph_reachability.py` (on `BP_BattleController`, `BP_BattleUI`), `ui_style_audit.py` (+ `test_ui_style_audit.py`), `t3d_dashboard.py --live` (if `9316 True`), `project_state.py --view staleness/integration`, `bp_live_path.py` on `BP_BattleUI` + `BP_MelodiaBattleUI`. All write to `Docs/Reports/` without touching `Content/`.

6. **Launch persistent overnight** — `muse cron_create "*/10 * * * *"` → `python Tools/overnight_persona_pie_loop.py --once` + keep current `setsid -f --loop --interval 600` as fallback; logs to `Saved/PersonaLoop_Tonight/` and `/tmp/persona_loop.log`.

7. **Morning triage** — read `_SUMMARY.json` + PNG via image tool, check `Saved/Logs/BS_GodFile.log` for `MELUSINA_*` + `MelodiaNarrativeRecord`, `Tools/echo_run.py status` + `Saved/Echo/state.txt` ledger rows, `git push v2` when `:443` reachable.

## Work Plan
* **Unit 1 — Loop enhancement (30 min, tonight, on C:):** edit `Tools/overnight_persona_pie_loop.py` `PIE_TASKS` → 6 entries, add `QuillSmoke` and `PauseSaveQuitReload` with `console_script` and HUD sample vars; `py_compile` check; `--once` dry-run (expect `Monolith not ready` until `9316 True`, then one full pass). Owner: Muse. Depends on: `9316 True`.
* **Unit 2 — Architecture deep research (45 min, read-only):** run `bp_sweep.py`, `graph_reachability.py`, `ui_style_audit.py`, `t3d_dashboard.py --live` (if UE up), `project_state.py --view staleness/integration`; write `Docs/Reports/jcode_swarm_recipe_a.md`, `_b_mpa.md`, `_b_ppa.md` + `Docs/Reports/arch_sweep_2026-08-12.md`; no `Content/` writes. Owner: Muse. Depends on: none (can run while shaders compile).
* **Unit 3 — Persistent overnight (10 min):** `muse cron_create` `*/10 * * * *` + verify `muse cron_list`; keep `setsid -f` loop as described; verify `ps aux | grep persona` + `ls Saved/PersonaLoop_Tonight`. Owner: Muse. Depends on: Unit 1.
* **Unit 4 — Morning validation (15 min, after 06:00):** `cat /tmp/persona_loop.log | tail`, `ls -R Saved/PersonaLoop_Tonight`, `muse cron_list`, `git log --oneline -3`, `git push v2 main` retry; screenshot image-read of at least one `*.png` per task. Owner: Muse + user eyeball. Depends on: Unit 3 overnight.

## Validation Plan
* **Unit 1:** `python -m py_compile Tools/overnight_persona_pie_loop.py` → `0`; `timeout 35 python Tools/overnight_persona_pie_loop.py --once` → `Monolith not ready — skipping` (when `9316 False`) then after `9316 True` → `PASS — frames:>0` per task + `_SUMMARY.json` with `frames>0`; `ls Saved/PersonaLoop_Tonight/*.png` → `>0`.
* **Unit 2:** `python Tools/bp_sweep.py` → `0 shadowed/orphan` (or list), `python Tools/graph_reachability.py` → no dead islands in `BP_BattleController`, `python Tools/ui_style_audit.py` → token set, all write to `Docs/Reports/*.md` and compile `py_compile` green.
* **Unit 3:** `muse cron_list` shows `*/10` job, `ps aux | grep persona` shows loop, `curl http://127.0.0.1:9316/mcp` → `200` when UE up.
* **Unit 4:** `cat Saved/PersonaLoop_Tonight/*_SUMMARY.json | grep -c PASS` → `≥15`, image tool read of `*.png` shows Melusina mesh + HUD text `A>0` (not invisible `0` from `2770c0e9` fix), `Automation RunTests Melodia` → `46/3` baseline (known 3 fails).

## Risks / Rollback
* **Risk:** `G:` DDC re-enabled on reboot — rollback: `User env UE-LocalDataCachePath=C:\UE_DDC` is persistent, but `G:\UE_DDC` can be re-disabled via `$env:UE-LocalDataCachePath=''`; `DerivedDataCache` will recreate `C:\UE_DDC` if deleted.
* **Risk:** `9316` never comes up due to Monolith plugin disabled — rollback: `Edit → Plugins → Monolith` → enable → restart; proxy `C:\...\monolith_proxy.exe` is on disk.
* **Risk:** Two editors reappear → `AGENTS.md:7` violation → rollback: `Stop-Process -Id <stale>` as done for `59492/57464`.
* **Risk:** `git push v2` still `Failed to connect :443` — not a code risk, commit `f1948852` stays on `C:` `[ahead 3]`, push retries in morning.

## Open Questions
* Should `PauseSaveQuitReload` use `BP_JRPGSaveGame` `melodiaNarrativeRecord` slot `0` or a dedicated `PersonaLoop` slot? (Default: slot `0` per `BP_JRPGSaveGame` docs, but can parameterize.)
* Is `BattleTestMap` or `MelodiaIntegrationMap` preferred for `battle_parity` tonight? (Default: `BattleTestMap` for isolated parity, `MelodiaIntegrationMap` for integrated loop — plan uses both.)
* Keep `capture_interval` at `0.25-0.5s` or bump to `1.0s` to save disk overnight? (Default `0.5s` ≈ 20 frames per 10s PIE, ~200 PNG/hour.)
