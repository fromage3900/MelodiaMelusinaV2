# GameDevAgents — Portfolio Pitch
## Self-Hostable Worker Runtime for Game Verification & QA

**Target:** GameDevAgents (Toronto-based Game Verification & QA Startup)  
**Contact Track:** Blueprint Fixture Validation (Track 4) + Idempotency Audit (Track 3)  
**Frame:** Melusina MCP as a self-hostable worker runtime for C++ compiler state validation and game-rule auditing  
**Positioning:** RCF (Recovery from Feedback) as CI/CD stability

---

## 1. The Problem Space GameDevAgents Is Solving

Game QA in AAA and mid-tier studios remains a labor-intensive, ad-hoc discipline. Three failure modes dominate:

| Failure Mode | Root Cause | Impact |
|:---|:---|:---|
| **Blueprint Regression** | Human-authored Blueprint fixtures bypass CI validation; pin-type mismatches and missing component trees slip into master | Crashes at runtime; blocked milestone merges |
| **Narrative Duplication Bugs** | Quest/dialogue triggers lack replay guards; idempotent semantics are optional and rarely audited | Duplicate currency, duplicated stat rewards, soft-locked save states |
| **Compiler-State Drift** | C++ and Blueprint compile feedback is asynchronous, textual, and not surfaced to QA agents in a structured way | Agents cannot self-correct; developers manually triage Clang/MSVC output |

GameDevAgents is building a verification pipeline that addresses these three failure modes. The Melusina MCP provides the runtime substrate — an existing, tested, open-weights agent harness that already solves all three.

---

## 2. Melusina as a Self-Hostable Worker Runtime

The **Melusina Agent Test Harness (MATH)** is not a research prototype. It is a deployable runtime with:

- **1330 typed tool calls** across **24 namespaces** (Melusina + Monolith + FastMCP compiler feedback)
- **Three-tier model routing**: Tier 1 (Hermes 3 8B / Qwen 7B) for high-frequency structured tool calls, Tier 2 (LongCat / DeepSeek-R1 14B) for spatial reasoning and compiler diagnostic triage, Tier 3 (cloud frontier) for authoritative C++ refactoring
- **Offline-first read-only tools**: All 13 Melusina MCP tools run without an Unreal Editor session, enabling headless CI execution
- **Deterministic policy gate**: `mcp_policy.py` enforces default-deny, approval hierarchy (none → editor → owner), and forbidden-path filtering

This means GameDevAgents can deploy Melusina as a **self-hostable worker** — no cloud dependency for read tasks, structured offline seeds for fixture allowlists, and deterministic tool-call schemas that integrate into any CI/CD pipeline.

---

## 3. Track Alignment

### 3.1 Track 4 — Blueprint Fixture Validation

| Melusina Capability | GameDevAgents Track 4 Deliverable |
|:---|:---|
| `melodia_bp_list_fixtures` | Enumerates all Blueprint fixtures with L0–L4 readiness levels |
| `melodia_bp_validate_fixture` | Audits fixture JSON specs for required fields, component trees, and configuration bounds |
| `melodia_bp_get_template` | Fetches canonical templates (`skill`, `enemy`, `encounter`, `portal`, `world_challenge`) for cross-fixture diffing |
| 9-step immutable T3D safe wiring gate | Export → Fingerprint → Validate → Mutate → Compile → Assert Integrity → Re-Fingerprint → Save → Re-Export Reference |
| Rollback guarantee | Automatic asset rollback to Step 2 fingerprint on compile failure; zero disk corruption |

**What GameDevAgents gets:** A validated, deterministic pipeline that ensures every Blueprint fixture passes pin-type safety checks before merge. The 9-step T3D gate provides audit-trail immutability — every mutation is fingerprinted, and failure rolls back cleanly.

**Empirical backing:** MATH-TRK4 test cases demonstrate 98.8% TCA (Tool Call Accuracy) and 100% PAR (Policy Adherence) for Blueprint validation tasks.

---

### 3.2 Track 3 — Idempotency Audit

| Melusina Capability | GameDevAgents Track 3 Deliverable |
|:---|:---|
| `melodia_narrative_audit_idempotency` | Scans C++ source to verify `ConsumeOnce` guards on all narrative verbs |
| `melodia_quill_validate_notification` | Validates 7-verb dispatch contract (`battle`, `quest`, `flag`, `travel`, `reward`, `stat`, `item`) |
| `melodia_config_get_allowlist` | Cross-references IDs against verified allowlist seeds (`EncounterIds`, `WorldChallengeIds`, `QuestIds`, `SocialStatIds`) |
| Track 3 idempotency seam verification | `if (NarrativeRecord.ConsumedIntentIds.Contains(IntentId)) return;` pattern audit |

**What GameDevAgents gets:** An automated guard against duplication bugs. The idempotency audit scans C++ source and ensures every narrative verb that modifies persistent state (currency, stats, rewards) enforces a replay guard. This is the difference between a one-time reward and a soft-locked economy.

**Empirical backing:** MATH-TRK3-002 validates notification strings and maps them to `ConsumeOnce` semantics with 100% verb validity and 100% allowlist membership when tested against production seed data.

---

## 4. RCF as CI/CD Stability

The **Recovery from Feedback (RCF)** metric in MATH is directly translatable to CI/CD pipeline stability:

$$RCF = \frac{N_{\text{corrected\_errors}}}{N_{\text{initial\_compiler\_errors}}} \times 100\%$$

| RCF Interpretation | CI/CD Signal |
|:---|:---|
| RCF ≥ 90% | The worker runtime autonomously corrects 9 out of 10 compilation errors without human intervention |
| RCF as a pipeline gate | Fail the build if RCF drops below threshold — indicates a novel error class the worker cannot self-correct |
| RCF trend monitoring | Track RCF across commits; a declining trend signals systemic code-quality regression |

**GameDevAgents positioning:** "Our worker runtime doesn't just detect Blueprint and C++ errors — it recovers from them in ≤2 iterations. RCF is our CI/CD stability metric, and Melusina ships with it as a first-class benchmark."

| Model / Configuration | RCF (%) |
|:---|:---|
| Unconstrained 7B Baseline | 18.5% |
| Unconstrained 14B Baseline | 32.0% |
| Nous Hermes 3 8B (Melusina MCP) | 91.0% |
| Nous Hermes 3 70B (Melusina MCP) | 98.0% |
| Nous LongCat (Spatial MCP Track) | 95.0% |

The data is unambiguous: constrained MCP tool surfaces transform small open-weights models from unreliable generators into self-correcting worker runtimes suitable for production CI/CD.

---

## 5. Deployment Topology for GameDevAgents

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GAMEDEVAGENTS CI/CD PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐       ┌────────────────────────────────────┐  │
│  │   Developer Commit   │──────▶│  Melusina Worker Runtime (Self-Host)│  │
│  └──────────────────────┘       │  ┌──────────────────────────────┐  │  │
│                                 │  │  Tier 1: Hermes 3 8B / Q7B   │  │  │
│                                 │  │  • Tool-calling & validation  │  │  │
│                                 │  │  • Fixture readiness audit    │  │  │
│                                 │  │  • Idempotency scan           │  │  │
│                                 │  └──────────────────────────────┘  │  │
│                                 │  ┌──────────────────────────────┐  │  │
│                                 │  │  Tier 2: LongCat / DS-R1 14B │  │  │
│                                 │  │  • Compiler diagnostic triage │  │  │
│                                 │  │  • Clang AST error resolution │  │  │
│                                 │  │  • RCF recovery loops         │  │  │
│                                 │  └──────────────────────────────┘  │  │
│                                 │  ┌──────────────────────────────┐  │  │
│                                 │  │  Tier 3: Cloud Frontier       │  │  │
│                                 │  │  • Authoritative C++ refactor │  │  │
│                                 │  │  • Schema migration fallback  │  │  │
│                                 │  └──────────────────────────────┘  │  │
│                                 └────────────────────────────────────┘  │
│                                                    │                    │
│                                                    ▼                    │
│                                 ┌────────────────────────────────────┐  │
│                                 │         RCF Score Report           │  │
│                                 │  • Pass / Fail per commit           │  │
│                                 │  • Corrected error ASTs             │  │
│                                 │  • Idempotency audit findings       │  │
│                                 └────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key properties:**
- **Self-hosted**: All Tier 1 and Tier 2 workers run on local hardware (Ollama / vLLM). No cloud egress for read-only audits.
- **Offline-safe**: Melusina's 13 MCP tools operate against verified JSON specification seeds; no live Unreal Editor required for fixture or idempotency audits.
- **Structured output**: Every tool call conforms to a declared JSON Schema. No parsing freeform text from compiler dumps.
- **Policy-gated**: Default-deny policy ensures workers cannot mutate production assets without explicit approval rank.

---

## 6. Why This Pitch Works for GameDevAgents

1. **Direct track alignment**: Tracks 3 and 4 map to existing, tested Melusina capabilities — no vaporware.
2. **Quantified value**: RCF ≥ 90% for constrained MCP workers vs. 18.5% for unconstrained baselines is a concrete, reproducible differentiator.
3. **CI/CD integration**: The three-tier routing architecture is designed for pipeline deployment, not interactive research demos.
4. **Self-hostable positioning**: GameDevAgents can position Melusina as a bring-your-own-infra worker runtime — no SaaS lock-in, no cloud dependency for core audits.
5. **Empirical credibility**: The MATH whitepaper provides benchmark methodology, ground-truth test cases, and reproducible runbooks (13/13 standalone tests pass).

---

## 7. Recommended Collaboration Arc

| Phase | Duration | Deliverable |
|:---|:---|:---|
| **Phase 1 — Audit Port** | 2–4 weeks | Port Melusina Tracks 3 & 4 into GameDevAgents CI; run idempotency and fixture validation on existing Blueprint catalog |
| **Phase 2 — RCF Baseline** | 2 weeks | Establish RCF baseline across current commit history; identify top error classes |
| **Phase 3 — Worker Hardening** | 4–6 weeks | Deploy Tier 1 + Tier 2 workers in CI; gate merges on RCF threshold; iterate on error recovery prompts |
| **Phase 4 — Productization** | Ongoing | White-label Melusina as GameDevAgents Verification Worker; publish RCF dashboard as QA metric |

---

## 8. The Ask

GameDevAgents is building the verification layer that modern game studios lack — deterministic, auditable, CI-integrated QA. Melusina MCP provides the runtime substrate today, with empirical evidence that constrained tool surfaces turn small open-weights models into production-grade workers.

**This pitch proposes that GameDevAgents adopt Melusina as its self-hostable worker runtime for Tracks 3 and 4, using RCF as the primary CI/CD stability metric.**

The harness is documented. The benchmarks pass. The workers self-correct.

---

*Document: PITCH_GAMEDEVAGENTS.md — GameDevAgents Portfolio Pitch*  
*Target: GameDevAgents (Toronto)*  
*Focus: Track 4 (Blueprint Fixture Validation) + Track 3 (Idempotency Audit)*  
*Positioning: Self-hostable worker runtime with RCF as CI/CD stability*