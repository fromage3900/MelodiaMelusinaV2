# START HERE — Humber Houdini Finishing Day — 2026-10-07

**Use this file first. Do not begin by reading the whole Foundry backlog.**

Today's bounded goal is:
1. recover/open yesterday's *working local* AnimationDoctor session from the synced project/SSD;
2. prove one Melusina regression;
3. extend the same diagnostic idea to Sir Melodious;
4. use the already-staged Shorewake outfit for one Vellum/finishing proof;
5. stop before architecture expansion.

Companion plan:
`Docs/Houdini/MELODIA_ANIMATION_OUTFIT_FINISHING_CONVERGENCE_2026-10-07.md`

The larger studio/world convergence plan is background only today:
`Docs/Houdini/MELODIA_HOUDINI_STUDIO_CONVERGENCE_2026-10-07.md`

---

## 0. Truth discovered by the 2026-10-07 repo audit

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

# 1. Ten-minute bootstrap

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

---

# 2. Recover yesterday's AnimationDoctor — 10 minute cap

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

# 3. First proof before new work

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

# 4. Sir Melodious source selection

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

# 5. Shorewake source selection

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

# 6. Copernicus dependency probe

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

# 7. Today's minimal order

Do these in this order:

1. **Bootstrap** — repo + license, max 10 minutes.
2. **Recover yesterday's Doctor** — max 10 minutes.
3. **Regression** — one Melusina clip.
4. **Sir** — one v5 ARP clip through avian diagnostics/polish.
5. **Shorewake** — one hero-skirt Vellum canary.
6. **Copernicus** — use existing Tidepool fields first; regenerate only if dependency-clean.
7. **UE** — only if the above are green and there is time.
8. **Workspace/shelf beautification** — last, not first.

Do **not** make a custom Houdini desktop the prerequisite for productive work today. A portable package/shelf is valuable, but today it is P3 polish after the working local pipeline has been recovered.

---

# 8. What Muse should report after bootstrap

One compact block only:

```text
ROOT:
LOCAL HEAD:
ORIGIN MAIN:
HOUDINI VERSION:
HEADLESS LICENSE:
GUI LICENSE:
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

# 9. Git/artifact caution

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
- Muse finds or conclusively fails to find yesterday's actual Doctor;
- one Melusina regression is run if found;
- the exact Sir v5 source is selected;
- the exact Shorewake source set is located;
- no time is lost rebuilding old scripts, fixing OSC ports, or beautifying the Houdini UI.

Only then execute the three-phase finishing plan.
