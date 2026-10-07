"""build_crystal_cathedral_v2_hda.py — headless HDA builder for 'CrystalCathedralV2'.

Produces a single, fully-parameterized HDA that packs, in one geo network:

  Cathedra:  arch -> nave -> crystal prisms -> rose window -> thicken/bevel/floor
  Corridor:  box-chain -> weld -> thicken/bevel -> LOD tiers -> VDB atmosphere (+vol light)
  Outputs:   main cathedal | rose window | collision proxy | corridor

Run:
    hython Tools/Houdini/cathedral/build_crystal_cathedral_v2_hda.py \
        --out hda/CrystalCathedralV2.hda
    hython Tools/Houdini/cathedral/build_crystal_cathedral_v2_hda.py --verify
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "CrystalCathedralV2.hda"

import hou  # noqa: E402  (run under hython)

# ---------------------------------------------------------------- VEX programs
# (identical to build_crystal_cathedral_hda.py — Gate 2 verified)
ARCH_PROFILE_VEX = r"""
// Fractal arch profile. Runs on DETAIL over a single seed point; the seed point
// is removed and replaced by the exact profile resolution.
int   depth   = chi("../controls/depth");
float span    = chf("../controls/span");
float height  = chf("../controls/height");
float tracery = chf("../controls/tracery");

int   segments = 16 * (depth + 1);
float half     = span * 0.5;
int   target   = segments + 1;          // 81 at depth=4

// Clear the upstream seed points. npoints() reflects QUEUED edits, not applied
// ones, so the count must be captured before the removal loop.
int seed_pts = npoints(0);
for (int i = 0; i < seed_pts; i++)
    removepoint(0, 0);

// the 1x1 seed grid also leaves one stray polygon
int seed_prims = nprimitives(0);
for (int i = 0; i < seed_prims; i++)
    removeprim(0, 0, 1);

for (int i = 0; i < target; i++)
    addpoint(0, set(0, 0, 0));

for (int i = 0; i < target; i++) {
    float t = (float)i / (float)segments;
    float x = -half + t * span;

    float base = 1.0 - pow(abs(x) / half, 1.5 + depth * 0.15);
    float y    = base * height;

    // wobble reads the PRE-wobble height, exactly as the python did
    float wobble = cos(8 * M_PI * t) * cos(6 * M_PI * (y / max(height, 1.0)))
                 * tracery * 0.08 * height;
    y += wobble;

    if (depth > 0 && t > 0.4 && t < 0.6) {
        float sub_h = height * 0.35;
        float sub_x = (t - 0.5) / 0.1;
        float sub_y = sub_h * (1.0 - abs(sub_x)) * 0.5;
        y += sub_y * (depth / 3.0);
    }

    setpointattrib(0, "P", i, set(x, y, 0.0), "set");
    setpointattrib(0, "arch_t", i, t, "set");
}
"""

NAVE_VEX = r"""
// input 0: arch profile points (arch_n of them), tagged f@arch_t
// The profile is CONSUMED here, not kept: clear it first so the output is exactly
// the swept nave, otherwise the arch_n source points ride along into the count.
int   bays = chi("../controls/bays");
float span = chf("../controls/span");
float height = chf("../controls/height");
float undulation_amp = chf("../controls/undulation_amp");
float undulation_period = chf("../controls/undulation_period");

int   arch_n = npoints(0);
float bay_len = span * 0.75;

// Baroque undulation: lateral X offset as a function of Y.
// Applied per y-station so both rings of a bay at a shared y take the same
// offset and the seams stay coincident.
// Inlined (no helper function) — VEX detail wrangle snippets reject
// user-defined functions in this Houdini build.

int src_pts = npoints(0);
for (int i = 0; i < src_pts; i++)
    removepoint(0, i);
int src_prims = nprimitives(0);
for (int i = 0; i < src_prims; i++)
    removeprim(0, 0, 1);

// --- per-bay shell: arch_n verts at y0 and y1, bridged --------------------------
for (int bay = 0; bay < bays; bay++) {
    float y0 = bay * bay_len;
    float y1 = (bay + 1) * bay_len;
    float ox0 = undulation_amp * sin(2.0 * M_PI * y0 / undulation_period);
    float ox1 = undulation_amp * sin(2.0 * M_PI * y1 / undulation_period);
    int base = npoints(0);

    for (int i = 0; i < arch_n; i++) {
        // H22 requires the attribute name: point(geohandle, "P", ptnum)
        vector p = point(0, "P", i);
        int a = addpoint(0, set(p.x + ox0, y0, p.z));
        int b = addpoint(0, set(p.x + ox1, y1, p.z));
        setpointattrib(0, "uv", a, set((p.x + span * 0.5) / span, (float)bay / bays), "set");
        setpointattrib(0, "uv", b, set((p.x + span * 0.5) / span, (float)(bay + 1) / bays), "set");
    }
    // Group the shell faces as they are created. A detail wrangle has no
    // @primnum, so the prim number must come from addprim's return value.
    for (int i = 0; i < arch_n - 1; i++) {
        int pr = addprim(0, "poly",
            base + i * 2, base + i * 2 + 1,
            base + (i + 1) * 2 + 1, base + (i + 1) * 2);
        setprimgroup(0, "shell", pr, 1, "set");
    }
}

// --- diagonal vault ribs: 4 verts + 1 face each, 2 per bay ---------------------
float rib_w = 0.12;
float apex_z = height;
for (int bay = 0; bay < bays; bay++) {
    float y0 = bay * bay_len;
    float y1 = (bay + 1) * bay_len;
    float ox0 = undulation_amp * sin(2.0 * M_PI * y0 / undulation_period);
    float ox1 = undulation_amp * sin(2.0 * M_PI * y1 / undulation_period);
    // the two crossing diagonals: (x0, ys, x1, ye) per rib
    float rib_x0[];
    float rib_x1[];
    resize(rib_x0, 2);
    resize(rib_x1, 2);
    rib_x0[0] = -span * 0.5;  rib_x0[1] = span * 0.5;
    rib_x1[0] =  span * 0.5;  rib_x1[1] = -span * 0.5;
    for (int r = 0; r < 2; r++) {
        float x0 = rib_x0[r];
        float x1 = rib_x1[r];
        float ys = y0;
        float ye = y1;
        int r0 = addpoint(0, set(x0 + ox0,       ys, apex_z - rib_w));
        int r1 = addpoint(0, set(x0 + rib_w + ox0, ys, apex_z));
        int r2 = addpoint(0, set(x1 + rib_w + ox1, ye, apex_z));
        int r3 = addpoint(0, set(x1 + ox1,       ye, apex_z - rib_w));
        setpointattrib(0, "uv", r0, set(0, 0), "set");
        setpointattrib(0, "uv", r1, set(1, 0), "set");
        setpointattrib(0, "uv", r2, set(1, 1), "set");
        setpointattrib(0, "uv", r3, set(0, 1), "set");
        int rib_prim = addprim(0, "poly", r0, r1, r2, r3);
        setprimgroup(0, "ribs", rib_prim, 1, "set");
    }
}
"""

CRYSTAL_VEX = r"""
// input 0: the nave mesh
// Everything the crystal pass ADDS goes into a "crystal" group, so collision can
// drop it. Prisms on the vault are decoration; they must not block a character.
int   bays    = chi("../controls/bays");
float span    = chf("../controls/span");
float height  = chf("../controls/height");
float crystal = chf("../controls/crystal");
int   facets  = chi("../controls/facets");
int   seed    = chi("../controls/seed");

float bay_len = span * 0.75;
int   shards  = (int)(3.0 + crystal * 3.0);   // 5 at crystal=0.85

// Build a faceted prism and put it in the "crystal" group.
// f*2+1 verts, f*2 faces.
int crystal_prism(vector c; float h; float rad; int f; float rot) {
    int   base = npoints(0);
    int   bottom[];
    int   top[];
    resize(bottom, f);
    resize(top, f);

    for (int i = 0; i < f; i++) {
        float ang = 2.0 * M_PI * (float)i / (float)f + rot;
        bottom[i] = addpoint(0, set(c.x + cos(ang) * rad,
                                    c.y + sin(ang) * rad,
                                    c.z));
    }
    for (int i = 0; i < f; i++) {
        float ang = 2.0 * M_PI * (float)i / (float)f + rot;
        float r2  = rad * 0.6;                 // tapered top ring
        top[i] = addpoint(0, set(c.x + cos(ang) * r2,
                                 c.y + sin(ang) * r2,
                                 c.z + h));
    }
    int tip = addpoint(0, set(c.x, c.y, c.z + h * 1.25));

    for (int i = 0; i < f; i++) {
        int pr = addprim(0, "poly", bottom[i], bottom[(i + 1) % f],
                                   top[(i + 1) % f], top[i]);
        setprimgroup(0, "crystal", pr, 1);
    }
    for (int i = 0; i < f; i++) {
        int pr = addprim(0, "poly", tip, top[i], top[(i + 1) % f]);
        setprimgroup(0, "crystal", pr, 1);
    }
    return base;
}

int pdetail = rand(seed);

// --- shards along the two crossing ribs of every bay -------------------------
for (int bay = 0; bay < bays; bay++) {
    float y0 = bay * bay_len;
    float y1 = (bay + 1) * bay_len;
    for (int r = 0; r < 2; r++) {
        float x0 = (r == 0) ? -span * 0.5 : span * 0.5;
        float x1 = (r == 0) ?  span * 0.5 : -span * 0.5;
        for (int s = 0; s < shards; s++) {
            float t = ((float)s + 0.5) / (float)shards;
            float cx = x0 + (x1 - x0) * t + rand(pdetail++) * 0.6 - 0.3;
            float cy = y0 + (y1 - y0) * t + rand(pdetail++) * 0.6 - 0.3;
            float cz = height            + rand(pdetail++) * 1.0 - 0.5;

            // Chladni (8,6) drives shard height
            float chlad = abs(cos(8.0 * M_PI * (cx / span * 0.5 + 0.5))
                            * cos(6.0 * M_PI * (cy / (bay_len * bays) * 0.5 + 0.5)));
            float h  = (0.8 + chlad * 1.2) * crystal * 2.5;
            float rr = 0.18 + rand(pdetail++) * 0.12;

            crystal_prism(set(cx, cy, cz), h, rr, facets,
                          rand(pdetail++) * 6.28318);
        }
    }
}

// --- buttress pinnacles: (bays+1)*2 prisms, always 6 facets -------------------
for (int bay = 0; bay <= bays; bay++) {
    float y = bay * bay_len;
    for (int s = 0; s < 2; s++) {
        float x = (s == 0) ? -span * 0.5 - 0.8 : span * 0.5 + 0.8;
        float h  = (1.2 + rand(pdetail++) * 0.8) * crystal * 2.0;
        crystal_prism(set(x, y, height * 0.9), h, 0.22, 6,
                      rand(pdetail++) * 6.28318);
    }
}
"""

ROSE_VEX = r"""
int   span    = (int)chf("../controls/span");
float tracery = chf("../controls/tracery");
float crystal = chf("../controls/crystal");
int   facets  = chi("../controls/facets");
int   seed    = chi("../controls/seed");

float radius = span * 0.42;
int   res    = 64;

// Drop the seed points before building the disc. Queued-edit safe: capture the
// count first, then remove exactly that many.
int seed_pts = npoints(0);
for (int i = 0; i < seed_pts; i++)
    removepoint(0, 0);
int seed_prims = nprimitives(0);
for (int i = 0; i < seed_prims; i++)
    removeprim(0, 0, 1);

// --- disc: one centre point + concentric rings --------------------------------
int   centre = addpoint(0, set(0, 0, 0));
setpointattrib(0, "uv", centre, set(0.5, 0.5), "set");

// Track where each ring starts instead of back-computing npoints() - outer_n.
int outer_start = -1;
int outer_count = 0;

for (int r = 1; r < res / 2; r++) {
    float rad = radius * (float)r / (float)(res / 2);
    int   ring_n = max(8, (int)(2.0 * M_PI * rad / (radius / 8.0)));
    int   ring_start = npoints(0);

    for (int a = 0; a < ring_n; a++) {
        float ang = 2.0 * M_PI * (float)a / (float)ring_n;
        float x = cos(ang) * rad;
        float y = sin(ang) * rad;
        // Chladni (8,6) cross-pair, tracery-scaled
        float cx_ = cos(8.0 * M_PI * (x / radius * 0.5 + 0.5))
                  * cos(6.0 * M_PI * (y / radius * 0.5 + 0.5));
        float cy_ = cos(6.0 * M_PI * (x / radius * 0.5 + 0.5))
                  * cos(8.0 * M_PI * (y / radius * 0.5 + 0.5));
        float th = (cx_ - cy_) * 0.15 * radius * tracery;
        int p = addpoint(0, set(x, y, th));
        setpointattrib(0, "uv", p, set(x / radius * 0.5 + 0.5,
                                      y / radius * 0.5 + 0.5), "set");
    }

    outer_start = ring_start;
    outer_count = ring_n;
}

// --- one fan face per outer-ring vertex, from the centre ----------------------
for (int i = 0; i < outer_count; i++) {
    int b = outer_start + i;
    int c = outer_start + ((i + 1) % outer_count);
    addprim(0, "poly", centre, b, c);
}

// --- crystal overlay on the disc: int(12*crystal) prisms ----------------------
int pdetail = rand(seed + 1);
int shards  = (int)(12.0 * crystal);      // 10 at crystal=0.85

for (int i = 0; i < shards; i++) {
    float ang = rand(pdetail++) * 2.0 * M_PI;
    float rad = radius * (0.1 + rand(pdetail++) * 0.75);
    float cx = cos(ang) * rad;
    float cy = sin(ang) * rad;
    float chlad = abs(cos(8.0 * M_PI * (cx / radius * 0.5 + 0.5))
                    * cos(6.0 * M_PI * (cy / radius * 0.5 + 0.5)));
    float h = (0.5 + chlad) * crystal * 1.2;

    int base = npoints(0);
    int bottom[]; int top[];
    resize(bottom, facets); resize(top, facets);
    float rot = rand(pdetail++) * 6.28318;
    for (int k = 0; k < facets; k++) {
        float a2 = 2.0 * M_PI * (float)k / (float)facets + rot;
        bottom[k] = addpoint(0, set(cx + cos(a2) * 0.12, cy + sin(a2) * 0.12, 0.0));
    }
    for (int k = 0; k < facets; k++) {
        float a2 = 2.0 * M_PI * (float)k / (float)facets + rot;
        top[k] = addpoint(0, set(cx + cos(a2) * 0.072, cy + sin(a2) * 0.072, h));
    }
    int tip = addpoint(0, set(cx, cy, h * 1.25));
    for (int k = 0; k < facets; k++)
        addprim(0, "poly", bottom[k], bottom[(k + 1) % facets],
                         top[(k + 1) % facets], top[k]);
    for (int k = 0; k < facets; k++)
        addprim(0, "poly", tip, top[k], top[(k + 1) % facets]);
}
"""

# Cathedral parameters (existing)
CATASTRAL_CONTROLS_PARMS = [
    ("depth",     "Recursion Depth",   1, (4,),  0, 8),
    ("span",      "Arch Span (m)",     1, (10.0,), 0.1, 100.0),
    ("height",    "Vault Height (m)",  1, (20.0,), 0.1, 200.0),
    ("tracery",   "Tracery Density",   1, (0.85,), 0.0, 1.0),
    ("bays",      "Bays",              1, (6,),  1, 32),
    ("crystal",   "Crystal Density",   1, (0.85,), 0.0, 2.0),
    ("facets",    "Facet Count",       1, (12,), 3, 32),
    ("seed",      "Seed",              1, (20260901,), 0, 999999),
    ("bevel_width",    "Bevel Width (m)",    1, (0.012,), 0.0, 0.5),
    ("bevel_segments", "Bevel Segments",     1, (2,), 1, 8),
    ("floor_divisions", "Floor Divisions",   1, (24,), 1, 256),
    ("undulation_amp", "Undulation Amplitude (m)", 1, (0.8,), 0.0, 5.0),
    ("undulation_period", "Undulation Period (m)", 1, (12.99,), 0.1, 100.0),
]
# Corridor parameters (new — tiled around the cathedral)
# chain_type is stored as an int code: 0=straight (1=spiral, 2=zigzag will
#  come later). Kept as an int to avoid the Houdini 22 StringParmTemplate
# default_value quirks seen in headless hython builds.
CORRIDOR_CONTROLS_PARMS = [
    ("chain_type", "Chain Type", 1, (0,), 0, 2),
    ("corridor_bays", "Corridor Bays", 1, (6,), 1, 32),
    ("corridor_span", "Corridor Span (m)", 1, (4.0,), 0.1, 100.0),
    ("corridor_height", "Corridor Height (m)", 1, (3.0,), 0.1, 200.0),
    ("bay_length", "Bay Length (m)", 1, (20.0,), 1.0, 200.0),
    ("lod_count", "LOD Tiers", 1, (3,), 1, 8),
]


def _set(node, parm_name, value=None, expression=None):
    """Set a parm if it exists; warn on missing, never fatal."""
    handle = node.parm(parm_name)
    if handle is None:
        print(f"[warn] {node.name()}: no parm '{parm_name}' -- skipped")
        return False
    try:
        if expression is not None:
            handle.setExpression(expression, hou.exprLanguage.Hscript)
        else:
            handle.set(value)
    except Exception as exc:
        print(f"[warn] {node.name()}.{parm_name}: {exc}")
        return False
    return True


def _build_controls(hou, geo):
    """controls null carrying every promoted parm for the V2 asset."""
    controls = geo.createNode("null", "controls")
    group = controls.parmTemplateGroup()
    for name, label, ncomp, default, lo, hi in CATASTRAL_CONTROLS_PARMS:
        # default may be an int (e.g. (4,)) or a float (e.g. (10.0,))
        if isinstance(default[0], float):
            group.append(hou.FloatParmTemplate(name, label, ncomp,
                                               default_value=default, min=lo, max=hi))
        elif isinstance(default[0], int):
            group.append(hou.IntParmTemplate(name, label, ncomp,
                                             default_value=default, min=lo, max=hi))
        else:
            group.append(hou.StringParmTemplate(name, label, ncomp,
                                                default_value=default))
    for item in CORRIDOR_CONTROLS_PARMS:
        if len(item) == 6:
            name, label, ncomp, default, lo, hi = item
        elif len(item) == 4:
            name, label, ncomp, default = item
            lo = hi = None
        else:
            name, label, default = item
            ncomp = 1
            lo = hi = None
        # default may be an int (e.g. (0,), (6,)) or a float (e.g. (4.0,), (0.35,))
        if isinstance(default[0], float):
            group.append(hou.FloatParmTemplate(name, label, ncomp,
                                               default_value=default, min=lo, max=hi))
        elif isinstance(default[0], int):
            group.append(hou.IntParmTemplate(name, label, ncomp,
                                             default_value=default, min=lo, max=hi))
        else:
            group.append(hou.StringParmTemplate(name, label, ncomp,
                                                default_value=default))
    controls.setParmTemplateGroup(group)
    return controls


def _seed_point(hou, geo, name: str):
    """A 1x1 Grid: exactly one point for a detail wrangle to iterate over."""
    grid = geo.createNode("grid", name)
    grid.parm("rows").set(1)
    grid.parm("cols").set(1)
    grid.parm("sizex").set(0.0)
    grid.parm("sizey").set(0.0)
    return grid


def build_cathedral(template: hou.GeoNode, controls) -> None:
    """Arch profile -> nave sweep -> crystal growth -> finish (thicken/bevel/floor)."""
    seed = _seed_point(hou, template, "arch_seed")

    profile = template.createNode("attribwrangle", "arch_profile")
    profile.parm("class").set(0)
    profile.parm("snippet").set(ARCH_PROFILE_VEX)
    profile.setInput(0, seed)
    profile.setNextInput(controls)

    nave = template.createNode("attribwrangle", "nave_sweep")
    nave.parm("class").set(0)
    nave.parm("snippet").set(NAVE_VEX)
    nave.setInput(0, profile)
    nave.setNextInput(controls)

    crystal = template.createNode("attribwrangle", "crystal_growth")
    crystal.parm("class").set(0)
    crystal.parm("snippet").set(CRYSTAL_VEX)
    crystal.setInput(0, nave)
    crystal.setNextInput(controls)

    # WELD THE BAY SEAMS before any finish work.
    weld = template.createNode("fuse", "weld_seams")
    _set(weld, "tol3d", 0.0001)
    weld.setInput(0, crystal)
    weld.setNextInput(controls)

    # THICKEN FIRST (solid slab), THEN BEVEL the exposed edges.
    thicken = template.createNode("polyextrude", "wall_thicken")
    _set(thicken, "group", "shell ribs")
    _set(thicken, "dist", None, 'chs("../controls/wall_thickness")')
    _set(thicken, "outputfront", 1)
    _set(thicken, "outputback", 1)
    _set(thicken, "outputside", 1)
    _set(thicken, "splittype", 1)
    thicken.setInput(0, weld)
    thicken.setNextInput(controls)

    bevel = template.createNode("polybevel::2.0", "edge_bevel")
    _set(bevel, "group", "shell ribs")
    _set(bevel, "offset", None, 'chs("../controls/bevel_width")')
    _set(bevel, "offsetmode", 1)
    _set(bevel, "divisions", None, 'chs("../controls/bevel_segments")')
    _set(bevel, "commonlimit", 1)
    _set(bevel, "groupflatangle", 30.0)
    bevel.setInput(0, thicken)
    bevel.setNextInput(controls)

    # Walkable floor, no shared points with the shell.
    floor_surface = template.createNode("grid", "floor_surface")
    _set(floor_surface, "orient", 0)
    _set(floor_surface, "sizex", None, 'chs("../controls/span")')
    _set(floor_surface, "sizey", None,
         'chs("../controls/span") * 0.75 * chs("../controls/bays")')
    _set(floor_surface, "ty", None,
         'chs("../controls/span") * 0.75 * chs("../controls/bays") * 0.5')
    _set(floor_surface, "rows", None, 'chs("../controls/floor_divisions")')
    _set(floor_surface, "cols", None, 'chs("../controls/floor_divisions")')
    _set(floor_surface, "tz", 0.001)

    normals = template.createNode("normal", "face_normals")
    _set(normals, "cuspangle", 40.0)
    normals.setInput(0, bevel)

    merged = template.createNode("merge", "merge_architecture")
    merged.setInput(0, normals)
    merged.setInput(1, floor_surface)

    out = template.createNode("output", "OUT_Cathedral")
    out.setInput(0, merged)
    out.setDisplayFlag(True)

    # Collision proxy (floor + walls, crystals dropped).
    blast = template.createNode("blast", "drop_crystals")
    _set(blast, "group", "crystal")
    _set(blast, "negate", 1)
    blast.setInput(0, merged)

    collision = template.createNode("output", "OUT_Collision")
    collision.parm("outputidx").set(2)
    collision.setInput(0, blast)
    collision.setDisplayFlag(True)

    # Rose window (decorative, separate output).
    rose_seed = _seed_point(hou, template, "rose_seed")
    rose = template.createNode("attribwrangle", "rose_window")
    rose.parm("class").set(0)
    rose.parm("snippet").set(ROSE_VEX)
    rose.setInput(0, rose_seed)
    rose.setNextInput(controls)

    rose_out = template.createNode("output", "OUT_Rose")
    rose_out.parm("outputidx").set(1)
    rose_out.setInput(0, rose)
    rose_out.setDisplayFlag(True)


def build_corridor(template: hou.GeoNode, controls) -> None:
    """Box-chain -> weld -> thicken/bevel -> LOD -> VDB atmosphere."""
    seed = _seed_point(hou, template, "corridor_seed")

    build = template.createNode("attribwrangle", "corridor_build")
    build.parm("class").set(0)
    build.parm("snippet").set(CORRIDOR_VEX)
    build.setInput(0, seed)
    build.setNextInput(controls)

    weld = template.createNode("fuse", "weld_corridor_seams")
    _set(weld, "tol3d", 0.0001)
    weld.setInput(0, build)
    weld.setNextInput(controls)

    thicken = template.createNode("polyextrude", "wall_thicken")
    _set(thicken, "group", "poly*")
    _set(thicken, "dist", None, 'chs("../controls/wall_thickness")')
    _set(thicken, "outputfront", 1)
    _set(thicken, "outputback", 1)
    _set(thicken, "outputside", 1)
    _set(thicken, "splittype", 1)
    thicken.setInput(0, weld)
    thicken.setNextInput(controls)

    bevel = template.createNode("polybevel::2.0", "edge_bevel")
    _set(bevel, "group", "poly*")
    _set(bevel, "offset", None, 'chs("../controls/bevel_width")')
    _set(bevel, "offsetmode", 1)
    _set(bevel, "divisions", None, 'chs("../controls/bevel_segments")')
    _set(bevel, "commonlimit", 1)
    _set(bevel, "groupflatangle", 30.0)
    bevel.setInput(0, thicken)
    bevel.setNextInput(controls)

    lod_chain = bevel
    lod_count = int(controls.parm("lod_count").eval())
    for i in range(lod_count):
        lr = template.createNode("polyreduce", "lod_remove_%d" % i)
        lr.setInput(0, lod_chain)
        # Simplify: progressive decimation, keep boundary
        lr.parm("decimationcontrol").set(1)
        lr.parm("percentage").set(0.25 - (0.1 * i))
        lr.parm("boundaryweight").set(1.0)
        lr.setDisplayFlag(True)
        lod_chain = lr

    vdb = template.createNode("volume", "vdb_fog_volume")
    vdb.setInput(0, lod_chain)
    vdb.parm("type").set(1)                   # 1 = fog
    vdb.parm("samplediv").set(20)
    vdb.setDisplayFlag(True)

    lit = template.createNode("volumevop", "vdb_light")
    lit.setInput(0, vdb)
    lit.setDisplayFlag(True)

    out = template.createNode("output", "OUT_Corridor")
    out.setInput(0, lit)
    out.setDisplayFlag(True)


# The corridor box-chain VEX referenced by build_corridor(). Defined after the
# builder that consumes it but executed at runtime by hython.
CORRIDOR_VEX = r"""
// Build the full corridor box chain, one axis-aligned box per bay.
// Input: a single seed point (kept at 1). Output: the complete corridor shell.
int corridor_bays    = chi("../controls/corridor_bays");
float corridor_span  = chf("../controls/corridor_span");
float corridor_height = chf("../controls/corridor_height");
float wall_thickness = chf("../controls/wall_thickness");
float bay_length  = chf("../controls/bay_length");
float seed_val = chf("../controls/seed");

float half_span  = corridor_span * 0.5;
float half_height = corridor_height * 0.5;
float bay_len = bay_length;

int seed_pts = npoints(0);
for (int i = 0; i < seed_pts; i++) removepoint(0, 0);
int seed_prims = nprimitives(0);
for (int i = 0; i < seed_prims; i++) removeprim(0, 0, 1);

// --- one box per bay; 6 faces each -----------------------------------------
for (int b = 0; b < corridor_bays; b++) {
    float z0 = b * bay_len;
    float z1 = z0 + bay_len;
    int base = npoints(0);

    int xl = addpoint(0, set(-half_span, 0.0, z0));
    int xr = addpoint(0, set( half_span, 0.0, z0));
    int xl2 = addpoint(0, set(-half_span, 0.0, z1));
    int xr2 = addpoint(0, set( half_span, 0.0, z1));
    int yb = addpoint(0, set(-half_span, corridor_height, z0));
    int yt = addpoint(0, set( half_span, corridor_height, z0));
    int yb2 = addpoint(0, set(-half_span, corridor_height, z1));
    int yt2 = addpoint(0, set( half_span, corridor_height, z1));

    addprim(0, "poly", xl, xr, xr2, xl2);
    addprim(0, "poly", yb, yt, yt2, yb2);
    addprim(0, "poly", xl, yb, yb2, xl2);
    addprim(0, "poly", xr, yt, yt2, xr2);
    addprim(0, "poly", xl, xr, yt, yb);
    addprim(0, "poly", xl2, xr2, yt2, yb2);
}
"""


def build_hda(out: Path) -> hou.ObjNode:
    """Build the full CrystalCathedralV2 HDA."""
    obj = hou.node("/obj")
    template = obj.createNode("geo", "CH_CrystalCathedralV2_Template")
    for child in template.children():
        try:
            child.destroy()
        except Exception:
            pass

    controls = _build_controls(hou, template)

    build_cathedral(template, controls)
    build_corridor(template, controls)

    template.layoutChildren()

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    asset = template.createDigitalAsset(
        name="CrystalCathedralV2",
        hda_file_name=str(out),
        description="Melodia Crystal Cathedral V2: vault + tiled corridor + LOD VDB atmosphere (commercial Houdini)",
        min_num_inputs=0,
        max_num_inputs=0,
    )
    return asset


def verify(out_path: Path) -> int:
    """Instantiate the HDA and assert output counts."""
    import hou
    obj = hou.node("/obj")
    inst = obj.createNode("CrystalCathedralV2", "verify_v2")
    if inst is None:
        print("[v2] FAIL: cannot instantiate HDA")
        return 1
    inst.cook(force=True, ignore_cached=True)

    out_cathedral = out_rose = out_collision = out_corridor = None
    for child in inst.allSubChildren():
        if child.type().name() != "output":
            continue
        if child.name() == "OUT_Cathedral":
            out_cathedral = child.geometry()
        elif child.name() == "OUT_Rose":
            out_rose = child.geometry()
        elif child.name() == "OUT_Collision":
            out_collision = child.geometry()
        elif child.name() == "OUT_Corridor":
            out_corridor = child.geometry()

    rc = 0
    labels = (
        ("Cathedral (post-finish)", out_cathedral),
        ("Rose window", out_rose),
        ("Collision proxy", out_collision),
        ("Corridor", out_corridor),
    )
    for label, geometry in labels:
        if geometry is None:
            print(f"FAIL {label}: no output geometry")
            rc = 1
            continue
        print(f"INFO {label}: verts={len(geometry.points())} "
              f"faces={len(geometry.prims())}")

    for child in inst.allSubChildren():
        errs = child.errors() if hasattr(child, "errors") else ()
        if not errs:
            continue
        first = str(errs[0]).strip().splitlines()[0]
        print(f"FAIL node error in {child.name()}: {first}")
        rc = 1

    inst.destroy()
    return rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--verify", action="store_true",
                    help="instantiate and check output counts without writing")
    args = ap.parse_args()

    try:
        import hou
    except ImportError:
        print("[v2] hou unavailable (run under hython)", file=sys.stderr)
        return 2

    print(f"[v2] Houdini {hou.applicationVersionString()} "
          f"license={hou.licenseCategory()}")

    if args.verify:
        return verify(args.out)

    asset = build_hda(args.out)
    print(f"[v2] HDA written: {args.out} ({args.out.stat().st_size} bytes) "
          f"as {asset.type().definition().nodeTypeName()}")
    return verify(args.out)


if __name__ == "__main__":
    sys.exit(main())
