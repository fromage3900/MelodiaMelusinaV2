# Houdini Creative Pipeline — Reference for Agents

**Date:** 2026-08-28
**Status:** PROVEN — every fact below was verified by a live run this session (hython 22.0.368,
Apprentice tier). This is the long-term "how we use Houdini creatively" document. It is a
reference, not a handoff: later agents extend the systems here, they do not reinvent them.
**Authority chain:** `AGENTS.md` working agreement →
`Docs/Handoffs/HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28.md` (plan + §3A roadmap) →
this document (how the lane actually works).
**Tool home:** `Tools/Houdini/sea_above_reef/` — artifacts land in `Saved/Audit/sea_above/`.

**Companion closeout review:** `Docs/Handoffs/SESSION_REVIEW_HOUDINI_CREATIVE_LANE_2026-08-28.md`
— the session-wide inventory (27 scripts, 55+8 staged assets, 121 renders), verification
ledger, consolidated lessons, and the open-items list.

---

## 1. The lane's law (read before writing any Houdini code here)

1. **Never invoke hython bare in a shared console.** When the license server is unhappy, hython
   hangs indefinitely and wedges the whole shell session (this cost one full session on
   2026-08-28). Always go through `Tools/Houdini/sea_above_reef/probe_hython_license.ps1`
   (Start-Process + 45 s hard timeout + kill) or the same Start-Process pattern.
2. **Determinism is the contract.** Every cook takes a seed (suite seed: `20260828`). RNG call
   order is part of the seed contract — do not parallelise cooks from one rng. A beautiful mesh
   you cannot reproduce is a one-off, not content.
3. **Manifests are outputs, never inputs.** Cooks write sha256 manifests; verifiers re-derive.
   Nothing is claimed shipped because a log said so.
4. **Evidence or it did not happen.** PNGs exist only when the ingest verifier says they exist
   (`tileable_pass == tiling_targets`). Meshes exist only when the manifest lists real byte
   counts. This repo has a documented history of staged-but-never-run claims (the overnight
   learn loop ran in demo mode; the groom lane's "real ABC via hython" was never cooked — see §6).
5. **No editor writes from this lane.** All editor imports are queued, manifest-driven tasks for
   the single-editor holder. No writes under `Content/_PROJECT/`. No master material edits.
6. **One MPC writer rule.** Pulse-reactive geometry/materials *sample* existing parameters
   (`User.SeaAbovePulse` from `BP_SeaAbove_PrototypeDirector`). This lane never adds a second
   writer. Content, not systems: no second combat/rhythm/HUD/wardrobe authority, ever.
7. **Ask-first for deletes and for `houdini_*` MCP mutate tools** (gated in
   `specs/mcp_tool_policy.v1.json`). Read-only MCP (`list_hips`, `inspect_hip`) is free.

## 2. Verified environment facts (grep these exact strings before trusting memory)

| Fact | Evidence |
|---|---|
| hython 22.0.368 headless imports `hou` fine when hserver is up | probe output: `HOU 22.0.368` |
| License server: `hserver -l` answers; **`Used Licenses: None`** → no Engine license | probe output 2026-08-28 |
| **FBX ROP export is Apprentice-blocked**: `"FBX export is not supported in Houdini Apprentice"` | hython stderr |
| **Alembic ROP export is Apprentice-blocked**: `"Alembic export is only supported in Houdini Core and Houdini FX versions"` | hython stderr (this also proves the groom lane's real-ABC claim was never cooked) |
| The working export path: **File SOP in write mode** — `filemode` menu tokens `('auto','read','write','none')`; index 3 is "No Operation" (a real bug we shipped once); use the token `"write"` | `probe_file_write.py` output |
| File SOP write produces `.obj` (UE-native import, carries point `uv` attribs) **and** `.bgeo.sc` (needs a future Engine license to read in UE) | cooked outputs, 8 files |
| **H22 Python SOP does not prebind `geo`** — `NameError: name 'geo' is not defined`. Always start with `node = hou.pwd()` / `geo = node.geometry()` | node error capture |
| `node.errors()` returns a **tuple**, not a string — `str()` it before slicing | `AttributeError: 'tuple' object has no attribute 'strip'` |
| `ParmTuple` has no `.size()` — use `len(pt)`; `node.parm("rad")` returns `None` for tuple parms — use `node.parmTuple()` | `'ParmTuple' object has no attribute 'size'` |
| The **Sweep SOP produced 0 primitives headless** (both input orders tried; input 0 = cross-section, input 1 = backbone) — tubes are instead built in Python SOP code (rings + caps): deterministic, version-proof | OBJ headers: `0 primitives` before, `610/200 primitives` after |
| SOP parm names drift across versions (`size` vs `sizex`, `cols` vs `columns`, `iterations` missing on Smooth) — always `setp()`/`setp_first()` with candidate lists, warn-not-crash | `[warn] parm not found:` lines |
| Mantra renders are **watermarked in Apprentice** — beauty renders go through the Blender lit-sphere path (`Tools/Houdini/blender_lit_sphere_render.py` pattern); COP/geometry export is fine | SideFX Apprentice tier limits |
| Houdini scale is **metres** — UE imports at 100× (cm). Recorded in every mesh manifest | manifest `ue_import` |
| Workstation runtimes: Python 3.14.5, numpy 2.4.6, Pillow 12.2.0; Blender headless is a valid fallback runtime for numpy-only scripts (Non-Color pass-through + bottom-up flip in `reef_common._save_bpy`) | session runs |
| Python 3.14 is strict: `global X` declared after any use of X in the same function is a hard `SyntaxError` | sand suite first run |
| **Raw-string escaped quotes poison injected SOP code**: `\"\"\"` inside an r-string template reaches the SOP as literal `\"` — use `#` comments in code templates | staghorn cook failures |
| **`hou.Vector3` has no `rotateAroundAxis`** — use a Rodrigues rotation helper (in `build_coral_generator.py`) | `AttributeError: 'Vector3' object has no attribute 'rotateAroundAxis'` |
| Noise/Voronoi lattice periods must **divide the grid size** — on 1024 that means powers of two only (96 fails, 128 works) | `ValueError: period 96 must divide size 1024` |
| R1 corals are **code-grown** (branching/rings in Python SOPs), not VDB-advection — deliberate trade for headless determinism; VDB upgrade path reserved | `coral_mesh_manifest.json` |
| **OBJ carries a single UV set and no custom attribs** — true per-vertex VAT (vertex-ID indexing) cannot ship via the OBJ path. The R3 kelp sway ships as a **half-wrap LUT** instead: U = time (loop-perfect integer harmonics), V = height (mesh `uv.y`), material WPO samples it; U-loop seam must be verified on the **U axis** (a V-axis check false-fails by comparing pinned base to free tip) | `kelp_vat_textures.py` output; `IMPORT_QUEUE.md` sway recipe |
| **FBX IMPORT works on Apprentice** (only EXPORT is blocked): `hou.hipFile.importFBX(path)` — no `suppress_warnings` kwarg. This is the weight-lab's read path for meshes + skeleton rest poses | `probe_fbx_import.py`, 2026-08-28 |
| **1D gradients must be broadcast-materialized** before in-place ops: `np.broadcast_to(grad, (size, size, 3)).copy()` — a pure 1D-profile base stays (size,1,3) and `*=` throws | dress_lookdev.py first run |
| **Render QA suite**: `render_qa_blender.py` runs inside headless Blender (5.2 works; 4.3/4.5 also installed at `C:\Program Files\Blender Foundation\`) — Cycles CPU is the reliable background engine, SeaAbove 3-point rig, camera auto-fit, meshes at ×100 scale, textures flat + on ×2-wrapped spheres; `--tex-dir/--tex-out` renders any other texture folder. Blender 5.2 can **hang at exit after all work is flushed** — `--skip-existing` resumes; killing is safe once `render_manifest.json` exists. Sheet assembly is `assemble_contact_sheets.py` in system Python (Pillow is not in Blender's interpreter) | 121 renders + 4 sheets in `Saved/Audit/sea_above/renders/`; jelly renders verified visually after two shipped render defects were caught by the visual review (clip_end blanking cm-scale scenes; light offsets in the wrong units) |
| **Background Blender render/QA traps**: always `-b --factory-startup -noaudio` (user addons abort scripts); raise `cam_data.clip_end` (default 100 units blanks cm-scale scenes); scale light/energy/camera distances with the bounding diag; **deselect before `bpy.ops.object.join()`** or it eats selected neighbors; JSON pose values may be dicts (iterating yields keys, not points); `mat.blend_method` is gone in 5.x | `render_qa_blender.py` + `jelly_shapekeys.py` session |
| **Subagent reports are claims; disk is truth** — an R4 subagent returned "completed" with an empty report and no file. Always `Test-Path` + `py_compile` a delegated artifact before building on it | this session |

## 3. Proven code patterns (copy these, do not reinvent)

**Defensive parm setting** (SOP names drift across versions):
```python
def setp(node, name, value, warn=True):
    p = node.parm(name)
    if p is not None: p.set(value); return True
    pt = node.parmTuple(name)
    if pt is not None:
        n = len(pt)
        vals = value if isinstance(value, (tuple, list)) else (value,) * n
        for i, v in enumerate(vals[:n]): pt[i].set(v)
        return True
    if warn: print(f"[warn] parm not found: {node.name()}.{name}")
    return False

def setp_first(node, names, value):  # try candidates, first hit wins
    for n in names:
        if setp(node, n, value, warn=False): return n
```

**Python SOP prelude** (stable across versions — all geometry built this way now):
```python
node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))
# ... createPoint/setPosition, createPolygon([is_closed=False]), addVertex,
#     setAttribValue(uv), computeVertexNormals() in try/except
```

**Dual-format export** (the only Apprentice-legal geometry out):
```python
f = g.createNode("file", "writer_obj")
setp(f, "file", str(target_obj)); setp(f, "filemode", "write"); f.setInput(0, out_node)
f.cook(force=True)   # repeat for .bgeo.sc; verify target.exists() and size > 0
```

**Diagnostics pattern:** on any cook failure, walk `g.children()` and print `str(n.errors())` —
hython's raised exceptions are generic ("Error while cooking"); the real traceback is on the node.

**Tiling texture core** (`reef_common.py`): lattice-periodic value noise / fBm (period must
divide size — powers of two for 1024), **toroidal-distance wrapped Voronoi F1** (plain lattice
wrapping leaves a real dead band at tile edges — the ingest verifier caught this), tileable sine
with periodic warp, wrap-Sobel normals (OpenGL Y+), `WrappedDraw` (9-offset seamless primitives).

**Seam metric v2** (in `ingest_reef_textures.py`): wrap step relative to the mean adjacent-sample
gradient (ratio < 1.6), with an absolute floor (< 2 levels) for sparse/near-flat masks — the raw
`|col0 − colN|` metric false-positives on both high-frequency fields and empty ones.

## 4. System inventory (what exists and how to run it)

| Tool | Purpose | Run |
|---|---|---|
| `probe_hython_license.ps1` | B0 verdict, wedge-proof (isolated probes, hard kill) | `powershell -File …` — first step, always |
| `probe_file_write.py` | format-discovery probe — the pattern for any future "can Apprentice write X?" question | `hython …` |
| `reef_common.py` | shared library: periodic noise suite, normals, dual-runtime save (PIL / bpy), manifests, WrappedDraw | imported, not run |
| `tilable_sand_suite.py` | sand material set + caustics | `python … [--seed --size]` |
| `tilable_shell_masks.py` | nautilus/scallop/conch/sand-dollar tilable masks + sheet | `python …` (Pillow required) |
| `underwater_clutter_atlas.py` | 12 RGBA decal sprites → 4×4 atlas + tilable floor-debris mask | `python …` (Pillow required) |
| `ingest_reef_textures.py` | the verifier: seam metrics, sha256, UE import contract, combined manifest | `python … --include-sheets` |
| `build_clutter_meshes.py` | 4 clutter meshes → `.obj` + `.bgeo.sc` + manifest | `hython …` |

Artifacts: `Saved/Audit/sea_above/houdini_variants/` (24 texture files, 3 suite manifests +
ingest manifest) and `Saved/Audit/sea_above/meshes/` (8 mesh files + manifest). Current verdicts:
**11/11 tiling targets pass**; all 4 meshes cooked with real geometry (PebbleSet 2800 verts,
SpiralShell 610 prims, SeaWeed 200 prims, Starfish puffed).

## 5. The workflow loop (for any new creative content in this lane)

```
probe license → author generator (seeded) → cook → INGEST VERIFY (must pass)
  → manifest (sha256 + params + import contract) → queued editor-import task
  → holder imports per contract → editor re-read confirms → THEN it is "in the game"
```

Editor-import contract lives in each manifest (`sRGB` flag per kind, LOD group, tiling vs decal,
scale for meshes). Sand/shell/clutter sets are imported with sRGB=false for all data maps; the
atlas is sRGB=true; meshes import at 100×. Nothing in this lane ever touches a master material;
pulse-reactive wiring reads `User.SeaAbovePulse` only.

## 6. Wins ledger + corrections this session made to standing assumptions

- Shipped 24 verified textures + 8 mesh files + 2 runnable probes + 1 reusable library, all
  deterministic and manifest-backed, in one session.
- The ingest verifier caught a **real algorithmic bug** (Voronoi dead band at tile edges) — the
  evidence culture paying for itself exactly as designed.
- **Correction:** `Tools/Houdini/README.md` claims hython 20.5 and "Apprentice grooms export as
  .abc" — the version is 22.0.368, and Apprentice cannot export Alembic via ROP at all. The
  Choral Sheep groom lane's real-ABC cook has therefore never happened; its placeholder fallback
  is the actual state. Any future groom work must either get Core/Indie or bake strands to
  meshes/cards via the File-SOP path.
- **Correction:** the Overnight Houdini Learn Loop ran in **demo mode** (PIL stub scoring, all
  zero state) — its generation folders are scaffolding, not results. Any real re-run must reset
  `Saved/Audit/overnight/state.json` and label the log first.
- The wedge-proof probe now exists, so the session-killing hython hang cannot recur silently.

## 7. Extending the lane (templates)

**New tilable texture generator:** copy `tilable_sand_suite.py` — seed → `rc.fbm` /
`rc.periodic_voronoi_f1` / `rc.tileable_sine` → colorize in sRGB space → `rc.save_image` →
manifest → **add the asset to the `CONTRACT` table in `ingest_reef_textures.py`** (missing the
contract row = "unlisted file - review" verdict) → contact sheet → README row.

**New mesh builder:** copy `build_clutter_meshes.py` — geometry in a Python SOP (prelude from §3;
tubes/rings in code, not Sweep) → `export_geo` dual-format → seed in manifest → mesh list in
README. Use `probe_file_write.py` before betting on any new export format.

**Creative roadmap** (what to build next, with ownership rules): `Docs/Handoffs/
HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28.md` §3A — R1 VDB coral generator (hython is
now proven, this is the next unlock), R3 kelp VAT, R5 texture suite v2, R6 one-writer rule, R7
optional offline quantum layout curator.

## 8. Open blockers (owner-side)

1. **Houdini Engine license** (FREE tier via SideFX login) — unblocks HDA cooking in UE and
   `.bgeo.sc` import; without it, UE consumes only the `.obj` copies.
2. **Editor-import queue** — reef assets are staged and hash-verified in
   `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/` (see `IMPORT_QUEUE.md` there); the
   holder imports per manifest when an editor window opens.
3. ~~R1 coral cooks~~ **DONE** — `build_coral_generator.py` + `coral_textures.py` + staging all
   executed 2026-08-28 (see plan doc §3A "R1 EXECUTED"). Next creative unlock: R3 kelp VAT.
