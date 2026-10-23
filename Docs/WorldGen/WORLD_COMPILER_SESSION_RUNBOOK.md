# World Compiler Session Runbook

**Status:** DURABLE RUNBOOK. How to run a World Compiler pass end to end.
Contract: [`WORLD_COMPILER_CONTRACT.md`](WORLD_COMPILER_CONTRACT.md).
Status of any compiled world lives only in [`CURRENT_STATE.md`](../../CURRENT_STATE.md).
Proven on the `melody_glitter` landing, 2026-09-23 (57 token piles, 7 band MIs).

> Compile stays CLI. The editor only consumes bundles. No second editor, no second
> Monolith — `127.0.0.1:9316` only. Never `git clean -fd` / `git checkout -- .`.

---

## 0. Preflight (every session, before any mutation)

1. One `UnrealEditor` process; port 9316 has one holder. Many `monolith_proxy.exe`
   owners (Codex, Claude, others) is normal — check Monolith still answers and
   `Saved/Logs/BS_GodFile_2.log` for a second editor.
2. `Binaries/Win64/UnrealEditor-BS_GodFile.dll` mtime newer than your last source
   edit (stale DLL = dead PIE evidence). Never UBT while the editor is open.
3. `python Tools/git_ok.py` — if OK, git is not the task.
4. Monolith `editor_query list_dirty_packages` — record the count (0 is the goal
   at both ends).
5. In the open editor: `scene_context_cycle.begin()` (via `editor_query run_python`).
   Confirm the packet level matches the recipe level. After the work:
   `scene_context_cycle.end()`.

## 1. Offline — recipe, compile, prove neutrality

```powershell
python Tools/world_compiler.py validate recipes/<id>.v1.json
python Tools/world_compiler.py compile recipes/<id>.v1.json
python Tools/test_world_compiler.py   # ALL PASS or stop
```

- Same recipe + same code = byte-identical tables. Hash `points.csv` /
  `fx_anchors.csv` before and after any compiler edit.
- Neutrality proof for compiler changes: `git show HEAD:Tools/world_compiler.py`
  to bytes (PowerShell `>` writes UTF-16 and **breaks** the file — use python to
  write it), compile both versions on the same recipe, compare hashes, restore.
- n ssuh
  The 2026-09-23 precedence/scale change reproduced the saved bundle exactly
  (`points b6a0f333`, `fx 9e5c33be`).
- Recipe rules that bite: `field.scale_range` is the global default the old code
  used — pin it explicitly on old species when activating per-species ranges or
  the whole field silently changes size. `band_mi_prefix` on a species now wins
  over the wind-lane prefix (flowers already carry the wind string verbatim, so
  legacy output is unchanged). Schema files are strict (`additionalProperties:
  false`) — new recipe keys need schema keys.

## 2. UE pass 1 — forge material families, verify by re-read

New MI families go through a lane step (mirrors `materials` / `_forge_wind_lane`;
`glitter_materials` is the template): create-if-missing under the existing
parent, enforce parent, set tint/scalar params only, `update_material_instance`,
save. Parents and MPCs are never written.

```powershell
# Monolith editor_query run_python, execute_file, unattended:
# Content/Python/world_compiler_ue.py <bundle_dir> glitter_materials
```

Verify — `success: true` means nothing threw:

- Read `Saved/WorldCompiler/<id>_<seed>/ue/<step>.json` (`all_ok`, per-band records).
- Re-read live: `material_query get_instance_parameters` on 2+ MIs — parent path
  correct, only intended overrides set, scalars/switches untouched.
- Precedent check: new families should copy an existing MI's parentage
  (`MI_MelodyToken_Water` → `M_Master_Toon_Universal` with sparkle). A master
  that renders flat white in a still after 15 minutes is the wrong parent, not a
  shader-compile delay — reparent, don't wait.

## 3. UE pass 2 — the driver, then the count gate

```powershell
python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/<id>_<seed> --skip-scaffold --fx --lookdev
```

- One `run_python` call per step (frame boundaries; never `time.sleep` inside).
- DT must report rows_in_csv == rows_in_table, `missing_columns: []`.
- **Warm the mesh:** a never-before-generated species mesh is still compiling on
  first generate (`Waiting for static meshes to be ready`) and the selector
  silently falls back per-point (first pass: 0 tokens, +53 mis-fallbacks).
  **Generate twice, recount per MI family.** The 95 % survival tolerance in
  `ground_probe` mode is the gate — 1085/1089 with glitter 57/57 exact is a pass.
- Per-MI proof query (ISM components on the field volume, group by
  mesh + materials): every CSV species must own instances; a missing family with
  a correct DT means selector fallback, not a data bug.

## 4. Stills — read them, don't trust the return value

- `lookdev_capture` writes fixed filenames; back the set aside before any
  diagnostic re-capture.
- White unlit squares: hide-test the suspect (`set_visibility` / actor hidden,
  transient, no save) and re-capture. Tokens survived this test; the 17
  re-placed FX actors didn't — separate Niagara FX-material defect, not WC.
- Black frames (`waterline_dolly`) and day/night drift vs the 09-19 board are
  camera/sky issues — never retune PPV or MPCs to compensate.
- Compare against the previous board (`Saved/Audit/Screens/*2026-09-19.png`)
  before claiming an improvement.

## 5. Close out

1. Driver `save` (or lane `save`), then `list_dirty_packages` → 0.
2. `scene_context_cycle.end()` — expect only tagged-actor churn.
3. `CURRENT_STATE.md` in the same change set: files, counts, evidence rung,
   open defects. Contractedit only for lasting rules.
4. Commit exact paths only (`git add` the files you touched — never the dirty
   tree). Uncommittable-by-design: `Content/EnvSandbox/*` MIs, `Content/__ExternalActors__/*`,
   `Saved/*` are gitignored — the level geometry and forged MIs are disk-only
   and must be re-applied from the recipe + lane on a fresh machine. Say so in
   the commit body.

## 6. Failure playbook (symptom → check)

| Symptom | Check |
|---|---|
| `points.csv` hash moved after a "neutral" edit | Species pins vs `field.scale_range`; prefix string equality; rerun the §1 neutrality proof |
| Test `test_attribute_ranges` fails | It encodes the global-scale assumption — assert per-species range like the compiler |
| New species, 0 instances, totals nearly right | Mesh still compiling — regenerate + per-MI recount (§3) |
| Family renders flat white in stills | Wrong parent — copy a working MI's parentage; verify by re-read + still, not by waiting |
| White squares in captures | Transient-hide suspects one family at a time; captures are cheap |
| `save_current_level()` True, nothing on disk | World Partition: external actors need `save_packages(..., only_dirty=False)` in ≤60-actor chunks; verify by mtime, and end with dirty 0 |
| Edits hit a discarded world | PIE was running (`get_editor_world()` None) — check first, never `load_level` right after stopping PIE |
