# Melodia / Melusina — Long-Term Claireon Integration Plan

Status: **PREP.** Claireon is not built, not running, and has never executed a
tool against this project. Nothing below is a completed step. This is the plan
and the guardrails, written while the decisions are cheap.

Companion docs:
- `Docs/CLAIREON_PREP_2026-08-20.md` — baseline audit, ports, dependency resolution
- `Docs/CLAIREON_PROBE_RESULTS_2026-08-20.md` — client-side model probe results
- `specs/echo_pipeline.json` → stage `claireon_bringup` — the gate contract

---

## 1. Why Claireon at all

The project already runs Monolith (~1330 typed actions / 24 namespaces). Claireon
is not a replacement — it is a different bet on the same problem.

| | Monolith | Claireon |
|---|---|---|
| Tool surface | Large, typed, explicit | **2 tools** (`tool_search`, `python_execute`) |
| Discovery | Model reads the manifest | Model searches an FTS5 + embedding index |
| Context cost | Grows with the surface | Flat |
| Crash survival | None — state dies with the session | Optional always-on proxy |
| Execution | Typed actions with schemas | Arbitrary editor Python |

The two properties worth having for Melusina specifically:

1. **Flat context cost.** Melusina work is long-horizon — 465-bone rig, ABP state
   machines, wardrobe/material spine. Sessions die from context exhaustion, not
   from lack of capability. A 2-tool manifest is the only surface that doesn't
   grow.
2. **Crash survival.** The proxy holds the worktree port while editors come and
   go. Every editor crash currently costs the whole session's working state.

The property worth fearing: `python_execute` is unsandboxed. See §5.

---

## 2. Non-negotiable boundaries

These exist because the project is unstable as of 2026-08-18 and stability
outranks new capability.

**B1 — SUPERSEDED 2026-08-21 by owner decision. Claireon IS enabled in the main checkout.**

> The owner enabled Claireon in `BS_GodFile.uproject` (`Enabled: true`) and ratified it on
> 2026-08-21. The original rule is kept below for its reasoning, which still explains *why* the
> test worktree exists — but it no longer binds.
>
> ~~Claireon never runs in the main checkout. All bring-up happens in
> `C:\EnvironmentPortfolio\Melodia_ClaireonTest` (branch `claireon-test`, port 57818). The main
> checkout stays on Monolith.~~
>
> **What still binds under the new decision:**
> - B3, B4 and B5 are unchanged. Claireon is a *tooling* surface only — never a gameplay
>   authority, never a second writer on a graph Monolith is driving, and no `.uasset` write
>   without a gate row.
> - The §5 security posture is unchanged and is now **more** relevant, not less: `python_execute`
>   is unsandboxed, "localhost-only" is header validation rather than a socket bind, and there is
>   no authentication. Do not expose the port through a tunnel, proxy or port forward.
> - **B2 is now the live hazard** — see below.

**B2 — Claireon and UEBlueprintMCP are never enabled together. ⚠ CURRENTLY VIOLATED.**

> **Live state 2026-08-21:** `BS_GodFile.uproject` has **both** `Claireon: Enabled=true` and
> `UEBlueprintMCP: Enabled=true`. Two unsandboxed Python surfaces are declared at once. With B1
> superseded, this is the rule that still needs an owner action: **disable `UEBlueprintMCP`.**
>
> `Docs/Career/OPENCODE_TECHNICAL_OBSERVATIONS.md:24` already records UEBlueprintMCP as
> permanently disabled (untrusted), so turning it off costs nothing currently relied on.
>
> Mitigating fact: no `Saved/Claireon/MCPServer.json` exists in the main checkout, so Claireon's
> server has not bound here yet. The exposure is latent until the first `-StartMCPServer` launch.
Both expose unsandboxed Python. `Docs/Career/OPENCODE_TECHNICAL_OBSERVATIONS.md:24`
records UEBlueprintMCP as permanently disabled (untrusted); Claireon's README says
explicitly not to run them side by side. Disable UEBlueprintMCP in the test
worktree's `.uproject` before the first launch.

**B3 — Claireon does not become a second combat/gameplay authority.**
Per `AGENTS.md`: the JRPG template owns party/turns/skills/damage/saves.
`UMelodiaNarrativeSubsystem` is the narrow Quill bridge. Claireon is a *tooling*
surface — it authors and inspects assets. It must never be wired into runtime
gameplay logic, and no Claireon-authored Blueprint may hold gameplay authority
that belongs to the template.

**B4 — Claireon writes no `.uasset` without a gate row.**
Same contract as every other lane: a change is not done until
`Tools/echo_run.py record <gate> pass` has a ledger row. Claireon's speed makes
it easy to produce unverified volume; the ledger is the brake.

**B5 — One MCP surface per graph at a time.**
`AGENTS.md` already forbids a second MCP surface on the same graph. Monolith and
Claireon must not both be driving the same Blueprint in one session.

---

## 3. Phased plan

Each phase has an exit condition. Do not start a phase until the previous one's
exit condition has a ledger row or a documented failure.

### Phase 0 — Bring-up (current phase)
Prove Claireon can exist on UE 5.8 at all.

- [ ] Disable `UEBlueprintMCP` in the test worktree `.uproject` (B2)
- [ ] Build `BS_GodFileEditor` with Claireon enabled in the test worktree
- [ ] Launch with `-StartMCPServer`; confirm `Saved/Claireon/MCPServer.json`
- [ ] `tool_search blueprint` returns ranked results
- [ ] Record `claireon_build` + `claireon_server_bind` pass **or fail**

**Exit:** a ledger row either way. A build failure on 5.8 is a legitimate
outcome and a real upstream contribution — upstream issue #6 covers 5.7+ build
errors and there is no public record of a 5.8 build. File it.

### Phase 1 — Read-only inspection
No writes. Establish that Claireon sees the project correctly.

Targets, in order of Melusina relevance:
- `ABP_Melusina*` — state machine and pose-binding inspection. Cross-check
  against `melodia_animation_validate_state_machine` / `..._validate_bindings`
  from the Melodia MCP server. **Two independent readings of the same asset is
  the point** — disagreement is a finding.
- `SK_Melusina` V2 (465-bone) — bone hierarchy vs.
  `melusina_arp_to_live_skeleton_map.json`
- The Substrate Toon material spine — 138 materials, compare to
  `Docs/T3D_Baseline/material_catalog.json`
- `WBP_*` battle HUD tree vs. `melodia_ui_get_battle_hud`

**Exit:** `claireon_tool_discovery` recorded, plus a written diff of anywhere
Claireon and Monolith disagree about the same asset.

### Phase 2 — Guarded writes in the test worktree
First mutations, on assets that cannot break the P0 route.

- Start with fixtures and test assets only (`BP_T3DSafeWireProbe` and similar)
- Every write: fingerprint before → write → fingerprint after → compile →
  `bp_regression_checker.py` compare
- Read `LogClaireon PythonAuditLog` after every single run, without exception
- Never touch `BP_MelodiaJRPGGameMode`, `BP_MelodiaJRPGGameInstance`,
  `BP_MelodiaBattleUI`, or anything on the First Dream golden run

**Exit:** `claireon_python_roundtrip` recorded; 10 consecutive writes with clean
fingerprint deltas and no audit-log surprises.

### Phase 3 — Crash-survival evaluation
The claim that actually justifies adopting Claireon.

- Start the proxy (`Start-MCPProxy.ps1`), attach a client, kill the editor
  mid-task, measure reconnection
- Record: seconds to reconnect, whether the agent *resumes* or silently *restarts*
- Compare against the current Monolith baseline (total state loss)

This is the single most valuable untested claim per
`Docs/Research/UE_AGENT_BENCHMARK_DESIGN_2026-08-19.md:415` — the resilience
claim is documented but has no published quantitative result. A measured number
here is publishable.

**Exit:** a dated measurement, not a vibe.

### Phase 4 — Conditional adoption
Only if Phases 0–3 all cleared.

- Claireon becomes the **long-horizon Melusina lane** (rig, ABP, wardrobe,
  material spine) where flat context cost and crash survival pay off
- Monolith stays the **typed-action lane** for anything gameplay-adjacent, where
  explicit schemas are worth the context
- Add a `claireon` model-lane class to `Tools/model_router.py` with the same
  must-not constraints as `mcp`
- Main checkout adoption requires a separate explicit owner decision

---

## 4. What the client-side probe already tells us

From `Docs/CLAIREON_PROBE_RESULTS_2026-08-20.md` (editor offline, n=2 models):

- `qwen2.5-coder:7b` — 7/8, **100% surface adherence**. Never invented a tool
  outside the 2-tool manifest; correctly searched instead of hallucinating a flat
  `bp_compile`. This is the behaviour Claireon's whole design depends on, and a
  7B local model produced it.
- `deepseek-coder:6.7b` — 1/8. Failure is format compliance, not reasoning: it
  frequently named the right tool in prose but emitted no JSON. Unusable as an
  MCP client without constrained decoding.

Implication for lane assignment: the discovery pattern does not require a large
model, but it does require a model that reliably emits structured output. Route
Claireon lanes to `qwen2.5-coder` class models, not `deepseek-coder`.

Caveat: 6 of 8 local models are unscored because Ollama's `llama-server` began
crashing on load mid-session (`NTSTATUS 0xffffffff`). Re-run
`Tools/test_claireon_toolcalls.py --all` once that host issue is resolved.

---

## 5. Security posture

Claireon's own SECURITY.md is candid, and these are not hypotheticals:

| Risk | Mitigation here |
|---|---|
| `python_execute` is unrestricted — full filesystem, network, editor API | Test worktree only (B1). Never the main checkout. |
| "Localhost-only" is header validation, not a socket bind | Host firewall must block inbound on 43017 and 49152-65535. Software enforcement is not a boundary. |
| No authentication — any local process can call it | Do not run untrusted local processes during a Claireon session. |
| Execution timeout is best-effort; blocking native calls aren't interrupted | Expect hangs. Upstream issue #7 is exactly this on `bp_compile`. |
| Two unsandboxed Python surfaces if UEBlueprintMCP is on | B2 — mutually exclusive, enforced before launch. |
| Known-fatal Python crash path on skills Blueprints (`D_DamageType`) | Do not point Claireon at skills Blueprints until Phase 2 is clean. Read the audit log for early warning. |

Never expose these ports through a tunnel, reverse proxy, or port forward.

---

## 6. Open questions worth answering publicly

These are unanswered in the community, per the project's own research doc. If
this integration produces any of them, it is a genuine contribution:

1. Does Claireon build on UE 5.8, and what breaks? (no public record)
2. Does `tool_search` → `python_execute` work with a non-Claude client?
   (no public record with any non-Claude client — the probe above is a partial
   first answer, client-side only)
3. How many seconds does proxy reconnection actually take, and does the agent
   resume or restart?
4. Measured context cost: Monolith vs. Claireon on identical tasks.

What NOT to publish: "my project ran X% faster with Claireon." n=1,
project-specific, not reproducible.

---

## 7. Immediate next action

Single step, in the test worktree only:

```
cd C:\EnvironmentPortfolio\Melodia_ClaireonTest
# 1. disable UEBlueprintMCP in BS_GodFile.uproject  (B2)
# 2. build
& Plugins\Claireon\Scripts\Utilities\Invoke-EditorBuild.ps1
```

Then record the result — pass or fail — with:

```
python Tools/echo_run.py record claireon_build pass|fail --note "UE 5.8 build result"
```

Do not proceed past a build failure by working around it. Document it and file
upstream.
