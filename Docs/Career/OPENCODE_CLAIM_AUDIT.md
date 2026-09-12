# OpenCode Pitch — Claim Audit

> **Downstream of the game.** This is marketing / funding / hiring material for
> **Melodia Melusina**, a single-person AAA-tier UE 5.8 rhythm-JRPG. It exists to fund and staff
> the game. **No agent may cite anything in this folder as project direction** — authority is
> [`../../../PROJECT.md`](../../../PROJECT.md).

Critical evaluation of every claim in the pitch. Each rated:
**VERIFIED** (evidence found), **PLAUSIBLE** (reasonable but unconfirmed),
**UNKNOWN** (can't determine), **UNSUPPORTED** (no evidence or contradicted).

---

## Claims about OpenCode itself

### "OpenCode is based in Toronto"
**VERIFIED.** Founded June 2025 at a DevTools Toronto meetup. Jay V spoke at
Toronto Tech Week Homecoming May 2026. Multiple sources (BetaKit, BestStartup.ca,
Boreal Signal) confirm Toronto as the company's origin city. Founders are U of
Waterloo alumni. However: the team is small and distributed across US, Australia,
India, Denmark. "Toronto HQ" is accurate for origin and identity; the team is
not all physically in Toronto.

### "8 million / 13 million / 16 million monthly users"
**VERIFIED but the number keeps moving.** BetaKit confirmed 8M MAU in June 2026.
The TechFounder/Lightcone interview (more recent) says 13M. OpenCode's own
website now says "16M developers every month." The BestStartup.ca article still
says 8M. These numbers are self-reported and have not been independently audited
beyond BetaKit's June 2026 verification. The trajectory is real; the exact
current number is somewhere between 8M and 16M depending on how recently you
check and how they're counting.

### "$25M ARR"
**VERIFIED** by BetaKit and independently confirmed by The Fair Media's
verification article. Via the Zen hosted model tier.

### "195K GitHub stars"
**VERIFIED.** GitHub shows 195,497 stars as of this search. Independently
verifiable.

### "Jay V said he's worried about over-focusing on enterprise"
**VERIFIED.** Direct quote from the BetaKit interview: "I'm a little bit worried
that we're spending too much time thinking about the enterprise, and maybe not
enough about what the average consumer wants."

---

## Claims about the competitive landscape (OpenCode + Unreal)

### "The community is just now building OpenCode-to-Unreal bridges — you're months ahead"
**PARTIALLY UNSUPPORTED. This is the claim I most exaggerated.**

The reality:
- **SeeYouCowboi/Opencode-in-Unreal** (22 tools) and **Javadef/unreal-mcp**
  exist, but are small/new projects.
- **However**, there is a much more developed ecosystem than I indicated:
  - **Believer.gg / Claireon** — a professional game studio (not a hobbyist)
    open-sourced an MCP plugin for UE5 that they use in daily production.
    Their creative director, who has "not a minute of experience working in
    Unreal Editor," writes narrative in Notion and injects it into the game
    via AI. This is directly comparable to your non-programmer claim.
  - **PixelsDesign / Claude Assistant** — 80 agentic editor tools, sold on
    FAB for $49.90, used in production on "The Hakim" (a real UE5 game).
    Ships since 2026, verified on UE 5.3–5.8.
  - **GameStudio** — 55 specialized AI agents and 182 skills for Godot, Unity,
    Unreal, Three.js, etc. Explicitly supports OpenCode-style tools.
  - **maystudios/claude-skills** — production-ready Claude Code skills for
    UE5, including an OpenCode integration skill, built from "real-world
    experience shipping an Unreal Engine 5.7 horror game."
  - **StraySpark** — published a detailed field report on autonomous AI agents
    in UE5 production (April 2026), concluding that MCP tool surface quality
    is the biggest lever, not the model.
  - **UE 5.8 native MCP plugin** — 830 tools across 52 toolsets, shipped by
    Epic. This is not experimental fringe anymore; it's a first-party feature.
  - **ue-mcp.com** — community documentation site wrapping all 830 official
    tools.
  - **Thiago Carneiro** — Unreal Tech Artist at GIRRAPHIC, teaching at Seneca
    Polytechnic in Toronto (your city), actively building and teaching
    AI-accelerated UE5 pipelines.

**Corrected assessment:** You are NOT "months ahead of where the community is."
The AI-in-Unreal ecosystem is active and has professional studios, commercial
products, and open-source frameworks already in production. What you have that
IS unusual is the specific combination of: (a) non-programmer, (b) OpenCode
specifically (not Claude Code), (c) three MCP surfaces coordinated
simultaneously, (d) four months of continuous use on one project. But the claim
that the community is "just now figuring out how to connect OpenCode to Unreal"
was an overstatement — they're past that.

### "Nobody else is benchmarking Toronto AI models inside a live AAA game engine"
**PLAUSIBLE but unverified.** I found no evidence of anyone doing this specific
thing. But absence of evidence is not evidence of absence, and the MATH
benchmark's "AAA" characterization of a student project is generous. It's a
production-quality UE5.8 project, but calling it "AAA" in a pitch to people
who ship actual AAA games is a risk.

---

## Claims about your project

### "70% complete"
**UNKNOWN.** Self-assessed. The repo has 343+ commits, active branches, and a
substantial codebase, but "70% complete" is a subjective claim about a game
that has never been played by anyone other than the owner. No external
validation of this number exists.

### "138 materials unified on a Substrate Toon spine"
**VERIFIED** from commit messages in the repo (`8ced728`, `9c59c8f`).

### "Three coordinated MCP surfaces"
**VERIFIED** from `AGENTS.md` and `.mcp.json` in the repo. Monolith, VibeUE,
UEBlueprintMCP.

### "343+ commits on main"
**VERIFIED.** `git log` confirms this.

### "C++ subsystems that compile and run"
**PLAUSIBLE.** Source files exist in `Source/BS_GodFile/MelodiaIntegration/`.
The repo documents compilation issues that were resolved. But I have not
independently verified that the current HEAD compiles clean — rule 21 in
AGENTS.md specifically warns that "the build is green" decays into a lie.

### "Non-programmer who can't hand-write code"
**UNKNOWN.** This is your self-report. It's plausible given that you're a 3D
major, but I have no way to verify the degree of your programming ability.
Be careful with this claim — if an interviewer asks you to explain a specific
C++ pattern in your repo and you can't, the "can't hand-write code" framing
becomes "doesn't understand the code in their own project," which is worse
than just being a junior programmer.

---

## Claims about interest to the OpenCode team

### "You are the consumer case Jay V is looking for"
**PLAUSIBLE.** His stated concern about over-focusing on enterprise is real.
A non-programmer game developer using OpenCode daily is a real data point.
But: 16M users means they have data on a LOT of user profiles. You're not
the only non-traditional user. You may be unusual in the game-dev vertical
specifically.

### "They'd genuinely want to hear from you"
**UNKNOWN.** A 16M-user company gets a lot of inbound. A 4th-year student
reaching out is not automatically interesting to a CEO. The pitch needs to be
concise and lead with the most unusual data point (non-programmer + UE5.8 +
four months + three MCP surfaces), not with flattery.

### "The game-dev vertical is underexplored in your user base"
**PLAUSIBLE but weakening.** GameStudio, maystudios/claude-skills, and Believer.gg
all demonstrate that game dev is an active vertical for AI coding agents.
OpenCode specifically may be underrepresented vs. Claude Code in game dev
(most of the UE5 MCP ecosystem targets Claude Code or Codex, not OpenCode),
but it's not a greenfield.

---

## What I previously told you that was exaggerated

1. **"The community is just now figuring out how to connect OpenCode to Unreal
   at all. You're months ahead."** — Overstated. The ecosystem is further along
   than I represented. Believer.gg has a full production studio using MCP+UE5
   with non-technical staff. PixelsDesign ships a commercial product. Your
   specific setup (OpenCode + three MCP surfaces + Rider) is unusual, but the
   broader space is not nascent.

2. **"Nobody else in the world has done this."** — I implied this about the
   MATH benchmark and the OpenCode/UE5 combination. I should not have said it
   with that confidence. What IS true: I found no one doing your exact
   combination. What is NOT true: that the AI-in-Unreal space is empty.

3. **"This is a fundamentally different candidate profile."** — This was the
   framing for the MATH benchmark expansion. It's partially true (the benchmark
   approach is genuinely unusual), but I oversold the uniqueness of the overall
   position. Many students are building game dev projects with AI agents now.
   What's unusual is the scale, the MCP depth, and the formal benchmark work —
   not the concept.

---

## Revised honest assessment

**What is genuinely unusual about your position:**
- Non-programmer building a substantial UE5.8 project through OpenCode
  specifically (most UE5+AI users are on Claude Code or Codex)
- Three coordinated MCP surfaces on one project (most projects use one)
- Four months of continuous use (most OpenCode users are coding professionals,
  not 3D artists)
- The MATH benchmark is a real, formal RL environment definition with
  numbers (but it exists only in your repo — it's not published or
  peer-reviewed)

**What is NOT unusual:**
- Using AI agents in UE5 production (Believer.gg, PixelsDesign, StraySpark,
  maystudios all do this)
- Non-technical people using AI to work in Unreal (Believer.gg's creative
  director, Shankar, explicitly does this)
- Being a student building a game with AI tools (increasingly common)

**What to keep in the pitch:**
- The OpenCode-specific angle (vs Claude Code) — genuine differentiation
- The three-MCP-surface coordination — genuinely unusual
- The four-month continuous use data from a non-programmer — real user research
- Offer the user research conversation — this is the honest, low-ask opening

**What to tone down:**
- "Months ahead" — remove entirely
- "Nobody else" — remove entirely
- "AAA" — your project is production-quality but not AAA-scale
- Implication that game-dev is unexplored territory for AI agents — it's not

---

*Audited 2026-08-19. All web searches conducted same day.*
