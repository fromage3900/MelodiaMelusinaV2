# Tools/Houdini/hda_verify — HDA audit + cook verification lane

| | |
|---|---|
| **Purpose** | One command that answers: *do our HDA files exist, hold real networks, load, cook, and emit the geometry they are supposed to?* |
| **Authority** | `hda_registry.v1.json` is the single source of truth for which HDAs exist and what a green cook looks like. Adding a HDA = adding one registry entry. |
| **Gate 0** | `hda_audit.py` — **stdlib only, no hou**. Existence, sha256, `Contents.gz` network present vs empty-shell stub, mirror drift (`Content/HDA` copy), unregistered files, label match. |
| **Gate 2** | `hda_verify.py` — **hython**. `hou.hda.installFile` → instantiate → `expect.parms` on the type (exposed-controls probe) → force cook every `output` node → point/prim/bbox vs golden pins → `parm_drive` probes (set a parm, prove the cook moved via `differ` counts or `differ_bbox` bounds, restore, re-prove pins) → node errors. Also dumps the internal node inventory for study. |
| **Runner** | `run_hda_verify.ps1` — runs both gates into one run folder. Pass/fail is read from each gate's **receipt**, not from a process exit code (this PowerShell build never populates `Process.ExitCode` for `Start-Process` children). |
| **Receipts** | `Saved/Audit/hda_verify/<run>/hda_inventory.json` + `hda_verify_report.json` (+ per-gate stdout). |
| **Exit codes** | gate scripts: `0` pass (warnings allowed), `1` at least one FAIL, `2` environment/registry problem. |

```powershell
# everything (both gates, one run folder)
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Houdini\hda_verify\run_hda_verify.ps1

# one gate, or one asset
powershell ... -Gate 0
powershell ... -Gate 2 -Only melodia_crystal_cathedral

# gates standalone (same registry)
hython Tools\Houdini\hda_verify\hda_audit.py
hython Tools\Houdini\hda_verify\hda_verify.py --only arpeggio_stair
```

## Entry statuses (registry `status` field)

| status | meaning | gate behaviour |
|---|---|---|
| `active` | file exists, must load + cook | golden pins enforced; miss = **FAIL** |
| `missing` | builder/recipe exists, file does not | reported as OWED = **WARN**, never blocks (keeps the debt visible) |
| `stub` (`globs.stub`) | `hda/backup/*.hda` empty shells | must *stay* empty; a backup that grows a network = unaudited edit → FAIL |
| `unregistered` | a `*.hda` under `scan_roots` with no entry | **WARN**: register it, never delete it |
| `vendor` (`globs.vendor`) | `Plugins/HoudiniEngine/Content` examples | counted only, never enumerated as failures |

## Pinning / changing a golden count

Counts are measured from a green cook and pasted into `expect.outputs`
(`points` / `prims`). If you change a network **on purpose**, re-run Gate 2,
read the measured values out of the receipt and update the pin in the same
change set. An unexpected count change failing the gate is the point of the
gate.

## Laws

- Read-only against `hda/` and `Content/` — this lane never writes, rebuilds or
  deletes an HDA. Rebuilding is the builder's job
  (`Tools/Houdini/cathedral/*`, `Content/Python/create_hda_*.py`).
- Cooking runs in its own hython process, never in the live Houdini session.
- The gate does not touch Unreal; UE-side import (`Content/HDA/*.uasset`) is a
  separate lane. Gate 0 only proves the `.hda` the uasset was imported from
  still matches byte-for-byte.

**`Tools/*` is gitignored with per-file allowlisting** — new files here need
`git add -f <path>` or they stay silently unstaged.
