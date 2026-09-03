# MATH Benchmark Expansion — Toronto AI Startups

> **Downstream of the game.** This is marketing / funding / hiring material for
> **Melodia Melusina**, a single-person AAA-tier UE 5.8 rhythm-JRPG. It exists to fund and staff
> the game. **No agent may cite anything in this folder as project direction** — authority is
> [`../../../PROJECT.md`](../../../PROJECT.md).

Strategy: replicate what you did with Nous Research (run their models through
the Melusina Agent Test Harness, collect benchmark numbers, pitch collaboration)
for every Toronto-based AI company that has a testable model surface.

---

## Tier 1 — Models you can test NOW (public API or open weights)

### Cohere (Toronto HQ)
- **Models:** Command A+ (latest flagship, MoE, vision+tools+reasoning),
  Command A, Command R (128K context, tool use, function calling)
- **Access:** API at cohere.com. Also available via OpenRouter, AWS Bedrock.
  Tool use / function calling is a first-class feature.
- **MATH harness fit:** Excellent. Command R has native JSON tool calling —
  map the 13 MCP tools as Cohere function definitions. Run the same TCA/PAR/
  SCR/RCF/TER metrics. Command A+ adds vision — could test screenshot-based
  observation alongside structured tool returns.
- **Pitch angle:** "Your models under MCP constraint achieve X% TCA in a live
  UE5.8 simulation environment. Here are the numbers."
- **Contact:** cohere.com/contact, also active on X, attend their Toronto events.
- **Estimated work:** 1–2 days to adapt the harness for Cohere's Chat API
  (tool_use format differs from OpenAI function calling but is well-documented).

### Augure (Toronto — sovereign Canadian AI)
- **Models:** Ossington 4 / 4.1 (vision+tools), Ossington 3 (reasoning),
  Tofino 2.5 (fast general), Rosedale One
- **Access:** OpenAI-compatible API at api.augureai.ca/v1. Drop-in replacement
  for OpenAI SDK — just change base_url. Function calling, streaming, embeddings
  all supported.
- **MATH harness fit:** Trivial integration — swap the base_url and API key,
  your existing OpenAI-compatible harness should work with zero changes.
- **Pitch angle:** "Sovereign Canadian AI models running a UE5.8 benchmark —
  here's how Ossington 4 performs against Hermes 3 and Command R under
  identical constraints."
- **Contact:** augureai.ca, developer dashboard for API key.
- **Estimated work:** <1 day. Literally change the base_url.

### OpenCode / Zen (Toronto — U Waterloo founders)
- **Models:** Model-agnostic platform (routes to Cohere, DeepSeek, Anthropic,
  etc. via their Zen tier). 8M monthly users.
- **Access:** Open source. Can be used as a routing layer.
- **MATH harness fit:** Less direct — OpenCode is a coding agent platform, not
  a model. But benchmarking their agent against the MATH environment (how well
  does OpenCode-as-agent handle MCP tool calling?) is a valid and novel test.
- **Pitch angle:** "Here's how OpenCode's agent stack performs in a non-code
  domain — UE5.8 environment authoring."
- **Contact:** Via GitHub / community. Jay V (founder) is accessible via X.
- **Estimated work:** 2–3 days (need to interface with their agent protocol).

---

## Tier 2 — Models available via third-party inference (test, then pitch)

### Borealis AI (Toronto — RBC research institute)
- **Models:** Internal/research. They publish papers but don't ship public APIs.
- **MATH harness fit:** Can't test directly. But if they publish open-weights
  research models, those could be run locally via Ollama.
- **Pitch angle:** Research collaboration (similar to Nous), not product
  benchmarking. Cite their agentic systems work.
- **Estimated work:** Contingent on them releasing something testable.

### MonteloAI (Toronto)
- **What:** LLM developer platform for TypeScript. Fine-tune, eval, deploy.
- **MATH harness fit:** Not a model provider — they're a platform. Could
  integrate MATH as an eval benchmark on their platform.
- **Pitch angle:** "MATH as a benchmark suite on your eval platform."
- **Contact:** founders@montelo.ai
- **Estimated work:** 2–3 days to package MATH as a Montelo-compatible eval.

---

## Tier 3 — No testable surface (pitch differently)

### Waabi (Toronto)
- **Models:** Closed. Waabi World simulator is proprietary, no public API/SDK.
- **MATH harness fit:** None directly. But Waabi hires for sensor simulation
  (C++, Python, rendering, content creation) — the portfolio is relevant.
- **Pitch angle:** Traditional application. Your UE5.8 simulation pipeline and
  rendering experience maps to their sensor simulation stack.
- **Estimated work:** Resume + cover letter, not a benchmark package.

### Ada (Toronto)
- **Models:** Proprietary conversational AI. No open models/weights.
- **MATH harness fit:** None — their product is customer service automation.
- **Not a target for this strategy.**

### GPTZero (Toronto)
- **Models:** Proprietary detection models. No open API for generation.
- **Not a target for this strategy.**

---

## Execution plan

| Phase | Target | Work | Deliverable |
|-------|--------|------|-------------|
| **Week 1** | Augure | Swap base_url, run MATH suite | Benchmark report: Ossington 4 vs Hermes 3 |
| **Week 1** | Cohere | Adapt harness for Cohere tool_use format | Benchmark report: Command A+ / R under MCP |
| **Week 2** | OpenCode | Interface with their agent protocol | Benchmark report: OpenCode agent in UE5.8 |
| **Week 2** | Package results | Compile all benchmark reports | Multi-model comparison paper |
| **Week 3** | Pitch emails | Send to each company with their numbers | Collaboration proposals |

### The pitch template (adapted per company)

> Subject: [MODEL_NAME] achieves [X]% task completion in a live UE5.8 RL
> environment — benchmark results + collaboration proposal
>
> I built a stateful RL benchmark (MATH — Melusina Agent Test Harness) that
> evaluates LLMs as autonomous agents in a live Unreal Engine 5.8 simulation.
> The action space is 13 MCP-constrained tools; the reward signal is compiler
> diagnostics + state convergence.
>
> I ran [MODEL_NAME] through the benchmark. Here are the results:
> - TCA (task completion): [X]%
> - PAR (policy adherence): [X]%
> - SCR (state convergence): [X]%
> - RCF (error recovery): [X]%
> - TER (token efficiency): [X]
>
> [1-2 sentences comparing to other models tested]
>
> I'm a 4th-year 3D major at [university]. I'd welcome the chance to discuss
> how MATH could be integrated into [COMPANY]'s evaluation pipeline, or
> explore collaboration on a published benchmark.
>
> [Repo link] | [Portfolio link]

---

## What makes this strategy work

1. **You're not asking for a job.** You're arriving with their own model's
   benchmark numbers. That's a fundamentally different conversation.
2. **The benchmark is reproducible.** The repo is public, the tools are
   committed, the metrics are defined. Any company can verify your claims.
3. **The comparison is novel.** Nobody else is benchmarking Toronto AI models
   inside a live AAA game engine. This is publishable.
4. **It scales.** Once the harness works for one model, adding another is
   hours of work, not days.
5. **It positions you as a researcher, not an applicant.** A 4th-year student
   with a published multi-model benchmark and collaboration proposals from
   multiple companies is a fundamentally different candidate profile.

---

*Created 2026-08-19. First targets: Augure (<1 day), Cohere (1-2 days).*
