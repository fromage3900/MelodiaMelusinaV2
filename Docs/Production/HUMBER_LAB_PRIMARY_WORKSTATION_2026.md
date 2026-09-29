# Humber Lab Primary Workstation + Home Render Worker — Fall 2026

**Status:** ACTIVE SEMESTER WORKFLOW  
**Primary interactive workstation:** authorized Humber lab PC during class/lab sessions  
**Secondary interactive workstation:** ASUS Nitro laptop  
**Dedicated long-job worker:** home Windows workstation  
**Git baseline:** protected `main`; "Humber is primary" refers to the machine role, not permission to bypass branch/PR discipline.

## 1. Semester topology

The Fall 2026 workflow deliberately separates high-attention authoring from long-running compute:

```text
HUMBER LAB — PRIMARY INTERACTIVE
UE 5.8 / Rider / Blender / Houdini where available
composition · modeling · animation · materials · PIE · reviews
        │
        │ commit / push explicit job inputs
        ▼
origin/main or short-lived task branch
        │
        ├──────────────► HOME PC — RENDER / BAKE WORKER
        │                Cycles · MRQ shots · bakes · batch jobs · long tests
        │
        └──────────────► LAPTOP — AUXILIARY
                         docs · Blender batches · Rider · validation · spare render chunks
```

The home PC is not the place you must physically sit to make progress. It is the machine that keeps working after the artistic decision has already been made.

## 2. What stays on the Humber workstation

Prefer the lab for work requiring fast human feedback:

- Unreal level dressing and composition;
- lighting iteration;
- Sequencer editing;
- character animation / mocap cleanup;
- material authoring and visual tuning;
- Blender modeling and Geometry Nodes iteration;
- Houdini graph authoring where installed and permitted;
- Rider / C++ inspection;
- PIE gameplay validation;
- capture review and art direction;
- assembling render queues / job manifests.

Avoid tying up the lab machine with hours of final rendering while you still need to work.

## 3. What goes to the home PC

Queue work that is expensive but does not need constant supervision:

- Blender Cycles animation frame ranges;
- Blender stills at final samples;
- texture / geometry bakes;
- Alembic / cache exports;
- Unreal Movie Render Queue shots;
- high-resolution image sequences;
- long packaged-build checks;
- long contract/test batches;
- video transcodes / proxy creation;
- deterministic procedural batch exports.

The worker should consume an explicit job and produce an explicit output. It should never invent project changes while acting as a render node.

## 4. Distribution rules

### Blender

Blender can split a single animation by frame range because background rendering accepts explicit start/end frames.

Example:

```text
Home PC       0001–0180
Laptop        0181–0240
Humber        interactive preview only
```

or, when the lab machine is temporarily free:

```text
Home PC       0001–0120
Laptop        0121–0180
Humber        0181–0240
```

Final frame chunks must use identical committed scene inputs and render settings.

### Unreal MRQ

Distribute by complete **camera cut / Level Sequence shot**, not arbitrary frame ranges.

Example:

```text
Home PC       SQ_Shorewake_Quay
Home PC       SQ_Starskiff_Departure
Laptop        SQ_ReefChoir
Humber        authoring / previews
```

Unreal temporal rendering depends on prior-frame history, so a shot is the smallest safe farm unit.

## 5. Source-control contract

### Before starting at Humber

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\humber_lab_bootstrap.ps1 -Mode Prepare -IConfirmAuthorizedUse
```

The normal synchronization target is `origin/main`. After the machine is synchronized, create/use a **small task branch** for actual authored changes when the task is more than a trivial doc-only correction.

### Sending work home

1. Save and close binary assets that are being handed off.
2. Run the workstation sync check.
3. Commit the exact source changes needed for the render.
4. Push them.
5. Create the render command/job manifest.
6. Home PC pulls the same commit.
7. Home PC renders; it does not edit authoring assets during the job.

### Returning outputs

Render outputs stay outside Git by default:

`Saved/RenderFarm/<job>/`

Curated final images/videos are deliberately promoted later into the portfolio/evidence location.

## 6. HumberSemester hydration profile

The school machine should hydrate only the active semester surface:

- Melusina character assets;
- First Dream / Shorewake route maps;
- MelodiaIntegration;
- Sea Above / Kaleido Nave content used by the route;
- current battle proof;
- material masters / toon profiles;
- current Chapter 02 assets.

Do not hydrate the entire historical binary workspace unless an assignment actually needs it.

## 7. Lab-machine policy boundary

Humber digital resources are for academic/research purposes and excessive resource use is prohibited. This workflow therefore assumes:

- you are actively authorized to use the lab machine/session;
- no network scanning or worker discovery;
- no hidden services;
- no leaving persistent jobs after your authorized session ends;
- no bypassing software/license/admin restrictions;
- final renders should preferentially move to the home PC when they would monopolize a lab machine.

The lab is the primary **workstation**, not an unauthorized permanent server.

## 8. Home worker command

Use the generic render worker:

```powershell
# Inspect capabilities
.\deploy\render_worker.ps1 -Mode Probe

# Blender frame chunk
.\deploy\render_worker.ps1 -Mode Blender `
  -BlendFile "C:\path\shorewake.blend" `
  -StartFrame 1 -EndFrame 180 `
  -JobName "shorewake_departure_A" `
  -IConfirmAuthorizedUse -Execute

# Unreal MRQ shot
.\deploy\render_worker.ps1 -Mode UnrealMRQ `
  -Map "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype" `
  -LevelSequence "/Game/Cinematics/Shorewake/SQ_Starskiff_Departure.SQ_Starskiff_Departure" `
  -MoviePipelineConfig "/Game/Cinematics/MRQ/MRQ_SemesterFinal.MRQ_SemesterFinal" `
  -JobName "shorewake_starskiff_final" `
  -IConfirmAuthorizedUse -Execute
```

The script records the Git commit and machine name with every render job.

## 9. Daily rhythm

### At Humber

- sync;
- make high-value artistic decisions;
- create / refine assets;
- test interactively;
- prepare render jobs;
- commit/push before leaving.

### At home

- sync the committed job input;
- launch final render / bake / batch;
- review output;
- only return to authoring when a result requires a creative change.

The objective is to eliminate the pattern where the strongest PC sits idle while the artist is away, or the artist sits idle while the strongest PC renders.

## 10. Semester success metric

A lab session is high-efficiency when it ends with both:

1. a visible improvement authored during the session; and
2. at least one long job ready for the home PC to execute.

That turns one school day into two overlapping production lanes rather than a serial workflow.

## 11. Cline execution contract — Humber Git + P4 sync

**Primary command:** `deploy/sync_humber_project.ps1`. This is now the canonical orchestrator; use the detailed gates below only to diagnose a failed run.

Cline should first run:

    .\deploy\sync_humber_project.ps1 -Mode Check

Then, for an actual synchronization:

    .\deploy\sync_humber_project.ps1 -Mode Sync -P4Port "<PRIVATE_HOME_HOST>:1666" -P4User "<P4_USER>" -ApplyP4

If P4V or the shell already has P4PORT/P4USER configured, the explicit P4Port/P4User arguments may be omitted. The script reuses those settings, creates a machine-specific Humber client, verifies the P4 ownership exclusion for Content/Python, previews all three creative roots, and only then applies the depot sync.

This is the executable handoff for a coding agent working on an authorized Humber lab machine.

### Objective

Bring the Humber workstation to the safest available project state without destroying local work or inventing a new source-control topology.

Mandatory order:

1. establish a healthy Git checkout;
2. synchronize to origin/main;
3. hydrate only the HumberSemester Git LFS profile;
4. inspect local workstation/tool readiness;
5. test whether the home Perforce service is privately reachable;
6. only if that private route passes, create/use a distinct Humber P4 client and preview its sync;
7. perform the P4 sync only after the preview is clean and ownership exclusions are correct.

### Hard safety rules

Cline must STOP instead of improvising if any gate fails.

Do not run destructive Git cleanup/reset/rebase operations, git add -A, p4 reconcile, p4 submit, p4 unshelve, broad writable-bit changes, or any public exposure of the P4 port. Do not bypass Humber admin/security restrictions.

Do not reuse the home workstation client Melodia_ws on the Humber PC. Every machine gets its own P4 client root.

### Gate A — recover or create the Git checkout

If a usable clone already exists, do not reclone it. Run:

    git status --short
    git remote -v
    git branch --show-current
    git rev-parse HEAD
    git lfs version

If the checkout is dirty, HOLD and report the exact files.

If there is no usable checkout, use a partial clone with LFS smudging disabled so the lab machine does not download the historical binary universe during clone:

    $env:GIT_LFS_SKIP_SMUDGE = "1"
    git clone --filter=blob:none --no-checkout https://github.com/fromage3900/MelodiaMelusinaV2.git C:\MelodiaMelusinaV2
    cd C:\MelodiaMelusinaV2
    git sparse-checkout init --cone
    git sparse-checkout set .github Config Docs Plugins Source Tools deploy specs BS_GodFile.uproject Content/Python Content/Melodia/Levels Content/Melodia/PCG Content/MelodiaIntegration Content/Characters Content/Melodia/Characters Content/TurnBasedJRPGTemplate/Blueprints/Battle Content/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns Content/EnvSandbox/Environments Content/EnvSandbox/PCG Content/EnvSandbox/Monoliths/SeaAbove Content/EnvSandbox/Materials/Masters Content/EnvSandbox/Materials/ToonProfiles
    git checkout main
    git lfs install
    git config core.hooksPath .githooks

If authentication, pack transfer, long paths, disk space, or school-network policy blocks the clone, HOLD and report the exact command plus final error lines. Do not keep retrying random clone strategies.

### Gate B — Humber bootstrap check

From the repository root:

    powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\humber_lab_bootstrap.ps1 -Mode Check

Expected reports:

    Saved/Workstation/<machine>-humber-lab.json
    Saved/Workstation/<machine>-workstation-report.json

Required before Prepare:

- Git available;
- Git LFS available;
- origin resolves to fromage3900/MelodiaMelusinaV2;
- worktree clean;
- enough free disk exists for the semester slice.

### Gate C — Git + semester hydration

When Gate B is clean and the user is in an authorized Humber session:

    powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\humber_lab_bootstrap.ps1 -Mode Prepare -IConfirmAuthorizedUse

This delegates to:

    .\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile HumberSemester

PASS requires:

- branch = main;
- sync state = synced;
- ahead/behind = 0 / 0 against origin/main;
- no dirty files created by synchronization;
- HumberSemester LFS pull reports success.

If any fail, HOLD before opening Unreal.

### Gate D — P4 client/tool readiness

The current production references use depot //Melodia and the home workstation talks to its local p4d at 127.0.0.1:1666.

That address is not valid from Humber.

Inspect only:

    Get-Command p4 -ErrorAction SilentlyContinue
    p4 -V
    p4 set

If p4 is unavailable, P4 remains HOLD while Git/LFS may still be usable.

A private route to the home machine is required before P4 sync. Use only an owner-approved private VPN/tunnel already permitted on the lab machine. Never expose TCP 1666 publicly.

Once a private home address/name is known:

    Test-NetConnection <PRIVATE_HOME_HOST> -Port 1666

If this fails, STOP: P4 transport is not ready. Do not point P4V at localhost and do not guess another public endpoint.

### Gate E — authenticate to remote P4

Only after Gate D passes:

    p4 set P4PORT=<PRIVATE_HOME_HOST>:1666
    p4 set P4USER=<OWNER_P4_USER>
    p4 info -s
    p4 login -s
    p4 changes -m 1 //Melodia/...

If the ticket is missing/expired, the owner performs the normal login interactively. Cline must not store credentials in Git, docs, scripts, or logs.

### Gate F — distinct Humber workspace

Create a machine-specific client name:

    $Client = "Melodia_Humber_$env:COMPUTERNAME"
    p4 set P4CLIENT=$Client
    p4 client -o $Client

The client root should be the same local project root used by Git.

The effective view must honor the ownership contract:

    //Melodia/Content/...            //<HUMBER_CLIENT>/Content/...
    -//Melodia/Content/Python/...    //<HUMBER_CLIENT>/Content/Python/...
    //Melodia/Exports/...            //<HUMBER_CLIENT>/Exports/...
    //Melodia/RawArt/...             //<HUMBER_CLIENT>/RawArt/...
    -//Melodia/RawArt/MelusinaArcherHarp/ME_WaveHarp_Rev08_UEAxisRibbonFix.blend //<HUMBER_CLIENT>/RawArt/MelusinaArcherHarp/ME_WaveHarp_Rev08_UEAxisRibbonFix.blend

Content/Python remains Git-owned and must stay excluded from P4. The standalone Rev08 WaveHarp handoff is also an explicit Git-LFS exception inside RawArt; larger source-art files in RawArt remain Perforce-owned.

Verify before sync:

    p4 client -o $Client
    p4 where //Melodia/Content/...
    p4 where //Melodia/Content/Python/...
    p4 where //Melodia/RawArt/MelusinaArcherHarp/ME_WaveHarp_Rev08_UEAxisRibbonFix.blend

Content/Python and the standalone Rev08 WaveHarp handoff must resolve as excluded/unmapped.

### Gate G — preview before P4 sync

Never make the first Humber P4 operation a blind sync.

Preview:

    p4 sync -n //Melodia/Content/...
    p4 sync -n //Melodia/Exports/...
    p4 sync -n //Melodia/RawArt/...

Review for unexpected deletes, paths outside creative roots, Content/Python, collisions with dirty local files, or an unexpectedly huge historical payload.

If anything is suspicious, HOLD and show the preview summary to the owner.

If the preview is clean and the owner approves:

    p4 sync //Melodia/Content/...
    p4 sync //Melodia/Exports/...
    p4 sync //Melodia/RawArt/...

### Important current limitation

A Humber sync from depot head does not prove that every latest home-machine creative edit is remotely available.

The current repository state records intentional held/open Perforce work plus a shelved changelist in addition to depot state. Do not submit, unshelve, or reconcile those merely to make Humber match.

Truthful readiness states:

- Git/main: ready through the existing Humber bootstrap and workstation sync tooling.
- Git LFS HumberSemester: ready to attempt once the clone is healthy.
- P4 client tooling: ready if P4 CLI/P4V exists on the lab machine.
- P4 remote transport: HOLD until private connectivity to home p4d is proven.
- Latest held home P4 edits: not automatically part of a depot-head Humber sync.

### Cline completion report

Cline finishes by reporting this checklist with command evidence:

    [ ] Git checkout healthy
    [ ] origin points to fromage3900/MelodiaMelusinaV2
    [ ] main == origin/main
    [ ] worktree clean
    [ ] Git LFS available
    [ ] HumberSemester hydration succeeded
    [ ] Humber workstation report generated
    [ ] P4 CLI available
    [ ] private home P4 route reachable
    [ ] P4 login valid
    [ ] unique Humber P4 client configured
    [ ] Content/Python excluded from P4
    [ ] p4 sync preview clean
    [ ] depot-head P4 sync completed
    [ ] no held/shelved owner work was mutated

If the P4 network gate is unavailable, the correct result is a successful Git/LFS setup plus an explicit P4 HOLD, not an improvised workaround.

