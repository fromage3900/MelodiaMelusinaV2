# Campaign 3 — Development Package Launch

**Gate id:** `package_launch`
**Long-standing P0:** `_ROADBLOCKS` (a) — the packaged build has never been
launch-tested; `Saved/StagedBuilds_20260730/` cooks clean (2.1 GB, all five
maps) but packaging is not launching.

## Preconditions

1. Cook clean: `Saved/StagedBuilds_20260730/` exists with all five maps
   (`_VERTICAL_SLICE_SCOPE.md` gate). If it does not, re-cook first.
2. Confirm the actual executable path for the current staging layout —
   the packaged layout has drifted between sessions; enumerate
   `Saved/StagedBuilds*/Windows*/BS_GodFile.exe` before assuming a path.
3. No editor instance holding a lock on the project while the packaged build
   runs.

## Run

1. Launch `BS_GodFile.exe` (Development) outside the editor.
2. Walk the route: Morning → Dreamstate → KaleidoNave.
3. Confirm the three maps load, Quill dialogue shows, and the battle chain
   starts.
4. **Known failure class:** cook exit 25 / modal-hang / shader compile stalls —
   if the app hangs at startup, grep the log for `MODAL_OPEN` and shader
   compile lines before blaming the build.

## Record

```text
python Tools/echo_run.py record package_launch pass --note "Development build launched; Morning -> Dreamstate -> KaleidoNave walked"
```

## If packaging is not launching (the standing failure)

Capture the failing step verbatim (launch command, log tail, exit code) and
record `fail` with that evidence. Do not record the cook as a launch — the
gate is the launch, not the cook.
