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
