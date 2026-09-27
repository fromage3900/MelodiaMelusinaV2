"""BRUTALIST material gate. Run inside Blender 5.2:

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" ^
        --background --factory-startup --python Tools/verify_brutalist_materials.py --

    options (after the `--`): --json OUT.json
             write the report (default Saved/Audit/brutalist_materials.json)
             --audit-blend PATH   open a staged .blend and audit real objects instead
             --skip-selftest      do not prove the detectors fire (NOT for CI)

Why this exists. For the whole life of `brutalist_materials.py` every surface rendered at
the Principled default grey. Two independent defects caused it and neither produced an
error anywhere:

  C  `_bsdf(nt, Base_Color=colour, ...)` -- underscore. The real socket is `Base Color`,
     with a space. The old helper's `if k in n.inputs:` guard failed and its
     `except Exception: pass` swallowed the miss, so the authored colour was dropped while
     `Roughness`/`Metallic` (correctly spelled) applied fine. Measured on the staged
     .blend: `Base Color` default_value == (0.8, 0.8, 0.8) on all 24 objects, including
     asphalt, which is authored at 0.13.

  A  `_board_form()` returned a raw Wave x Noise mix -- both greyscale 0..1 -- and the
     caller linked it straight into Base Color, so concrete's colour was *replaced* by
     the detail field instead of being detailed by it.

Both are silent-by-construction: the graph compiles, the material loads, the sheet
renders, nothing throws. A gate that only asks "did it build" cannot see either one. So
this gate asks the only question that matters -- what colour actually reaches Base Color
-- by resolving the socket backwards through whatever mix chain feeds it, and comparing
that against the authored value.

C8 is the part that makes the rest trustworthy: it re-creates both defects on purpose and
asserts this file notices. A detector that has never been shown to fail is a rumour. C10 does the
same for the stale-socket trap - it builds the order that shipped (a modifier first evaluated while
the Material socket was still None), requires the evaluation read to report the unstamped result,
then rebuilds the modifier and requires it to report the stamp.

With `--audit-blend` the gate judges the staged artifact instead of the library: every
group-input Material socket on every staged object must resolve to a material, each object must
carry exactly the slots it recorded on itself, every slot (not just slot 0) must reach its
authored Base Color, the multi-surface objects must actually be multi-slot, and - the check that
earns its keep - each of those objects must EVALUATE to at least two stamped materials. That last
one is not redundant: a GN modifier captures the socket values at its first evaluation, so a
modifier built while the sockets were still None keeps None as an instance value that outranks the
interface default forever. Every interface then reads as wired and only the evaluated output shows
the split never happened. None of these read the staging manifest - it can be stale while the
.blend is new. The one-slot cases (office, cubicle, roof) are derived from what each object
recorded rather than from a builder allowlist, because a hand-written allowlist reports a correct
file as broken.

Exit codes:
    0  all checks pass
    1  a check failed
    2  invoked without bpy (plain `python Tools/verify_brutalist_materials.py`)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

try:
    import bpy
except ImportError:
    sys.stderr.write(
        "\n[verify_brutalist_materials] bpy not available - must run inside Blender.\n"
        "  Correct invocation:\n"
        '    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"'
        " --background --factory-startup --python Tools/verify_brutalist_materials.py\n\n"
    )
    raise SystemExit(2)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(REPO, "deploy")
sys.path.insert(0, DEPLOY)

from surreal_arch.melodia_gn import brutalist_materials as bmat   # noqa: E402

TOL = 2e-3            # colours are float; authored tuples are exact assignments
MAX_WALK = 8          # Base Color may sit behind Komikaze overlay + detail tint

results = []


def check(name, ok, detail="", tier="FAIL"):
    status = "SKIP" if tier == "SKIP" else ("PASS" if ok else "FAIL")
    results.append((name, status, detail))
    print("MATGATE %-5s %-30s %s" % (status, name, detail))
    return ok


def _principled(mat):
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None


def resolve_base(mat):
    """What colour actually reaches Base Color.

    Walks backwards following each ShaderNodeMix's `A` input -- `A` is the base in both
    the detail tint (MULTIPLY: colour x pattern) and the Komikaze overlay (MIX: colour +
    ink), so the authored value always sits on that spine. Returns
    (kind, colour_or_None, terminal_node):

        flat     unlinked default                                -> colour present
        tinted   a MULTIPLY mix whose A holds the authored value   -> colour present
        overlay  a MIX overlay whose A is a literal                -> colour present
        opaque   chain ends at something with no literal (a raw texture) -> THE DEFECT
        deep     chain longer than MAX_WALK
        nobrdf / nosocket
    """
    b = _principled(mat)
    if b is None:
        return ("nobrdf", None, None)
    sock = b.inputs.get("Base Color")
    if sock is None:
        return ("nosocket", None, None)
    if not sock.is_linked:
        return ("flat", tuple(sock.default_value), None)
    node = sock.links[0].from_node
    for _ in range(MAX_WALK):
        blend = getattr(node, "blend_type", None)
        if blend not in ("MIX", "MULTIPLY"):         # a texture/bump: no colour literal
            return ("opaque", None, node)
        a = node.inputs.get("A")
        if a is None:
            return ("opaque", None, node)
        if not a.is_linked:
            kind = "tinted" if blend == "MULTIPLY" else "overlay"
            return (kind, tuple(a.default_value), node)
        node = a.links[0].from_node
    return ("deep", None, node)


GOOD_KINDS = ("flat", "tinted", "overlay")


def _close(a, b):
    if a is None or b is None or len(a) < 3 or len(b) < 3:
        return False
    return all(abs(a[i] - b[i]) <= TOL for i in range(3))


def _chroma(rgb):
    return max(rgb[:3]) - min(rgb[:3]) if rgb and len(rgb) >= 3 else 0.0


def eval_materials(ob):
    """What the modifier stack ACTUALLY outputs: (faces, index_hist, stamped, unmapped).

    Returns None if the object cannot be evaluated. This is the only read in this
    file that can see the instance-value trap: a GN modifier captures the Material
    socket values at its first evaluation, so a modifier built while the sockets
    were still None keeps None as an INSTANCE value that outranks the group
    interface default forever after. Every static read - the interface, the
    outliner, the material slots - then says "wired" while the output geometry is
    unstamped. Measured 2026-09-26: all 11 cities reported hist {0: 738} and a
    [None] material list in that state; deleting and re-adding the modifier on the
    same object produced {0:102, 1:60, 2:576} and the real material names.
    """
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev = ob.evaluated_get(deps)
    try:
        me = ev.to_mesh()
    except Exception:
        return None
    if me is None:
        return None
    hist, stamped, unmapped = {}, set(), 0
    for poly in me.polygons:
        idx = poly.material_index
        hist[idx] = hist.get(idx, 0) + 1
        mat = me.materials[idx] if idx < len(me.materials) else None
        if mat is None:
            unmapped += 1
        else:
            stamped.add(mat.name)
    faces = len(me.polygons)
    ev.to_mesh_clear()
    return faces, dict(sorted(hist.items())), sorted(stamped), unmapped


# ---------------------------------------------------------------------------
# C8: the failure proof. Re-create both defects and require this file to see them.
# ---------------------------------------------------------------------------
def inject_defect_c():
    """Defect C exactly as shipped: the underscore kwarg, silently dropped by the guard."""
    before = len(bmat.SKIPPED_INPUTS)
    mat = bpy.data.materials.new("BR_SELFTEST_DEFECT_C")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    bmat._bsdf(nt, **{"Base_Color": (0.60, 0.59, 0.55, 1.0), "Roughness": 0.88})
    return mat, before


def inject_defect_a():
    """Defect A exactly as shipped: raw greyscale detail linked straight into Base Color."""
    mat = bpy.data.materials.new("BR_SELFTEST_DEFECT_A")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.60, 0.59, 0.55, 1.0)
    wave = nt.nodes.new("ShaderNodeTexWave")       # greyscale 0..1
    noise = nt.nodes.new("ShaderNodeTexNoise")     # greyscale 0..1
    raw = nt.nodes.new("ShaderNodeMix")            # the OLD _board_form return value
    raw.data_type = "RGBA"
    nt.links.new(wave.outputs["Color"], raw.inputs["A"])
    nt.links.new(noise.outputs["Color"], raw.inputs["B"])
    nt.links.new(raw.outputs["Result"], b.inputs["Base Color"])
    return mat


def purge_selftest():
    for name in ("BR_SELFTEST_DEFECT_C", "BR_SELFTEST_DEFECT_A"):
        mat = bpy.data.materials.get(name)
        if mat is not None:
            bpy.data.materials.remove(mat)
    for ob_name in ("SELFTEST_STAMP_OB",):
        ob = bpy.data.objects.get(ob_name)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
    for name in ("SELFTEST_TREE", "SELFTEST_STAMP_TREE"):
        tree = bpy.data.node_groups.get(name)
        if tree is not None:
            bpy.data.node_groups.remove(tree)
    for me_name in ("SELFTEST_MESH", "SELFTEST_STAMP_MESH"):
        me = bpy.data.meshes.get(me_name)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def build_wiring_selftest_tree():
    """A throwaway tree + mesh that exercise the staging wiring path itself."""
    name = "SELFTEST_TREE"
    old = bpy.data.node_groups.get(name)
    if old is not None:
        bpy.data.node_groups.remove(old)
    from surreal_arch.melodia_gn import core as _core
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    tree.nodes.new("NodeGroupInput")
    tree.nodes.new("NodeGroupOutput")
    _core.add_material_param(tree, "Massing Material")
    _core.add_material_param(tree, "Ground Material")
    me = bpy.data.meshes.get("SELFTEST_MESH") or bpy.data.meshes.new("SELFTEST_MESH")
    ob = bpy.data.objects.new("SELFTEST_OB", me)
    return tree, ob

def build_stamp_selftest_tree():
    """The smallest real instance of the staging pattern: one cube, one Set
    Material node, fed from one group-input Material socket. Unlike the wiring
    tree above this one produces geometry, so it can be evaluated."""
    name = "SELFTEST_STAMP_TREE"
    old = bpy.data.node_groups.get(name)
    if old is not None:
        bpy.data.node_groups.remove(old)
    from surreal_arch.melodia_gn import core as _core
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    _core.add_material_param(tree, "Surface Material")
    gin = tree.nodes.new("NodeGroupInput")
    gout = tree.nodes.new("NodeGroupOutput")
    cube = tree.nodes.new("GeometryNodeMeshCube")
    stamp = tree.nodes.new("GeometryNodeSetMaterial")
    tree.links.new(cube.outputs["Mesh"], stamp.inputs["Geometry"])
    tree.links.new(gin.outputs["Surface Material"], stamp.inputs["Material"])
    tree.links.new(stamp.outputs["Geometry"], gout.inputs["Geometry"])
    me = bpy.data.meshes.new("SELFTEST_STAMP_MESH")
    ob = bpy.data.objects.new("SELFTEST_STAMP_OB", me)
    bpy.context.scene.collection.objects.link(ob)      # must be in the view layer to evaluate
    return tree, ob


def build_checks():
    """The 14x2 library, checked against what was authored rather than against 'it built'."""
    stems = [v[0] for v in bmat.SURFACES.values()]
    check("C1_surface_library", len(stems) == len(set(stems)) and len(bmat.SURFACES) >= 14,
          "%d surfaces, %d unique stems" % (len(bmat.SURFACES), len(set(stems))))
    check("C1b_finish_sets",
          bmat.BOARD_FORM.issubset(set(bmat.SURFACES))
          and bmat.VEINED.issubset(set(bmat.SURFACES))
          and not (bmat.BOARD_FORM & bmat.VEINED),
          "BOARD_FORM=%s VEINED=%s" % (sorted(bmat.BOARD_FORM), sorted(bmat.VEINED)))

    bmat.SKIPPED_INPUTS.clear()
    lib = {}
    for surface in bmat.SURFACES:
        for look in bmat.LOOKS:
            lib["%s:%s" % (surface, look)] = bmat.build_brutalist_material(surface, look)
    check("C2_no_skipped_inputs", not bmat.SKIPPED_INPUTS,
          ("%d dropped: %s" % (len(bmat.SKIPPED_INPUTS), bmat.SKIPPED_INPUTS[:4]))
          if bmat.SKIPPED_INPUTS else
          "%d materials built, every requested socket landed" % len(lib))

    bad = []
    for key in sorted(lib):
        authored = bmat.SURFACES[key.split(":")[0]][1]
        kind, colour, term = resolve_base(lib[key])
        if kind not in GOOD_KINDS:
            bad.append("%s kind=%s terminal=%s" % (key, kind, getattr(term, "type", term)))
        elif not _close(colour, authored):
            bad.append("%s resolved %s authored %s" % (key, colour[:3], authored[:3]))
    check("C3_authored_colour", not bad,
          ("%d/%d wrong: %s" % (len(bad), len(lib), bad[:3])) if bad
          else "all %d resolve to their authored colour" % len(lib))

    flat = []
    for key in sorted(lib):
        authored = bmat.SURFACES[key.split(":")[0]][1]
        if _chroma(authored) < 0.02:
            continue                       # genuinely neutral surface, nothing to preserve
        kind, colour, _t = resolve_base(lib[key])
        if colour is None or _chroma(colour) < 0.02:
            flat.append("%s authored chroma %.3f -> resolved %s"
                        % (key, _chroma(authored),
                           "%.3f" % _chroma(colour) if colour else "None"))
    check("C4_chroma_survives", not flat,
          ("%d lost their hue: %s" % (len(flat), flat[:3])) if flat
          else "every chromatic surface still reads chromatic")

    wrong = []
    for surface in bmat.SURFACES:
        kinds = set(n.type for n in lib["%s:PBR" % surface].node_tree.nodes)
        wave, ramp = "TEX_WAVE" in kinds, "VALTORGB" in kinds
        if surface in bmat.BOARD_FORM and not wave:
            wrong.append("%s is a cast pour but has no board wave" % surface)
        elif surface in bmat.VEINED and (wave or not ramp):
            wrong.append("%s is quarried but carries board marks" % surface)
        elif surface not in bmat.BOARD_FORM and surface not in bmat.VEINED and wave:
            wrong.append("%s was never cast or quarried but has wave marks" % surface)
    check("C5_finish_follows_origin", not wrong,
          "; ".join(wrong[:3]) if wrong else "board marks only on poured surfaces")

    same = [s for s in bmat.SURFACES
            if len(lib["%s:PBR" % s].node_tree.nodes)
            == len(lib["%s:Komikaze" % s].node_tree.nodes)]
    check("C6_looks_differ", not same,
          ("%d identical to PBR: %s" % (len(same), same[:4])) if same
          else "Komikaze adds nodes on all %d surfaces" % len(bmat.SURFACES))
    return lib




def selftest():
    """Prove the two detectors fire, by re-creating the two shipped defects."""
    purge_selftest()
    mc, before = inject_defect_c()
    grew = len(bmat.SKIPPED_INPUTS) > before
    kind, colour, _t = resolve_base(mc)
    check("C7_detects_defect_C", grew and not _close(colour, (0.60, 0.59, 0.55, 1.0)),
          "underscore kwarg -> %d new skip(s); resolved colour %s vs authored 0.60/0.59/0.55"
          % (len(bmat.SKIPPED_INPUTS) - before,
             [round(v, 2) for v in colour[:3]] if colour else None))
    ma = inject_defect_a()
    kind, colour, term = resolve_base(ma)
    check("C8_detects_defect_A", kind == "opaque",
          "raw greyscale detail -> kind=%s terminal=%s (gate requires 'opaque')"
          % (kind, getattr(term, "type", term)))
    tree, ob = build_wiring_selftest_tree()
    wire = bmat.set_material_slots(
        tree, {"Massing Material": "concrete",
               "Ground Material": "asphalt",
               "Nope Material": "concrete"})
    slots = bmat.assign_surfaces(ob, ["concrete", "asphalt", "concrete"])
    bpy.data.objects.remove(ob, do_unlink=True)
    ok_wire = (len(wire["set"]) == 2 and len(wire["missing"]) == 1
               and slots == [bmat.material_name("concrete", "PBR"),
                             bmat.material_name("asphalt", "PBR")])
    check("C9_wiring_path", ok_wire,
          "2 sockets set, 1 missing reported, slots=%s" % slots)
    # C10: the instance-value trap, and its fix. Reproduce the order that shipped
    # - modifier created and evaluated while the Material socket is still None -
    # and require this file's own evaluation read to see the unstamped output;
    # then rebuild the modifier (the fix) and require it to see the stamp. Both
    # halves matter: without the first the detector is unproven, and without the
    # second "wire the sockets before the modifier" is an unverified theory.
    tree2, ob2 = build_stamp_selftest_tree()
    mod = ob2.modifiers.new("GN", "NODES")
    mod.node_group = tree2
    bpy.context.view_layer.update()            # first evaluation: socket still None
    bmat.set_material_slots(tree2, {"Surface Material": "concrete"})
    bpy.context.view_layer.update()
    trapped = eval_materials(ob2)
    ob2.modifiers.remove(mod)
    mod = ob2.modifiers.new("GN", "NODES")
    mod.node_group = tree2
    bpy.context.view_layer.update()
    freed = eval_materials(ob2)

    def _brief(got):
        return "None" if got is None else "faces=%d stamped=%s" % (got[0], got[2])

    check("C10_instance_value_trap",
          trapped is not None and freed is not None
          and not trapped[2] and len(freed[2]) >= 1,
          "socket set after first evaluation -> %s; modifier rebuilt -> %s"
          % (_brief(trapped), _brief(freed)))
    purge_selftest()
    bmat.SKIPPED_INPUTS.clear()


def audit_blend(path):
    """Read a staged .blend and report what its objects really carry.

    Every judgement here is measured against something the FILE holds - the
    object's own `brutalist_surfaces` record, and the group-interface Material
    sockets on the object's live modifier. A sibling manifest is not consulted,
    because it can be stale in either direction relative to the .blend.

    Office and cubicle builders expose no Material sockets, so one slot is their
    correct state; the roof exposes exactly `Roof Material`, which resolves to
    the same surface it already carries on slot 0, so one slot is correct there
    too. Both of those are DERIVED from the recorded surface list. The previous
    revision carried a hand-written `single_ok` builder allowlist and would have
    reported a correct file as broken the first time anyone audited the roof
    sheet.
    """
    if not os.path.exists(path):
        check("blend_present", False, "no such file %s" % path)
        return
    bpy.ops.wm.open_mainfile(filepath=path)
    rows, unwired, mismatch, wrong = [], [], [], []
    expect_multi = multi = recorded_n = 0
    unsplit, blank = [], {}
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.data.materials:
            continue
        if ob.name.startswith("SWATCH_"):        # palette board, not a staged object
            continue
        mod = next((m for m in ob.modifiers
                    if m.type == "NODES" and m.node_group), None)
        # (1) every Material socket on the live group interface must be wired.
        # An unwired one is exactly the shipped defect: the tree stamps nothing
        # on those faces, so they inherit slot 0 and the sheet looks plausible.
        if mod is not None:
            for it in mod.node_group.interface.items_tree:
                if (getattr(it, "in_out", "") == "INPUT"
                        and getattr(it, "socket_type", "") == "NodeSocketMaterial"
                        and it.default_value is None):
                    unwired.append("%s.%s" % (ob.name, it.name))
        recorded = [s.strip() for s in str(ob.get("brutalist_surfaces", "")).split(",")
                    if s.strip()]
        actual = [m.name for m in ob.data.materials if m is not None]
        # (2) what the object was asked for must be what it carries, in order.
        if recorded:
            recorded_n += 1
            if recorded != actual:
                mismatch.append("%s asks %s carries %s" % (ob.name, recorded, actual))
            if len(recorded) > 1:
                expect_multi += 1
                multi += 1 if len(actual) > 1 else 0
        # (2b) BEHAVIOURAL, and the reason this check exists: a GN modifier
        # captures the Material socket values at its first evaluation. If they
        # were still None then, the modifier keeps None as an INSTANCE value
        # which outranks the group-interface default forever after - so every
        # interface reads as wired, check (1) passes, and the output geometry is
        # still unstamped. Measured 2026-09-26: hist {0:738} on all 11 cities
        # while all three interfaces held real materials. Only evaluating the
        # modifier sees this.
        if mod is not None and len(recorded) > 1:
            got = eval_materials(ob)
            if got is None:
                unsplit.append("%s: could not evaluate" % ob.name)
            else:
                faces, hist, named, unmapped = got
                if len(named) < 2:
                    unsplit.append("%s: %d faces -> index %s, stamped %s (wanted >=2 of %s)"
                                   % (ob.name, faces, hist, named, recorded))
                if unmapped:
                    blank[ob.name] = unmapped
        # (3) EVERY slot must reach its authored colour, not just slot 0 - a
        # split that routes asphalt/glazing through a broken node is the defect
        # slot 0 cannot see.
        for slot, mat in enumerate(ob.data.materials):
            if mat is None:
                continue
            kind, colour, _t = resolve_base(mat)
            surface = mat.get("brutalist_surface")
            authored = bmat.SURFACES[surface][1] if surface in bmat.SURFACES else None
            if kind not in GOOD_KINDS or (authored and not _close(colour, authored)):
                wrong.append("%s[%d]=%s kind=%s" % (ob.name, slot, mat.name, kind))
        rows.append({"ob": ob.name, "slots": actual, "builder": ob.get("brutalist_builder"),
                     "missing": ob.get("brutalist_socket_missing")})
    n = len(rows) or 1
    check("blend_sockets_wired", not unwired,
          ("%d group-input Material socket(s) left unset: %s"
           % (len(unwired), unwired[:4])) if unwired
          else "every Material socket on %d staged object(s) resolves to a material" % n)
    check("blend_slots_match_surfaces", not mismatch,
          ("%d object(s) carry different slots than they recorded: %s"
           % (len(mismatch), mismatch[:2])) if mismatch
          else ("no object records a surface list (artifact predates the recording, "
                "nothing to compare)" if not recorded_n
                else "all %d recorded object(s) carry exactly the material(s) they asked for"
                % recorded_n))
    check("blend_colours_authored", not wrong,
          ("%d slot(s) do NOT reach their authored Base Color: %s"
           % (len(wrong), wrong[:4])) if wrong
          else "all %d objects, every slot, reach the authored Base Color" % n)
    check("blend_split_present", expect_multi > 0 and multi == expect_multi,
          "%d/%d multi-surface objects actually carry more than one slot"
          % (multi, expect_multi))
    note = ("; unstamped faces (no material, they render as the default grey): %d across %d object(s)"
            % (sum(blank.values()), len(blank))) if blank else "; no unstamped faces"
    check("blend_eval_split", not unsplit,
          ("%d object(s) record a split but EVALUATE to one material: %s%s"
           % (len(unsplit), unsplit[:2], note)) if unsplit
          else ("all %d multi-surface object(s) evaluate to >=2 stamped materials%s"
                % (expect_multi, note)))
    return rows


def main(argv):
    ap = argparse.ArgumentParser(description="BRUTALIST material gate")
    ap.add_argument("--json", dest="json_out", default=None)
    ap.add_argument("--audit-blend", dest="audit_blend", default=None)
    ap.add_argument("--skip-selftest", action="store_true",
                    help="do not prove the detectors fire; never use in CI")
    args = ap.parse_args(argv)

    if args.audit_blend:
        audit_blend(args.audit_blend)
    else:
        build_checks()
        if not args.skip_selftest:
            selftest()
        elif not any(r[0] == "C7_detects_defect_C" for r in results):
            check("C7_C8_selftest", False, "--skip-selftest given: detectors unproven",
                  tier="SKIP")

    failed = [r for r in results if r[1] == "FAIL"]
    out = args.json_out or os.path.join(REPO, "Saved", "Audit", "brutalist_materials.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"checks": [{"name": n, "status": s, "detail": d} for n, s, d in results],
                   "failures": len(failed)}, fh, indent=1)
    print("MATGATE %s  %d checks, %d failed -> %s"
          % ("FAIL" if failed else "PASS", len(results), len(failed), out))
    return 1 if failed else 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    raise SystemExit(main(argv))
