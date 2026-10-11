# Melusina P0 — Runtime Animation & Retarget Convergence
**Plan date:** 2026-10-09 | **Owner:** Brennan | **Repo:** `fromage3900/MelodiaMelusinaV2` | **Target:** smallest proven, visually correct P0 overworld animation set

## Mission
Audit actual **runtime references**, identify duplicates/broken/stale animation sequences, retargeters, IK rigs, skeletons and Animation Blueprint transitions, fix defects in the canonical graph, and archive **only confirmed unreferenced** old paths reversibly. One runtime pose authority. This is **not** a new rig, locomotion framework, or blanket asset deletion.

**Recommended frontier:** GPT-6 Sol / existing runtime specialist session, because context is critical and the graph is integration-sensitive; a single Claude Sonnet 5.5 reviewer is an optional *targeted* second opinion for a captured pose defect, not a parallel editor writer. **Recon scout:** DeepSeek V4.1 Flash for static reference inventory + P4/G: status. Reserve deep/expensive reasoning for a concrete graph or pose contradiction.

## Canonical authority (must read FIRST)
- `Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md` **wins over older guides**. Target `SK_Melusina_Skeleton`, runtime `ABP_Melusina_Current`; no second pose authority; canonical idle is **CuteIdle V10**, not the old mocap reference clip.
- Correct retarget recipe: batch retarget without `overwrite=true` (known crash), copy `arm_stretch_l/r` and `forearm_stretch_l/r` translations from `A_Melusina_Idle_Mocap_RootX` to *all target frames*, sample world-space shoulder/arm/hand chain, then `save_asset` EACH output. Preserve owner-approved data.
- Canon document's reference-pose test: correct arm chain ~15.774 / 28.561 / 28.615 cm, known-defective ~34.789 / 9.520 / 28.615. Validate with actual editor API on affected clips rather than assuming these historical readings remain current.
- **Frozen/do-not-modify without owner approval:** canonical skeleton, six approved SparrowArchery source clips, WaveHarp keys. Older doc says Sparrow archer draw had remaining arm pop at LMB/RMB mode boundary. Treat as **investigate**, not assert it is still broken.
- Keep working `IK_Melusina_Body_Current` and `IK_UE4Mannequin_Source`. Existing archived retarget paths and intentional legacy assets must NOT be reactivated.
- `CURRENT_STATE.md` opening October 5 block says gameplay WASD/bow/damage already work. Do not waste a frontier session re-proving unrelated old blockers.
- Existing tools: `Content/Python/audit_melusina_gameplay_animation_chain.py`, `Content/Python/melusina_animation_doctor.py` and `Saved/Audit/melusina_animation_doctor/README.md`; test their outputs for staleness against live graph.

## Stage M0 — cheap static inventory, zero modifications
1. Gather exact local/remote `main` SHA, branch, dirty changes, `refs/agents/*`, worktrees, relevant P4 opens and **content ownership**. `G:` / P4 is not visible to the GitHub authoring connection.
2. Traverse **actual runtime roots**: player/character BP mesh and AnimClass, `ABP_Melusina_Current` state machine and slot nodes, C++/BP montages / variables, component overrides, input triggers, cinematic references that share assets. Enumerate paths and redirectors through UE AssetRegistry *read-only* if a local editor is available; otherwise label incomplete.
3. Write dependency table `ASSET | TYPE | TARGET_SK | REFERENCED_BY | CURRENT_RUNTIME_PATH? | CANON? | DUPLICATE_CONTENT_HASH? | STATUS | CONFIDENCE | PROPOSED_ACTION`. Classify `KEEP`, `FIX IN PLACE/COPY`, `ARCHIVED ALREADY`, `CANDIDATE QUARANTINE`, `UNKNOWN`. Names alone are **not** duplicate evidence; compare actual content/curves, skeleton and refs.
4. Produce `Saved/Audit/melusina_p0_anim_20261009/recon.json` + `handoff.md` with the top 3 graph defects and specific call stacks/node refs. NO delete, rename, redirector fix-up, asset-save or P4 submit at this stage.

## Stage M1 — bounded P0 whitelist and visual graph
- Resolve a *minimal* **P0 overworld** graph from actual mechanics, not asset folder titles:
  - **Required when used:** canonical idle; directional locomotion + start/stop/turn; sprint/dash; jump/fall/land if P0 traversal exercises it.
  - **Hybrid instrument combat must remain intact:** LMB caster stance/release using floating astrolabe; RMB+LMB charged archer draw/hold/fire using bow form. Upper-body layered slot must not replace legs.
  - Hit react / death / interaction/cutscene clip are retained **only if active P0 flow references them**. Leave film/cinematic assets alone if they are separate consumers.
- Compare graph state players, transitions, animation loops and montage slot hierarchy to canon. The UpperBody layer mask must include spine chain and both full arm chains; ensure the 11 filters in canon are present. FootPlacement/KawaiiPhysics/blink/eye CopyBone must remain if actively used.
- Expose a single runtime truth table: input/state → BP entry → slot → clip → skeleton → expected contact/pose. Highlight anything missing or shadowed.

## Stage M2 — repair, prove, and *then* quarantine
1. Fix only verified animation routing faults (wrong asset references, stale idle/walk state, broken loops, inconsistent skeleton, invalid montage slot, retarget translation pose defect). Never rebuild whole ABP.
2. For the six **frozen** SparrowArchery clips, produce **corrected copies in a new isolated folder** only with owner approval, compare pose metrics and staged RMB preview before swapping references. Do not mutate the originals.
3. Inspect duplicates project-wide (UE AssetRegistry hard/soft references, redirects, sequencer, BP/C++ soft paths, P4 and LFS). If a supposed duplicate is referenced elsewhere or not conclusively identical: KEEP and mark. If truly obsolete: propose reversible `_Archive` movement **using UE asset operations** (not OS file moves), resolve redirectors, compile/save then PIE, and leave original/source backups and a move manifest. Actual archive/deletion still needs explicit owner approval.
4. No mass delete, no `Fix Up Redirectors` across the full project, no canonical skeleton swap, no unreviewed retargeter removal.

## Stage M3 — P0 visual acceptance ladder
- In one editor-owner session run PIE and capture consistent camera angles: idle 3 sec → WASD travel + stop/turn → dash/jump if used → **LMB caster** release → **RMB aim+LMB** draw/hold/fire → recovery to idle → packaged/restart smoke if quick and already configured.
- Capture at least 3 diagnostic pose phases at the caster↔archer boundary; quantify the left/right arm-chain translations against §1 canon, and inspect face/torso, foot plant and cloth intersections. File a known defect rather than masking with a second AnimBP.
- Confirm no missing montage, deformation pop, upper-body animation suppression, T-pose, locomotion leg hijack, transient frame issue, or restart-only default clip. Log exact tested assets and build/branch refs.
- **Acceptance:** canonical SK and ABP remain sole game-runtime owners; P0 graph references only active, justified animations; duplicate inventory audited with safe disposition; observed P0 playback shows stable poses; no unrelated content changed. Package concise PASS/FAIL matrix, screenshots/clip and a reversible diff.

## Stage M4 — limited integration
- Commit scripts/docs or explicitly approved asset changes in an isolated branch/worktree and target the current `origin/main` with Echo gates; avoid working directly on live editor-owned main. Preserve P4 ownership and owner-reserved assets.
- If read-only sweep finds no runtime defects, the win is a **verified slim whitelist and an archival proposal**, NOT gratuitous deletion. Backlog P1–P3 animations separately.

## Cost / concurrency contract (all lanes)

1. **Flash read-only reconnaissance, then frontier intervention.** Use DeepSeek V4.1 Flash (`deepseek-flash`) or an already-paid low-cost model. Bound reconnaissance to 1 repo search + 1 local filesystem inventory + 1 targeted report; max ~15 tool invocations; no binary mutation, UE editor launch, shader rebuilding, file deletion, P4 submit, or commits. Cap output to 1-2 pages and machine-readable candidate files. Do not dump whole logs or old plans into the frontier model's context.
2. Hand the expensive agent: (a) current head SHA + branch/worktree, (b) `git status --short` and P4 opens when relevant, (c) exact absolute paths *as locally observed*, (d) authoritative references / conflicts, (e) prioritized defects with evidence and confidence, (f) exact next runnable commands and rollback path. Mark **UNKNOWN** rather than inventing data.
3. Only one writer per `.blend` or UE `.uasset` / level at a time. Work on a new generation or isolated worktree / `refs/agents/<lane>`; never overwrite an open scene, force-push, merge another agent's branch, bulk-delete assets, or submit unrelated P4 changelists.
4. Run bounded **inventory → one fix → test → evidence → next fix**. Two unsuccessful attempts on the same issue trigger a documented blocker and owner review, not a token-expensive loop. Restrict frontier context to the current lane's evidence packet and relevant files.
5. CI/headless checks establish structure only; *visual* success requires inspected images / video and *UE* gameplay success requires actual editor/PIE playback where specified. Never report success from a manifest alone.
6. `G:` is local storage, not accessible through this GitHub-only plan authoring session. The local reconnaissance agent must resolve G: against its own running machine and report `unavailable` if not mounted. Never confuse a GitHub snapshot with current disk or P4 state.

## Frontier handoff prompt
> Perform one bounded P0 Melusina runtime animation convergence session, not a redesign. Treat `Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md` as higher authority than any old plan. Consume the Flash static inventory, validate live AnimBP references and P0 whitelist, fix only proven broken paths, and run PIE evidence for idle/locomotion/caster/archer return-to-idle. Preserve SK_Melusina_Skeleton, ABP_Melusina_Current and frozen Sparrow source clips. Do not mass-delete or auto-archive. Return a keep/fix/quarantine matrix with before/after evidence and required owner approvals.

## Boundary
The film repo's rig and the ANMN301 Shorewake animatic are separate output projects. Do not use those to justify changes to the game runtime graph.
