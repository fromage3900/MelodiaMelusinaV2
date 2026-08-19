# Pitch: A Non-Programmer Shipped 70% of a UE5.8 JRPG Through OpenCode

**Prepared for:** OpenCode (Jay V, Frank Wang, Dax Raad, Adam Elmore)
**Date:** 2026-08-19
**Author:** 4th-year 3D major, zero formal programming background
**Subject:** What happens when a non-coder uses OpenCode as their primary
development harness for four months in a production game engine

---

## The headline

I'm a 3D animation student who cannot hand-write code. Over the past four
months, I've used OpenCode in JetBrains Rider as my primary development
harness to build a production UE5.8 JRPG — C++ subsystems, Blueprint wiring,
material pipelines, agent orchestration, quality gates, and all. The game is
now approximately 70% complete, and the final 30% is actively being built
through OpenCode right now.

I am not a programmer who adopted your tool. I am a non-programmer who could
not have built this without it.

---

## What was built

### The project: Melodia / Melusina V2

A vertical-slice JRPG in Unreal Engine 5.8 with:

- **C++ integration layer** — `UMelodiaNarrativeSubsystem` (narrative-to-JRPG
  bridge), `UMelodiaRhythmCombatSubsystem`, `UMelodiaTravelSubsystem`,
  `UMelodiaMusicClockSubsystem`, plus 15+ additional subsystems and components
- **Blueprint wiring** — battle controller, rhythm HUD, party management,
  save/load, post-battle restoration
- **Material pipeline** — 138 materials unified onto a Substrate Toon spine,
  procedural PCG scatter, SDF math-art materials, Baroque/Sakura/Zen
  environment families
- **Three coordinated MCP surfaces** — Monolith (116 Blueprint actions),
  VibeUE (150 flat tools), UEBlueprintMCP (60 tools, deliberately kept off
  by default)
- **Agent orchestration** — parallel coding lanes with Echo evidence ledger,
  quality gates (graph fingerprinting, regression testing, PIE smoke tests),
  jcode swarm coordination
- **T3D wiring pipeline** — spec → inject → compile → fingerprint → regress →
  promote, fully automated content authoring
- **40+ authored costume specs** for the protagonist (MelodiaWardrobe plugin)
- **Rhythm battle system** — highway notes, damage scaling, A/B testing
  framework, owner-confirmed working in live PIE

### The evidence

The repository is public: every commit, every tool, every pipeline script,
every decision log. 343+ commits on main, 6 active feature branches,
11 pull requests, CI/CD pipeline, and a committed evidence ledger that
tracks which claims have been verified and which haven't.

---

## What this tells you about OpenCode

### 1. Your tool works for non-programmers. Genuinely.

This is not "a developer who uses AI to go faster." This is a 3D art student
who had no path to building C++ subsystems, MCP orchestration, or agent
coordination frameworks without an agentic coding harness. OpenCode didn't
accelerate my workflow — it created a workflow that didn't exist.

The game has:
- C++ that compiles and runs (subsystems, components, reflection macros,
  UFUNCTION/UPROPERTY declarations)
- Blueprint wiring that connects to that C++ layer
- Python tooling (verification scripts, audit tools, pipeline runners)
- JSON spec formats (toon profiles, Niagara bindings, costume drafts)
- CI/CD configuration (GitHub Actions, echo gates, regression suites)

None of this was hand-written. All of it works.

### 2. Your tool survives hostile environments

UE5.8 is not a forgiving development environment. Over four months, OpenCode
(via DeepSeek and other models) navigated:

- **Fatal editor crashes** from touching Blueprint skill enums via Python
  (D_DamageType PyWrapper crash — the workaround is C++ via Monolith, not
  Python)
- **Three simultaneous editor instances** that corrupted assets and lost 39
  unsaved packages
- **Unity build symbol collisions** that only appear on full rebuilds
- **Shadowed parent events** in child Blueprints (10 empty-body overrides in
  BP_MelodiaBattleUI, including ShowBattleUI — invisible to compilation,
  fingerprinting, and smoke tests)
- **Sibling-graph drift** (OnKeyDown remapped to Q/W/O/P, OnKeyUp stayed on
  D/F/J/K — lanes latched lit)
- **Modal dialogs blocking the game thread** (Monolith goes silent, Windows
  reports "Not Responding" — not a hang, not a crash)
- **Expose-on-spawn pins** invisible to variable reference censuses
- **Live Coding failing silently** on new imports

Every one of these was discovered, diagnosed, documented, and worked around
through OpenCode sessions. The `_DECISION_LOG.md` has 49+ numbered decisions.
`AGENTS.md` has 24 safe-working rules that exist because something went wrong
and the agent (via OpenCode) learned from it.

### 3. Your dual-agent architecture matters in complex projects

The Plan/Build separation in OpenCode is not a nice-to-have in this project —
it's load-bearing. The project has:
- 24 MCP namespaces with 1330+ actions
- Protected files that must never be modified by an agent
- A decision log of settled questions that must be checked before re-litigating
- Asset paths that look identical but resolve to different objects (two
  BP_BattleUI, a 33-asset mirror tree)

The Plan agent catches cross-file dependencies, checks the decision log, and
identifies which MCP namespace has the capability before the Build agent
touches anything. Without that separation, agents scope-creep, re-investigate
settled questions, and write to protected files. (All three happened. Multiple
times. The safe-working rules exist because of it.)

### 4. Four months of continuous use data

I have four months of OpenCode session history across a single complex project.
That includes:
- What models work best for which task types (DeepSeek for spatial reasoning,
  smaller models for repetitive tool calling)
- Where the agent gets stuck and needs human intervention
- What error patterns recur and how the agent learns to avoid them
- How the dual-agent architecture performs under real multi-file, multi-system
  refactoring
- Token consumption patterns across different project phases

This is user research data that's hard to get from telemetry alone — it's
contextual, it has the "why," and it comes from a user profile (non-programmer,
3D artist, game dev) that your current user base probably underrepresents.

---

## What I'm proposing

### Option A: User research conversation
30 minutes with your product team. I walk through four months of OpenCode in a
hostile UE5.8 environment — what worked, what broke, what patterns emerged. You
get contextual user research from a non-programmer power user. No commitment
needed from either side.

### Option B: Case study / testimonial
"A non-programmer shipped a UE5.8 JRPG through OpenCode." That's a story your
marketing would want. I have the repo, the commits, the evidence ledger, and
the decision log to back it up. We write it together.

### Option C: Community contribution
I've been running OpenCode against UE5.8 with three MCP surfaces for months.
The community is just now building OpenCode-to-Unreal bridges
(SeeYouCowboi/Opencode-in-Unreal, Javadef/unreal-mcp). I'm ahead of where
those projects are. I can contribute documentation, patterns, and known
failure modes for the game-dev use case.

### Option D: All of the above, plus a job
I'm a 4th-year student graduating in 2027, based in Toronto. You're in
Toronto. If there's a role where "person who stress-tested your product in
the hardest possible environment and can tell you exactly where the edges
are" is useful, I'd like to talk about that too.

---

## Why this should matter to Jay V specifically

In the BetaKit interview, you said:

> "I'm a little bit worried that we're spending too much time thinking about
> the enterprise, and maybe not enough about what the average consumer wants."

I am the consumer case. I'm not an enterprise. I'm not a professional
developer. I'm a student who needed to build something that was beyond my
technical skill, and your tool is the reason it exists. The game-dev vertical
is underexplored in your user base, and it's one of the largest creative
communities in the world. I can help you understand what that market needs,
because I've been living in it for four months.

---

**Repository:** https://github.com/fromage3900/MelodiaMelusinaV2
**Tool:** OpenCode in JetBrains Rider
**Primary model routing:** DeepSeek (via OpenCode)
**Duration:** ~4 months continuous use (April–August 2026)
**Project state:** ~70% complete, actively building final 30%
