# START HERE — Humber Houdini Finishing Day — 2026-10-07

**Use this file first. Do not begin by reading the whole Foundry backlog.**

Today's bounded goal is:
1. **install/activate the repo-backed Melodia Houdini Studio package and save the Blender-like working desktop first;**
2. recover/open yesterday's *working local* AnimationDoctor session from the synced project/SSD;
3. prove one Melusina regression;
4. extend the same diagnostic idea to Sir Melodious;
5. use the already-staged Shorewake outfit for one Vellum/finishing proof;
6. stop before architecture expansion.

Companion plan:
`Docs/Houdini/MELODIA_ANIMATION_OUTFIT_FINISHING_CONVERGENCE_2026-10-07.md`

The larger studio/world convergence plan is background only today:
`Docs/Houdini/MELODIA_HOUDINI_STUDIO_CONVERGENCE_2026-10-07.md`

---

## 0. Truth discovered by the 2026-10-07 repo audit

### Houdini studio setup

Git currently has **no project-authored Houdini package, desktop, or shelf framework** for Melodia. The existing convergence plan describes one, but repo search found no `HOUDINI_PACKAGE_DIR`, project package JSON, `.desk`, or Melodia `.shelf` implementation.

Therefore the first productive task at Humber is to create a **portable, repo-backed Melodia Houdini Studio plugin/setup** and make Houdini feel closer to the Blender workflow before asking Muse to do hours of KineFX/Vellum work.

Use SideFX's package system rather than editing `houdini.env`. Keep the repo copy authoritative and make the school-machine install a thin local pointer to it.

### AnimationDoctor

Git currently contains the **specification/front door only**:
- `START_HERE_HOUDINI_2026-10-06.md`
- `Docs/Houdini/FoundryDay_2026-09-24/README.md`

Git does **not** currently contain:
- `HDA_Melodia_AnimationDoctor*.hda`;
- a tracked AnimationDoctor `.hip`;
- a tracked 2026-10-06 AnimationDoctor PASS receipt.

The owner reports the pipeline worked yesterday and synchronized the working state to the portable `G:` project/SSD. Therefore **local G: state is the recovery source for yesterday's actual Houdini work; Git is the architecture/spec source.**

Do not rebuild the HDA from the prose until local recovery has been attempted.

### Sir Melodious

Do not start from the old v3 Houdini probe. The tracked Sir plan records that `hython_kinefx_probe.py` was staged locally when Houdini licensing was blocked, but the script itself is not in Git.

The useful current source-of-truth for Sir is:
`Saved/Audit/SirMelodious_FlightUnit_20261003/PLAN.md`

Important current handoff from that plan:
- canonical/runtime Sir work has advanced beyond v3;
- v5 ARP work is the newest described source family;
- feather chains, head-lock and crest/tie work already exist;
- do not accidentally regress to the 126-bone pre-crest source merely because an old P2 paragraph is easier to find.

### Shorewake

Do not start from the historical Aug-30/31 48MAT transform lane.

Runtime contract:
`specs/wardrobe/wardrobe_shorewake_manifest.v1.json`
currently points at:
`/Game/Melodia/Characters/Melusina/Textures/Clothes/Retargeted/SK_ShorewakeDress_Melusina465`

Relevant source/evidence:
- `Saved/Audit/melusina_lookdev/retargeted/SK_ShorewakeDress_Melusina465.fbx`
- `Saved/CANONICALSHOREWAKEOUTFITWEIGHTEDUNWRAPPED.usdc` when present locally
- `Docs/Production/CANONICAL_SHOREWAKE_SUBSTANCE_STAGING_PIPELINE_2026-09-02.md`
- `Docs/Art/UNIVERSAL_GARMENT_FABRIC_DRAPERY_2026-09-02.md`
- `Saved/Audit/copernicus_cymatic/ShorewakeTidepool/` when present locally

Prove local existence and identity before sim.

### Copernicus warning

`Tools/Houdini/copernicus/copernicus_dress_bake.py` is tracked, but Foundry intake records that it imports the untracked/missing-on-clean-clone `reef_common.py`.

Therefore:
- if `reef_common.py` exists on the synced G: project, record its path/hash and the lane may be used;
- if absent, **do not burn the session repairing the historical dress baker**;
- use the already-baked ShorewakeTidepool resources for today's look/VFX canary, or use a self-contained tracked Copernicus lane that passes a dependency probe.

---

# 1. Two-minute preflight — only enough to launch the studio setup

## 1A — find the repo, do not assume the lab's drive letter

In PowerShell:

```powershell
$root = $null
try {
  $root = (git rev-parse --show-toplevel 2>$null).Trim()
} catch {}

if (-not $root -and (Test-Path 'G:\EnvironmentPortfolio\BS_GodFile')) {
  Set-Location 'G:\EnvironmentPortfolio\BS_GodFile'
  $root = (git rev-parse --show-toplevel 2>$null).Trim()
}

if (-not $root) {
  throw 'Melodia repo not found. Mount the synced SSD/project before doing Houdini work.'
}

$env:MELODIA_ROOT = $root
Set-Location $root
Write-Host "MELODIA_ROOT=$env:MELODIA_ROOT"
```

Do not copy project files into a random Documents folder just to make Houdini happy.

## 1B — Git safety

```powershell
git fetch origin
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
```

Rules:
- if clean and simply behind `origin/main`, use `git pull --ff-only`;
- if there are local changes, **do not reset/clean/stash automatically**;
- record the local SHA and `origin/main` SHA;
- today's generated caches remain outside Git.

## 1C — Houdini/license probe

```powershell
Get-Command houdini,hython,hserver -ErrorAction SilentlyContinue
hython -c "import hou; print('Houdini', hou.applicationVersionString())"
hserver -l
```

If `hython` cannot acquire the Education licence but the GUI can:
- use the GUI;
- record `HEADLESS_LICENSE_BLOCKED_GUI_OK`;
- do **not** spend more than 10 minutes debugging license plumbing.

Full-license GUI success is enough for today's Vellum/KineFX work.

Do not begin Doctor/Shorewake discovery yet. Launch the studio setup next.

---

# 2. FIRST PRODUCTIVE TASK — Melodia Houdini Studio package + Blender-like desktop

**Timebox: 20–30 minutes. This is not optional setup debt; it is the working environment for the rest of the day.**

## 2A — canonical repo-backed plugin layout

Muse should scaffold this exact shape unless a concrete SideFX constraint requires a tiny adjustment:

```text
deploy/houdini/
  packages/
    melodia_studio.json
  melodia_studio/
    desktop/
      Melodia_Studio.desk
      Melodia_KineFX.desk
    toolbar/
      Melodia.shelf
    scripts/
      python/
        melodia_studio/
          __init__.py
          project.py
          evidence.py
    python_panels/        # optional today
    viewer_states/        # optional today
  install_melodia_studio.ps1
```

The install script must:
1. resolve the current repo root dynamically;
2. resolve the active Houdini user-pref directory;
3. write/copy only a thin local package pointer into the user's Houdini `packages` folder;
4. point `HOUDINI_PATH`/package `hpath` at the repo-backed `deploy/houdini/melodia_studio` content;
5. expose convenience variables such as `MELODIA_ROOT`, `MELODIA_HDA_ROOT`, `MELODIA_AUDIT_ROOT`, and `MELODIA_CACHE_ROOT`;
6. leave `houdini.env` untouched;
7. be idempotent and safe to rerun on another Humber PC.

Do not hardcode `C:`, `G:`, a username, or the Humber machine name into the committed package.

## 2B — desktop 1: `Melodia_Studio` (Blender-like daily authoring)

The layout should preserve Blender muscle memory while keeping Houdini's Network Editor one click away:

```text
┌───────────────────────────────────┬───────────────┐
│                                   │ Scene/Tree    │
│          SCENE VIEW               ├───────────────┤
│          ~65-70% visual focus     │ PARAMETERS    │
│                                   │               │
├───────────────────────────────────┼───────────────┤
│ NETWORK EDITOR                    │ tabs:         │
│ wide, shallow, easy to maximize   │ Geo Sheet /   │
│                                   │ Python Shell  │
└───────────────────────────────────┴───────────────┘
```

Goals:
- Scene View is the visual center, like Blender's 3D Viewport.
- Scene/Tree behaves as the Outliner analogue.
- Parameters stay in a stable right-hand column, like Blender Properties.
- Network Editor lives in the lower work strip and can be maximized instantly.
- Geometry Spreadsheet and Python Shell exist as tabs, not permanent visual clutter.
- dark, uncluttered viewport; useful grid/axis; no diagnostic overlays by default.
- save the desktop as `Melodia_Studio`, do not overwrite Houdini's factory Build desktop.

## 2C — desktop 2: `Melodia_KineFX`

For AnimationDoctor/character days:

```text
┌──────────────────────────┬────────────────────────┐
│                          │ NETWORK EDITOR         │
│       SCENE VIEW         │ KineFX graph           │
│                          ├────────────────────────┤
│                          │ PARAMETERS             │
├──────────────────────────┴────────────────────────┤
│ Animation Editor / MotionClip / diagnostic tabs  │
└───────────────────────────────────────────────────┘
```

Keep source/target skeleton comparison visually large. Geometry Spreadsheet and Python Shell remain tabs.

## 2D — first Melodia shelf

Create a small shelf that calls repo-backed helpers rather than embedding giant one-off scripts:

- **Project** — show `MELODIA_ROOT`, current HIP, current Git SHA when available.
- **AnimationDoctor** — locate/open the recovered Doctor artifact/session.
- **Shorewake** — locate current runtime FBX, canonical USD and Tidepool assets.
- **Vellum Cache** — open/create today's local cache root.
- **Copernicus** — dependency probe + open relevant current scene/tool.
- **Foundry Validate** — call the existing Foundry validator, no duplicate validator.
- **Evidence** — open today's `Saved/Audit/houdini_foundry/` target.
- **UE Handoff** — reveal/export handoff location only; do not mutate UE automatically.

The shelf is a launcher/navigation surface, **not a new authority**.

## 2E — day-one hotkeys

Do **not** spend the morning remapping all of Houdini to Blender.

For today:
- preserve Houdini's context-sensitive transform/network hotkeys;
- adjust only navigation/frame-selected behavior if the user actually finds it disruptive;
- save any hotkey override separately from the plugin and document it;
- no global `G/R/S/Tab` rewrite on day one.

## 2F — setup acceptance

Before touching AnimationDoctor, prove:
- Package Browser / Houdini path can see the Melodia plugin content.
- `Melodia_Studio` desktop survives desktop switch/reload.
- `Melodia_KineFX` desktop survives switch/reload.
- Melodia shelf appears and at least **Project**, **Evidence**, and **AnimationDoctor** launch without path errors.
- screenshot both desktops.
- write a tiny setup manifest with Houdini version, package path, repo root, and desktop names.

Only then continue.

---

# 3. Recover yesterday's AnimationDoctor — 10 minute cap

Search the likely local project locations first:

```powershell
$roots = @(
  "$env:MELODIA_ROOT\hda",
  "$env:MELODIA_ROOT\Houdini",
  "$env:MELODIA_ROOT\Saved\HoudiniFoundry",
  "$env:MELODIA_ROOT\Saved\Audit\houdini_foundry"
) | Where-Object { Test-Path $_ }

Get-ChildItem $roots -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Name -match 'AnimationDoctor|AnimDoctor' -or
    (($_.Extension -in '.hip','.hiplc','.hipnc','.hda','.hdalc','.hdanc') -and
     $_.LastWriteTime -gt (Get-Date).AddDays(-3))
  } |
  Sort-Object LastWriteTime -Descending |
  Select-Object LastWriteTime,Length,FullName
```

If nothing useful appears, do one broader SSD search only:

```powershell
if (Test-Path 'G:\EnvironmentPortfolio') {
  Get-ChildItem 'G:\EnvironmentPortfolio' -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
      $_.Name -match 'AnimationDoctor|AnimDoctor' -or
      (($_.Extension -in '.hip','.hiplc','.hipnc','.hda','.hdalc','.hdanc') -and
       $_.LastWriteTime -gt (Get-Date).AddDays(-2))
    } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 50 LastWriteTime,Length,FullName
}
```

### Recovery decision

**A — HDA + HIP found**
- open the newest plausible yesterday session;
- do not install/rename it globally yet;
- save a new today's working HIP under local scratch;
- run the exact clip that worked yesterday as a regression.

**B — HIP found, no HDA**
- open the HIP;
- inspect whether the Doctor network is embedded/subnetted;
- use that exact network today;
- packaging as an HDA is a later task, not a bootstrap blocker.

**C — HDA found, no HIP**
- install it for the session from its local path;
- create a tiny scratch HIP;
- run yesterday's specimen.

**D — neither exists after 10 minutes**
- STOP searching.
- Record `ANIM_DOCTOR_LOCAL_ARTIFACT_MISSING`.
- Do not reconstruct a new canonical HDA from docs.
- Continue useful work with Shorewake Vellum/Copernicus or Sir source inspection while a separate recovery task resolves yesterday's local artifact.

---

# 4. First proof before new work

Before Sir or Shorewake, rerun **one known-good Melusina specimen** through the recovered Doctor.

Minimum evidence:
- source/target loaded;
- REST report visible;
- ROOT trail visible;
- CONTACT markers visible;
- JOINT HEALTH produces a ranked result;
- output/report writes to a *new* today's folder.

Suggested evidence root:

`Saved/Audit/houdini_foundry/animation_doctor/2026-10-07_regression/`

Large geometry/caches:
`Saved/HoudiniFoundry/` or school scratch.

If the regression does not work, today's task is **recovery**, not feature expansion.

---

# 5. Sir Melodious source selection

Read only:
`Saved/Audit/SirMelodious_FlightUnit_20261003/PLAN.md`

Then locate the newest local v5 ARP artifacts described there before importing anything.

Prefer the current described v5 family when present:
- `arp/SirMelodious_ARP_CrestTie_v5.blend`
- `arp/SirMelodious_ARP_Clips_v5b.blend`
- `exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5.fbx`
- `exports/ue_arp/A_Sir_*_v5_ARP.fbx`
- `arp/arp_v5_verify.json`

Do not use the old `hython_kinefx_probe.py` as a prerequisite; it is not in Git.
Do not use the older 126-bone source merely because it is easy to locate.

Sir's first Houdini goal is diagnostic/polish only:
- import one v5 clip;
- map avian semantic groups;
- test wing/feather/head/crest health;
- add restrained Secondary Motion only after the raw clip passes rest/root checks.

No UE re-import is required to prove the Houdini pass.

---

# 6. Shorewake source selection

Run existence checks:

```powershell
$shorewake = @(
  "$env:MELODIA_ROOT\Saved\Audit\melusina_lookdev\retargeted\SK_ShorewakeDress_Melusina465.fbx",
  "$env:MELODIA_ROOT\Saved\CANONICALSHOREWAKEOUTFITWEIGHTEDUNWRAPPED.usdc",
  "$env:MELODIA_ROOT\Saved\Audit\copernicus_cymatic\ShorewakeTidepool"
)
$shorewake | ForEach-Object { [pscustomobject]@{Exists=(Test-Path $_); Path=$_} }
```

Use:
- runtime retargeted FBX as the current runtime identity/skinning reference;
- canonical weighted/unwrapped USD as the higher-fidelity garment source only when its relation to runtime is demonstrated;
- ShorewakeTidepool as existing material/field input.

Never silently substitute:
- `Shorewake_48MAT_frozen_snapshot.blend`;
- `SK_ShorewakeDress_Magical.fbx`;
- the superseded `dress_transform.py` result;
for the current runtime dress.

First Vellum canary:
- one short approved Melusina clip;
- hero outer skirt only;
- waistband pin;
- simple body collision proxy;
- 3 deterministic presets maximum;
- cache locally;
- no full 10-layer solve.

---

# 7. Copernicus dependency probe

Before calling the old dress baker:

```powershell
$reef = Get-ChildItem $env:MELODIA_ROOT -Recurse -File -Filter reef_common.py -ErrorAction SilentlyContinue |
  Select-Object -First 5 FullName,Length,LastWriteTime
$reef
```

If absent:
- do not use `copernicus_dress_bake.py` today;
- use existing ShorewakeTidepool outputs;
- or use a self-contained current Copernicus script after checking its imports.

Today's transformation canary does **not** require regenerating every Shorewake texture.

---

# 8. Today's minimal order

Do these in this order:

1. **Preflight** — locate repo + prove GUI licence, ~2 minutes.
2. **Melodia Houdini Studio** — install package, build/save Blender-like daily + KineFX desktops, verify shelf, 20–30 minutes.
3. **Recover yesterday's Doctor** — max 10 minutes.
4. **Regression** — one Melusina clip.
5. **Sir** — one v5 ARP clip through avian diagnostics/polish.
6. **Shorewake** — one hero-skirt Vellum canary.
7. **Copernicus** — use existing Tidepool fields first; regenerate only if dependency-clean.
8. **UE** — only if the above are green and there is time.

The custom desktop/package is deliberately first because the rest of today's work is interactive Houdini-heavy. Build the comfortable workstation once, then stay inside it.

---

# 9. What Muse should report after bootstrap

One compact block only:

```text
ROOT:
LOCAL HEAD:
ORIGIN MAIN:
HOUDINI VERSION:
HEADLESS LICENSE:
GUI LICENSE:
MELODIA PACKAGE:
MELODIA STUDIO DESKTOP:
MELODIA KINEFX DESKTOP:
MELODIA SHELF:
ANIMATION DOCTOR ARTIFACT:
ANIMATION DOCTOR TYPE: HDA | HIP | EMBEDDED | MISSING
YESTERDAY REGRESSION: PASS | FAIL | NOT RUN
SIR SOURCE SELECTED:
SHOREWAKE FBX:
SHOREWAKE CANONICAL USD:
SHOREWAKE TIDEPOOL:
REEF_COMMON:
NEXT GATE:
```

Do not write a research essay before returning this block.

---

# 10. Git/artifact caution

`Tools/*` and `Saved/` have ignore rules in this project. New source/evidence may not appear in normal `git status`.

Before claiming a new source file is tracked:

```powershell
git check-ignore -v <path>
git status --ignored --short
```

Use force-add only for intentional small source/evidence, never for caches.

Project-authored versioned HDAs belong under `hda/` and are LFS-routed, but **do not promote/rename yesterday's local AnimationDoctor during bootstrap**. First recover and prove it.

---

# Done for the first hour

The first hour succeeds if:
- the repo-backed Melodia Houdini package is installed/visible;
- both `Melodia_Studio` and `Melodia_KineFX` desktops are saved and reload correctly;
- the Melodia shelf launches at least Project/Evidence/AnimationDoctor without path errors;
- Muse finds or conclusively fails to find yesterday's actual Doctor;
- one Melusina regression is run if found;
- the exact Sir v5 source and Shorewake source set are selected;
- no time is lost rebuilding old scripts or fixing OSC ports.

Only then execute the three-phase finishing plan.
