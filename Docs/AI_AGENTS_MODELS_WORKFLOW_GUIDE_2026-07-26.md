# AI Agents & Models — Workflow Guide (2026-07-26)

Web-researched current benchmarks (July 2026), matched against the actual distinct workflows this project runs. Not a general "best AI" ranking — matched to what each lane in this project actually needs.

## The four workflow lanes in this project

### 1. Environment-art agentic work (Monolith/Unreal material-graph, Niagara, PCG authoring)
**What this needs**: long sustained tool-use sessions, careful multi-step verification (this session alone hit and fixed 4+ silent-drop tool bugs by re-checking after every write), large context to hold a whole material graph/level state.
**Best fit**: **Claude Opus 4.7/4.8 or Sonnet 5** — Opus 4.7 leads raw coding benchmarks (87.6% on the hardest coding test), Sonnet 5 close behind (85.2%) at lower cost. This is genuinely the tier this session has been running on. Gemini 3.1 Pro's 2.5M context window is worth knowing about if a single session needs to hold an entire 1000+ node material graph export in context at once (this project hit that exact wall today with `M_Master_Toon_Universal`'s 130K-character export).

### 2. Gameplay/C++ integration work (Sol's lane — JRPG/QuillScript/MelodiaCore)
**What this needs**: precise, evidence-graded reasoning (Sol's own Evidence Register doc is a great example of the rigor this lane requires), C++ compile-cycle awareness, resistance to overclaiming ("Compile-proven" vs "Runtime-proven" as separate categories is exactly right).
**Best fit**: **GPT-5.4/5.5** — GPT-5.4 leads Terminal-Bench 2.0 (75.1%, the actual agentic/terminal-driven benchmark, ahead of Claude's 65.4% there) — this specifically favors GPT for compile-test-iterate C++ loops, which is Sol's daily work. This matches what's already happening (Sol = GPT/Codex per this project's existing setup) — current setup is already right for this lane, not a change to make.

### 3. Documentation, research, and career/application work
**What this needs**: good writing, real web-research grounding (today's studio-research corrections are a good example of why "good enough" recall isn't good enough here), doesn't need frontier-tier reasoning.
**Best fit**: cheaper tier is fine — **Gemini 3.1 Pro** (widest free tier, cheapest API, still 80.6% coding) or **DeepSeek V4/V4-Pro-Max** (80.6%, ~50x cheaper than Opus on input token cost) both do this well. This is exactly the kind of work worth routing to the cheap-subscription options discussed earlier (Poe, OpenRouter) rather than burning frontier-tier usage on it.

### 4. Bulk/mechanical delegation (the 163-instance texture sweep pattern from earlier tonight)
**What this needs**: nothing clever — repetitive, well-specified, single-heuristic checks across many items.
**Best fit**: cheapest available tier — Haiku-class Claude, or any of the cheap open-weight options (Qwen 3.7 Max, Kimi K2.6, DeepSeek) via OpenRouter/Poe. Don't spend frontier-tier budget here; this project's own memory already has this as an established pattern ("delegate mechanical scripted work to cheap subagents").

## Current July 2026 benchmark snapshot (for reference)
| Model | Coding benchmark | Notes |
|---|---|---|
| Claude Opus 4.7 | 87.6% | Top raw coding score |
| Claude Sonnet 5 | 85.2% | This session's model |
| Claude Opus 4.8 | — | Top human-preference ranking |
| GPT-5.4 | 75.1% (Terminal-Bench 2.0) | Leads agentic/terminal-driven work |
| GPT-5.5 | matches Opus on bug-fixing | Furthest-pushed agentic tooling |
| Gemini 3.1 Pro | 80.6% | 2.5M context, cheapest API, widest free tier |
| DeepSeek V4-Pro-Max | 80.6% | ~50x cheaper input cost than Opus |
| Qwen 3.7 Max | 80.4% | |
| Kimi K2.6 | 80.2% | (burned a day's tokens fast under a subscription wrapper per direct experience — verify any subscription's real usage caps before relying on it) |
| MiniMax M3 | 80.5% | |

## IDE/tool note specific to Unreal work
Research surfaced **Epic Developer Assistant** as a UE-specific AI tool (distinct from general-purpose Copilot/Cursor) — worth a look given how much of this project's work is UE-API-specific; general-purpose coding assistants don't know Unreal's API surface as deeply as a UE-native tool would. Not yet evaluated hands-on — a candidate to try, not a confirmed recommendation.

## Practical takeaway
The current setup (Claude/Sonnet 5 for environment-art agentic work, Sol/GPT for gameplay C++) already matches what the July 2026 benchmarks say is the right split — Claude for careful multi-tool-call verification-heavy work, GPT for terminal/compile-loop-driven work. The actual lever available is routing lanes 3 and 4 (docs/research, bulk mechanical sweeps) to cheaper tiers via Poe/OpenRouter, freeing frontier-tier budget for lanes 1 and 2 where it actually matters.
