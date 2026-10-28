# DeepSeek V4.1 Flash — Melodia specialist-agent independent review and test handoff
**Date:** 2026-10-15  
**Model label:** DeepSeek-V4.1-Flash (`deepseek-flash` official API alias)  
**Status:** NOT EXECUTED. This file is a prompt, not a claimed DeepSeek output or passing canary.  
**Input:** [trench sweep 07](EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_07_SPECIALIST_MODELS_2026-10-15.md) + [manifest](../../specs/agent_canaries/specialist_models_20261015.json)

## Launch (no spending, no writes)
On the PC, sync a worktree to the **committed docs branch or merged main**; do not reset an occupied/dirty primary tree. Check `git status --short`, `git rev-parse HEAD`, available GPUs, Ollama, Houdini, Blender, Unreal/TD versions, and active single-writer/editor/P4 leases. Do not run downloads, installers, or paid API calls unless the user separately authorizes. If there is no free DeepSeek 4.1 route currently available, use the prompt through the user's existing subscription/UI, or return `HOLD_COST`; the official API is metered. The model cannot assume the user has a free quota.

## Copy/paste to DeepSeek V4.1
> You are DeepSeek-V4.1-Flash operating as a **critical independent evaluator** for the Melodia Melusina Unreal Engine 5.8 environment/technical-art project. Your goal is to identify which new specialist model or free local agent actually improves the existing production workflow, not to generate new architecture.  
>
> **Read before deciding:** `AGENTS.md`; `CURRENT_STATE.md`; `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`; `START_HERE_TONIGHT_PI_HERMES_UNIVERSE_FOUNDRY.md`; `Docs/PCG/MELODIA_PCG_SCHEMA.md`; `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_06_2026-10-02.md`; `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_07_SPECIALIST_MODELS_2026-10-15.md`; `specs/agent_canaries/specialist_models_20261015.json`. If any file cannot be read, mark the missing context and HOLD the affected claim.  
>
> **Authority:** Hermes dispatches existing mission DAG; Jev only chooses authored closed-set candidates; World Compiler/PCG, Hython/KineFX, TD, Unreal and SaveGame retain their separate owners. One editor writer; all tool discovery read-only. No second MPC, OSC bridge, game save owner, TD audio owner, runtime compiler, editor process or invented asset path. Do not re-create existing PCG Python material variation, cymatics, procedural cathedral, or KineFX AnimationDoctor.  
>
> **First phase:** Audit each manifest row against its upstream URL and license. Separately classify downloaded weights, bridges that need an LLM, research releases with GPU demands, free local software and paid APIs. Return `VERIFIED_LINK`, `UNVERIFIED_ARTIFACT`, `LICENSE_HOLD` or `NOT_ELIGIBLE`, with links and exact upstream versions/commits. Distinguish what you personally executed from what an upstream claims.  
>
> **Second phase:** Rank by net new value *against the actual repo*. Select at most three bounded canaries. Required first two are `houdini-vex-v11` and `ue-expert-v2` if hardware and model-access gates pass; optional third `tdmcp`. Give one precise input fixture, executable action, observed proof and rollback for each. Baseline against the current general coding model/workflow on identical inputs; no apples-to-oranges claims.  
>
> **Third phase:** For all safe, authorized tests, produce evidence, not just text. Collect source version, exact model artifact hash, inference mode, GPU/RAM, costs, prompt, deterministic seed, stdout/stderr, compiler/tool logs, side-by-side baseline, images and file hashes. Never claim `PASS` when you have not actually run the model or app. Output to `Saved/Audit/specialist_canaries_20261015/<candidate_id>/` only after confirming that destination is outside tracked/binary/P4 source and approved by the operator. If permission to run or write is missing, return a plan with `NOT_RUN`.  
>
> **Fourth phase:** Independently evaluate: exact functional correctness (30), deterministic rerun (20), compatibility with current production (20), local cost/resources (15), evidence quality (15). A score >=80 plus hard gates => `RECOMMEND_TO_OWNER` only, never production promotion. Every unknown hardware/license/cost/editor lease = `HOLD`. No self-certification and no modifications of production UE/TD/Houdini files.  
>
> **Required report:** 1) machine/repo preflight + HEAD, 2) verified candidate table with links/license/availability, 3) duplication-vs-existing-system analysis, 4) exactly which tests were physically run, 5) evidence index + hashes + independent verifier identity, 6) benchmark score and limitations, 7) ADOPT-LATER/PARK/REJECT with the smallest next authorized action. Prefer one strong specialist over a model swarm.
>
> Start with read-only inspection and report any blocker before requesting or using execution permissions.

## First two canary prompts (identical for specialist and general baseline)
### Houdini VEX
```text
Context: point wrangle in a disposable Houdini 22 SOP grid, centimeters, seed=3900.
Create VEX source for a deterministic bounded Chladni-like displacement:
f(x,y)=cos(3*pi*x)*cos(5*pi*y)-cos(5*pi*x)*cos(3*pi*y), with x,y normalized from local P.
Expose amp and frequency_scale; write f@resonance; change @P.z using amp * resonance;
handle zero-range bounds; no random external state and no undefined attributes.
Return a single compilable VEX snippet and list wrangle context + exact parameters.
Do not create nodes, export HIP, or touch UE.
```
Evidence: source + compile log + finite geometry attributes + two identically seeded runs + hash comparison; reject unsafe code or unsupported VEX calls.

### UE 5.8 flight
```text
You are reviewing real source/Blueprint export supplied separately, read-only.
Why can Sir Melodious flap/move in the correct horizontal direction yet lack controllable
body yaw turn-rate and altitude? Cite exact supplied file + symbol for each hypothesis.
Do not invent UFUNCTIONs, asset paths, or BP pins. Specify cheapest isolated runtime
measurements for yaw rotation and vertical input, before proposing a change.
If only prose is available, answer HOLD_SOURCE and request a read-only export.
```
Evidence: exact paths and symbols checked against current repo/actual BP, runtime trace or explicit HOLD, no changes.

## Review worksheet
| Field | Requirement |
|---|---|
| Candidate / model | Exact repo/model link and version or commit |
| Status | NOT_RUN / HOLD / FAIL / CANDIDATE_PASS (never production PASS) |
| Local execution | Hardware, licenses, runtime, installer and model hash |
| Cost | Free existing entitlement / local compute / metered API; explicit zero-spend proof |
| Safety | Disposable file, read-only owner, writer lease and rollback |
| Baseline | Identical task from existing general coder, with same constraints |
| Proof | Compiler logs, exact symbols, media, checksums, repeated run |
| Independent review | Evaluator different from producing agent; no self-certification |
| Verdict | RECOMMEND_TO_OWNER / PARK / REJECT / HOLD |

Do **not** write a “all tests passed” message for static manifest validation. A static validation PASS only means the packet is well-formed.
