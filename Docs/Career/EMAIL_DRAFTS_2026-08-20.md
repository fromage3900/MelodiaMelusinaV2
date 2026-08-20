# Application Emails — Draft for 2026-08-20

All details sourced from `Docs/Career/STUDIO_*.md` files. Review each draft,
personalize the brackets, and send.

---

## 1. NVIDIA — DevRel Manager, Higher Ed & Research (URGENT)

**Deadline: August 21, 2026** (tomorrow)
**Role:** Developer Relations Manager, Foundational AI (JR2023172)
**Location:** Toronto
**Salary:** $170K–$275K CAD (L4/L5)
**Apply:** https://jobs.nvidia.com/careers/job/893397075768

### Email / cover letter points

- Address the seniority honestly upfront: "I'm a 4th-year 3D student. I know
  this is scoped for more experience. Here's why the portfolio closes the gap."
- Lead with the SIL / Sanja Fidler connection — spatial intelligence, 3D
  content creation research. This is the Toronto lab's identity.
- Concrete artifacts:
  - 138-material Substrate Toon spine unified in UE5.8
  - T3D wiring pipeline with Echo evidence ledger (AI-authored content + quality gates)
  - Multi-MCP agent orchestration (3 surfaces, parallel lanes)
  - PCG procedural scatter pipeline
- Mention Vector Institute awareness — NV is platinum sponsor through 2027.
- Close with interest in SIL research internship / Omniverse intern if this
  role isn't the right level fit — gets your name in the system for fall
  postings.

### Attach
- Resume
- Link to portfolio site
- Link to GitHub repo (the pipeline IS the artifact)

### Draft opening
> I'm applying for the Developer Relations Manager role (JR2023172) in the
> Toronto office. I'm a 4th-year 3D major, which I know is earlier-career than
> this posting targets — but over the past [N] months I've built a production
> UE5.8 environment pipeline with AI-driven content authoring that I believe
> demonstrates the cross-discipline fluency this role needs.
>
> [2-3 sentences on the strongest portfolio pieces mapped to SIL research]
>
> I'm particularly drawn to the Toronto lab because of the Spatial Intelligence
> Lab's work in 3D synthesis and content creation — my portfolio is the applied
> production side of exactly those research problems. I'd welcome the chance to
> discuss this role, or if the timing is better, a research internship in
> Sanja Fidler's lab for 2027.

---

## 2. Infold Games — 2027 Campus Recruitment

**Deadline: October 31, 2026** (10 weeks)
**Track:** Art & Visual Design
**Apply:** https://lnkd.in/g8za_gzD (campus recruitment portal)
**Location:** Singapore HQ, LA, Tokyo, Seoul, Taipei (confirm remote/relocation)

### Email / cover letter points

- Apply through the **campus recruitment portal**, not the Senior Concept
  posting.
- Lead with Love and Deepspace aesthetic alignment: Sakura moonlit garden,
  Zen garden family, Baroque gilded ornament — cinematic, romantic, atmospheric.
- Mention UE5.8 production experience — their new AAA project uses UE5.
- Be honest about 3D pipeline strength vs. traditional concept/hand-drawing.
- Check portal for specific 3D Environment Artist track (preferred over
  concept art track if available).

### Attach
- Resume
- Portfolio reel (lead with stylized/romantic renders, not toon-action)
- ArtStation if you have one

### Draft opening
> I'm applying through Infold Games' 2027 Campus Recruitment for the Art &
> Visual Design track. I'm a 4th-year 3D major with a production portfolio
> built in UE5.8 — procedural environment art, cinematic lighting, and a
> material pipeline that maps to the romantic-atmospheric visual register
> Love and Deepspace is known for.
>
> [2-3 sentences on specific renders that match their aesthetic]
>
> I've followed Infold's work since [context] — the cinematic environment
> craft in Love and Deepspace, especially the attention to lighting and mood
> in scene composition, is what drew me to this application.

---

## 3. Nous Research — Research Collaboration Proposal (PRIMARY)

**Deadline:** None (rolling)
**Contact:** Research / eval team — find via nousresearch.com or X (@NousResearch,
@Teknium). Also cc recruiting@nousresearch.com.
**Subject:** Research Collaboration Proposal: MATH — Stateful RL Environment for
Constrained Open-Weights Models

### What this is

NOT a job application. A pitch for a joint benchmark / whitepaper. The full
proposal is at `Docs/Portfolio/PITCH_NOUS_RESEARCH.md` (committed 2026-08-18,
pending merge via PR #9).

### Key numbers to lead with

**⚠ 2026-08-20 CORRECTION — READ BEFORE SENDING.**
The previously drafted headline ("Hermes 3 8B: 98.8% TCA / 100% PAR / 95.5% SCR /
91.0% RCF / 85% token reduction" and "LongCat 14B: 99.2% TCA, 97.5% SCR") is
**WITHDRAWN**. Those figures were formally unpublished on 2026-08-19 — see the
withdrawal notice at `Docs/melusina-agent-harness.html:468-478`: *"withdrawn and
unpublished — it was never backed by a committed run log."* Do not send them to a
research lab. Nous would ask for the run log and there isn't one.

Verified numbers, each with a run JSON on disk (`Saved/Audit/`):

| Claim | Value | Evidence file |
|---|---|---|
| Harness self-eval (tool surface) | **31/32, TCA 100%** | `math_run_latest.json` (2026-08-20, `kind: harness_self_eval`) |
| qwen2.5-coder:7b via MCP | **21/32, TCA 90.3%, exec 67.7%** | `math_run_qwen2.5-coder_7b_2026-08-20.json` |
| qwen3.8-27b via MCP | **21/32, TCA 81.2%, exec 65.6%, TER 3.18** | `math_run_qwen3.8-27b_2026-08-19.json` |
| muse-glimmer-30b | **0/32** (harness hosts it; model failed) | `math_run_muse-glimmer-30b_2026-08-19.json` |
| Echo gate ledger | **41 rows — 32 pass, 9 fail** | `Saved/gate_ledger.json` |
| Completion gates | runtime / save_load / repeat_consume / package_launch all **PASS** | `Tools/echo_run.py status` |

Note both caveats honestly — they are the interesting part, not a weakness:
- `editor_contacted: false` on the self-eval. Editor-required tasks HOLD rather
  than silently pass.
- muse-glimmer-30b scored 0/32. Report it. A harness that reports a zero is a
  harness worth trusting.

The real pitch is the **environment and the methodology**, not a leaderboard:
UE5.8 as a live stateful RL environment, MCP as a constrained action space,
compiler diagnostics as the reward signal, and a ledger that refuses unbacked
claims — demonstrated by this very correction.

### Email structure
1. One-line hook: "I built a live UE5.8 environment where MCP is the constrained
   action space and compiler diagnostics are the reward signal — and a gate ledger
   that withdraws its own unbacked numbers."
2. Two sentences on MATH (Melusina Agent Test Harness) as a formal RL env.
3. Propose the four-phase collaboration roadmap from the pitch doc.

4. Ask for a 30-minute call with their eval/research team.

### Attach
- `Docs/Portfolio/PITCH_NOUS_RESEARCH.md` (full proposal)
- GitHub repo link (the pipeline IS the evidence)

### Secondary ask (if appropriate)
Mention interest in ML Engineer, Evals role or Forward Deployed Engineer as a
secondary note — but don't lead with it. The collaboration pitch is stronger.

---

## 4. Certain Affinity — Sr Advanced Technical Artist (Toronto)

**Deadline:** Rolling (posted June 2026, still active)
**Role:** Senior Advanced Technical Artist
**Location:** Toronto (hybrid)
**Salary:** $130K–$175K CAD
**Apply:** https://hiring.camp/job/yzlE9G

### Notes
- This is a Senior role but Certain Affinity is known to hire strong juniors.
- Dead-center skill match: UE5 materials, procedural env art, Blueprint,
  Substance, Houdini, performance profiling.
- The Substrate Toon spine work is directly relevant — mention material
  pipeline optimization, shader instruction budgets.
- Reports to Technical Art Director.

### Draft opening
> I'm a 4th-year 3D major applying for the Senior Advanced Technical Artist
> role in the Toronto office. My portfolio includes a production UE5.8
> environment pipeline: 138 materials unified on a Substrate Toon spine,
> PCG procedural scatter, and AI-driven content authoring tooling. I know this
> is scoped at Senior level — I'd welcome the chance to show the work and
> discuss where I'd fit on the team.

---

## 5. Velan Studios — Technical Artist (Sr+/Lead)

**Deadline:** Rolling
**Role:** Technical Artist (Senior+/Lead)
**Location:** Toronto (hybrid, 3 days/week)
**Salary:** $95K–$150K CAD
**Apply:** https://gamejobs.co/Technical-Artist-Senior-Lead-at-Velan-Studios-2062

### Notes
- Custom engine + Unreal. Unannounced title.
- Values experimental/NPR work — the Toon material work is a direct fit.
- Also hiring Senior Environment Artist ($85K–$120K) — may be more
  realistic as a first target.

---

## 6. OpenCode — User Research + Case Study + Contribution

**Deadline:** None (but momentum matters — reach out while you're actively using it)
**Contact:** Jay V via X (@jayv), OpenCode Discord, or Toronto meetup circuit.
Also: hello@opencode.ai or via GitHub.
**Subject:** "A non-programmer shipped 70% of a UE5.8 JRPG through OpenCode —
4 months of user data"

### What this is

NOT a benchmark package. A user research conversation. The full pitch is at
`Docs/Portfolio/PITCH_OPENCODE.md`.

### Why this is different from the other pitches

You're not testing their model from outside. You've been a daily power user
for four months. The community is just now building OpenCode-to-Unreal bridges —
you're months ahead. Jay V explicitly said he's worried about over-focusing
on enterprise and losing the consumer story. You ARE the consumer story.

### Four options to offer (from the pitch doc)
A. 30-min user research conversation with their product team
B. Co-written case study ("non-programmer ships UE5.8 JRPG via OpenCode")
C. Community contribution — UE5.8 MCP patterns, failure modes, documentation
D. All of the above + a job conversation (you're in Toronto, they're in Toronto)

### Draft opening
> I'm a 4th-year 3D student who can't hand-write code. Over the past four
> months I've used OpenCode in Rider as my primary development harness to
> build a production UE5.8 JRPG — C++ subsystems, MCP orchestration, material
> pipelines, agent coordination, the whole stack. The game is 70% done and
> I'm building the last 30% in OpenCode right now.
>
> I have four months of contextual use data from a user profile your base
> probably underrepresents: non-programmer, game dev, hostile environment
> (UE5.8 + three MCP surfaces). I'd love 30 minutes with your product team
> to walk through what I learned. Also happy to co-write a case study or
> contribute UE5 patterns to the community.

---

## Priority order for tomorrow

| # | Company | Action | Deadline |
|---|---------|--------|----------|
| 1 | **NVIDIA** | Submit DevRel application + resume | **Aug 21** |
| 2 | **OpenCode** | Send pitch email / DM Jay V | ASAP (momentum) |
| 3 | **Nous Research** | Send MATH collaboration proposal | Rolling |
| 4 | **Certain Affinity** | Send application | Rolling |
| 5 | **Infold Games** | Visit campus portal, identify track | Oct 31 |
| 6 | **Velan Studios** | Send application | Rolling |

---

## Pre-send checklist

- [ ] Resume updated with UE5.8 pipeline work, MCP orchestration, material spine
- [ ] Portfolio site live and loading
- [ ] GitHub repo has recent commits visible (push local state first)
- [ ] Hermes test results committed (for Nous application)
- [ ] ArtStation updated with stylized renders (for Infold application)
- [ ] Each email personalized — no generic "I love your company" language
- [ ] **No withdrawn metrics anywhere** (98.8 / 99.2 / 95.5 / 91.0 / TER 0.15)
- [ ] Every number you send has a file in `Saved/Audit/` you could attach

---

# SEND-READY BODIES

Copy-paste ready. Only `[[...]]` fields need your input. Written flat and factual
per tone preference — no flourish, no "I'm passionate about".

Signature block for all of them:

```
Brennan Shepherd
brennan.shepherd3900@gmail.com
Portfolio: https://fromage3900.github.io/my-site/
GitHub:    https://github.com/fromage3900/MelodiaMelusinaV2
Toronto, ON
```

---

## A. Nous Research — collaboration proposal

**To:** recruiting@nousresearch.com (cc research contact if you find one)
**Subject:** MATH: a UE5.8 stateful environment for evaluating constrained open-weights models

> Hi,
>
> I've built something I think is relevant to how you evaluate Hermes, and I'd
> like to propose a collaboration rather than apply for a job.
>
> MATH (Melusina Agent Test Harness) treats Unreal Engine 5.8 as a live stateful
> environment for tool-using models. MCP is the constrained action space —
> models emit typed tool calls, not free-form code. Compiler diagnostics and
> Blueprint graph state are the observation and reward signal. Episodes
> terminate on a gate, and every gate result is written to an append-only ledger.
>
> Current state, all backed by run logs in the repo:
>
> - Harness self-eval: 31/32 tasks, 100% tool-call accuracy
> - qwen2.5-coder:7b through the MCP surface: 21/32, 90.3% TCA
> - qwen3.8-27b: 21/32, 81.2% TCA, token efficiency ratio 3.18
> - muse-glimmer-30b: 0/32 — the harness hosted it fine, the model failed
> - 41 gate-ledger rows: 32 pass, 9 fail
>
> I'm including the zero deliberately. I withdrew an earlier scorecard from my
> own whitepaper this week because it wasn't backed by a committed run log, and
> I'd rather show you a harness that refuses unbacked numbers than a leaderboard.
>
> What I think is interesting for Nous specifically: this is a long-horizon
> environment where small open-weights models have to hold state across dozens
> of steps in a hostile, real codebase — not a synthetic benchmark. I have four
> months of daily operating data on where they break.
>
> Full proposal with the four-phase roadmap is attached. Would your eval team be
> open to a 30-minute call?
>
> [[SIGNATURE]]

**Attach:** `Docs/Portfolio/PITCH_NOUS_RESEARCH.md`

---

## B. NVIDIA — DevRel Manager (deadline Aug 21)

**Apply at:** https://jobs.nvidia.com/careers/job/893397075768
**Subject:** JR2023172 — Developer Relations Manager, Foundational AI (Toronto)

> Hello,
>
> I'm applying for Developer Relations Manager, Higher Ed & Research —
> Foundational AI (JR2023172) in Toronto.
>
> I'm a 4th-year 3D major at Humber College. That is earlier-career than this
> posting assumes and I want it stated plainly rather than discovered. I'm
> applying because the work already shipped maps onto what Toronto's Spatial
> Intelligence Lab and Vector-facing DevRel engage with: spatial content
> systems, AI-augmented production pipelines, and agent orchestration an
> academic can actually inspect.
>
> The artifact is a production UE5.8 project, not coursework:
>
> - 138 materials unified onto a single Substrate Toon master spine
> - PCG procedural scatter systems and a documented Blender → UE content path
> - A multi-agent MCP harness against that same project, with an evidence
>   ledger — completion gates for runtime, save/load, repeat-consume and
>   packaged launch all recorded PASS as dated rows
> - Agent evaluation: harness self-eval 31/32 (100% tool-call accuracy), local
>   Qwen through MCP at 21/32 (90.3%)
>
> Every number above has a run log or ledger row in the public repo. Where a
> claim didn't, I withdrew it.
>
> I'm drawn to Toronto specifically because SIL's lineage — 3D vision, neural
> rendering, content-creation research — is the research side of the production
> problems I've been solving. If JR2023172 isn't the right level, I'd welcome
> redirection toward an SIL or Omniverse-adjacent research internship for 2027.
> I'm Toronto-based and available for an on-site technical screen.
>
> Resume attached; portfolio and repo links below.
>
> [[SIGNATURE]]

**Do NOT include:** Muse 30B as a win, TokenRouter, Nemotron product claims,
or any withdrawn TCA figure. See `NVIDIA_DEVREL_PACKET_2026-08-20.md:77`.

---

## C. OpenCode — user research

**To:** hello@opencode.ai (or DM @jayv on X)
**Subject:** Four months of UE5.8 power-user data from a non-programmer

> Hi Jay,
>
> I'm a 4th-year 3D student who cannot hand-write code. For the past four months
> OpenCode in Rider has been my primary development harness for a production
> UE5.8 JRPG — C++ subsystems, MCP orchestration across three surfaces, material
> pipelines, multi-agent coordination. The project is roughly 70% done and I'm
> building the rest in OpenCode now.
>
> I think I'm a user profile your data underrepresents: non-programmer, game dev,
> genuinely hostile environment. I've kept records of where the workflow breaks —
> context compaction losing MCP state mid-task, tool-surface size blowing up
> context, recovery behaviour after editor crashes.
>
> You've mentioned worrying about over-indexing on enterprise and losing the
> consumer story. I have four months of the consumer story written down.
>
> Any of these work for me:
> 1. 30 minutes with your product team, no prep needed on your side
> 2. A co-written case study
> 3. Contributing UE5.8 MCP patterns and failure modes to the community docs
>
> I'm in Toronto, same as you, so in person is easy if that's simpler.
>
> [[SIGNATURE]]

---

## D. Certain Affinity — Sr Advanced Technical Artist

**Apply at:** https://hiring.camp/job/yzlE9G
**Subject:** Senior Advanced Technical Artist — application (Toronto)

> Hello,
>
> I'm applying for the Senior Advanced Technical Artist role in the Toronto
> office. I'm a 4th-year 3D major, so I'm reaching above the posted level and
> want that clear from the start.
>
> The reason I'm applying anyway is that the skill list matches what I've
> actually built:
>
> - UE5.8 material pipeline: 138 materials consolidated onto one Substrate Toon
>   master, with shader instruction budgets tracked as a build gate
> - PCG procedural environment scatter
> - Blueprint tooling — automated graph injection, fingerprint-based regression
>   detection, and static audits that catch defect classes like shadowed parent
>   events and dead execution islands
> - Python/MCP editor automation across a live UE project
>
> The Blueprint audit tooling exists because those defects shipped in my own
> project and passed review — a child Blueprint silently shadowing a parent's
> event, compiling clean, and breaking the battle UI. I wrote the sweep so it
> couldn't happen twice.
>
> Happy to walk a Technical Art Director through the pipeline and talk about
> where I'd realistically fit on the team.
>
> [[SIGNATURE]]

---

## E. Infold Games — 2027 campus recruitment

**Apply at:** campus portal (https://lnkd.in/g8za_gzD) — Art & Visual Design track
**Subject:** 2027 Campus Recruitment — Art & Visual Design (3D environment focus)

> Hello,
>
> I'm applying through Infold Games' 2027 Campus Recruitment for the Art &
> Visual Design track. I'm a 4th-year 3D major graduating [[GRAD MONTH/YEAR]].
>
> My strength is 3D environment and material work in UE5.8 rather than 2D
> concept illustration, and I'd like to be considered on that basis. The work
> sits in the romantic-atmospheric register Love and Deepspace occupies:
> moonlit Sakura gardens, a Zen garden family of environments, and Baroque
> gilded ornament systems — built with a stylized non-photoreal material spine
> and cinematic lighting.
>
> [[1-2 sentences naming the specific renders you're leading with]]
>
> I understand your new project is UE5-based; my pipeline experience is UE5.8
> end to end, including procedural scatter and a Blender-to-engine content path.
>
> Portfolio and reel links below. If there's a dedicated 3D Environment Artist
> track in the portal I'd prefer to be routed there.
>
> [[SIGNATURE]]

**Before sending:** confirm whether the portal has a 3D Environment track, and
whether Toronto-remote or relocation applies.

---

## F. Velan Studios — Technical Artist / Senior Environment Artist

**Apply at:** https://gamejobs.co/Technical-Artist-Senior-Lead-at-Velan-Studios-2062
**Subject:** Technical Artist — application (Toronto, hybrid)

> Hello,
>
> I'm applying for the Technical Artist opening in Toronto. I'm a 4th-year 3D
> major — below the posted seniority — and I'd also like to be considered for
> the Senior Environment Artist posting if that's the better fit.
>
> The reason I'm writing is the experimental/NPR emphasis. My UE5.8 project runs
> a unified Substrate Toon material spine across 138 materials: stylized shading
> with hand-authored control rather than a photoreal target, plus a post-process
> stack built for a non-photoreal look. Alongside that: PCG scatter systems,
> Blueprint automation tooling, and Python editor pipelines.
>
> I'd welcome the chance to show the material system and discuss either role.
>
> [[SIGNATURE]]


---

## PRs pending merge (for owner to squash-merge from GitHub UI)

| PR | Title | Status |
|----|-------|--------|
| [#7](https://github.com/fromage3900/MelodiaMelusinaV2/pull/7) | docs: First Dream is playable — PIE board + QUICKSTART | MERGEABLE |
| [#8](https://github.com/fromage3900/MelodiaMelusinaV2/pull/8) | docs: Twinmotion + RealityScan side-lane handoff | MERGEABLE |
| [#10](https://github.com/fromage3900/MelodiaMelusinaV2/pull/10) | Add full asset credits suite | MERGEABLE |
| [#1](https://github.com/fromage3900/MelodiaMelusinaV2/pull/1) | Foundation: V2 game plan, repo hygiene, post-battle restore | MERGEABLE |
| [#9](https://github.com/fromage3900/MelodiaMelusinaV2/pull/9) | Repo lock-in: LFS/hooks, art gate, Perforce plan (touches `.gitattributes`) | MERGEABLE |
| [#5](https://github.com/fromage3900/MelodiaMelusinaV2/pull/5) | Model lanes, AGENTS slim | DRAFT |
| [#11](https://github.com/fromage3900/MelodiaMelusinaV2/pull/11) | Career research (this branch) | DRAFT |
