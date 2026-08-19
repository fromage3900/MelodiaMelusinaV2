# Nous Research — Application Draft

## Company profile

- **Name:** Nous Research
- **HQ:** Fully remote (US-based leadership)
- **Mission:** Advance open-source AI — train world-class open models, build
  infrastructure for distributed unbiased training.
- **Core products:**
  - **Hermes** model series (Hermes 4 latest) — open-weight, user-aligned,
    steerable fine-tunes. Trained with DataForge (graph-based synthetic data)
    and Atropos (open-source RL framework).
  - **Hermes Agent** — open-source self-improving AI agent with built-in
    learning loop, autonomous skill creation, cross-platform (Telegram,
    Discord, Slack, CLI). 140K GitHub stars. 224B tokens/day on OpenRouter.
  - **Forge Reasoning API** — inference-time reasoning (MoA, Chain of Code,
    MCTS). Augments open models to compete with GPT-4/Claude/Gemini.
  - **Psyche** — distributed training network based on DisTrO (training
    without gradient synchronization).
  - **Nous Portal** — hosted inference platform.
- **Funding:** Private, undisclosed. Scaling aggressively (hiring compute
  management, partnerships, engineering).
- **Culture:** Open-source maximalist. "Democratize access to world-class AI."
  Community-driven development (Hermes Agent built partly by itself via PRs).

## Open roles (Aug 2026)

| Role | Focus |
|------|-------|
| Forward Deployed Engineer | Deploy Hermes Agent Enterprise in customer envs |
| ML Engineer, Evals | Eval infrastructure, benchmarks, judge calibration |
| Product Analytics Engineer | Measurement systems for Hermes Agent usage |
| Security Engineer | End-to-end security across infra + products |
| Software Engineer, GUI/Product | Customer-facing surfaces (Portal, Hermes Agent) |
| Software Engineer, Hermes Cloud | Cloud platform powering Hermes Agent + Portal |
| UI/UX Designer | Agent workflow UX, AI-native product design |
| Research Scientist | Fundamental AI research (DisTrO, Hermes fine-tuning) |
| ML Engineer | Scale training/deployment, Psyche network, quantization |
| Compute Management | Internal compute portal operations |
| Partnership Development | Scaling Hermes Agent platform partnerships |

**Apply:** recruiting@nousresearch.com — Subject: role name, attach resume/CV,
cover letter, portfolio/GitHub.

## Fit assessment

### Strong angles
- **Agent tooling + MCP expertise.** This project runs three MCP surfaces
  (Monolith, VibeUE, UEBlueprintMCP) coordinated across parallel agent lanes.
  Hermes Agent uses MCP servers for tool integration. Direct experience.
- **Distributed agent orchestration.** jcode swarm, parallel coding lanes,
  Echo pipeline with evidence ledger — all agent coordination patterns that
  map to Hermes Agent's subagent delegation and skill-learning loop.
- **Production AI pipeline.** The T3D wiring pipeline (spec → inject → compile
  → fingerprint → regress → promote) is a concrete shipped example of
  AI-driven content authoring with quality gates.
- **Open-source alignment.** Portfolio is public, tools are committed, process
  is documented in the repo.

### Stretch areas
- Core ML research (DisTrO, model training) — not the portfolio's strength,
  but the Forward Deployed Engineer and Software Engineer roles don't require it.
- Python infrastructure at scale (vLLM, quantization, serving) — adjacent but
  not primary experience.

### Best-fit roles
1. **Forward Deployed Engineer** — deploy and adapt Hermes Agent in customer
   environments. Closest to current work (deploying AI agents in a complex
   UE5 production environment with MCP integration).
2. **Software Engineer, GUI/Product** — build Portal/Hermes Agent surfaces.
   Relevant if leaning into the wix portfolio + tool UI work.
3. **Software Engineer, Hermes Cloud** — cloud platform. Maps to the Echo
   pipeline and agent orchestration experience.

## Local work — NOW COMMITTED (feature/repo-lockin-20260813)

The following have landed in the repo and are pending merge to main:

### `Docs/Portfolio/PITCH_NOUS_RESEARCH.md` (2026-08-18)
Full research collaboration proposal: **"Melusina Agent Test Harness as a
Stateful RL Environment for Constrained Small-Model Research."**

This is NOT a job application — it's a proposal for a joint benchmark,
positioning the UE5.8 MCP pipeline as a formal RL environment for Hermes 3 /
LongCat. Key claims backed by benchmark numbers:

- Hermes 3 8B under MCP: **98.8% TCA, 100% PAR, 95.5% SCR, 91.0% RCF,
  85% token reduction (TER = 0.15)**
- LongCat 14B: **99.2% TCA, 97.5% SCR** on spatial/Blueprint tracks
- Formal RL environment definition: state space, action space, observation,
  reward signal, episode termination — all mapped to UE5.8 + MCP
- Five-metric reward function: TCA / PAR / SCR / RCF / TER
- Four-phase collaboration roadmap: benchmark integration → LoRA fine-tuning
  + RLVR → headless CI/CD swarms → open benchmark standard
- Proposed outcome: Nous Research × Melusina whitepaper, open leaderboard

### Other research tools committed
- `Tools/bedrock_research.py` + `Tools/bedrock_research_run.py` — AWS Bedrock
  research harness
- `Tools/rhythm_research_runner.py` — rhythm RL research runner
- `Docs/Research/INFINITY_NIKKI_PIPELINES_AND_PROJECT_UPDATES_2026-08-14.md`
- `Docs/Research/MELODIA_UE_JRPG_WORKFLOW_RESEARCH_2026-08-15.md`
- `Docs/Research/UE_RETARGET_PIPELINES_LONG_TERM_2026-08-15.md`

## Updated approach for Nous contact

The pitch is a **collaboration proposal**, not a job application. The email
should go to the research/eval team specifically, not just recruiting@.
Subject: "Research Collaboration Proposal: MATH — Stateful RL Environment for
Constrained Open-Weights Models"

Attach: `Docs/Portfolio/PITCH_NOUS_RESEARCH.md` + repo link.

If a job inquiry is also relevant, mention the Forward Deployed Engineer or
ML Engineer Evals role as a secondary ask — but the collaboration proposal
is the stronger opening.

---

*Researched 2026-08-19. Pitch committed 2026-08-18. Pending merge via PR #9.*
