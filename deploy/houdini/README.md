# Melodia Houdini Studio — package contract

Operational contract for the repo-backed Houdini plugin scaffolded for **Gate 0A**
(2026-10-07). This file records how the package behaves and must keep behaving.

It is **not** a status board. Current status, evidence level, and what is still
owed live in `CURRENT_STATE.md`. Session narrative lives in the commit body.

## Layout

```text
deploy/houdini/
  packages/melodia_studio.json      committed package definition (path-independent)
  melodia_studio/                   content added to HOUDINI_PATH
    desktop/Melodia_Studio.desk     Blender-like daily authoring desktop
    desktop/Melodia_KineFX.desk     character / AnimationDoctor desktop
    toolbar/Melodia.shelf           8-tool launcher shelf + melodia_shelf_set
    scripts/python/melodia_studio/  project / evidence / launch helpers
  install_melodia_studio.ps1        activate and deactivate
  verify_melodia_studio.py          headless proof, run through hython
  README.md                         this file
```

## Use

```powershell
.\deploy\houdini\install_melodia_studio.ps1 -Verify    # activate + prove
.\deploy\houdini\install_melodia_studio.ps1 -CheckOnly # report, write nothing
.\deploy\houdini\install_melodia_studio.ps1 -Remove    # deactivate cleanly
```

Verification alone, once installed:

```powershell
hython deploy\houdini\verify_melodia_studio.py
```

## How activation works

Two layers, deliberately separated:

1. **Committed** `packages/melodia_studio.json` — path-independent. Everything
   it declares is expressed with `$HOUDINI_PACKAGE_PATH`, so it resolves to the
   repository no matter which drive or folder holds the checkout. It declares
   the `MELODIA_*` environment variables and the `hpath` entry that puts the
   plugin content on `HOUDINI_PATH`. This is the single source of truth.
2. **Machine-local** `<houdini user pref>/packages/melodia_studio_local.json`
   holding exactly one key:
   `{"package_path": "<repo>/deploy/houdini/packages"}`.

The installer resolves the repository root from its own location, so it works
from any checkout. Nothing machine-local is committed, and no committed file
contains a drive letter, user name, or Houdini install path.

## Invariants — do not break

- **Never edit `houdini.env`.** Activation is the pointer file, nothing else.
- **No machine-local paths in committed files** under `deploy/houdini/`.
  `verify_melodia_studio.py` fails on this and scans `.py`, `.json`, `.desk`,
  `.shelf`, `.ps1` and `.md`.
- **Do not overwrite Houdini's factory desktops** (`Build`, `KineFX`, …). Ours
  are additional desktops, saved under our own names.
- **Names are cross-referenced by the verifier**: shelf name `melodia`, shelf
  set `melodia_shelf_set`, tool ids `melodia_*`, desktops `Melodia_Studio` and
  `Melodia_KineFX`. Changing one requires changing all three.
- **Icons stay factory-confirmed names only** (`MISC_generic`, `SOP_object_merge`,
  `SOP_group`, `CHOP_network`, `SHOP_material`, `MISC_python`, `CHOP_file`,
  `MISC_present`).
- **Shelf tools stay thin**: one `melodia_studio.launch('<key>')` call each.
  Behaviour lives in the module so it can be tested headless. A tool must never
  mutate Unreal, launch processes, or write anywhere except `Saved/Audit/`.

## Reuse on a new machine, or after the repo moves

The pointer is machine-local, so it goes stale when you clone fresh, change the
repo's drive letter, or upgrade Houdini (new user-pref directory). Re-run the
installer. `-Verify`'s `pointer_installed` check reports the exact mismatch, so
a dead pointer is diagnosed rather than silently leaving the package unloaded.
Nothing else needs redoing — the committed package is path-independent.

To deactivate (for example on a machine without the repo), `-Remove` deletes
only a pointer whose content still points at this repository's package
directory. Anything else is left untouched.

## Local desktop overrides — the one silent hazard

Houdini's **Save Current Desktop** writes to `<user pref>/desktop/`. Such a file
shadows the repository `.desk` on the next launch, so later repo improvements
stop appearing while everything looks fine.

The verifier warns (`desk_local_override`) when a local copy exists. Fix it by
deleting the local file, or by promoting its content back into
`deploy/houdini/melodia_studio/desktop/` after scrubbing machine-local paths.

If a save lands in the repository instead, `no_machine_paths` fails the
verification, so neither route corrupts the repo silently.

## Evidence receipts

Verifier output is written to `Saved/Audit/houdini_studio/*.json`. Receipts
record one run on one machine and therefore contain that machine's real paths —
they are **evidence, never configuration**. Never copy a value out of a receipt
into a committed file.

## Verification boundary

Headless verification proves: pointer resolution, `MELODIA_*` environment,
`HOUDINI_PATH` entry, desktop discovery, shelf and all eight tools, module
import, tool launch, `.desk` structural syntax, shelf/shelf-set cross
reference, and absence of machine-local paths.

It deliberately does **not** prove that the desktops look right, switch, or
survive reload — that is GUI acceptance and remains owner-held.
