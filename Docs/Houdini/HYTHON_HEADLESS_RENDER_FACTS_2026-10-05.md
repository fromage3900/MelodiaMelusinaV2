# hython 22.0.368 Headless Render — Verified Facts

Established by probing on this workstation, 2026-10-05. Every line below was
observed, not inferred. Use these when writing any new headless Houdini render
script for the Melodia lanes.

## The rule that matters most

**Never guess a Houdini parm name.** Enumerate first:

```python
print([p.name() for p in node.parms()])
```

`node.parm("x")` returns `None` for a wrong name, and a script that guards with
`if node.parm(...)` then *silently skips the step*. That is how a render ends up
writing a 0-byte file or none at all, with no error.

## Verified API names (22.0.368)

| Thing | Correct | Wrong (crashes / no-ops) |
|---|---|---|
| cam / hlight translate | `tx`, `ty`, `tz` | `t` |
| IFD output picture | `vm_picture` | `picture` (does not exist) |
| IFD object list | `vobject` | — |
| IFD CPU/GPU selector | `vm_device` (a **string** menu) | `vm_device.set(0)` → TypeError |
| set a node's world xform | `setWorldTransform(m)` | `setTransform(m)` |
| build a Matrix4 basis | `m.setAt(row, col, v)` | `m.setRow(...)` |
| object render flag | *(none — use the ROP's `vobject`)* | `setRenderFlag` |
| object visibility | `setDisplayFlag`, `setGenericFlag` | — |
| SOP shading | `material` SOP | `principledshader::2.0` (not in SOP category) |
| camera | `resx`, `resy`, `focal`, `projection` | — |
| light | `light_intensity`, `light_type` | — |
| geometry from an output node | `output_node.geometry()` | `obj_node.createPoint()` (OBJ geo has no geometry API) |
| license | `hou.isApprentice()` (a function) | `hou.licenseSummary` (absent) |

`hou.hda.installFile(path, change_priority=True)` → `TypeError`; the kwarg does
not exist in this build.

## Renders work. "Segfault" was usually my own timeout.

Shell exit **143 / -1073741502 is SIGTERM** — that is `timeout` killing a slow
render, *not* a Houdini crash. Before concluding anything from a failed render,
check whether the PNG is non-empty: several apparent "segfaults" were complete,
correct frames already written to disk.

Mantra is **slow** here (Apprentice license, CPU only). Even 800x450 at 1 sample
takes minutes on 8.6k polys. Never wrap a render in a short `timeout` and read
the failure as a crash — run it in the background and verify by file size.

A **0-byte `.png` plus a `.mantra_checkpoint`** is the genuine failure
signature: Mantra died during shading init before writing any pixels.

Real cause of the 0-byte failures, once traced properly:

1. **`vm_picture` unset** → renders into nowhere.
2. **The HDA instance itself was never shootable.** There is no
   `setRenderFlag` on an object node in this build; what Mantra shoots is chosen
   by the IFD ROP's `vobject` parm. Fix: bake the HDA output into a **plain
   `geo`** via an `object_merge`, then point `vobject` at that.
3. **A `material` SOP with an unset `shop_materialpath`** → fails mid-render.

An `hlight` node does **not** crash Mantra — that was my misreading of a
timeout. Lights are safe; they are only slow.

## Framing: measure it, never guess it

`_probe_framing.py` projects the geometry bbox corners into camera space and
reports the frame fill. It settles framing questions **without rendering**, in
seconds instead of the ~6 minutes a Mantra frame costs.

The first framing table was simply too far away, which is why every early frame
showed a thin strip plus a slab with acres of empty background:

| view | distance | frame fill (horizontal) |
|---|---|---|
| hero | 70.5 m | 33% |
| front | 55 m | 12% |
| side | 70 m | 39% |
| top | 80 m | 12% |

All 8 bbox corners were **in front of the camera** in every case — so the aim
maths was correct and pure distance was the whole problem. That distinction
matters: had the aim been wrong, no amount of moving the camera back would help.

Rule of thumb from the numbers: at focal 35 mm on a 36 mm sensor, filling ~70% of
the frame with this asset (bbox diagonal 53.56 m) needs roughly **40–45 m**.

The `--view` table in `render_cathedral.py` is now computed from this, and
includes `aisle` / `aisle_high` — standing inside the west front looking down the
nave, which is the view that actually shows an arcade and a vault.

## Lighting: register lights on the ROP, do not rely on the scene

This was the cause of the flat black silhouettes. Once `vobject` is set on the
IFD ROP, **scene lights are not picked up automatically** — every light must be
listed explicitly or the geometry renders unlit:

```python
rop.parm("vobject").set(plain_geo_path)
rop.parm("forcelights").set(1)
rop.parm("alights").set(" ".join(light_paths))   # SPACE-separated, one parm
```

Verified 22.0.368: `alights` is a single **space-separated string** parm. Passing
a tuple raises `Cannot set parameter value to unsupported type <class 'tuple'>`.
There is no `alights2` / `alights3`.

## The OpenGL ROP cannot render headless here

It segfaults in `DM_RenderVulkan::compositePasses` / `DM_VPortAgent::renderVulkan`
— it needs a real GPU/Vulkan context and hython has none on this box. This is
**environmental, not a code bug**; do not spend time re-diagnosing it. Mantra is
the only working headless renderer here.

Its parm layout (useful on a GPU machine): `picture`, `camera`, `vobjects`
(plural), `forceobjects`, `alights`, `forcelights`, `imagetype`, `gamma`.

## Lighting: a surround rig, not key/fill

Two lights (key + fill) left the shell **pure black against a white background**
— unreadable for review. With only direct lights, any surface facing away from
every light is unlit, and this asset's normals are not all outward-facing.
Six lights on a sphere around the nave fixed readability completely.
`soho_autoheadlight` alone is not enough either.

## Framing matters as much as lighting

The cathedral is ~12.04 x 45.46 x 25.63 m centred near y = +22.5. A camera at
the origin, or at y=0 / z=20, sits *inside or edge-on to* the geometry — which
is why early frames showed a thin strip and a lit floor slab instead of a
building. Aim with an explicit 4x4 built via `setAt` (row 2 is `-forward`,
because a Houdini camera looks down its own -Z).

## Reading a frame honestly

A byte count proves *a file was written*, not that the architecture reads. Open
the PNG and look at it — 35 KB of unreadable silhouette is still a failure.

## License

`hou.isApprentice()` → **True**. It is a *function*; printing the bare attribute
shows a function object (always truthy) and misleads you into "commercial".

Consequence: **every render carries the Houdini logo in a corner.** Verified by
reading the actual PNG — it is the "Houdini" wordmark with the orange icon, not
an "Apprentice" text overlay. Fine for internal review; a watermark is a problem
for portfolio plates, so portfolio frames should come from UE, not Houdini.

## Process facts

- `hython` renders, then **idles** — the shell call blocks until killed. Expect
  exit 124 from `timeout` even on success. **Verify by checking the PNG exists
  and is non-empty**, never by exit code.
- Always redirect to a log file (`> log 2>&1`) and read the log; piping a
  blocking render through `tail` hides the result behind the hang.
- Isolate each render path in its own process. A segfault in one path otherwise
  cascades and you cannot tell which stage died.

## The geometry itself is sound

`HDA_Melodia_CrystalCathedral` instantiates and produces
**9278 pts / 8641 prims** on OUT_Cathedral — byte-matching the school receipt on
G:. The rebuild is deterministic. Crashing is a *rendering* problem, not a
geometry problem.
