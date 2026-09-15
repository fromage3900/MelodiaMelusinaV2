# Outline Jitter — Deep Research & Investigation Plan

> **For Hermes:** research first, no MI/PPV writes until a hypothesis wins a viewport A/B.

**Goal:** Find why L_MelusinaMorning ink still crawls after the FXAA verdict went live, and fix it once with evidence.

**Architecture:** Eliminate hypotheses in order of cheapness — live-method proof, full-inkwell audit, shader-core A/B — with the owner's viewport as the only beauty gate.

**Tech Stack:** UE 5.8, Monolith MCP (read-only until decided), Python log/query harnesses, committed audit JSON.

---

## 1. Settled ground (do not re-litigate without new evidence)

- 2026-09-14 verdict: fullscreen depth-edge ink shimmers under temporal AA; FXAA holds still. Sir = stencil 4 hero ward. MelodiaInk 4-param sane reset.
- 2026-09-15 findings: the committed `r.DefaultFeature.AntiAliasing=1` sat under `[/Script/Engine.RendererSettings]` where `r.*` cvars never load — the project booted TSR all along. Fixed in 276ed580 (line now under `[ConsoleVariables]`), console FXAA fired live, boot log shows `r.DefaultFeature.AntiAliasing:1` queued at startup. Editor relaunched, Monolith serving.
- Morning PPV (`PPV_NikkiDream`, actor `.../6/2U/SXESN1EMPQO4ZW3Q2U4IED.uasset`) blends ONLY the frozen four: `MI_StorybookOutline_Frozen`, `MI_MelodiaInk_Frozen`, `MI_MeluColorGrade_Frozen`, `MI_StarryNight_Frozen`. No Hero/Gameplay garbage in the blendable list. No AA override strings in the PPV actor. Scalability sets qualities only, never the method.
- Disk state: frozen outline + ink MIs currently hold master-true values (15/15 verified by re-read, saved, dirty count 0). Pre-change (12:12 hand) values are recorded in session chat and restorable in one go. Morning map + touched actors UNCOMMITTED. Greybox toon conversion QUEUED, untouched.

## 2. Hypotheses, cheapest first

- H1: The live viewport is still on a temporal method. FXAA fired via console pre-restart; post-restart proof is one boot-log line (`deferred dummy`). If the deferred value never applied to the real cvar, or PIE/editor-viewport scalability overrides the method, nothing else matters.
- H2: Pattern swim in the V7.1 frozen core. `Docs/Plans/OUTLINE_FINALIZATION_2026-09-14.md` §V7.3: with JitterCompensation=1 the tap rotation and paper-grain hash read JITTERED uvC — the pattern itself swims every frame. V7.3 (uvSnap hashing) exists, compiled, saved, NEVER made live. FXAA cannot cure shader-core swim; it only removes buffer jitter.
- H3: A second inkwell still crawls. MelodiaInk/StarryNight/grade all blend fullscreen. Audit already flagged: StarryNight VanGogh MD_SURFACE drop, grade weight 0.18 vs 0.69 mismatch, MelodiaInk custom node 42-declared/38-wired. Any one of these can read as fullscreen shimmer misattributed to the edge shader.
- H4: Stencil membership drift. If Sir (or a new Morning actor from the 12:13–12:43 hand edits) lost stencil 4, it takes default ink; fullscreen impression if the actor is large/close.
- H5: Inverted distance fade. Live frozen MI carries DistanceFadeStart=4000 / End=2537 (end < start). Master defaults for these two were never pulled. An inverted fade can pop ink bands with camera motion.
- H6: Scene variance, not ink. The 09-14 shimmer-metric experiment was NEGATIVE (clean run shimmered most). Sky/Lumen/sheep-idle can dominate full-frame diffs.

## 3. Investigation tracks

### Task 1: Prove the live method on the fresh boot

**Objective:** Read back the actual AA method in the running editor, no guessing.

**Files:** none (read-only queries).

**Step 1:** Send `r.AntiAliasingMethod` via `editor_query run_console_command`, then pull `search_logs pattern=AntiAliasing` AND `tail_log lines=100`; look for the Cmd echo value line, not just the command receipt.
**Step 2:** If no value echoes, run editor Python to read it: `editor_query run_python` with a snippet that finds the console variable and prints `get_int()`. (Read-only; never touch skill-blueprint assets from Python — this snippet touches no assets.)
**Step 3:** Record the value + boot timestamp into `Saved/Audit/outline_method_proof_2026-09-15.json` (allowed path per pre-commit allowlist).
**Decide:** method==1 → H1 dead, move to Task 3. method!=1 → fix the delivery (cvar name/shelf/scalability), re-verify, then viewport check before anything else.

### Task 2: Audit the whole inkwell live vs masters

**Objective:** Every fullscreen blendable's live overrides next to its master default, one table.

**Files:** read-only; output `Saved/Audit/outline_inkwell_audit_2026-09-15.json`.

**Step 1:** `material_query get_material_parameters` for all four live frozen MIs + their four frozen masters (8 calls; batch pattern already proven this session).
**Step 2:** Diff each pair; flag |delta| beyond float noise, plus known-garbage shapes (density/band/light/angle extremes, negative jitter, inverted start/end).
**Step 3:** Same pass for stencil: `mesh get_actor_info` (or component query) on Morning Sir actor + any actor touched 12:13–12:43 today; confirm stencil value 4 where the hero ward applies.
**Decide:** any drifted fullscreen param → viewport A/B (sane vs drifted) before writing. No drift → H3/H4 dead, move to Task 3.

### Task 3: V7.1 vs V7.3 viewport A/B at the portfolio camera

**Objective:** Settle H2 with eyes, not theory.

**Files:** `Docs/Plans/OUTLINE_FINALIZATION_2026-09-14.md` (protocol), candidates under `Content/EnvSandbox/Materials/PostProcess/Candidates/` (read-only until decision).

**Step 1:** Owner opens `CAM_MelusinaMorning_Portfolio`, holds the frame; agent takes NO captures as evidence (byte-unreliable) — owner narrates still vs crawl for: (a) current frozen V7.1, (b) V7.3 proto swap (one reversible blendable swap, kill-switch documented in the doc).
**Step 2:** If V7.3 stills the ink → promote per doc's remaining freeze rites (swap, save map, hash row). If both crawl → H2 dead; escalate to H5/H6 (fade inversion, then scene-variance isolation: hide sheep/sky lanes one at a time in viewport).
**Rule:** one blendable swap at a time, reversible, map saved only after owner calls it.

### Task 4: Harden so it never drifts again

**Objective:** Slider garbage fails loudly instead of shipping silently.

**Files:** lookdev audit tool + `Docs/Plans/OUTLINE_FINALIZATION_2026-09-14.md` (value-range guard proposal).

**Step 1:** Add min/max guard per outline param from the doc's measured-profiles table (master-true ± art intent).
**Step 2:** Commit the guard + the audit JSONs from Tasks 1–2.
**Step 3:** Canonical commit of the Morning set (map + touched external actors + frozen MIs) with `git add -f` (no .gitignore edit needed); message documents MI values + revert offer. Only when the editor is at rest — the 12:43 PPV touch today is a live-hand warning.

## 4. Validation

- Beauty gate: owner eyes at `CAM_MelusinaMorning_Portfolio`, still vs crawl. Agent captures never count.
- Data gates: method value in audit JSON; 8-way param diff committed; swap decision + rationale in the freeze doc.
- Frame-honesty rule holds: byte-identical frames = cached/black, reported not hidden.

## 5. Risks and standing rules

- No MI/PPV/map writes until a hypothesis wins (owner: STOP WORRYING ABOUT THE MIs).
- One editor holder; never commit mid-edit (12:43 touch); verify saves via re-read + `list_dirty_packages`, never via `success:true`.
- Protected files (`Config/*.ini`, `.gitignore`) need `SKIP_PROTECTION=1` + cited owner approval per change.
- Never touch `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python (fatal enum glue bug).
- Showcase freeze: outline stability is approved render work; no redesigns, no new capture frameworks.
- Open threads behind this plan: Greybox 11-mat toon conversion (queued), my 15-param MI reset (on disk, revertible), Morning canonical commit (waiting editor at rest).
