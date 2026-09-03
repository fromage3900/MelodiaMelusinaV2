# Lane coordination — Qwen/Muse vs Nemotron (2026-08-20)

**Peer chat:** [General chat](5344e2d5-18a2-403f-80aa-5f6c1a304283)  
**Transcript path (note):** `C:\Users\froma\.cursor\projects\c-EnvironmentPortfolio\agent-transcripts\5344e2d5-18a2-403f-80aa-5f6c1a304283\` (not under `g-EnvironmentPortfolio`)  
**This lane (Nemotron / NVIDIA packet):** OpenRouter-only experiment + DevRel materials; do not fight local Ollama.

---

## What the Qwen/Muse lane owns right now

From recent peer messages (through **11:22 AM** user ask: *"we need more tests and mcp calls to local qwen and muse glimmer"*):

| Own | Detail |
|-----|--------|
| **Local Ollama models** | `qwen2.5-coder:7b` / `:14b`, `muse-glimmer-30b:latest`, HF Muse Glimmer tag; also DeepSeek tags present |
| **Setup / runner scripts** | `Tools/setup_muse_glimmer.py`, `Tools/run_math_models.py` (`--model qwen…`, `--run-muse`), `scripts/daemon_content_gen.py` |
| **Harness restore + MATH goldens** | Restored MCP tool surface (34 tools), P0 golden alignment; self-eval **31/32 TCA 100%** (1 HOLD = editor SM) |
| **Site dashboard publish** | Snapshots into `C:\EnvironmentPortfolio\wix\` / `my-site-clean` (lookbook dashboards) — keep website lane on `wix` |
| **Overnight / health ops** | `Tools/overnight_run.ps1`, `Tools/health.py`, claims under `Saved/Audit/project_health_claims.json` |

**Not actively owned by them for Nemotron:** OpenRouter Nemotron Super/Ultra smoke, `specs/nemotron_experiment_harness.json` Phase 0–2.

**Live at sample time:** `ollama serve` up; Monolith **`:9316` listening** (ESTABLISHED clients). No `run_math_models` / `setup_muse` process matched in a quick scan, but peer just requested more local Qwen/Muse MCP runs — treat Ollama + MATH `*_latest.json` as **about to be hot**.

---

## Shared resources

| Resource | Who uses it | Collision mode |
|----------|-------------|----------------|
| **Ollama GPU/CPU** (`127.0.0.1:11434`) | Qwen/Muse lane (primary) | Loading Muse 30B or Qwen 27B/14B saturates VRAM/RAM; second heavy pull stalls both |
| **MATH evidence JSON** | Both if careless | `Saved/Audit/math_run_latest.json`, `math_run_models_latest.json` are **overwrite targets**; dated `math_run_*_<model>_*.json` are safer |
| **MCP / Monolith `:9316`** | Peer MATH (editor-contacted runs); any UE MCP harness | One Monolith rule ([PARALLEL_LANES_2026-08-12](PARALLEL_LANES_2026-08-12.md)); concurrent agent tool spam → flaky HOLDs / false FAILs |
| **OpenRouter API key** | Muse cloud path (`meta/muse-spark…`); Nemotron lane | Rate limits / spend if both hit at once — serialize or use separate budgets |
| **`C:\EnvironmentPortfolio\wix`** | Peer dashboard publish | Website lane only; Nemotron docs stay under `Docs/` / Career packet |

---

## Conflict risk: **MED** (→ **HIGH** if boundaries broken)

- **MED** while Nemotron stays on **OpenRouter only**, writes **dated/nemotron-named** evidence (never clobber `math_run_latest.json`), and does not pull/load local Muse/Qwen.
- **HIGH** if Nemotron also calls `run_math_models.py` against Ollama, `--run-muse`, or rewrites peer `*_latest` MATH files while they expand local MCP tests.
- **HIGH** on `:9316` if both lanes drive editor-required MATH / UE MCP in parallel.

---

## Recommended boundaries

1. **Muse/Qwen lane** — local Ollama + Hermes MCP MATH; owns `setup_muse_glimmer.py`, `run_math_models.py --model qwen* / --run-muse`, daemon dry-runs; may use OpenRouter Muse only if local blocked.
2. **Nemotron lane** — **OpenRouter only** (Claude vs Nemotron Super gate); no Ollama pulls/chats; no Muse Glimmer local load; evidence under `Saved/Audit/nemotron_*` or dated paths — **do not overwrite** `math_run_latest.json` / `math_run_models_latest.json`.
3. **Website lane** — stay on `C:\EnvironmentPortfolio\wix` (and site repo copies); Nemotron/Career packet does not republish dashboards.
4. **Read-only courtesy** — do not kill peer Ollama/python, do not delete/overwrite their Audit MATH files; cite dated copies.

---

## Evidence reusable in NVIDIA DevRel packet (agent harness MATH)

| Artifact | Usable? | One-liner |
|----------|---------|-----------|
| `Saved/Audit/math_run_latest.json` (2026-08-20) | **Yes** | Hermes MCP harness self-eval **31/32 pass, TCA 100%** (1 editor HOLD) — tool surface, not an LLM leaderboard |
| `math_run_qwen2.5-coder_7b_2026-08-19.json` | **Yes (local baseline)** | Local Qwen **via Hermes**: **24/32**, TCA **96.9%** (tool-choice / exec metrics present) |
| `math_guardrails_qwen2.5-coder_7b_2026-08-19.json` | **Yes** | Guardrailed agentic workflow **30/32**, TCA **96.8%** |
| `math_run_muse-glimmer-30b_2026-08-19.json` | **No as a win** | Muse run **0/32** (HTTP 500s) — cite only as “harness can host Muse; score not yet green” |

**Packet sentence:** Melodia already has a dated Hermes MCP MATH harness with self-eval **31/32 (TCA 100%)** and a local Qwen-via-MCP tool-choice run at **24/32 (TCA 96.9%)**, suitable as agent-orchestration evidence without pitching Nemotron product claims.

---

## Ops checklist for Nemotron agents

- [ ] Do not run `ollama pull` / `setup_muse_glimmer.py --pull`
- [ ] Do not invoke `run_math_models.py` with local `--model` / `--run-muse`
- [ ] Prefer OpenRouter smoke + T1/T4/T5; write `Saved/Audit/nemotron_*` only
- [ ] If `:9316` needed, confirm peer is idle on editor MATH first
- [ ] Link peer as [General chat](5344e2d5-18a2-403f-80aa-5f6c1a304283) in any follow-up handoff

---

## Sonnet closeout note (2026-08-20): `C:\EnvironmentPortfolio\wix` is now a local git repo

`C:\EnvironmentPortfolio\wix` (214+ files, 48 HTML pages, all modified today) had **zero** version
control — the single biggest data-loss exposure found in this session's git-health pass. It now
has a local-only git repo (`git init`, one commit, `.gitignore` for `node_modules/`/`.DS_Store`/
`*.log`). **No remote, no push** — this is a local safety net only, not a publishing change, and
it does not touch this lane's ownership of that directory.

This does **not** resolve the two-`wix`-trees question — it just stops the untracked one from
being one `rm -rf` away from gone. There are still two divergent trees and no source-of-truth
decision:

- `BS_GodFile/wix` (tracked in the main repo) and `C:\EnvironmentPortfolio\wix` (now its own local
  repo) are **not** a superset/subset pair.
- The sibling (`C:\EnvironmentPortfolio\wix`) has ~19 pages `BS_GodFile/wix` lacks, including
  dashboards, the agent harness, the hiring dossier, credits, pipeline, and t3d-catalog pages.
- `BS_GodFile/wix` has 5 embed/component pages the sibling lacks (`melodia-hero-embed.html`,
  `melodia-passport-embed.html`, `melodia-project-card.html`, `melodia-smooth-scroll.html`, plus
  an `environment-template.html`-style component set under its own archive).

Neither tree should be treated as canonical until the owner decides which one the live site
actually deploys from. This lane (Qwen/Muse) still owns `C:\EnvironmentPortfolio\wix` per the
boundary above — the git init only adds history, it does not change who writes there.
