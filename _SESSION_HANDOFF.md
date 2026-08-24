> ## Start here — 2026-08-24
>
> **[`Docs/Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md`](Docs/Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md)**
> — current P0 truth, the shortest live-proof path, and the post-P0 architecture order.
>
> Status: [`Docs/MELODIA_OVERALL_STATUS_2026-08-24.md`](Docs/MELODIA_OVERALL_STATUS_2026-08-24.md) ·
> P0 test playbook: [`Docs/P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md`](Docs/P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md) ·
> Git: [`Docs/GIT_HEALTH_2026-08-24.md`](Docs/GIT_HEALTH_2026-08-24.md) ·
> Worktrees: [`Docs/GIT_WORKTREE_INVENTORY_2026-08-24.md`](Docs/GIT_WORKTREE_INVENTORY_2026-08-24.md)
>
> Authority: [`../PROJECT.md`](../PROJECT.md) ·
> [`Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`](Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md) ·
> [`Docs/ORCHESTRA_CONTRACT_2026-08-20.md`](Docs/ORCHESTRA_CONTRACT_2026-08-20.md)
>
> **P0 is still open.** Preserve the mixed worktree, keep proof tiers distinct,
> and do not expand the nine economy/song/HUD/dungeon items into the convergence critical path.

> **Historical body notice:** The August 20 session record below is preserved for evidence and
> context; it is no longer the current task router.

# ♪ Session Handoff — BS_GodFile

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧  ┊ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```

**Read this first. Every session. No exceptions.**

♫ Last updated: **2026-08-20 16:45 ET** · ♪ **THE PARADIGM SHIFT**

---

## ♪ Current session — 2026-08-20 — read the closeout first

**Full record:** [`Docs/Handoffs/SESSION_CLOSEOUT_2026-08-20.md`](Docs/Handoffs/SESSION_CLOSEOUT_2026-08-20.md)

**The project is a game.** `PROJECT.md` is now the authority statement: QuillScript and the
TurnBased JRPG template are absolute; rhythm rides on JRPG command input; wardrobe is a core
pillar; music acts as a key in the world. The AI tooling is a tool and may not set direction.

**The shipping gates are closed.** `runtime`, `save_load`, `repeat_consume`, `package_launch`
all have PASS rows. Several docs said otherwise and were six days stale — reconciled.
`static_gates` is still FAIL on two material drifts.

**What landed:**
- Governance rewritten across `PROJECT.md`, `README.md`, `_VERTICAL_SLICE_SCOPE.md`, `AGENTS.md`, `DOC_INDEX.md`
- [`Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`](Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md) — one OWNER per pillar, evidence-cited
- [`Docs/ORCHESTRA_CONTRACT_2026-08-20.md`](Docs/ORCHESTRA_CONTRACT_2026-08-20.md) — 7 seams; one violated, one unwired
- Six `orchestra` gates added to the Echo pipeline — all OPEN
- **Music-as-key adapter written** (`MelodiaPCGNarrativeChallengeBridgeComponent`) — **never compiled**
- **Wardrobe Resonant Form authored** (`form.first_resonance_echo` → Glide) — the money-pouch accessory
- Five local-model production lanes; the 60.35% benchmark was traced to a harness bug and fixed

**⚠ Do not start work without reading these two:**
1. [`Docs/MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md`](Docs/MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md) — `Speed`, `bIsGliding` and `bJumpWindup` are **never assigned** in `ABP_Melusina_Current`, so `Locomotion` and `Glide` are unreachable states. Melusina cannot walk from the state machine.
2. `BP_Melusina` has **no** `MelodiaWardrobeComponent` and **no** `MelodiaTraversalComponent`, and still uses `SK_Melusina` rather than the V2 body.

**Next session, in order:** close the editor and build → fix the `Speed` binding → add the two
components to `BP_Melusina` → PIE the full chain → only then record a gate.

**Standing rule learned this session:** MelodiaCore being quarantined does **not** mean everything
inside it is dead. Grep for callers before any DEAD verdict, and exclude `Intermediate/`.

---

## ♪ NOW (2026-08-20 00:30 ET)

### ♫ Nemotron × OpenCode × Unreal — Research Complete

♪ Research DONE — model lineup, OpenCode integration paths, Unreal public evidence.
♪ Experiments DESIGNED — Tasks 4–7 (harness compare, long-context, MCP surface, background agent).
♪ Spec: `specs/nemotron_experiment_harness.json` (on main).

**Decision gate:** Run Phase 0–2 (OpenRouter smoke → T1/T4/T5 on Claude vs Nemotron Super) before committing to Ultra or long-context tests.

> ♪ **Do not use Nemotron Ultra via NIM in OpenCode** until #34026 fixed. OpenRouter only.

### ♫ T3D Pipeline — RESTORED ♪

♪ T3D tools (`t3d_safe_wire.py`, `t3d_*.py`) are ACTIVE and CURRENT.
♪ Moved back from `Tools/_Archive/T3D_20260818/` — that archive was wrong.
♪ 9-step immutable wiring gate is the sanctioned path for Blueprint/C++ mutation.
♪ `PIPELINE_CONSOLINE_GROUND_RULES` claim of T3D retirement is **WRONG** — ignore it.

---

## ♪ Three Active Tracks (2026-08-20)

### 1. ♫ Gameplay Vertical Slice — "First Dream"

```
L_MelusinaMorning
  ♪ sanctuary conversation (QuillScript) — WORKED
    ♪ authored departure gate
      ♪ short dream traversal
        ♪ L_KaleidoNave — stock JRPG + Harmonix rhythm
          ♪ typed terminal result
            ♪ narrative consequence + idempotent social stat
              ♪ canonical save
```

| System | Status | Evidence |
|--------|--------|----------|
| QuillScript | ♪ WORKED | `QUILLSCRIPT_LOCKED_2026-08-12.md` |
| Rhythm highway | ♪ WORKED | `RHYTHM_GAME_LOCKED_2026-08-12.md` |
| PIE runtime input | ♪ PASS | `gate_ledger.json` 2026-08-13 |
| Stock JRPG battle | ◻ BROKEN | Morning → KaleidoNave open |
| P0 economy | ◻ IN PROGRESS | `P0_TASK_LEDGER.json` — 9 tasks open |
| T3D gate | ♪ EXPANDING | `t3d_safe_wire.py` active |

### 2. ♪ Melodia MCP + Agent Harness (MATH)

♪ 1330 typed MCP actions across 24 namespaces.
♪ 3-tier model routing: Hermes 8B → LongCat 14B → Cloud frontier.
♪ Per-model evidence in `Saved/Audit/math_run_models_latest.json`.

### 3. ♪ Echo Pipeline

♪ `static_gates` PASS · `runtime` PASS · `save_load` PASS · `repeat_consume` PASS · `package_launch` PASS.
♪ 37 ledger rows. No row = not done.

---

## ♪ Career Pipeline (Aug 2026)

| Studio | Lane | Draft | Deadline |
|--------|------|-------|----------|
| Nous Research | Agent / Fwd Deployed Eng | ♪ Gmail draft | Rolling |
| Infold Games | Campus 2027 Art & Design | ♪ Template ready | Oct 31 |
| NVIDIA | DevRel Higher Ed | ♪ Research drafted | Aug 21 |
| Certain Affinity | Sr Adv Tech Artist | ♪ Ready | Rolling |
| Velan Studios | Tech Artist Sr+/Lead | ♪ Ready | Rolling |
| Cohere | Agent Engineer | ♪ Gmail draft | — |
| AgenTao | Agent Engineer | ♪ Gmail draft | — |
| GameDevAgents | Agent Engineer | ♪ Gmail draft | — |
| Autor | Agent Systems | ♪ Gmail draft | — |
| Rulelet | Modular UE5 Logic | ♪ Gmail draft | — |

---

## ♪ Project Health (2026-08-20)

```
Assets:        22,143 .uasset
Maps:          210 .umap
C++ Source:    137 files
Python Tools:  151 files
JSON Specs:    87 schemas
Plugins:       15 active
Commits:       40 (main)
```

### ♫ Plugin Roster

| Plugin | Status |
|--------|--------|
| Monolith | ♪ Compiled — live MCP bridge |
| MelodiaCore | ♪ Compiled — battle, narrative, persona |
| MelodiaWardrobe | ♪ Compiled — cosmetic + gacha |
| QuillScript | ♪ WORKED |
| UEBlueprintMCP | ♪ Compiled — Blueprint TCP |
| MeshBlend | ♪ Compiled |
| KawaiiPhysics | ♪ Active |
| VRM4U | ♪ Active |
| PCGExtendedToolkit | ♪ Active |
| Oceanology | ◻ Disabled in .uproject |
| MelodiaTokenWallet | ◻ Scaffolded |

---

## ♪ PC State (2026-08-20)

♪ Temp files cleared (~50K deleted).
♪ Thumbnail cache cleared.
♪ Recycle Bin cleared.
♪ Windows Update cache cleared.
♪ VSIX/JetBrains/cursor debris removed.
◻ **UE Build crashed** — RHI.dll GPU driver issue. Fix: use `RunUAT.bat` not direct `UnrealEditor-Cmd.exe`.
◻ **Restart required** — run `shutdown /r /t 30` yourself (agent blocked).

---

## ♪ Quick Links

```
♪ README               → README.md (this repo's front page)
♪ Session history      → _SESSION_HANDOFF.md (this file)
♪ Task queue           → _TASK_QUEUE.md
♪ Vertical slice scope → _VERTICAL_SLICE_SCOPE.md
♪ Architecture map     → PIPELINE.md
♪ Blender cockpit      → Docs/BLENDER_MELODIA_COCKPIT.md
♪ Onboarding           → Docs/ENVIRONMENT_RUNBOOK_2026-08-11.md
♪ Career drafts        → Docs/Career/STUDIO_*.md
♪ Nemotron plan        → Docs/Handoffs/NEMOTRON_OPENCODE_UE_RESEARCH_2026-08-19.md
♪ Gate ledger          → Saved/gate_ledger.json
♪ Math evidence        → Saved/Audit/math_run_models_latest.json
```

---

## ♪ Previous Sessions (condensed)

### 2026-08-19 (Nemotron research)
♪ Nemotron lineup researched, OpenCode integration paths mapped.
♪ Ultra 550B broken via NIM (#34026), use OpenRouter only.
♪ 7 experiments designed — harness, long-context, MCP surface, background agent.

### 2026-08-13 ~23:36 (UE idle apply)
♪ T1/T2/T3 landed in PID 38184.
♪ Cathedral 41/41 under `/Game/EnvSandbox/Meshes/Cathedral/`.
♪ KaleidoNave `CathedralKit_Review` (8 pieces) **unsaved**.

### 2026-08-12 ~23:20 (Website & Security)
♪ 100% AI purge, CSP headers, 232 hex errors resolved.
♪ Figma UI suite integrated. `npm run verify:all` PASSED.

### 2026-08-12 ~22:53 (Live 5.2 MCP)
♪ Blender 5.2 PID 27644, MCP 9876, v22 open, **not saved**.
♪ 165 builders, 12/12 sections, 165 section trees.

### 2026-08-12 ~20:40 (Continuation)
♪ Handpainted hunt done (1208 hits).
♪ Cathedral kit = 41 FBX, 0 uassets.
♪ `assign_hero_zentrim.py` inventory written.

### 2026-08-12 evening (Rhythm + Quill LOCKED)
♪ ✧ RHYTHM + QUILLSCRIPT WORKED ✧ — tell the family.
♪ Do not reopen either as unverified.

### 2026-08-12 evening (Source control)
♪ `main` @ `43d0a9ae`, playable route levels now tracked.
♪ `static_gates` moved PASS · 12 material drifts accepted.
♪ LFS budget funded (~$10 ≈ 50 GB).

---

## ♪ Owner-Locked Systems

```
✧ RHYTHM GAME — WORKED (owner "yes")
✧ QUILLSCRIPT — WORKED (owner "yes")
✧ Do not reopen either as unverified.
```

---

## ♪ STOP Flags (ACTIVE)

| Flag | Meaning |
|------|---------|
| `MELUSINA_SHADER_AGENT_STOP` | No Melusina shader/world/stage saves by agents |
| `sheet_hud_loop_STOP` | No HUD sheet loop modifications |

---

## ♪ Evidence Standard

> **No row = not done.** Every claim in this document links to a capture artifact, a gate ledger row, or a run JSON. Prose is not evidence.

```
Ledger: Saved/gate_ledger.json
Math:   Saved/Audit/math_run_models_latest.json
T3D:    Saved/T3D/
Audit:  Saved/Audit/
```

---

## ♪ Get Running (Post-Restart)

```bash
# 1. Pull latest
git pull origin main
git lfs pull

# 2. Open project (DO NOT use UnrealEditor-Cmd.exe for builds)
start BS_GodFile.uproject

# 3. Verify gates
python Tools/project_state.py --view integration

# 4. Run static gate suite
python Tools/run_contract_tests.py --json

# 5. Check T3D wiring
python Tools/t3d_safe_wire.py --help
```

---

♪ **Ledger rule:** No row = not done.
♪ **T3D is alive:** `t3d_safe_wire.py` is current and operational.
♪ **Evidence over prose:** Link every claim.

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧  ┊ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```
