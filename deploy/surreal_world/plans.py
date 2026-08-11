"""Massing plan spawners with vertex-group tags."""

from __future__ import annotations

import bpy
import math


def create_plan_mesh(name, verts, edges, faces, vgroup_assignments=None, location=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, edges, faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    if vgroup_assignments:
        for gname, vids in vgroup_assignments.items():
            vg = obj.vertex_groups.new(name=gname)
            vg.add(list(vids), 1.0, "REPLACE")
    obj["surreal_plan_kind"] = name.split("_")[-1] if "_" in name else "custom"
    return obj


def spawn_castle_plan(location=(0, 0, 0), size=12.0):
    s = size / 2
    verts = [
        (-s, -s, 0), (0, -s, 0), (s, -s, 0), (s, 0, 0),
        (s, s, 0), (0, s, 0), (-s, s, 0), (-s, 0, 0),
        (-s * 0.3, -s * 0.3, 0), (s * 0.3, -s * 0.3, 0),
        (s * 0.3, s * 0.3, 0), (-s * 0.3, s * 0.3, 0),
    ]
    faces = [
        [8, 9, 10, 11], [0, 1, 9, 8], [1, 2, 3, 9], [9, 3, 4, 10],
        [10, 4, 5, 11], [11, 5, 6, 7], [8, 11, 7, 0],
    ]
    vgroups = {
        "is_corner_tower": [0, 2, 4, 6],
        "is_gate": [1],
        "is_keep": [8, 9, 10, 11],
    }
    return create_plan_mesh("SurrealPlan_Castle", verts, [], faces, vgroups, location)


def spawn_zen_roji_plan(location=(0, 0, 0), path_len=16.0, courtyard_w=8.0):
    """Roji approach: path strip + courtyard pad — torii at entry, sacred courtyard."""
    hl = path_len * 0.5
    cw = courtyard_w * 0.5
    verts = [
        (-2.0, -hl, 0), (2.0, -hl, 0), (2.0, 0, 0), (-2.0, 0, 0),
        (-cw, 0, 0), (cw, 0, 0), (cw, cw, 0), (-cw, cw, 0),
    ]
    faces = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
    ]
    vgroups = {
        "is_gate": [0, 1],
        "is_plaza": [4, 5, 6, 7],
        "is_sacred": [4, 5, 6, 7],
        "is_corner_tower": [0, 1],
    }
    return create_plan_mesh("SurrealPlan_ZenRoji", verts, [], faces, vgroups, location)


def spawn_zen_temple_plan(location=(0, 0, 0), path_len=20.0, courtyard_w=12.0, engawa_w=6.0):
    """Temple compound: roji path + sacred courtyard + engawa/teahouse wing."""
    hl = path_len * 0.5
    cw = courtyard_w * 0.5
    ew = engawa_w * 0.5
    verts = [
        (-2.2, -hl, 0), (2.2, -hl, 0), (2.2, 0, 0), (-2.2, 0, 0),
        (-cw, 0, 0), (cw, 0, 0), (cw, cw, 0), (-cw, cw, 0),
        (cw, cw, 0), (cw + ew, cw, 0), (cw + ew, cw + ew * 0.8, 0), (cw, cw + ew * 0.8, 0),
    ]
    faces = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
    ]
    vgroups = {
        "is_gate": [0, 1],
        "is_plaza": [4, 5, 6, 7],
        "is_sacred": [4, 5, 6, 7],
        "is_keep": [8, 9, 10, 11],
        "is_corner_tower": [0, 1],
    }
    return create_plan_mesh("SurrealPlan_ZenTemple", verts, [], faces, vgroups, location)


def spawn_village_plan(location=(0, 0, 0), n_plots=8, radius=8.0):
    """Radial village: plaza center + ring of plot quads."""
    verts = [(0.0, 0.0, 0.0)]
    inner_r = radius * 0.25
    for i in range(n_plots):
        ang = (i / n_plots) * math.tau
        verts.append((math.cos(ang) * inner_r, math.sin(ang) * inner_r, 0))
    for i in range(n_plots):
        ang = (i / n_plots) * math.tau
        verts.append((math.cos(ang) * radius, math.sin(ang) * radius, 0))
    plaza = [i + 1 for i in range(n_plots)]
    faces = [plaza]
    for i in range(n_plots):
        i_in = 1 + i
        i_in_n = 1 + (i + 1) % n_plots
        i_out = 1 + n_plots + i
        i_out_n = 1 + n_plots + (i + 1) % n_plots
        faces.append([i_in, i_out, i_out_n, i_in_n])
    vgroups = {
        "is_plaza": plaza,
        "is_corner_tower": [1 + n_plots + i for i in range(n_plots)],
        "is_gate": [1 + n_plots],
    }
    return create_plan_mesh("SurrealPlan_Village", verts, [], faces, vgroups, location)


def spawn_grid_city_plan(location=(0, 0, 0), grid=4, plot=4.0, street=1.5):
    """Grid city: NxN plot quads separated by street gaps."""
    verts = []
    faces = []
    cell = plot + street
    plaza_verts = set()
    for j in range(grid):
        for i in range(grid):
            base = len(verts)
            cx = (i - (grid - 1) / 2) * cell
            cy = (j - (grid - 1) / 2) * cell
            verts.append((cx - plot / 2, cy - plot / 2, 0))
            verts.append((cx + plot / 2, cy - plot / 2, 0))
            verts.append((cx + plot / 2, cy + plot / 2, 0))
            verts.append((cx - plot / 2, cy + plot / 2, 0))
            faces.append([base, base + 1, base + 2, base + 3])
            if i == grid // 2 and j == grid // 2:
                plaza_verts.update([base, base + 1, base + 2, base + 3])
    gate_verts = []
    for face in faces:
        for v in face:
            if verts[v][1] < -(grid - 1) / 2 * cell + 0.1:
                gate_verts.append(v)
    vgroups = {
        "is_plaza": list(plaza_verts),
        "is_gate": list(set(gate_verts))[:2],
    }
    return create_plan_mesh("SurrealPlan_City", verts, [], faces, vgroups, location)


def spawn_motte_bailey_plan(location=(0, 0, 0), motte_r=3.0, bailey_r=9.0):
    """Motte & Bailey: elevated motte keep + bailey ward ring."""
    n_motte = 8
    n_bailey = 12
    verts = []
    for i in range(n_motte):
        ang = (i / n_motte) * math.tau
        verts.append((math.cos(ang) * motte_r, math.sin(ang) * motte_r, 0.8))
    for i in range(n_bailey):
        ang = (i / n_bailey) * math.tau + math.pi / n_bailey
        verts.append((math.cos(ang) * bailey_r, math.sin(ang) * bailey_r, 0))
    motte_face = list(range(n_motte))
    faces = [motte_face]
    for i in range(n_bailey):
        i_b = n_motte + i
        i_b_n = n_motte + (i + 1) % n_bailey
        ang_b = ((i + 0.5) / n_bailey) * math.tau + math.pi / n_bailey
        m_idx = int(round(ang_b / math.tau * n_motte)) % n_motte
        faces.append([m_idx, i_b, i_b_n, (m_idx + 1) % n_motte])
    vgroups = {
        "is_keep": list(range(n_motte)),
        "is_corner_tower": [n_motte + i for i in range(0, n_bailey, 3)],
        "is_gate": [n_motte],
    }
    return create_plan_mesh("SurrealPlan_MotteBailey", verts, [], faces, vgroups, location)


PLAN_SPAWNERS = {
    "castle": spawn_castle_plan,
    "zen_roji": spawn_zen_roji_plan,
    "zen_temple": spawn_zen_temple_plan,
    "village": spawn_village_plan,
    "grid_city": spawn_grid_city_plan,
    "motte_bailey": spawn_motte_bailey_plan,
}
