# Phone + Multi-Agent Setup

How this MelodiaMelusinaV2 workspace is driven from phone, GitHub cloud agents, and parallel research (SuperGrok / Cursor Pro).

## Stack

| Layer | Tool | Role |
|---|---|---|
| Phone UI | Cursor iOS / mobile agents | Kick off cloud runs, review diffs, steer priorities |
| Cloud code | Cursor Cloud Agents (`MelodiaMelusinaV2`) | Read/write repo, PRs, docs, audits |
| Deep research | SuperGrok (or similar) | Scratchpads, strategy, cross-tool synthesis — often no git push |
| Local production | UE 5.8 + Blender 5.2 + MCP | Materials, PCG, Live Link, capture (desktop) |
| Planned private SSH | Blink → Tailscale (or overlay) → Windows → WSL2 → tmux | Local agent CLIs; **not** public SSH — [REMOTE_WSL_AGENT_STACK_2026-08-25.md](REMOTE_WSL_AGENT_STACK_2026-08-25.md) |
| Source of truth | This GitHub repo | `main` + `cursor/*` agent branches |

Repo: `github.com/fromage3900/MelodiaMelusinaV2`  
UProject: `BS_GodFile.uproject` (UE 5.8)  
Foundation plan: `Docs/GAME_FOUNDATION_PLAN_2026-08-11.md`  
Lane handoff: [AGENT_LANE_HANDOFF.md](AGENT_LANE_HANDOFF.md)

## Cursor Pro (phone / cloud)

1. Open Cursor Agents on phone → target **MelodiaMelusinaV2**.
2. Prefer short, one-lane prompts (docs, audit, one script family). Follow the parallel lanes in the foundation plan — do not contend the live editor.
3. Cloud agents create branches like `cursor/<name>-098b`, commit, push, open draft PRs.
4. You approve merge / art direction / external publish — agents do not.

Useful first prompts from phone:

- `Read Docs/GAME_FOUNDATION_PLAN_2026-08-11.md and execute the next cloud-safe lane item`
- `Read Docs/PhoneOps/INDEX.md and Docs/PhoneOps/NORTH_STAR.md, then do the top Now item in BACKLOG.md`
- `Study CURRENT_STATE.md + NEXT_ACTIONS.md; summarize blockers only`
- `Do not edit L_SakuraPath or Content/_PROJECT/; stay in EnvSandbox / deploy / Docs`

## SuperGrok (parallel research)

Typical Grok outputs (setup notes, index, scratchpad, north star, backlog) land in a local `/artifacts` folder and are **not** auto-pushed.

Handoff pattern:

1. Grok writes planning docs → you paste paths or text into a Cursor phone agent.
2. Cursor agent recreates/updates `Docs/PhoneOps/*` in-repo and opens a PR.
3. Treat Grok as research; treat this repo as canonical.

## GitHub / cloud agent guardrails

From `AGENT_OPERATING_MODEL.md` and `AGENTS.md`:

- **Green**: read, report, index, non-destructive docs.
- **Yellow**: run existing look-dev/manifest loops; `L_Template` only for captures.
- **Red (need you)**: delete assets, rewrite masters, edit Sakura composition, publish externally.

Ownership reminders:

- Materials Python → MPA
- PCG Python → PPA
- `deploy/surreal_os/` → PGA
- `deploy/surreal_world/` → WIA
- Audits / verify → SQA

## Desktop companions (when you are at a machine)

```text
UE MCP        :55557 / :9316
Blender Live  :9876
VOICEVOX      :50021
```

Sparse Blender-only clone: see `Docs/SETUP_COLLAB.md` (~50 MB, not full Content).

Preflight (Windows production box): `.\deploy\validate_setup.ps1`

## Monolith Skills (Cursor-compatible)

When MCP/Monolith is available, load domain skills from:

`Plugins/Monolith/Skills/<name>/<name>.md`

Highest-value for this project: `unreal-materials`, `material-reference`, `unreal-niagara`, `unreal-cpp`, `unreal-debugging`, `unreal-build`.

On the Windows box, install the same set into jcode via `.\deploy\install_jcode_melodia_skills.ps1`.

Full inventory + history context: [RECENT_STUDY.md](RECENT_STUDY.md).

There is **no** root `.cursorrules` / `CLAUDE.md` in MelodiaMelusina; use `AGENTS.md` + PhoneOps + Monolith/jcode skills instead.

## jcode swarm (desktop parallel coding)

Primary parallel coding lane on the UE workstation:

```powershell
.\deploy\start_jcode_swarm.ps1
```

See [JCODE_SWARM_PIPELINE.md](JCODE_SWARM_PIPELINE.md) and [`.jcode/README.md`](../../.jcode/README.md). Cursor iOS cloud agents remain the phone/PR lane.

## Capture / mocap (phone + desktop)

Scan on phone (**Polycam** primary, **Kiri** secondary) → always **ZBrush** on desktop → `Imports/Sculpt/Inbox`.  
Rokoko: Live Link rehearses on `SK_MocapSource`; game clips are FBX → `Imports/Mocap/Rokoko/Inbox` → retarget.  
Do not push LFS meshes from iOS — sync FBX to the Windows tree, then intake/import there.

Full SOP: [`Docs/MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md`](../MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md).

## What phone agents cannot do well

- Live Unreal editor / Blender viewport taste checks
- Live Coding rebuild of Monolith capture fixes
- Gumroad / external publish
- Final Sakura art direction
- Running the local jcode TUI (needs the Windows box)
- LFS mesh / mocap pushes from iOS

Use phone agents for docs, queues, audits, PR hygiene, and bounded Python/doc fixes; park visual look-dev and jcode swarm for desktop.
