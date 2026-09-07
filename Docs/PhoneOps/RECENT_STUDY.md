# Recent Changes + Agent/Skills Study

Study date: 2026-08-11 (iOS Cursor cloud agent).  
Scope: `main` history since ~2026-07-01, open PRs, Monolith Skills, Cursor/Junie/Kiro agent tooling.

## 1. Timeline of recent `main` (compressed)

### Website / portfolio surface (latest on main)

| When | Commit | What |
|---|---|---|
| 2026-07-24 | `950d268` | Nav cleanup; footer deep-dives; moved many pages to `wix/_deprecated/` |
| 2026-07-21 | `9440213` | Dedicated env pages: Space Cathedral, Cosmic Orrery, Baroque Grotto |
| 2026-07-21 | `6e555c4` | Recruiter one-sheet, index, sakura case study, shader breakdowns overhaul |
| 2026-07-20 | `65f3743` | Auto-deploy from Unreal Pipeline |
| 2026-07-15 | `68db0ee` | Gilded ivory + Figma lookbook foundations sync |

Live site lane is **`wix/`**. Deprecated dashboard/hero/systems pages still exist under `wix/_deprecated/` for archaeology.

### Melodia Live Collab + MelodiaCore (July 15 drama)

Important sequence:

1. PR #50 `d903cbd` — large Live Collab push (bridge, material crosswalk, GN, portrait, NPC, C++ P0, voice lines).
2. Follow-up PRs #51–#53 restored missing docs/tools (bridges, VOICEVOX, Zundamon specs, onboarding).
3. `ceb9d6a` — **Revert** of the Live Collab mega-commit (huge churn; restored earlier AGENTS/state/config patterns in places).
4. PR #54 `fe7b1da` / `991d5be` — **re-added complete MelodiaCore C++ source** (87 files: 43 `.cpp`, 42 `.h`, plugin + Build.cs).
5. `ab33b23` — enable `ProceduralDungeon` plugin (MelodiaCore dependency).

Implication for agents: MelodiaCore source is present on `main`, but do not assume every Live Collab UI/doc path from `d903cbd` survived the revert intact — verify before editing.

### Universal master / Dream stack (2026-07-04 burst)

Dense material work on `M_Master_Toon_Universal`:

- Dream features (rim, bloom, flow, pulse, mist, dawn wash, twinkle, sigil, halo) mostly **gated default OFF**
- Substrate Toon max-capability (`TP_NikkiDream`), anisotropic spec, inline triplanar (with break/fix/bypass history)
- Instance clamp passes (garbage overrides)
- Water/landscape dream port **reverted** after rendering break (`d6985d8`)
- Docs: `Docs/Production/DREAM_SYSTEM.md`, HLSL snippets, RVT terrain-blend scope

Earlier July also saw master restore/rebuild cycles (`949e22f`, `df7858d`, `40d4fba`, `0725e6a`) — treat master mutation as high-risk Yellow/Red.

### Surreal architecture agent loops

- Loop state doc claims **v2.131.0**, endless Tier-B genome expansion armed.
- Open draft PR **#80** (`cursor/surreal-architecture-slices-b618`) — Art Deco lobby tower-ban rematerialize v2.132.0.
- Many closed duplicate surreal-slice PRs (#67–#79) with the same title — loop spam / rematerialize retries. Prefer #80 if reviewing surreal work; ignore closed twins unless bisecting.

### Still open besides PhoneOps

| PR | Branch | Notes |
|---|---|---|
| #81 | `cursor/phone-ops-docs-0e29` | This mobile ops doc set |
| #80 | `cursor/surreal-architecture-slices-b618` | Surreal Art Deco slice |
| #55 | `fix-final-gaps` | Material Maker subgraphs / surreal_arch gaps (older) |

## 2. Cursor / agent tooling in this repo

### Project-level agent constitution (root)

| File | Role |
|---|---|
| `AGENTS.md` | PGA/MPA/PPA/WIA/SQA ownership |
| `AGENT_OPERATING_MODEL.md` | Green/Yellow/Red lanes; human-owned Sakura |
| `AGENT_BOUNDARIES.md` / `AGENT_OWNERSHIP.md` | Write boundaries |
| `Docs/PhoneOps/*` | Mobile control plane (new) |

**No** root `.cursorrules` or `CLAUDE.md` in this checkout. Monolith deliberately stopped shipping `CLAUDE.md.example` (conventions drift).

### Cursor wake loops (`deploy/`)

| Script | Purpose |
|---|---|
| `start_cursor_agent_loop.ps1` / `cursor_surreal_agent_loop.ps1` | **ARCHIVED** — Emitted `AGENT_LOOP_TICK_surreal_micro2` every N seconds |
| `start_surreal_tierb_loop.ps1` / `cursor_surreal_tierb_loop.ps1` | **ARCHIVED** — AAA genome expansion micro-cycle |
| `stop_*_loop.ps1` + `*_STOP` / `*_LOOP_STOP` | Safety interlocks |

Tick prompts explicitly say: implement one slice, sync+verify, update LOOP_STATE, **do not edit plan files**.

### Other assistant scaffolds

| Path | Origin | Status signal |
|---|---|---|
| `.junie/plans/pcg-universal-expansion.md` | Junie | Universal PCG biome expansion plan |
| `.junie/plans/pcg-biome-expansion.md` | Junie | Related PCG plan |
| `.kiro/specs/material-library-improvements/` | Kiro | Spec + partial impl (layering done; Nikki landscape / water groups / cleanup queued) |
| `.kiro/hooks/audit-material-library.kiro.hook` | Kiro | Hook for material audits |

### Referenced but missing

`NEXT_HIGHEST_LEVERAGE_TASK.md` points at `Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md` — **not present** in this tree (gap / lost in revert or never landed). Treat MelodiaCore GS list in `NEXT_HIGHEST_LEVERAGE_TASK.md` as the surviving handoff.

## 3. Former / current Cursor-style Skills (Monolith)

Canonical skill pack lives under **`Plugins/Monolith/Skills/`** — YAML frontmatter skills for MCP agents (Cursor/Claude/Cline). These are the project’s real “Cursor skills” inventory.

Naming note: Monolith docs sometimes say `Skills/<topic>/SKILL.md`, but **on disk** files are `Skills/<topic>/<topic>.md` (e.g. `unreal-materials/unreal-materials.md`).

### Inventory (18 skills)

| Skill | Lines (approx) | Use when |
|---|---|---|
| `unreal-niagara` | 478 | Niagara systems/modules/HLSL |
| `unreal-mesh` | 392 | Mesh ops |
| `unreal-audio` | 271 | Sound cues / MetaSounds |
| `unreal-gas` | 259 | GAS abilities/effects |
| `unreal-blueprints` | 225 | BP graph/CDO |
| `unreal-ui` | 218 | UMG / CommonUI |
| `unreal-materials` | 184 | Material graph/instances via `material_query` |
| `unreal-logicdriver` | 180 | Logic Driver state machines |
| `unreal-project-search` | 119 | Project FTS search |
| `unreal-animation` | 119 | Anim assets / ABP / Control Rig |
| `unreal-performance` | 104 | Perf / profiling |
| `unreal-cpp` | 99 | Engine API / includes / UHT |
| `unreal-level-sequences` | 88 | Sequencer bindings |
| `unreal-combograph` | 77 | ComboGraph |
| `unreal-build` | 73 | Live Coding vs UBT |
| `unreal-debugging` | 70 | Logs / crashes / build errors |
| `niagara-reference` | 36 | Niagara budgets/gotchas index |
| `material-reference` | 35 | PBR/HLSL/perf quick ref + deep docs |

### How agents should use them

1. Prefer `monolith_discover` / `monolith_guide(section="skills_map")` when MCP is live.
2. For materials work offline: read `unreal-materials` + `material-reference` before editing masters.
3. Lint helper: `Plugins/Monolith/Scripts/lint_agent_tools.py` (agent tool frontmatter discipline from Monolith’s own agent pack).

### Not Cursor skills (name collision)

- `Content/TurnBasedJRPGTemplate/Blueprints/Skills/*` — **gameplay** skill BPs (FireBall, etc.), not AI skills.
- `MelodiaSongSkillLibrary.*` — Melodia combat/song skill C++ library.

## 4. Producer priority still true after study

Aligned with PhoneOps BACKLOG / NORTH_STAR:

1. Don’t touch Sakura composition / `_PROJECT/`.
2. Website truth is `wix/` (+ `_github_deploy` for package configs until promotion).
3. Material master is powerful but fragile (Dream gates, restore history) — prefer instances/audits.
4. Surreal loop is active but PR hygiene is noisy — review #80 carefully; don’t spawn more duplicate slice PRs from phone without reading LOOP_STATE.
5. MelodiaCore C++ is on main; GS-001+ from `NEXT_HIGHEST_LEVERAGE_TASK.md` remain the gameplay leverage path.
6. Kiro material-library remaining tasks (Nikki landscape UV, water groups) still open in `.kiro/specs/…`.

## 5. Suggested phone prompts after this study

```text
Read Docs/PhoneOps/RECENT_STUDY.md. Summarize open PR #80 vs closed surreal duplicates; recommend merge or close.
```

```text
Using Plugins/Monolith/Skills/unreal-materials/unreal-materials.md as the skill,
propose a Yellow-lane L_Template material capture checklist only — no master edits.
```

```text
Locate whether Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md exists on any branch; if missing, draft a stub under Docs/ from NEXT_HIGHEST_LEVERAGE_TASK.md GS list.
```