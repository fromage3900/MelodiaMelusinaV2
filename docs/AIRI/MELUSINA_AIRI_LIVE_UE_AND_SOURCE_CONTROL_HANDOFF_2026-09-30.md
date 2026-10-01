# Melusina ↔ AIRI: live UE and source-control handoff

**Purpose:** owner-run execution plan for finishing the lightweight Melusina AIRI embodiment and bringing AIRI into day-to-day Unreal and repository work.

**Status authority:** [`CURRENT_STATE.md`](../../CURRENT_STATE.md) remains the only live status record. This file is a plan and handoff, not proof that any gate has passed. Update the status record only when fresh evidence exists.

## Read these first

- [`MELUSINA_AIRI_ARCHITECTURE.md`](MELUSINA_AIRI_ARCHITECTURE.md) — ownership boundaries and integration design.
- [`MELUSINA_AIRI_PROTOCOL.md`](MELUSINA_AIRI_PROTOCOL.md) — v1 envelopes, allowlists, limits, and endpoints.
- [`MELUSINA_AIRI_P0_STATUS.md`](MELUSINA_AIRI_P0_STATUS.md) — acceptance criteria and outstanding runtime proof.
- [`BRANCH_WORKSTATION_POLICY.md`](../Production/BRANCH_WORKSTATION_POLICY.md) — current main-only and Git-operation rules.
- [`RIDER_UE58_CANONICAL_WORKFLOW.md`](../Production/RIDER_UE58_CANONICAL_WORKFLOW.md) — native UE build/debug path.

The older P0 plan and original pasted request mention a feature branch. The current project policy supersedes that: continue in the existing local `main` checkout, preserve its work, and do not create a branch, worktree, or PR.

## Working model

Keep three capabilities separate:

1. **AIRI companion:** conversation, voice, vision, and a lightweight VRM presentation. AIRI's selected Qwen model can reason and propose; its conversational memory is not Melodia canon.
2. **Game bridge:** Unreal sends bounded semantic context; AIRI may return only a validated `melusina.emote` diagnostic intent in P0. Unreal, Jev, and authored systems retain game authority.
3. **AIRI workbench:** a future, local, least-privilege observer/proposal surface for UE and Git/P4 work. It is not part of the game protocol and must not expose arbitrary shell, filesystem, console, Blueprint, reflection, or source-control execution.

The immediate useful version is **observer → proposal → owner executes**. Any later write tool must preview the exact paths and operation, then require the owner's explicit approval for that exact operation. AIRI must never infer approval from a conversation about the task.

## What exists, and what it proves

| Area | Present evidence | Still required |
|---|---|---|
| UE ↔ AIRI bridge | Versioned loopback relay and UE subsystem; `melodia.world.location` is the only UE event currently emitted. Only `melusina.emote` is accepted, into debug state. | A real local AIRI session, PIE event delivery, intent return, and offline PIE proof. P0 remains **PARTIAL** until these pass. |
| AIRI identity | Generated card and manifest under `Docs/AIRI/MelusinaCard/Generated/`; canonical source documents are recorded by hash in the card. | Import/inspect the card in the current AIRI desktop build; regenerate after canon edits rather than editing the projection by hand. |
| VRM | A local derived avatar exists outside the project checkout. The latest headless scale audit measured 2.125 m overall, 1.988 m for the body mesh, and armature scale 1.0. No production stature target was established and no rescale was made. | Compare against the canonical UE body in a measured scene; inspect eyes/lashes, shirt textures, sleeve/glove placement, materials, facial expressions, and retarget map in AIRI. |
| Live tracking | Project has Rokoko and Cascadeur source/import paths to inspect. | Prove the OBSBot Meet2 feed is accepted by the chosen tracker and yields usable body/face data before building an animation route. A camera feed alone is not a validated rig stream. |
| Repository state | Read-only Git status at handoff authoring showed local `main` at `origin/main` **ahead 24 / behind 1**, with many pre-existing modifications and untracked files. | Re-read `CURRENT_STATE.md` and `git status` before every work session. This snapshot is not permission to sync, stage, commit, clean, or reconcile anything. |

The avatar audit and AIRI source experiments live in the separate Codex task workspace, not as canonical project assets. Preserve that source; promote only reviewed outputs through the normal project asset lane. The prior AIRI source checkout's focused test run was blocked by missing workspace dependencies; lint reported no errors but five existing warnings. Do not describe that as a passing test/build gate.

## Owner execution sequence

### 0. Establish the live work window

- Read the current top of `CURRENT_STATE.md`, then inspect `git status --short --branch`, the active UE editor PID/map, current Monolith ownership, and any open Perforce work before touching assets.
- Work only in the existing `main` checkout. Keep one Unreal editor and one Monolith writer; do not open a second MCP/editor automation surface against the same project.
- The checkout was already dirty when this handoff was written. Classify existing work from current evidence; do not blanket-stage, reset, stash, clean, fetch, merge, or submit it.
- Do not close/restart the live editor, change maps, or build while it is open. Schedule a closed-editor build only when the editor owner has released that lane.

### 1. Normalize and approve the AIRI avatar

- Keep the production UE hero mesh/rig untouched. Work on the derived Blender/VRM source only.
- Establish the target stature from the canonical UE character in a known metric scene. Compare feet, head top, eye line, and arm span; do not choose a scale from appearance alone. Apply any correction at the derived export/root stage, then record the resulting measured height and transform.
- Resolve the export report discrepancy: the Blender build log reports more assigned humanoid bones than the exported round-trip report, which lists only 15. Verify the actual VRM humanoid mapping, especially shoulders, chest, eyes, and fingers, in the consuming runtime.
- Inspect front/side/back views and facial expressions. Confirm shirt albedo/normal/roughness assignments, sleeve and glove bind/weights at rest and in a relaxed pose, eye geometry, lashes, blink, and mouth shapes. The current body source was reported without eye geometry, so locate the approved eye source or mark that feature blocked; do not claim it is present by inference.
- Open the candidate in AIRI desktop and capture a clean visual receipt at normal pet scale and close-up. Promote the VRM only after scale, materials, silhouette, and face checks pass.

### 2. Prove the camera-to-animation path

- Inventory the installed OBSBot camera driver and the current Rokoko/Cascadeur/Blender versions and import scripts. Record the exact tool versions and the camera device name.
- First prove stable camera capture in the selected tracker. Then prove that tracker produces the required body pose and, if desired, face/expression channels in a format the existing retarget path can consume. If it does not, select a compatible capture/tracking method before writing integration code.
- Keep the route offline and reviewable: camera capture → tracked pose → Blender cleanup/retarget → Cascadeur polish when useful → guarded existing UE import route. Do not write directly into the canonical ABP or production animation assets during calibration.
- Validate a short neutral motion, shoulder/hand reach, turn, and seated/standing transitions. Compare root scale, axes, floor contact, shoulder alignment, and hand reach; retain source capture, retarget settings, and a preview.

### 3. Bring up the existing P0 bridge in PIE

- Re-check the local AIRI install and its current Server SDK/module endpoint. Keep credentials in the local environment only; never paste AIRI tokens into logs, receipts, prompts, or Git.
- Start the existing relay on loopback (`127.0.0.1:8765`) and verify `/v1/health`. Confirm the AIRI connection is ready before starting the test.
- In an owner-approved session, run the existing UE build and PIE flow for `L_MelusinaMorning` with `-MelodiaAiriBridge`. If that map/editor lane is not available, stop and resolve the current asset/editor gate rather than substituting a different production map silently.
- Verify in order: UE emits `melodia.world.location`; AIRI receives it as transient context; an ordinary AIRI conversation produces one supported ACT emotion marker; the relay queues it; UE validates it and updates only its debug field.
- Repeat with AIRI and relay absent. PIE must start and continue without a wait, crash, save change, or gameplay change. Record these as separate live receipts. A build or relay unit test alone does not pass this gate.

### 4. Expand game context one owner seam at a time

After the P0 round trip and offline case pass, wire only useful semantic values from their existing owners. Suggested order: `world.phase`, `melusina.state`, `instrument.active`, `rhythm.combo`, then `sir_melodious.distance`. Several are schema/validator-only today; schema presence is not implementation. Add one event, validate payload/limits, and prove both delivery and offline behavior before adding another.

Keep `melusina.emote` diagnostic-only. `speak`, `look_at`, `gesture`, combat, narrative, save, actor-property, and console actions remain out of the bridge until an owner-defined deterministic gate and separate runtime acceptance exist.

### 5. Start using AIRI for UE and source-control work

Build an AIRI workbench as a separate, local capability with these initial tools only:

- `project.status`: summarize current branch, dirty/staged/untracked counts, and editor/P4 ownership signals.
- `project.diff`: show a diff only for caller-specified paths; redact secrets and large binary payloads.
- `project.context`: retrieve named, bounded sections of `CURRENT_STATE.md` and the relevant AIRI contract.
- `ue.status`: read current editor/map/session and existing test/build receipts through the already-approved owner surface.
- `ue.propose`: return a human-readable proposed change with exact assets/files, owner seam, risk, and verification gate. It does not execute.

Reuse the project's existing Git, Perforce, Rider, and single Monolith workflows. Do not give the model a general terminal, arbitrary MCP tool routing, file-write, or free-form Unreal console tool. Keep game events (`melodia.*`) separate from developer/workbench data.

For each proposed source-control batch, AIRI should show: exact paths, Git vs P4 ownership, current diff summary, why the files belong together, ignored/LFS considerations, and the exact command it proposes. The owner reviews the diff and requests each mutating operation explicitly. Never use `git add -A` or blanket `p4 reconcile`; do not stage, commit, push, fetch, merge, rebase, reset, stash, clean, delete refs, or submit a P4 changelist without an exact owner request. The present main checkout's ahead/behind and dirty state make this inventory the first task, not a commit batch.

## Acceptance gates and receipts

Keep the proof levels distinct in `CURRENT_STATE.md`:

1. **Avatar source:** measured VRM scale, material/face checklist, mapped humanoid bones, and AIRI desktop capture.
2. **Tracking:** named camera/tracker versions, raw sample, retarget settings, preview, and contact/axis review.
3. **Bridge source/build:** focused protocol evidence and a closed-editor UE 5.8 build when authorized.
4. **Live UE:** actual PIE context arrival, validated debug intent, and separate AIRI-offline run.
5. **Workbench:** read-only Git/P4/UE output compared with the tools of record; later write operations proven only under exact owner approval and path-scoped receipts.

Do not promote scaffolding, schema coverage, static checks, or a headless avatar audit into live AIRI/UE proof. Keep the final `MELUSINA_AIRI_P0_STATUS.md` status at **PARTIAL** until its live round-trip and offline criteria are freshly satisfied.

## First session checklist

- [ ] Read current `CURRENT_STATE.md`; confirm the editor, Monolith, Git, and P4 owners.
- [ ] Inspect AIRI desktop and the existing VRM without changing the hero asset.
- [ ] Establish the target UE stature and close the VRM face/clothing/bone-map questions.
- [ ] Prove OBSBot capture through a compatible tracker before retarget work.
- [ ] Run the existing P0 live and offline PIE gates in an owner-approved window.
- [ ] Start the AIRI workbench in read-only proposal mode; compare outputs against Git/P4/Monolith directly.
- [ ] Update `CURRENT_STATE.md` with only the receipts actually earned. Leave source-control mutation for a separately explicit owner instruction.
