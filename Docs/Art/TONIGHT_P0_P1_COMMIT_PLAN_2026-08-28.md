# Tonight P0/P1 Commit Execution Plan — 2026-08-28

This is the one-file entry point for working from another PC after the docs stack is merged.

## Start here

1. Pull `main`.
2. Read `Docs/Art/SEA_ABOVE_P0_BEAUTY_LOCK_TONIGHT_2026-08-28.md`.
3. Read `Docs/Art/SHOREWAKE_DRESS_P0_SHADER_COOKBOOK_2026-08-28.md`.
4. Read `Docs/Art/STARSKIFF_TONIGHT_FREE_SYSTEMS_AND_DOWNLOADS_2026-08-28.md`.
5. Only then begin Unreal implementation.

## Implementation commit plan

Keep implementation work isolated and reversible. Preferred order:

```text
feat(p0): lock Sea Above hero camera and false-horizon composition
feat(p0): add local Bell membrane pulse presentation
fx(p0): add restrained upward-droplet anomaly pass
art(shorewake): add painterly fabric material family
art(shorewake): add Second Horizon embroidery and sea-glass clasp
art(shorewake): add separate translucent hem and Tide Seam response
feat(starskiff): add minimal mountable pawn shell
feat(starskiff): add Oceanology adapter facade
feat(starskiff): add skim movement prototype
feat(starskiff): add authored Current Rail prototype
fx(starskiff): add prototype wake and rail response
```

## P0 gate before P1 feature work

Do not let Starskiff or P1 consume the night until these are true:

- shoreline hero camera is locked;
- real ocean / fog gap / false ocean / Bell layers read clearly;
- Bell perimeter is never visible;
- one Bell pulse communicates biological scale;
- Shorewake reads beautifully before magic;
- Shorewake wrong-gravity hem / Second Horizon response is subtle and legible;
- no new water authority, no new global framework, no Water V10 regression.

## Shorewake order for Claude / Rider agent

```text
Batch 1 — painterly opaque cloth
Batch 2 — Second Horizon gradient / embroidery
Batch 3 — separate translucent asymmetric hem
Batch 4 — seam-direction WPO
Batch 5 — sea-glass clasp + subtle rhythm
Batch 6 — Lite switches / compile-cost validation
```

The outfit should remain recognizably Melusina first and magical second.

## Starskiff order

Use Oceanology as the world-water source, but keep Melodia ownership behind:

```text
BP_Starskiff
BPC_StarskiffMovement
BPC_StarskiffOceanologyAdapter
BP_StarskiffRail
IMC_Starskiff
```

Do not spread Oceanology-specific calls across gameplay Blueprints. Do not import an old vehicle/buoyancy framework as a dependency tonight.

Optional public reference repos can be cloned outside the project with:

```powershell
powershell -ExecutionPolicy Bypass -File .\Tools\External\Download_Starskiff_References.ps1
```

They are references only, not dependencies.

## PC sync

After the documentation stack is merged to `main`:

```powershell
git status
git fetch origin
git switch main
git pull --ff-only origin main
```

If `git status` is not clean, do not discard local Unreal work just to pull. Commit/stash intentionally first.

## Tonight's definition of done

P0 should end with a player remembering five images:

```text
beautiful coast
→ tiny wrongness
→ Second Horizon
→ Bell breath
→ quiet impossible aftermath
```

P1 work earns time only after that sequence reads.