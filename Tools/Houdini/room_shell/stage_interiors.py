"""Stage the Poitou interior room-shell family as drop-in Houdini Digital Assets.

One HDA per interior variant, with that variant's parameters baked as TYPE
DEFAULTS: dropping melodia::room_shell_poitou_bedroom::1.0 into a level and
touching nothing yields exactly the staged bedroom. Nothing in Content/ is
overwritten and no level is touched.

The family has one owner (the RoomShell definition) and one standard portal:
a 2.4 m (one bar) wide, 3.2 m high floor-level opening. Rect rooms stay on the
2.4 m bay grid; the measured artist salon is the single documented exception.

Every variant is cooked from pure defaults and gated on:
  * the module gate (gate_json.all_pass),
  * declared vs measured footprint,
  * standard portal width/height and 0.6 m head clearance,
  * portal corner clearance and same-wall separation,
  * window/portal plan separation on shared walls (the module gate does not
    check this - a window and a door can currently intersect),
  * engine Y-up/up-axis mapping and determinism.

Run with hython:
  hython Tools/Houdini/room_shell/stage_interiors.py \
      --rect-source <contact-floor hda> --rounded-source <rounded hda> \
      --out Saved/Staging/PoitouInteriors_20261025 \
      --audit Saved/Audit/PoitouInteriors_20261025
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

import hou

RECT_TYPE = "melodia::room_shell_contact::1.0"
ROUNDED_TYPE = "melodia::room_shell_rounded::1.0"

BAY_M = 2.4
MODULE_M = 0.6
STANDARD_PORTAL = dict(width=2.4, height=3.2)
HEAD_CLEARANCE_M = 0.6
CORNER_CLEARANCE_M = 0.3
WINDOW_PORTAL_CLEARANCE_M = 0.3  # keep a reveal between a window and a door

# The staged family. `params` land as TYPE defaults; anything omitted is
# inherited from the converged contact-floor definition.
VARIANTS = [
    dict(
        id="bedroom",
        family="rect",
        label="Melodia Poitou Interior - Bedroom",
        story_tag="the scholar's own clutter breaking the clean system",
        room_w=7.2, room_d=9.6, room_h=4.2,
        decor="nikki_bead_swag",
        windows_long=2, windows_short=0,
        portals=[dict(id="bedroom_door", wall="S", s=3.6, width=2.4, height=3.2)],
    ),
    dict(
        id="bedroom_small",
        family="rect",
        label="Melodia Poitou Interior - Small Bedroom",
        story_tag="a narrower bedchamber of the same house, same system",
        room_w=4.8, room_d=7.2, room_h=4.2,
        decor="paris_haussmann",
        windows_long=2, windows_short=0,
        portals=[dict(id="bedroom_small_door", wall="S", s=2.4, width=2.4, height=3.2)],
    ),
    dict(
        id="landing",
        family="rect",
        label="Melodia Poitou Interior - Landing",
        story_tag="a threshold, barely lived in",
        room_w=4.8, room_d=4.8, room_h=4.2,
        decor="paris_haussmann",
        windows_long=0, windows_short=0,
        portals=[dict(id="landing_in", wall="W", s=2.4, width=2.4, height=3.2),
                 dict(id="landing_out", wall="E", s=2.4, width=2.4, height=3.2)],
    ),
    dict(
        id="landing_wide",
        family="rect",
        label="Melodia Poitou Interior - Long Landing",
        story_tag="the stair hall: the house's circulation held in one long room",
        room_w=9.6, room_d=4.8, room_h=4.2,
        decor="paris_haussmann",
        windows_long=1, windows_short=0,
        portals=[dict(id="landing_in", wall="W", s=2.4, width=2.4, height=3.2),
                 dict(id="landing_out", wall="E", s=2.4, width=2.4, height=3.2)],
    ),
    dict(
        id="salon_measured",
        family="rounded",
        label="Melodia Poitou Interior - Salon (measured)",
        story_tag="the library reaching into the salon - the house's scholarship on display",
        room_w=15.84, room_d=12.06, room_h=7.6,
        plan_shape=0, plan_sides=16, plan_exponent=2.6, plan_segments=96,
        tiers=[1.0, 0.92, 0.84],
        bay_aligned=False,
        bay_note="measured artist salon from L_MelusinaHouse_P0; 15.84/2.4 = 6.6 bays",
        portals=[dict(id="salon_entry", theta=0.25, width=2.4, height=3.2),
                 dict(id="salon_front", theta=0.75, width=2.4, height=3.2)],
    ),
    dict(
        id="salon_bay",
        family="rounded",
        label="Melodia Poitou Interior - Salon (bay aligned)",
        story_tag="the same salon snapped to the 2.4 m bay grid so it joins the house kit",
        room_w=16.8, room_d=12.0, room_h=7.2,
        plan_shape=1, plan_sides=16, plan_exponent=2.6, plan_segments=96,
        tiers=[1.0, 0.92, 0.84],
        portals=[dict(id="salon_entry", theta=0.25, width=2.4, height=3.2),
                 dict(id="salon_front", theta=0.75, width=2.4, height=3.2)],
    ),
    dict(
        id="salon_bay_stepped",
        family="rounded",
        label="Melodia Poitou Interior - Salon (bay, stepped massing)",
        story_tag="the salon seen from the canal: the ziggurat that tells you it is the big room",
        room_w=16.8, room_d=12.0, room_h=7.2,
        plan_shape=1, plan_sides=16, plan_exponent=2.6, plan_segments=96,
        tiers=[1.0, 0.85, 0.70],
        portals=[dict(id="salon_entry", theta=0.25, width=2.4, height=3.2),
                 dict(id="salon_front", theta=0.75, width=2.4, height=3.2)],
    ),
]

DECOR_MENU = ("paris_haussmann", "nikki_bead_swag", "nikki_star_pendant",
              "gothic_reveal", "heart_filigree")


# ------------------------------------------------------------------ definition surgery
def set_defaults(definition, values):
    """Set TYPE defaults with clone()+replace(); returns what actually landed."""
    group = definition.parmTemplateGroup()
    applied, missing = {}, []
    for name, value in values.items():
        template = group.find(name)
        if template is None:
            missing.append(name)
            continue
        template = template.clone()
        if isinstance(template, hou.MenuParmTemplate):
            template.setDefaultValue(int(value))
        elif isinstance(template, hou.ToggleParmTemplate):
            template.setDefaultValue(bool(value))
        elif isinstance(template, hou.StringParmTemplate):
            template.setDefaultValue(tuple(value) if isinstance(value, (tuple, list)) else (str(value),))
        else:
            template.setDefaultValue(tuple(value) if isinstance(value, (tuple, list)) else (value,))
        group.replace(name, template)
        applied[name] = value
    definition.setParmTemplateGroup(group)
    return applied, missing


def copy_variant(source_hda, module_path, type_name, label, destination):
    """Copy one definition into a new type, swap its PythonModule, leave source intact."""
    source_hda, module_path, destination = Path(source_hda), Path(module_path), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    before = hashlib.sha256(source_hda.read_bytes()).hexdigest()
    definition = hou.hda.definitionsInFile(str(source_hda))[0]
    definition.copyToHDAFile(str(destination), type_name, label)
    after = hashlib.sha256(source_hda.read_bytes()).hexdigest()
    assert before == after, "source HDA changed during copy: %s" % source_hda
    hou.hda.installFile(str(destination))
    candidate = next(d for d in hou.hda.definitionsInFile(str(destination))
                     if d.nodeTypeName() == type_name)
    candidate.addSection("PythonModule", module_path.read_text(encoding="utf-8"))
    return candidate, before, hashlib.sha256(destination.read_bytes()).hexdigest()


# ------------------------------------------------------------------ measurement
def load_module(path):
    """Load a RoomShell module by path so its material contract can be read without hou."""
    spec = importlib.util.spec_from_file_location("melodia_%s" % path.stem, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_game_path(game_path, content_root):
    """Resolve a /Game/ asset path to its .uasset on disk, or None when it does not exist."""
    if not game_path.startswith("/Game/"):
        return None
    candidate = Path(content_root) / (game_path[len("/Game/"):] + ".uasset")
    return candidate if candidate.is_file() else None


def snapshot(node, yup, role_materials=None):
    node.parm("engine_y_up").set(yup)
    if node.parm("engine_flip"):
        node.parm("engine_flip").set(yup)
    node.cook(force=True)
    if node.errors():
        raise RuntimeError("cook errors: %s" % list(node.errors()))
    geo = node.geometry()
    digest = hashlib.sha256()
    digest.update(repr(geo.pointFloatAttribValues("P")).encode())
    digest.update(repr(geo.vertexFloatAttribValues("uv")).encode())
    digest.update(repr([[v.point().number() for v in p.vertices()] for p in geo.prims()]).encode())
    rendered = geo.findPrimGroup("rendered_main_geo")
    collision = geo.findPrimGroup("collision_geo_simple_box_main_geo")
    prim_attrs = [a.name() for a in geo.primAttribs()]
    role_counts, material_mismatch = {}, []
    if role_materials and "unreal_material" in prim_attrs:
        for prim in geo.prims():
            role = prim.attribValue("material_role")
            if not role:
                continue                       # the collision slab carries no material role
            target = prim.attribValue("unreal_material")
            role_counts[role] = role_counts.get(role, 0) + 1
            if target != role_materials.get(role):
                material_mismatch.append([role, target])
    collision_bounds = None
    if collision:
        points = [tuple(v.point().position()) for p in collision.prims() for v in p.vertices()]
        collision_bounds = [[min(p[i] for p in points) for i in range(3)],
                            [max(p[i] for p in points) for i in range(3)]]
    return dict(
        y_up=bool(yup),
        points=len(geo.points()),
        prims=len(geo.prims()),
        bbox=[list(geo.boundingBox().minvec()), list(geo.boundingBox().maxvec())],
        geometry_sha256=digest.hexdigest(),
        gate=json.loads(geo.attribValue("gate_json")),
        sockets=json.loads(geo.attribValue("sockets_json")),
        rendered_group_prims=len(rendered.prims()) if rendered else None,
        collision_group_prims=len(collision.prims()) if collision else None,
        collision_bounds=collision_bounds,
        vertex_attributes=[a.name() for a in geo.vertexAttribs()],
        prim_attributes=prim_attrs,
        role_prim_counts=dict(sorted(role_counts.items())),
        unmapped_roles=[r for r in sorted(role_counts) if r not in (role_materials or {})],
        material_mismatch=material_mismatch[:8],
        material_mismatch_count=len(material_mismatch),
        errors=list(node.errors()),
        warnings=list(node.warnings()),
    )


def intervals_clear(a0, a1, b0, b1, gap):
    """True when two 1-D intervals keep at least `gap` of separation."""
    return a1 + gap <= b0 or b1 + gap <= a0


def check_portal(portal, axis_length, room_h):
    """Structural rules a portal must satisfy before it is worth cooking."""
    out = {}
    out["standard_width"] = abs(portal["width"] - STANDARD_PORTAL["width"]) < 1e-9
    out["standard_height"] = abs(portal["height"] - STANDARD_PORTAL["height"]) < 1e-9
    out["head_clearance_ok"] = portal["height"] <= room_h - HEAD_CLEARANCE_M + 1e-9
    if axis_length is not None:
        half = portal["width"] / 2.0
        out["corner_clearance_ok"] = (portal["s"] - half >= CORNER_CLEARANCE_M - 1e-9
                                      and portal["s"] + half <= axis_length - CORNER_CLEARANCE_M + 1e-9)
    return out


def main(rect_source, rounded_source, out_dir, audit_dir):
    out_dir, audit_dir = Path(out_dir), Path(audit_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    modules = dict(rect=Path(__file__).with_name("room_shell.py"),
                   rounded=Path(__file__).with_name("room_shell_rounded.py"))
    loaded = {k: load_module(v) for k, v in modules.items()}
    # One material contract for the whole family: the two modules must not drift into two
    # vocabularies (the rounded shell used to emit a "wall" role that no instance answers to).
    role_maps_agree = loaded["rect"].DEFAULT_ROLE_MATERIALS == loaded["rounded"].DEFAULT_ROLE_MATERIALS
    role_materials = dict(loaded["rect"].DEFAULT_ROLE_MATERIALS)
    content_root = Path(__file__).resolve().parents[3] / "Content"
    material_targets = {role: [path, resolve_game_path(path, content_root) is not None]
                        for role, path in sorted(role_materials.items())}
    sources = dict(rect=Path(rect_source), rounded=Path(rounded_source))
    source_sha = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in sources.items()}

    for path in (sources["rect"], sources["rounded"]):
        hou.hda.installFile(str(path))

    parent = hou.node("/obj").createNode("geo", "poitou_interiors_staging")
    parent.deleteItems(parent.children())

    report = dict(
        version=hou.applicationVersionString(),
        license=str(hou.licenseCategory()),
        source_hdas={k: dict(path=str(v), sha256=source_sha[k]) for k, v in sources.items()},
        modules={k: dict(path=str(v), sha256=hashlib.sha256(v.read_bytes()).hexdigest())
                 for k, v in modules.items()},
        standard_portal=dict(STANDARD_PORTAL, bay_m=BAY_M, module_m=MODULE_M,
                             head_clearance_m=HEAD_CLEARANCE_M),
        material_contract=dict(role_materials=role_materials,
                               targets=material_targets,
                               role_maps_agree=role_maps_agree,
                               content_root=str(content_root)),
        variants={},
        checks={},
    )

    for variant in VARIANTS:
        family = variant["family"]
        type_name = "melodia::room_shell_poitou_%s::1.0" % variant["id"]
        hda_path = out_dir / ("MelodiaRoomShell_Poitou_%s_1.0.hda" % variant["id"])
        candidate, source_before, hda_sha = copy_variant(
            sources[family], modules[family], type_name, variant["label"], hda_path)

        defaults = dict(room_w=variant["room_w"], room_d=variant["room_d"], room_h=variant["room_h"],
                        wall_t=0.24, engine_y_up=1, engine_flip=1)
        if family == "rect":
            defaults["decor"] = DECOR_MENU.index(variant["decor"])
            defaults["windows_long"] = variant["windows_long"]
            defaults["windows_short"] = variant["windows_short"]
            defaults["openings_json"] = json.dumps(variant["portals"], separators=(",", ":"))
            defaults["simple_floor_collision"] = 1
        else:
            defaults.update(plan_shape=variant["plan_shape"], plan_sides=variant["plan_sides"],
                            plan_exponent=variant["plan_exponent"],
                            plan_segments=variant["plan_segments"],
                            tiers_json=json.dumps(variant["tiers"], separators=(",", ":")))
            defaults["openings_json"] = json.dumps(variant["portals"], separators=(",", ":"))
        applied, missing = set_defaults(candidate, defaults)

        node = parent.createNode(type_name, variant["id"])
        # A freshly created node is the drop-in test: nothing is touched below
        # until the pure-default snapshot has been taken.
        at_default = dict(
            room_w=node.evalParm("room_w"), room_d=node.evalParm("room_d"),
            room_h=node.evalParm("room_h"), wall_t=node.evalParm("wall_t"),
            engine_y_up=node.evalParm("engine_y_up"), engine_flip=node.evalParm("engine_flip"),
            openings_json=node.evalParm("openings_json"),
            decor=node.parm("decor").evalAsString() if node.parm("decor") else None,
            windows_long=node.evalParm("windows_long") if node.parm("windows_long") else None,
            windows_short=node.evalParm("windows_short") if node.parm("windows_short") else None,
            simple_floor_collision=(node.evalParm("simple_floor_collision")
                                    if node.parm("simple_floor_collision") else None),
            tiers_json=node.evalParm("tiers_json") if node.parm("tiers_json") else None,
            plan_shape=node.evalParm("plan_shape") if node.parm("plan_shape") else None,
        )
        defaults_landed = (
            abs(at_default["room_w"] - variant["room_w"]) < 1e-9
            and abs(at_default["room_d"] - variant["room_d"]) < 1e-9
            and abs(at_default["room_h"] - variant["room_h"]) < 1e-9
            and at_default["engine_y_up"] == 1 and at_default["engine_flip"] == 1
            and json.loads(at_default["openings_json"]) == variant["portals"]
        )
        if family == "rect":
            defaults_landed = defaults_landed and at_default["decor"] == variant["decor"] \
                and at_default["simple_floor_collision"] == 1
        else:
            defaults_landed = defaults_landed and json.loads(at_default["tiers_json"]) == variant["tiers"] \
                and at_default["plan_shape"] == variant["plan_shape"]

        native = snapshot(node, 0, role_materials)   # measure in the native Houdini frame
        repeat = snapshot(node, 0, role_materials)
        ue = snapshot(node, 1, role_materials)       # UE/Houdini Engine frame stays the shipped default

        W, D, H = variant["room_w"], variant["room_d"], variant["room_h"]
        t = 0.24
        windows = native["sockets"].get("windows") or []
        # Exterior drip ledges project 3 cm past the wall face on walls that carry a
        # window (room_shell.gate uses the same allowance). The floor slab and the
        # simple collision box never project.
        projection = 0.03 if windows else 0.0
        project_x = projection if any(w.get("wall") in ("W", "E") for w in windows) else 0.0
        project_y = projection if any(w.get("wall") in ("S", "N") for w in windows) else 0.0
        lo, hi = native["bbox"]
        footprint_exact = (abs(lo[0] + t + project_x) < 1e-3
                           and abs(hi[0] - (W + t + project_x)) < 1e-3
                           and abs(lo[1] + t + project_y) < 1e-3
                           and abs(hi[1] - (D + t + project_y)) < 1e-3
                           and -0.25 <= lo[2] <= 0.0 and H <= hi[2] <= H + 0.25)
        ue_lo, ue_hi = ue["bbox"]
        ue_axis_exact = (abs(ue_lo[0] - lo[0]) < 1e-6 and abs(ue_hi[0] - hi[0]) < 1e-6
                         and abs(ue_lo[1] - lo[2]) < 1e-6 and abs(ue_hi[1] - hi[2]) < 1e-6
                         and abs(ue_lo[2] + hi[1]) < 1e-6 and abs(ue_hi[2] + lo[1]) < 1e-6)

        # Footprint must land on the 2.4 m bay grid; the measured artist salon is
        # the single documented exception and is declared exempt per variant.
        bay_aligned = all(abs(v / BAY_M - round(v / BAY_M)) < 1e-9 for v in (W, D))
        bay_expected = variant.get("bay_aligned", True)

        portal_checks = {}
        sockets_out = native["sockets"].get("opening_sockets") or []
        for portal in variant["portals"]:
            axis_length = None
            if portal.get("wall") in ("S", "N"):
                axis_length = W
            elif portal.get("wall") in ("W", "E"):
                axis_length = D
            portal_checks[portal["id"]] = check_portal(portal, axis_length, H)

        sockets_by_id = {q["id"]: q for q in sockets_out}
        portals_survive = sorted(sockets_by_id) == sorted(p["id"] for p in variant["portals"])
        portals_floor_level = all(q["floor_z_m"] == 0.0 for q in sockets_out)
        portals_native_cut = all(q["native_cut"] for q in sockets_out)
        socket_widths = {q["id"]: q["clear_width_m"] for q in sockets_out}

        # window/portal separation on shared walls - not covered by the module gate
        window_conflicts = []
        for portal in variant["portals"]:
            wall = portal.get("wall")
            if not wall:
                continue
            p0, p1 = portal["s"] - portal["width"] / 2.0, portal["s"] + portal["width"] / 2.0
            window_conflicts += [
                dict(portal=portal["id"], window=w.get("id"), wall=wall)
                for w in windows
                if w.get("wall") == wall
                and not intervals_clear(p0, p1, w["s0"], w["s1"], WINDOW_PORTAL_CLEARANCE_M)
            ]

        collision_ok = True
        if family == "rect":
            bounds = native["collision_bounds"]
            expected = [[-t, -t, -0.2], [W + t, D + t, 0.0]]
            collision_ok = (native["collision_group_prims"] == 6
                            and bounds is not None
                            and native["rendered_group_prims"] ==
                                native["prims"] - native["collision_group_prims"]
                            and all(abs(bounds[j][i] - expected[j][i]) < 1e-5
                                    for j in range(2) for i in range(3)))
        variant_report = dict(
            id=variant["id"], family=family, type_name=type_name,
            label=variant["label"], story_tag=variant["story_tag"],
            hda=str(hda_path), hda_sha256=hda_sha,
            module=str(modules[family]), module_sha256=report["modules"][family]["sha256"],
            source_sha256=source_before,
            declared=dict(room_w=W, room_d=D, room_h=H, wall_t=t,
                          exterior_projection_m=projection,
                          portals=variant["portals"],
                          decor=variant.get("decor"),
                          windows_long=variant.get("windows_long"),
                          windows_short=variant.get("windows_short"),
                          plan_shape=variant.get("plan_shape"),
                          tiers=variant.get("tiers"),
                          bay_aligned_expected=bay_expected,
                          bay_note=variant.get("bay_note")),
            defaults_requested=applied, defaults_missing=missing, at_default=at_default,
            native=dict(points=native["points"], prims=native["prims"], bbox=native["bbox"],
                        geometry_sha256=native["geometry_sha256"], gate=native["gate"],
                        rendered_group_prims=native["rendered_group_prims"],
                        collision_group_prims=native["collision_group_prims"],
                        collision_bounds=native["collision_bounds"],
                        warnings=native["warnings"]),
            ue_frame=dict(points=ue["points"], prims=ue["prims"], bbox=ue["bbox"],
                          geometry_sha256=ue["geometry_sha256"]),
            sockets=[dict(id=q["id"], wall=q.get("wall"), theta=q.get("theta"), bay=q.get("bay"),
                          centre_local_m=q.get("center_local_m") or q.get("centre_local_m"),
                          clear_width_m=q["clear_width_m"], clear_height_m=q["clear_height_m"],
                          floor_z_m=q["floor_z_m"], s0=q["s0"], s1=q["s1"],
                          native_cut=q.get("native_cut"))
                     for q in sockets_out],
            windows=[dict(wall=w.get("wall"), s0=w["s0"], s1=w["s1"]) for w in windows],
            portal_checks=portal_checks,
            checks=dict(
                defaults_landed=defaults_landed,
                cooks_at_defaults=not native["errors"],
                gate_all_pass=native["gate"]["all_pass"],
                deterministic=repeat["geometry_sha256"] == native["geometry_sha256"],
                footprint_exact=footprint_exact,
                engine_y_up_axis=ue_axis_exact,
                prims_unchanged_by_engine_frame=
                    ue["prims"] == native["prims"] and ue["points"] == native["points"],
                bay_aligned=bay_aligned == bay_expected,
                portals_survive=portals_survive,
                portals_floor_level=portals_floor_level,
                portals_native_cut=portals_native_cut,
                portals_match_standard_width=all(
                    abs(socket_widths.get(p["id"], -1) - STANDARD_PORTAL["width"]) < 1e-9
                    for p in variant["portals"]),
                portal_rules=all(all(v.values()) for v in portal_checks.values()),
                windows_clear_of_portals=not window_conflicts,
                uv_attribute_present="uv" in native["vertex_attributes"],
                material_role_present="material_role" in native["prim_attributes"],
                material_path_present="shop_materialpath" in native["prim_attributes"],
                unreal_material_present="unreal_material" in native["prim_attributes"],
                unreal_material_matches_role=native["material_mismatch_count"] == 0,
                roles_mapped=native["unmapped_roles"] == [],
                module_gate_roles_mapped=bool(native["gate"].get("roles_mapped")),
            ),
            role_prim_counts=native["role_prim_counts"],
            window_conflicts=window_conflicts,
        )
        # Simple floor collision is a rect-only feature; the rounded plan has no
        # slab yet, so it is recorded as unsupported rather than asserted true.
        variant_report["declared"]["simple_floor_collision_supported"] = family == "rect"
        if family == "rect":
            variant_report["checks"]["rendered_group_matches"] = (
                native["rendered_group_prims"] ==
                native["prims"] - native["collision_group_prims"])
            variant_report["checks"]["simple_floor_collision"] = collision_ok
        variant_report["all_pass"] = all(variant_report["checks"].values())
        report["variants"][variant["id"]] = variant_report

    report["checks"]["all_variants_pass"] = all(v["all_pass"] for v in report["variants"].values())
    report["checks"]["sources_unchanged"] = all(
        source_sha[k] == hashlib.sha256(sources[k].read_bytes()).hexdigest() for k in sources)
    report["checks"]["role_maps_agree"] = role_maps_agree
    report["checks"]["material_targets_exist"] = all(ok for _, ok in material_targets.values())
    report["checks"]["one_standard_portal_across_family"] = all(
        v["checks"]["portals_match_standard_width"] and v["portal_checks"] and
        all(q["standard_height"] for q in v["portal_checks"].values())
        for v in report["variants"].values())
    report["all_pass"] = all(report["checks"].values())
    report["limits"] = ("Native packaged-HDA geometry only. Each variant now emits an "
                        "`unreal_material` prim attribute resolving material_role to an existing "
                        "/Game/ material instance, and every target .uasset was found on disk; that "
                        "is file presence, NOT proof that Unreal Engine resolves the override or that "
                        "the material looks correct - both need an import, cook and material readback "
                        "in the editor. Nothing was imported into UE: HDA asset registration, actor "
                        "placement, capsule/BodySetup sweep, lighting, dressing fill and the packaged "
                        "route remain pending (editor was held by another session). opening_sockets "
                        "stay diagnostic JSON - no Houdini Engine mesh_socketX_* attributes are "
                        "emitted yet. The rect family inherits the absolute streamer_lib type "
                        "default from the source HDA.")

    manifest = dict(
        contract="melodia.p0.poitou_interior_stage.v1",
        generated=dict(version=report["version"], license=report["license"]),
        standard_portal=report["standard_portal"],
        sources=report["source_hdas"],
        variants=[dict(id=v["id"], family=v["family"], type_name=v["type_name"],
                       hda=v["hda"], hda_sha256=v["hda_sha256"],
                       label=v["label"], story_tag=v["story_tag"],
                       declared=v["declared"], sockets=v["sockets"],
                       prims=v["native"]["prims"], points=v["native"]["points"],
                       bbox=v["native"]["bbox"])
                  for v in report["variants"].values()],
    )
    gate_path = audit_dir / "interior_stage_gate.json"
    manifest_path = out_dir / "interior_manifest.json"
    durable_manifest = audit_dir / "interior_manifest.json"
    gate_path.write_text(json.dumps(report, indent=2))
    manifest_path.write_text(json.dumps(manifest, indent=2))
    durable_manifest.write_text(json.dumps(manifest, indent=2))

    summary = dict(
        checks=report["checks"],
        variants={k: dict(prims=v["native"]["prims"], all_pass=v["all_pass"],
                          failed=[c for c, ok in v["checks"].items() if not ok])
                  for k, v in report["variants"].items()},
        all_pass=report["all_pass"],
        evidence=str(gate_path),
        manifest=str(manifest_path),
    )
    print(json.dumps(summary, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rect-source", required=True)
    ap.add_argument("--rounded-source", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audit", required=True)
    a = ap.parse_args()
    raise SystemExit(main(a.rect_source, a.rounded_source, a.out, a.audit))
