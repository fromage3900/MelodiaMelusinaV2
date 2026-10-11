# Melodia Houdini Studio

Repo-backed Houdini 22 authoring surface for Melodia. The package exists to make the same shelves, Python helpers and saved desktops available on a Humber workstation, the portable project, or another Windows machine without committing machine-local paths.

## Install

From the repository root in PowerShell:

```powershell
.\deploy\houdini\install_melodia_studio.ps1 -Verify
```

The installer:

1. derives the repository root from its own path;
2. locates `hython.exe`;
3. asks Houdini for `hou.homeHoudiniDirectory()`;
4. writes one local pointer:
   `<Houdini user prefs>/packages/melodia_studio_local.json`;
5. points that file at this checkout's `deploy/houdini/packages` directory;
6. leaves `houdini.env` and unrelated package files untouched.

The committed package definition is `deploy/houdini/packages/melodia_studio.json`. It exposes the repo-backed `melodia_studio` HOUDINI_PATH root and the `MELODIA_*` convenience variables.

## Dry run / repair

See what the installer would do without writing:

```powershell
.\deploy\houdini\install_melodia_studio.ps1 -CheckOnly
```

Re-running the normal installer is the repair operation after a clone path, drive letter, or Houdini user-pref location changes. It rewrites the local pointer to the current checkout.

## Safe removal

Remove only the local pointer owned by the current checkout:

```powershell
.\deploy\houdini\install_melodia_studio.ps1 -Remove
```

Preview the removal:

```powershell
.\deploy\houdini\install_melodia_studio.ps1 -Remove -CheckOnly
```

Removal is intentionally conservative. The script refuses to delete an unreadable pointer or a pointer whose `package_path` does not match this repository's `deploy/houdini/packages` path. It never removes the repo-backed package content itself.

## Verification

Headless verification:

```powershell
hython deploy/houdini/verify_melodia_studio.py
```

or use `-Verify` on the installer.

The verifier checks package discovery, environment variables, HOUDINI_PATH registration, the two desktop files, the Melodia shelf and its eight tools, Python module import/launch, and machine-local-path leakage. It writes a small receipt under `Saved/Audit/houdini_studio/`.

A headless PASS is **not** GUI acceptance. The owner still needs to confirm in Houdini that:

- `Melodia_Studio` appears and switches correctly;
- `Melodia_KineFX` appears and switches correctly;
- the Melodia shelf is visible;
- Project, Evidence and AnimationDoctor open without path errors;
- both desktops still appear after Houdini restart.

## Package contents

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
    scripts/python/melodia_studio/
      __init__.py
      project.py
      evidence.py
  install_melodia_studio.ps1
  verify_melodia_studio.py
```

The shelf is a launcher/navigation surface, not a second authority. Its tools report or reveal the existing AnimationDoctor, Shorewake, Vellum cache, Copernicus, Foundry validation, evidence and UE handoff lanes.

## Desktop shadowing caution

Houdini may save a user-local desktop with the same name as a package desktop. If a GUI-edited `Melodia_Studio` or `Melodia_KineFX` seems to ignore a repo update, check the Houdini user preference directory for a local desktop that is shadowing the repo-backed `.desk`.

Do not commit the user-local preference file as the portable source by accident. Deliberate layout changes should be copied/re-authored into the repo-backed desktop and re-verified.

## Authority / storage rules

- Do not edit `houdini.env` for Melodia Studio.
- Do not hardcode machine drive letters, usernames, Humber hostnames, license paths, or user-pref paths in committed package files.
- Keep heavy Vellum caches, temporary HIPs, generated bgeo, turntables and large bake outputs out of Git unless a specific tracked-artifact contract says otherwise.
- Small manifests and receipts may live under the existing audit conventions.
- Unreal remains runtime/gameplay authority; this Houdini package never makes Houdini a runtime world-state or wardrobe authority.
