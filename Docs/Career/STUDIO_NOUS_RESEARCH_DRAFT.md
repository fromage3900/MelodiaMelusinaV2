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

## Local drafts (not yet committed)

> **TODO:** Owner has local Hermes test results, work proposals, and drafts on
> the Windows workstation. Commit and merge those here when synced. Expected
> content:
> - Hermes model test results / benchmarks
> - Work proposal drafts for Nous
> - Application materials

---

*Profile researched 2026-08-19. Sync local drafts to complete.*
