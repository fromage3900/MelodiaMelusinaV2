# Emerging 3D Toolchain — Trench Sweep 07: specialist AI / DeepSeek V4.1
**Date:** 2026-10-15  
**Scope:** experimental, zero-production-writer model/agent shortlist  
**Baseline:** `main@0c8c714e2970d5dc9fe31f7879096c65a4150ebb` at research preparation  
**Status:** research only; every candidate NOT_RUN; no new runtime authority, install or model download  
**Companions:** [DeepSeek review packet](DEEPSEEK_V41_SPECIALIST_AGENT_REVIEW_PACKET_2026-10-15.md) · [machine manifest](../../specs/agent_canaries/specialist_models_20261015.json)

## Purpose
Package the specialist-agent trench sweep as a *falsifiable set of Melodia-shaped canaries*, not a recommendation to install eighteen systems. Each item below was located at a public upstream project/model page on 2026-10-15; locating an upstream is not a verified local download, working build, license clearance, benchmark win or working UE 5.8/Houdini 22 integration.

**Important correction to earlier informal research:** an open-source MCP bridge and an LLM with free downloadable weights are different categories. Bridges require an inference model; downloads cost storage/compute; official DeepSeek API inference is metered (no free API entitlement assumed). Do not log a result as PASS without the required real evidence.

## Existing authority, before any test
- `CURRENT_STATE.md` is the only live/proven status authority. Historical audit notes are not the live editor.
- `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`: Hermes dispatch, Jev closed-set decisions, World Compiler/PCG/Hython/TD/Unreal specialist owners, independent Echo acceptance.
- `START_HERE_TONIGHT_PI_HERMES_UNIVERSE_FOUNDRY.md`: single editor writer and read-first Unreal MCP gate.
- `Docs/PCG/MELODIA_PCG_SCHEMA.md`: L0 primitives, L1 data, L2 recipes, L3 hosts; no duplicate world/compiler owner.
- `Docs/Plans/MELUSINA_SKIRT_KINEFX_KAWAII_STABILIZATION_2026-10-10.md`: KineFX AnimationDoctor + garment copy, never casual canonical reimport.
- `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_06_2026-10-02.md`: architecture expansion is consume/maintain-only; Python PCG semantic/material variation already exists. Do not claim it as a discovery.
- TD has a dedicated `MelodiaTouchDesigner` repo and `ChordAtelier` lane; do not write `grandmaster_melodia` or introduce duplicate OSC/audio owners.
- Do not modify `AGENTS.md`, `CURRENT_STATE.md`, current Editor/Perforce state, critical P0 assets or branches as part of this packet. Use fresh sandbox scenes, throwaway rigs, independent review.

## Fast intake matrix
| Candidate (source) | Classification | Local/free status | Priority | Test against Melodia | Limitation/gate |
|---|---|---|---|---|---|
| [Qwen3 Houdini VEX v11](https://huggingface.co/anshulVashist/Qwen3-8B-Houdini-VEX-v11) | Specialist weights | Apache-2.0, local GGUF | **P0** | Chladni VEX wrangle compilation + deterministic point field | VEX compiles only in correct SOP context; GPU/RAM on host to verify |
| [UE Expert v2](https://huggingface.co/o-duffy/ue-expert-v2) | Specialist weights | Apache-2.0; card advertises GGUF | **P0** | Sir Melodious turn/height bug audit, actual symbol citations | Model card size/download availability must be checked; no UE 5.8 API guarantee |
| [BlenderLLM](https://github.com/FreedomIntelligence/BlenderLLM) | Specialist weights | Apache-2.0, HF weights | P1 | Parameterized cathedral rib/window using disposable bpy | ~15GB weights; generated scripts require isolation |
| [Procedura](https://github.com/SpatiaOS/Procedura) | Agent / parametric code | Source public, local-backend path | P1 | Named-parts mechanical organ-pipe fixture | Verify repo license and optional network usage |
| [UniMate](https://github.com/Friedrich-M/UniMate) | Skeleton-aware motion model | Research code/checkpoint | P2 | Disposable animal idle | Check weights license, checkpoint, GPU, skeleton mapping |
| [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens) | Rigging model | Research checkpoints | P2 | Existing-skeleton skinning copy | Approx 14 GB NVIDIA VRAM minimum reported; verify locally |
| [rheadsh Houdini MCP](https://github.com/rheadsh/houdini-mcp) | MCP **bridge**, not model | Free source | P1 | Cathedral HIP dependency readout | 123 tools, broad scene/file writes; localhost not sandbox |
| [ysk424 Houdini MCP](https://github.com/ysk424/houdini-mcp) | MCP **bridge**, not model | MIT fork | P2 | Headless Hython diagnostic | 88 tools and auto-launch; verify license usage; no concurrent writers |
| [UE Box](https://github.com/ueboxai/uebox) | Agent/plugin, not specialist model | Apache-2.0 source | P2 | Official Unreal MCP tool coverage comparison | Has editor mutation/build capability; disposable UE project only |
| [mcp-unreal-agent](https://github.com/PoBruno/mcp-unreal-agent) | MCP **bridge**, not model | Source public | P2 | Sequencer/MRQ tool discovery | Additional C++ editor plugin, verify UE 5.8 locally |
| [TouchDesigner TDMCP](https://github.com/TouchDesigner/TDMCP) | Official-project MCP bridge | Shared Use License | P1 | Read TD COMP/CHOP/TOP inventory in copy | Beta; `execute_code` arbitrary Python; 26 tools; no production .toe |
| [MuScriptor](https://github.com/muscriptor/muscriptor) | Music transcription weights | **Noncommercial weights** | P2 | Authored MIDI vs audio transcription | CC BY-NC 4.0 weights, avoid commercial work |
| [MT3-Infer](https://github.com/openmirlab/mt3-infer) | Multi-backend model wrapper | Free weights, backend-dependent licenses | P2 | Audio/MIDI reference precision | One vendored backend missing upstream license declaration |
| [Material Anything](https://github.com/3DTopia/MaterialAnything) | PBR diffusion model | Research checkpoint | P3 | Proxy PBR maps vs Copernicus baseline | Check checkpoint rights/Blender version |
| [NVIDIA Audio2Face 3D SDK](https://github.com/NVIDIA/Audio2Face-3D-SDK) | Speech animation SDK/models | Free code; separate licensing | P3 | Experimental cinematic face curves | NVIDIA SDK/weights/compute approvals |
| [Hugging Face MeshGen](https://github.com/huggingface/meshgen) | Blender agent | Local Ollama option | P2 | Safe GN decorator fixture | 8GB recommendation for in-process CUDA; Ollama different path |
| [BlendAgent](https://github.com/paulinastern/blender-agent) | Blender whitelisted-tool agent | MIT, local backend option | P2 | GN edit using prewritten tool | Ensure allowlist genuinely enforced |
| [AniGen](https://github.com/VAST-AI-Research/AniGen) | Animatable 3D research model | GPU-heavy research | P3 | Creature proxy | Check license/checkpoints/resource fit |

## First-wave experiments: only three
### A. Houdini VEX v11 — primary specialist canary
Supply a **small point grid**, one Chladni field formula from existing repo math as reference, seed 3900 and a precise point-wrangle context. The specialist must return VEX plus a brief attribute contract; have DeepSeek review it without editing production. Compile in a throwaway HIP. Capture compiler result, one screenshot, point positions/attributes and a hash of seed+parameter+geometry summary. Run twice and compare. Benchmark against existing general coder with exactly the same prompt. **PASS candidate:** compilable, numerically sane, seeded reproducible, no invented attributes/ops. **HOLD:** inability to run Hython/license; **FAIL:** noncompiling or fabricated API.

Suggested free local command (only after hardware/network/space approval):
```powershell
ollama run hf.co/anshulVashist/Qwen3-8B-Houdini-VEX-v11:Q5_K_M
```
No automatic download is performed by this repo.

### B. UE Expert v2 — offline symbol audit
Provide minimal **actual** flight source or serialized BP inspection for Sir Melodious (not prose), relevant UE 5.8 headers/docs, read-only scope. Ask for exact mechanism governing yaw/body turn rate, vertical input, and why wing animation without height control is possible. Demand citation of file paths + symbols, a HOLD for unavailable BP internals, minimal test plan and zero mutations. Human/repo-owner checks against source. **PASS candidate:** accurate, reproducible source-bound diagnosis; **FAIL:** nonexistent UFUNCTION/class or invented path. UE Expert needs GGUF/Modelfile availability preflight; do not assume model page alone guarantees a runnable checkpoint.

### C. TDMCP — read-only copy inspection
Load a **copy** of a TD network in a separate TouchDesigner process/session, loopback only, no arbitrary Python tool calls and deletion confirmations enabled. Discover operator hierarchy and cook errors. Compare to existing TD read-only inspection; record exact operator paths and zero unapproved writes. **PASS candidate:** structurally accurate report and independent readback. Explicitly **not** a new audio, OSC, field or runtime integration.

## Later waves
- P1: BlenderLLM and Procedura ornament/organ-pipe output; Houdini MCP capability-only comparison.
- P2: UniMate/SkinTokens on throwaway skeletons; MuScriptor vs MT3 MIDI ground truth; constrained Blender agents.
- P3: MaterialAnything/AniGen/Audio2Face only if licensing, VRAM and meaningful P0/P1 need clear.
- UE Box and mcp-unreal-agent remain alternative bridges, **not** authorized concurrent Unreal writers. Compare features first; do not install into Melodia.

## Scoring / promotion
Hard gates (any false => HOLD, no score-based override): upstream/artifact genuine, weights/dependency license appropriate, no surprise charge, correct branch/current canon, disposable sandbox, single-writer lease, no secrets, independent evidence. For each canary record 0–5 scores in: functional correctness (30%), determinism/reproducibility (20%), existing-pipeline compatibility (20%), resource/cost (15%), evidence quality (15%). Score >=80/100 *and* every hard gate permits **recommendation to owner**, not runtime promotion. Otherwise PARK/HOLD/REJECT. No agent self-certification.

Evidence belongs under ignored or independently staged `Saved/Audit/specialist_canaries_20261015/<id>/`; include source revision, exact weights hash, runtime versions, prompts, inputs, seed, logs, artefact hashes, benchmark baseline, and screenshots. Never write model binaries, .hip caches, .toe copies, credentials, or generated render assets to Git accidentally. `CURRENT_STATE.md` stays unchanged until a separate owner-approved production result.

## DeepSeek model and budget
The official DeepSeek 2026-09-10 release is **DeepSeek-V4.1-Flash**; official API model alias `deepseek-flash` (see https://api-docs.deepseek.com/updates/ and https://api-docs.deepseek.com/quick_start/pricing/). API calls are billed, not assumed free. Prefer an existing user-authorized free chat or included quota. **Do not create accounts, buy credits, or call a paid endpoint automatically.** DeepSeek is first the critical reviewer, not a second Hermes or Unreal operator. Full copy/paste packet is in the companion doc.

## Verification commands (no DCC/network needed)
```powershell
python Tools/Research/specialist_canary.py validate
python Tools/Research/specialist_canary.py list
python Tools/Research/specialist_canary.py packet houdini-vex-v11
python Tools/Research/specialist_canary.py self-test
```
These are *static packet checks* only, not proof models or editors ran. The tool never downloads models, calls APIs or mutates project source.

## Decision
**TEST NOW:** Houdini VEX v11, UE Expert v2. **TEST READ-ONLY:** TDMCP. **PARK until resource/legal fit:** large geometry/animation/multimodal models. **DO NOT:** new orchestration, silent editor writes, parallel UE/houdini writers or P0 architecture reopening.
