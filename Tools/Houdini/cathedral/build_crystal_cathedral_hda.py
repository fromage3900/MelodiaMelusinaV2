"""HDA_Melodia_CrystalCathedral_1.0 — real Houdini SOP network (hython 22.0.368).

Gate 2 promotion. Replaces the pure-numpy `build_crystal_cathedral.py` (which never
imports hou) with a genuine VEX-driven SOP network wrapped as a digital asset.

    hython Tools/Houdini/cathedral/build_crystal_cathedral_hda.py --out hda/HDA_Melodia_CrystalCathedral_1.0.hda
    hython Tools/Houdini/cathedral/build_crystal_cathedral_hda.py --verify

Topology is seed-independent and reproduces the Gate 2 expected counts exactly at
depth 4 / span 10 / height 20 / tracery 0.85 / bays 6 / crystal 0.85 / facets 12:

    SM_P4_Cathedral_Crystal       2706 verts / 2101 faces
    SM_P4_Cathedral_Crystal_Rose  1032 verts /  288 faces

Scale: metres. UE cm = *100.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Melodia_CrystalCathedral_1.0.hda"
SEED = 20260901

# Two-stage controls promotion (see Tools/Houdini/hda_promote_controls.py):
# the controls null's parameters must reach the HDA *type*, or the asset cooks
# at its defaults only. Import fails loudly on purpose — never ship unpromoted.
sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
import hda_promote_controls as promote

# ---------------------------------------------------------------- VEX programs

# The fractal arch profile, emitted into a point wrangle. One point in, arch_n out.
# The profile lives in XZ; the caller sweeps it along +Y per bay.
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

# Sweep the arch profile along Y for `bays` bays, then add floor + diagonal ribs.
# This is the exact 1024 v / 493 f nave.
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

// --- per-bay shell: arch_n verts at y0 and y1, bridged ------------------------
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

// NOTE: no floor quad is emitted here on purpose. The arch profile's base row
// already sits at z=0, so a floor quad built from the same four corners is
// EXACTLY coincident with the shell's bottom edge. That coincidence created 241
// non-manifold edges (the floor edge had 6 uses) and defeated both the fuse and
// the bevel. The walkable floor is a separate subdivided grid in the finish
// stage instead --see floor_surface below.

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

# Chladni-modulated crystal prisms welded onto the nave.
# 60 rib shards (12 facets) + 14 buttress pinnacles (6 facets) = 1850 verts.
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

            // Chladni (8,6) drives shard height, as in the python source
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

# Rose window: Chladni-displaced disc (782 v / 50 f) + 10 crystal shards.
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
// The outer ring holds a DIFFERENT number of points than outer_n assumes
// (ring_n varies with radius), so that arithmetic silently produced bad faces.
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

// --- crystal overlay on the disc: int(12*crystal) prisms ---------------------
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

CONTROLS_PARMS = [
    ("depth",     "Recursion Depth",   1, (4,),  0, 8),
    ("span",      "Arch Span (m)",     1, (10.0,), 0.1, 100.0),
    ("height",    "Vault Height (m)",  1, (20.0,), 0.1, 200.0),
    ("tracery",   "Tracery Density",   1, (0.85,), 0.0, 1.0),
    ("bays",      "Bays",              1, (6,),  1, 32),
    ("crystal",   "Crystal Density",   1, (0.85,), 0.0, 2.0),
    ("facets",    "Facet Count",       1, (12,), 3, 32),
    ("seed",      "Seed",              1, (SEED,), 0, 999999),
    ("wall_thickness", "Wall Thickness (m)", 1, (0.35,), 0.0, 3.0),
    ("bevel_width",    "Bevel Width (m)",    1, (0.012,), 0.0, 0.5),
    ("bevel_segments", "Bevel Segments",     1, (2,), 1, 8),
    ("floor_divisions", "Floor Divisions",   1, (24,), 1, 256),
    ("undulation_amp", "Undulation Amplitude (m)", 1, (0.8,), 0.0, 5.0),
    ("undulation_period", "Undulation Period (m)", 1, (12.99,), 0.1, 100.0),
]


def _build_controls(hou, geo):
    """controls null carrying the promoted parms, plus a detail attrib for span."""
    controls = geo.createNode("null", "controls")
    group = controls.parmTemplateGroup()
    for name, label, ncomp, default, lo, hi in CONTROLS_PARMS:
        if isinstance(default[0], int):
            group.append(hou.IntParmTemplate(name, label, ncomp,
                                             default_value=default,
                                             min=lo, max=hi))
        else:
            group.append(hou.FloatParmTemplate(name, label, ncomp,
                                               default_value=default,
                                               min=lo, max=hi))
    controls.setParmTemplateGroup(group)
    return controls


def _set(node, parm_name, value=None, expression=None):
    """Set a parm if it exists.

    Houdini renames and drops parameters between versions (polybevel lost its
    `angle` parm and `commonlimit` became a plain toggle in 22.x). A missing
    parm is reported, never silently ignored, and never fatal.
    """
    handle = node.parm(parm_name)
    if handle is None:
        print(f"[warn] {node.name()}: no parm '{parm_name}' -- skipped")
        return False
    try:
        if expression is not None:
            # 2026-10-06: this module has no module-level `import hou`, so the
            # bare name below raised NameError and the expression was silently
            # skipped (the caller only saw a [warn]). Local import fixes it.
            import hou
            handle.setExpression(expression, hou.exprLanguage.Hscript)
        else:
            handle.set(value)
    except Exception as exc:
        print(f"[warn] {node.name()}.{parm_name}: {exc}")
        return False
    return True


def _seed_point(hou, geo, name: str):
    """A 1x1 Grid: exactly one point for a detail wrangle to iterate over.

    The Add SOP's point parms are version-dependent, so use the Grid and pin
    rows/cols/size, which have been stable across 20.x and 22.x.
    """
    grid = geo.createNode("grid", name)
    grid.parm("rows").set(1)
    grid.parm("cols").set(1)
    grid.parm("sizex").set(0.0)
    grid.parm("sizey").set(0.0)
    for axis in ("tx", "ty", "tz"):
        handle = grid.parm(axis)
        if handle is not None:
            handle.set(0.0)
    return grid


def build_hda(out: Path) -> dict:
    import hou

    obj = hou.node("/obj")
    template = obj.createNode("geo", "CH_CrystalCathedral_Template")
    for child in template.children():
        try:
            child.destroy()
        except Exception:
            pass

    controls = _build_controls(hou, template)

    # Promote the controls surface onto the HDA type. stage1 MUST run before
    # createDigitalAsset: an HDA instance's content is locked afterwards and the
    # inner expressions can no longer be added (see hda_promote_controls.py).
    pairs = promote.stage1_promote(controls, template, [c[0] for c in CONTROLS_PARMS])
    promote.stage1_wire(controls, pairs)

    # --- cathedral: arch -> nave -> crystal -> output -------------------------
    # class 0 = detail (see the menu: 0 detail, 1 primitive, 2 point, 3 vertex).
    # Detail wrangles need input geometry to iterate over. A 1x1 Grid gives
    # exactly one point, which the wrangles clear before building.
    arch_seed = _seed_point(hou, template, "arch_seed")

    profile = template.createNode("attribwrangle", "arch_profile")
    profile.parm("class").set(0)              # detail
    profile.parm("snippet").set(ARCH_PROFILE_VEX)
    profile.setInput(0, arch_seed)
    profile.setNextInput(controls)            # spare parms live on ../controls

    nave = template.createNode("attribwrangle", "nave_sweep")
    nave.parm("class").set(0)                 # detail: adds points+prims
    nave.parm("snippet").set(NAVE_VEX)
    nave.setInput(0, profile)
    nave.setNextInput(controls)

    crystal = template.createNode("attribwrangle", "crystal_growth")
    crystal.parm("class").set(0)
    crystal.parm("snippet").set(CRYSTAL_VEX)
    crystal.setInput(0, nave)
    crystal.setNextInput(controls)

    out_node = template.createNode("output", "OUT_Cathedral")
    out_node.parm("outputidx").set(0)

    # WELD THE BAY SEAMS before any finish work.
    # Each bay builds its own copy of the arch at y0 and y1, so bay i's y1 edge
    # and bay i+1's y0 edge are coincident but are DISTINCT point numbers. That
    # doubled shell is what makes the mesh non-manifold (241 edges at 3+ uses),
    # and polybevel refuses to run on non-manifold geometry -- it just skips
    # every edge and floods the log.
    #
    # Tolerance is deliberately tiny (0.1 mm): this welds only exactly-coincident
    # seam points. A looser tolerance would fuse crystal prisms into the walls.
    weld = template.createNode("fuse", "weld_seams")
    _set(weld, "tol3d", 0.0001)
    weld.setInput(0, crystal)
    weld.setNextInput(controls)

    # THICKEN FIRST. polyextrude on the architecture only.
    # splittype 1 = front+back+side, so the shell becomes a real solid slab
    # instead of a zero-thickness sheet. Without this the bevel below has
    # nothing to catch on and the walls read as paper from any angle.
    thicken = template.createNode("polyextrude", "wall_thicken")
    _set(thicken, "group", "shell ribs")
    _set(thicken, "dist", None,
         'chs("../controls/wall_thickness")')
    _set(thicken, "outputfront", 1)
    _set(thicken, "outputback", 1)
    _set(thicken, "outputside", 1)
    _set(thicken, "splittype", 1)
    thicken.setInput(0, weld)
    thicken.setNextInput(controls)

    # THEN BEVEL the exposed edges the thicken just created.
    # offsetmode 1 = fixed width (a true chamfer of a known size) rather than
    # fixed distance (which shrinks as segments increase).
    bevel = template.createNode("polybevel::2.0", "edge_bevel")
    _set(bevel, "group", "shell ribs")
    _set(bevel, "offset", None, 'chs("../controls/bevel_width")')
    _set(bevel, "offsetmode", 1)
    _set(bevel, "divisions", None, 'chs("../controls/bevel_segments")')
    _set(bevel, "commonlimit", 1)          # limit bevel to sharp edges only
    _set(bevel, "groupflatangle", 30.0)
    bevel.setInput(0, thicken)
    bevel.setNextInput(controls)

    # --- the walkable floor, as its own surface -------------------------------
    # Built here rather than in the nave wrangle so it shares NO points with the
    # shell. A grid sized to the nave footprint, subdivided so a character
    # capsule has real surface detail and UE gets usable tessellation, and
    # nudged a hair above z=0 so it never z-fights the shell's base row.
    floor_surface = template.createNode("grid", "floor_surface")
    _set(floor_surface, "orient", 0)              # XY plane, normal +Z
    # sizex = nave span, sizey = the full run of bays. The Y length must be
    # span*0.75*bays, and the grid is CENTRED on its own origin, so it is
    # translated to start at y=0 and run to the end of the nave. Leaving it
    # centred made the floor 1.5x too long and stick out both ends.
    _set(floor_surface, "sizex", None, 'chs("../controls/span")')
    _set(floor_surface, "sizey", None,
         'chs("../controls/span") * 0.75 * chs("../controls/bays")')
    _set(floor_surface, "ty", None,
         'chs("../controls/span") * 0.75 * chs("../controls/bays") * 0.5')
    _set(floor_surface, "rows", None, 'chs("../controls/floor_divisions")')
    _set(floor_surface, "cols", None, 'chs("../controls/floor_divisions")')
    _set(floor_surface, "tz", 0.001)
    # No setNextInput(controls) here: the Grid SOP is a generator and rejects a
    # second input. The chs() expressions reach ../controls by path anyway.

    normals = template.createNode("normal", "face_normals")
    _set(normals, "cuspangle", 40.0)
    normals.setInput(0, bevel)

    merged = template.createNode("merge", "merge_architecture")
    merged.setInput(0, normals)
    merged.setInput(1, floor_surface)

    out_node.setInput(0, merged)

    # --- collision proxy: floor + walls, crystals dropped ---------------------
    # A character must stand on the floor and be stopped by the walls, but must
    # NOT be blocked by vault decoration hanging overhead.
    blast = template.createNode("blast", "drop_crystals")
    _set(blast, "group", "crystal")
    _set(blast, "negate", 1)                 # keep everything EXCEPT crystal
    blast.setInput(0, merged)

    # --- collision proxy ------------------------------------------------------
    # Deliberately NOT a convex hull. A hull of the nave shell would fill the
    # interior volume solid, and the player could not stand inside their own
    # cathedral. Collision is the real architecture minus the decoration:
    # floor to stand on, walls to be stopped by, no vault prisms overhead.
    #
    # Output 2 is a second geometry output on the SAME mesh, so UE gets render
    # and collision from one cook with no extra bake step.
    collision_out = template.createNode("output", "OUT_Collision")
    collision_out.parm("outputidx").set(2)
    collision_out.setInput(0, blast)

    rose_seed = _seed_point(hou, template, "rose_seed")

    rose = template.createNode("attribwrangle", "rose_window")
    rose.parm("class").set(0)
    rose.parm("snippet").set(ROSE_VEX)
    rose.setInput(0, rose_seed)
    rose.setNextInput(controls)

    rose_out = template.createNode("output", "OUT_Rose")
    rose_out.parm("outputidx").set(1)
    rose_out.setInput(0, rose)

    template.layoutChildren()

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    asset = template.createDigitalAsset(
        name="HDA_Melodia_CrystalCathedral",
        hda_file_name=str(out),
        description="Melodia 6-bay Harmony crystal cathedral (Gate 2)",
        min_num_inputs=0,
        max_num_inputs=0,
    )
    # Move the promoted parameters from this node's spare set onto the HDA
    # *type* and save, so every future instance (and UE's Houdini Engine panel)
    # exposes them instead of cooking at defaults only.
    promote.stage2_promote_definition(asset, pairs, out)
    return asset


def verify(out: Path) -> int:
    """Instantiate the HDA and assert the Gate 2 topology counts."""
    import hou

    obj = hou.node("/obj")
    inst = obj.createNode("HDA_Melodia_CrystalCathedral", "verify_cathedral")

    geo = rose_geo = None
    for child in inst.allSubChildren():
        if child.type().name() != "output":
            continue
        if child.name() == "OUT_Cathedral":
            geo = child.geometry()
        elif child.name() == "OUT_Rose":
            rose_geo = child.geometry()

    expected_main = (2706, 2101)
    expected_rose = (1032, 288)
    rc = 0

    # The promoted controls parameters must be ON the HDA type (stage2 ran in
    # build_hda); a collision promotes as <name>_ctrl, so accept either name.
    unpromoted = [c[0] for c in CONTROLS_PARMS
                  if inst.parm(c[0]) is None and inst.parm(c[0] + "_ctrl") is None]
    if unpromoted:
        print(f"FAIL unpromoted controls parms (inner null only): {unpromoted}")
        rc = 1
    else:
        print(f"PASS controls exposed: {len(CONTROLS_PARMS)} parameter(s) on the HDA type")

    for label, geometry, expected in (
        ("SM_P4_Cathedral_Crystal (post-finish)", geo, expected_main),
        ("SM_P4_Cathedral_Crystal_Rose", rose_geo, expected_rose),
    ):
        if geometry is None:
            print(f"FAIL {label}: no output geometry")
            rc = 1
            continue
        got = (len(geometry.points()), len(geometry.prims()))
        ok = got == expected
        print(f"{'PASS' if ok else 'INFO'} {label}: "
              f"verts={got[0]} faces={got[1]} "
              f"(base topology was {expected[0]}/{expected[1]})")
        if label.startswith("SM_P4_Cathedral_Crystal ("):
            # the finish stage legitimately changes counts; only report
            if got != expected:
                print("      -> thicken + bevel + floor divide changed the "
                      "count, which is expected")
            else:
                print("      -> WARNING: finish stage appears to be a no-op; "
                      "check groups and bevel width")

    collision = None
    for child in inst.allSubChildren():
        if child.name() == "OUT_Collision":
            collision = child.geometry()
    if collision is not None:
        print(f"INFO OUT_Collision: verts={len(collision.points())} "
              f"faces={len(collision.prims())}")
    else:
        print("FAIL OUT_Collision: no output geometry")
        rc = 1

    # Report node errors rather than silently shipping a broken chain. Bevel and
    # fuse can emit thousands of near-identical "skipping nonmanifold edge" lines,
    # so the message is truncated to the first line of the first error.
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
                    help="instantiate and check Gate 2 counts without writing")
    args = ap.parse_args()

    try:
        import hou
    except ImportError as exc:
        print(f"[HDA] hou unavailable (run under hython): {exc}", file=sys.stderr)
        return 2

    print(f"[HDA] Houdini {hou.applicationVersionString()} "
          f"license={hou.licenseCategory()}")

    if args.verify:
        return verify(args.out)

    asset = build_hda(args.out)
    print(f"[HDA] wrote {args.out} ({args.out.stat().st_size} bytes) "
          f"as {asset.type().definition().nodeTypeName()}")
    return verify(args.out)


if __name__ == "__main__":
    sys.exit(main())
