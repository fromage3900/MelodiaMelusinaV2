# GOAL (bounded) — jcode fleet on verified lanes, same day (2026-09-26, owner: "execute that through a proper /goal")

**Bound:** repair + re-point the EXISTING jcode swarm (`Docs/PhoneOps/JCODE_SWARM_PIPELINE.md`, `.jcode/`)
and the Hermes orchestrator plan to today's verified model lanes. No new framework, no new router.
Ends when the owner can run one setup script, launch the swarm, and dispatch the first 4-worker fleet.

## Verified lanes (2026-09-26, live calls)
- Bedrock **Mantle** `https://bedrock-mantle.us-east-1.api.aws/v1` (OpenAI-compatible, Mantle API key):
  OK `qwen.qwen3-coder-next`, `qwen.qwen3-235b-a22b-2507`, `zai.glm-4.7-flash`, `openai.gpt-oss-120b` (<1 s).
  Claude on Mantle → `permission_error` (account not cleared) — **not a lane**.
- Ollama local: `muse-glimmer:30b`, `heretic-27b`, `qwen3-coder:30b`, `qwen3:8b`, `granite4.2`.
- Nous Portal = Hermes default. jcode v0.75.3: `jcode provider add <name> --base-url --model --api-key-env`.

## Steps
- **F1 Swarm policy repair** (`.jcode/swarm-prompt.md`, `coordinator-bootstrap.md`): retired PGA/MPA/PPA/WIA/SQA
  roles (Decision 002) → lanes (`code`, `fast`, `local`, `review`); each worker in its own git worktree,
  returns a patch/branch, **no `/commit`** (git law); swarm workers get **no editor MCP** (editor = one agent,
  Hermes-in-Claireon); done = an artifact the verifier opens.
- **F2 Lanes wired, no secrets in repo:** `deploy/setup_agent_lanes.ps1` (owner runs) adds jcode profiles
  `mantle-code` / `mantle-fast` / `ollama-local` reading `BEDROCK_MANTLE_API_KEY` from env; `.jcode/mcp.json`
  drops Monolith; `.jcode/config.example.toml` + `.opencode/opencode.jsonc` gain the same lanes.
- **F3 Docs converge:** orchestrator plan lane table → Mantle/Nous/Ollama; `JCODE_SWARM_PIPELINE.md` +
  `CURRENT_STATE.md` point here. One PR, CI green, merge; p4 mirror.
- **F4 First fleet (owner launches):** 4 file-disjoint workers — (a) regression harness
  `frames_captured 0`, (b) harness battle-trigger via tagged contract, (c) plan H1 router + editor lease
  scripts + offline tests, (d) Figma kit export script (W2, token from env). Hermes-in-Claireon alone runs
  ladder rung 4 (`issue51_ladder.ps1 launch` + log triage). Claude verifies artifacts.

**Done =** F1–F3 merged; setup script dry-runs clean; F4 packets written in the bootstrap file.
