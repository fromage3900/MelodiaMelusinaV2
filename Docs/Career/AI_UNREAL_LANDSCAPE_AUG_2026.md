# AI Agents in Unreal Engine Development — Landscape Report, August 2026

Evidence-based survey. Every claim has a source. Written to establish where
this project's workflow actually sits, not where we'd like it to sit.

---

## 1. The Ecosystem (what exists right now)

### First-party: Epic's native MCP plugin (UE 5.8)
- Shipped June 17, 2026 with UE 5.8. Experimental.
- Embeds an MCP server at `http://127.0.0.1:8000/mcp` inside the editor.
- 830 tools across 52 toolsets (via AllToolsets companion plugin).
- Covers: Blueprints, levels, materials, meshes, Niagara, Sequencer,
  animation, PCG, widgets, GAS, StateTrees, DataFlow, Conversation.
- No authentication. Local-only. Serial execution on game thread. No in-editor
  UI — terminal-first.
- Officially supports: Claude Code, Codex CLI, Cursor, Windsurf, Copilot.
- **UE 5.8 only.** Most shipping projects are still on 5.3–5.7.
- Source: Epic release notes, ue-mcp.com, explainx.ai writeup.

### Third-party MCP servers (commercial)

**StraySpark Unreal MCP Server (v4.5)**
- 400+ tools across 60 categories. UE 5.7 and 5.8.
- Catalog mode (~3K tokens vs ~60K for full tool list).
- `run_tool_script` for multi-step transactions. `describe_graph` for
  agent self-verification. PIE control. Runtime debugging. Automation tests.
- Bearer auth, per-token scopes (read/scene/destructive), undo per mutation.
- Imports Epic's first-party toolsets as `epic_*` at the same endpoint.
- Paid product, one-time pricing. Full source included.
- Field report (April 2026): "The single biggest lever for improving agent
  productivity on a UE project is the tool surface, not the model."
- Source: strayspark.studio, Epic forums, field report blog post.

**UAIP — Unreal AI Integration Platform (v1.0)**
- 540+ native semantic commands + 190+ bridges to UE 5.8 Toolset (~730+ total).
- Cross-asset graph editing: Blueprint, Material, Niagara, AnimBP, ControlRig,
  Sequencer, PCG, MetaSound, BehaviorTree, StateTree, Dataflow, EQS.
- HTTP / WebSocket / MCP transports. PIE lifecycle. Crash recovery.
- Per-session Capability + process-wide SafetyPolicy.
- UE 5.7 and 5.8. Available on Fab.
- Source: Epic Developer Community Forums post.

**Claude Assistant (PixelsDesign)**
- 80 agentic editor tools via local MCP bridge. $49.90 one-time on Fab.
- In-editor chat panel. UE 5.3–5.8 (BuildPlugin-verified on all six versions).
- Used in production on "The Hakim" (1920s Bahrain action-adventure).
- Every mutation is an undoable editor transaction.
- Source: pixelsdesign.it blog, Fab listing.

### Third-party MCP servers (open-source)

**Believer.gg / Claireon**
- Open-sourced June 2026 under MIT. 600+ tools. UE 5.5+.
- Used daily with Claude Code at Believer Entertainment (a real studio).
- "Doubled our delivery into the game across its first three months."
- Non-technical staff use it: designers build simulations, creative director
  (zero Unreal experience) writes narrative in Notion and injects it via AI.
- Deliberately small MCP surface: `tool_search` + `python_execute`.
- Local proxy for session persistence across editor restarts.
- 127 GitHub stars. Source: believer.gg blog, GitHub.

**DONXAKer/unreal-mcp**
- ~118 low-level tool commands + `build_blueprint_graph` (declarative graph
  builder in one atomic call with rollback). Python MCP server ↔ C++ plugin.
- Claude Desktop, Cursor, Windsurf, AI-Workflow pipelines.
- Source: GitHub.

**IvanMurzak/Unreal-MCP**
- Cross-engine (Unity, Godot, Unreal) via shared GameDev-MCP-Server.
- Cloud backend at ai-game.dev or self-hosted. Available on Fab.
- Source: GitHub, npm.

**UEBridgeMCP**
- Native C++ plugin. Streamable HTTP. UE 5.6+.
- Extension modules for Control Rig, PCG, External AI.
- Source: GitHub.

**mariuz/unreal-mcp-cpp**
- Pure C++, no Python. Deep Blueprint tool access. Cursor-focused.
- Source: GitHub.

**SeeYouCowboi/Opencode-in-Unreal**
- OpenCode-specific. 22 tools. Slate chat panel. UE 5.7+.
- Source: GitHub.

**Javadef/unreal-mcp**
- OpenCode-specific bridge. 0 stars. Very early.
- Source: GitHub.

### Agent skill frameworks

**GameStudio (bullish0x)**
- 55 specialized AI agents, 182 skills across Godot, Unity, Unreal, Three.js,
  PixiJS, Phaser, R3F. Provider-neutral (Claude Code, Codex, OpenCode, Cursor,
  Gemini-style tools).
- `unreal-specialist` agent with sub-specialists: GAS, Blueprints,
  Replication, UMG/CommonUI.
- Source: GitHub (51K+ file, substantial project).

**maystudios/claude-skills**
- Production-ready Claude Code skills for UE5, llama.cpp, and OpenCode CLI.
- Built from "real-world experience shipping an Unreal Engine 5.7 horror game."
- Includes an `opencode` skill for using OpenCode as a sub-agent.
- Source: GitHub.

---

## 2. Who's using AI agents in UE5 production — with evidence

| Who | Agent | MCP surface | Project | Status |
|-----|-------|-------------|---------|--------|
| **Believer Entertainment** | Claude Code | Claireon (600+ tools) | Unannounced game | Production. Doubled delivery. Non-technical staff contributing. |
| **PixelsDesign** | Claude (via Claude Assistant) | Claude Assistant (80 tools) | The Hakim (UE5 action-adventure) | Production. Shipping on Fab. |
| **StraySpark** | Claude Opus/Sonnet/Haiku | StraySpark MCP Server (400+ tools) | Multiple real UE5 projects | Production. Published field report. |
| **maystudios** | Claude Code + OpenCode | Claude skills | UE 5.7 horror game | Shipped. |
| **Thiago Carneiro (GIRRAPHIC/Seneca)** | Various | Various | Teaching + production pipelines | Active in Toronto. |
| **This project** | OpenCode (DeepSeek) + Cursor | Monolith + VibeUE + UEBlueprintMCP | Melodia/Melusina V2 (UE5.8 JRPG) | ~70% complete. |

---

## 3. Where this project actually sits

### What's common (not differentiating)
- Using AI agents to work in UE5. Everyone above does this.
- Non-technical person contributing to an Unreal project via AI. Believer.gg's
  creative director (zero UE experience) does this daily.
- MCP as the bridge protocol. This is the industry standard as of mid-2026.
- Blueprint wiring, material authoring, asset creation via agents. Multiple
  tools cover this (StraySpark: 400+ tools, UAIP: 730+, Epic native: 830).

### What's uncommon (genuinely differentiating)
- **OpenCode as the primary harness** (not Claude Code). The entire UE5 + MCP
  ecosystem is Claude Code-first. StraySpark, Claireon, Claude Assistant, UAIP,
  and Epic's own tutorial all target Claude Code. OpenCode-specific UE5 projects
  have 0 stars (Javadef) or are small community projects (SeeYouCowboi, 22
  tools). Using OpenCode as the primary harness for a substantial UE5.8 project
  is genuinely rare. I found ONE other person who shipped a UE game with
  OpenCode involvement (maystudios, who uses it as a sub-agent under Claude
  Code, not as the primary harness).
- **Three simultaneous MCP surfaces** on one project. Believer uses Claireon
  (one surface). PixelsDesign uses Claude Assistant (one surface). StraySpark
  recommends one server. Nobody I found coordinates three MCP servers
  simultaneously the way this project does (Monolith + VibeUE + UEBlueprintMCP
  with explicit rules about never running two against the same graph).
- **Non-programmer as the sole developer** (not part of a studio team).
  Believer.gg's non-technical staff contribute alongside a full engineering
  team. PixelsDesign has professional developers. You are a solo 3D student
  with no engineering team behind you. This is a different claim.
- **Formal benchmark framework (MATH)** with defined RL metrics. Nobody else
  has published a formal RL environment definition for UE5 + MCP. StraySpark
  published a field report with qualitative assessments. The MATH benchmark
  with TCA/PAR/SCR/RCF/TER is quantitative and reproducible (though
  unpublished and un-peer-reviewed).
- **Four months continuous** on one project. Most of the ecosystem reports are
  "three months" (Believer, StraySpark). Four months on a single project with
  detailed failure documentation (24 safe-working rules, 49+ decisions) is
  substantial continuous-use data.
- **DeepSeek as the primary model** routed through OpenCode. The entire
  ecosystem runs Claude (Opus/Sonnet/Haiku). DeepSeek-through-OpenCode
  performing at production level in UE5.8 is novel.

### What's weaker than the ecosystem
- **Tool count.** Monolith has ~116 actions. StraySpark has 400+. UAIP has
  730+. Epic native has 830. Your MCP surface is smaller than the commercial
  options.
- **No commercial product.** StraySpark, UAIP, and Claude Assistant are all
  available on Fab with documentation, versioning, and support. Your pipeline
  is a project-specific setup.
- **No published results.** StraySpark published a field report. Believer
  open-sourced their tool. PixelsDesign sells theirs. Your MATH benchmark
  exists only in your repo — not published, not peer-reviewed, not
  independently verified.
- **Scale.** Believer is a funded studio. PixelsDesign is a commercial
  developer. You're a solo student. The project is real and substantial, but
  it's not "AAA" — don't use that word in pitches to people who ship AAA games.

---

## 4. Honest positioning for pitches

### To OpenCode:
"I'm one of the only people using OpenCode (not Claude Code) as the primary
harness for a substantial UE5.8 project. The entire MCP ecosystem is
Claude-first — I have four months of data on what it's like to be the
non-default path. Plus I'm a non-programmer who can't hand-write code, which
is the consumer story you said you're worried about losing."

### To Nous Research:
"The MATH benchmark is a formal RL environment definition with five quantitative
metrics tested against your models. Nobody else has published this for UE5+MCP.
The numbers are real but un-peer-reviewed — I'm proposing we validate and
publish them together."

### To NVIDIA / Infold / game studios:
"I built a production UE5.8 environment pipeline with AI-driven content
authoring — three coordinated MCP surfaces, procedural materials, agent
orchestration. This is the applied production side of what your research lab /
art team works on." Don't mention OpenCode or AI agents as the headline —
lead with the artifacts (the materials, the environments, the game).

---

*Researched 2026-08-19. All sources verified via web search same day.*
