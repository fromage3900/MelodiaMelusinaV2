# Scratchpad

Append-only research notes for phone + Grok + Cursor handoffs. Promote durable conclusions into `Docs/AgentMemory/Decisions.md` or `RejectedIdeas.md`. Do not treat this file as SSOT.

---

## 2026-08-11 — iOS Cursor + Grok experiment

- User testing Cursor from iOS; also experimenting with SuperGrok.
- Grok prepared five planning docs under `/artifacts` (setup, index, scratchpad, north star, backlog) but **did not push**.
- This Cursor cloud agent (`bc-019ff1ec-…`, source `mobile`, repo `MelodiaMelusina`) found `/opt/cursor/artifacts` empty of those files and recreated them under `Docs/PhoneOps/`.

### Repo dig (high-signal)

- **Identity**: Melodia — live collaborative environment art platform; `BS_GodFile.uproject` @ UE 5.8; Blender 5.1 surreal OS.
- **Remotes**: `origin` → `github.com/fromage3900/MelodiaMelusina`; branch `main` + many historical `cursor/surreal-architecture-slices-*` remotes.
- **Agent framework**: PGA / MPA / PPA / WIA / SQA in `AGENTS.md`; green/yellow/red lanes in `AGENT_OPERATING_MODEL.md`.
- **Python surface**: ~176 scripts under `Content/Python/`; heaviest: `setup_master_universal.py` (~2410 LOC), Sakura Niagara, texture catalog, substrate conversion.
- **EnvSandbox**: Environments, Materials, Meshes, PCG, VFX, `_Template` — preferred agent content root.
- **Deploy**: `surreal_os`, `surreal_arch`, `surreal_world`, verify loops (`run_verify.ps1`, `_mcp_verify_*.py`).
- **Plugins of note**: MelodiaCore (gameplay rules), Monolith (editor capture/index), MeshBlend, PCG ecosystem, Ultra Dynamic Sky content.
- **Portfolio site**: `wix/` + `melodia-design-system/` + `_github_deploy/`; `my-site-clean/` is alternate/unpromoted lane.
- **Recent product narrative on main**: navigation cleanup; dedicated environment pages (Space Cathedral, Cosmic Orrery, Baroque Grotto); recruiter one-sheet / sakura case study overhaul.

### Gotchas worth remembering (from CURRENT_STATE)

- In-place MI scalar/vector edits: `save_asset(path, only_if_is_dirty=False)` or disk may not update.
- PCG `Rotator` writes: no-arg `Rotator()` then set pitch/yaw/roll properties — positional ctor can silently no-op.
- Capture checkerboard was PSO precaching; Monolith Live Coding patch does not survive editor restart until full rebuild.
- Niagara preview scenes are unlit — lit petal materials look black in capture even when systems are correct.

### Open questions for next dig

- Which MelodiaCore GS items are already fixed on `main` vs still open?
- Is `package_to_website_handoff.py` still the preferred bridge after the July site overhaul?
- Any LOOP_STOP files or audit JSON currently blocking agent loops on a production machine? (not visible in this cloud VM)

---

## 2026-08-11 — Recent changes + skills deep dig

Full write-up: [RECENT_STUDY.md](RECENT_STUDY.md).

Highlights:

- Latest `main` product work is **website** (`wix/` env pages + nav cleanup); many older portfolio pages parked in `wix/_deprecated/`.
- July 15: Live Collab mega-commit landed then **reverted**; MelodiaCore C++ **re-added** via PR #54 — verify paths before assuming collab UI still exists.
- Dense July 4 Dream/Universal master history; water/landscape dream port reverted.
- Surreal loop at ~v2.131; open draft #80; many closed duplicate Art Deco slice PRs.
- **Cursor-style skills** = `Plugins/Monolith/Skills/*` (18 YAML-frontmatter skills). No root `.cursorrules` / `CLAUDE.md`.
- Also: `.junie/plans` (PCG), `.kiro/specs` (material library partial), `deploy/cursor_*_loop.ps1` wake ticks.
- Missing doc gap: `Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md` referenced but absent.

## 2026-08-11 — jcode swarm implemented in-repo

- Harness: `.jcode/*`, `deploy/start_jcode_swarm.ps1`, `deploy/install_jcode_melodia_skills.ps1`
- `AGENTS.md` §5 + deprecated `deploy/cursor_*` wake loops for parallel coding
- Acceptance checklist: `Docs/Reports/jcode_swarm_acceptance.md` (fill after Recipe A/B on Windows)

---

<!-- Append new dated sections below -->

## 2026-08-12 — Drive / Grok fold-in status (this cloud run)

- **Google Drive MCP:** still `needsAuth` in cloud agents (interactive auth only works in
  Cursor desktop). Cannot list Drive from this VM until owner connects Drive on desktop
  (or starts a new agent after authorizing).
- **Known Drive folder (from PROJECT_HANDOFF_2026-08-09):** `EnvironmentPortfolio-2026-08-09`
  id `14gTS8ohx-6rdsZXIzcFO5c8p40VXyKn-` — six handoff docs verified; **full archive never
  uploaded** (500 MiB connector timeout). Do not treat Drive as complete project backup.
- **SuperGrok PhoneOps:** already folded (`Docs/PhoneOps/*` + `CLOUD_RESEARCH_FOLD_IN_2026-08-11.md`).
  Original `/opt/cursor/artifacts` Grok dumps were empty at recreate time.
- **Folded now:** `PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md` (was only on PR #3).
- **Not folded (owner decide):** website-repo MelodiaMelusina PRs — #81 Nikki-scale intake
  (large; overlaps jcode already on V2), #82 portfolio cloud-env (website repo), #83
  MelodiaCore GS combat (conflicts with V2 ownership: MelodiaCore presentation-only).
- **V2 still open:** PR #4 git-health batches; PR #3 can close once bridge is on main.
