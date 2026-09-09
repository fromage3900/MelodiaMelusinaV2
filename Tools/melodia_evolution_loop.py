"""Melodia Studio creative evolution loop — script-only (no LLM), deterministic.

Recursive overnight-style iteration over REGISTERED Melodia Studio builders:

  pick family (rotation) -> instantiate builders -> mutate exposed group-input
  params (seeded RNG, generation-derived) -> realize headless -> measure metrics
  -> score -> keep top-N winners per family -> winners seed the next generation
  -> Workbench thumbnail contact sheet -> append ledger JSONL + latest report

State:   Saved/Evolution/state.json          (generation counters, winner genomes)
Output:  Saved/Evolution/gen_NNN/*.png        (thumbnails)
         Saved/Evolution/ledger.jsonl         (one scored row per variant)
         Saved/Evolution/latest_report.md     (human digest of the last tick)

Families (documented Melusina/Melodia systems, all live registry ids):
  house     — melodia_house / mh6 / mh_foundation (Melusina House lineage)
  music     — notation + instruments (69-builder family)
  city      — city_gen + civic kit (city cell rewire targets)
  zen       — zen_kit (sanding/garden systems)
  filigree  — filigree + ornament (detail systems)
  sdf       — experimental SDF-ish forms (core_forms + experimental kit)

Run (one generation):
  blender.exe --background --factory-startup --python Tools/melodia_evolution_loop.py
Exit code 0 = generation completed and recorded. Safe to re-run; state advances.

Design rules honored:
  - read-only against the addon registry (never edits builder code)
  - never writes .uasset, never touches git
  - Saved/ only (gitignored) — outputs are proposals for human review
  - deterministic: seed = (generation, family, builder, slot) — reproducible
"""
import json
import os
import random
import sys
import time

import bpy

REPO = r"P:\MelodiaMelusinaV2-Laptop"
LIVE = os.path.expandvars(
    r"%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons")
sys.path.insert(0, LIVE if os.path.isdir(os.path.join(LIVE, "surreal_arch"))
                else os.path.join(REPO, "deploy"))

EVO_ROOT = os.path.join(REPO, "Saved", "Evolution")
STATE_PATH = os.path.join(EVO_ROOT, "state.json")
LEDGER_PATH = os.path.join(EVO_ROOT, "ledger.jsonl")
REPORT_PATH = os.path.join(EVO_ROOT, "latest_report.md")

FAMILIES = {
    "house": ["MEL_mh6_room_shell", "MEL_mh_aaa_cornice",
              "MEL_mh_aaa_dentil", "MEL_city_house_cell"],
    "music": ["MEL_music_staff", "MEL_music_treble_clef", "MEL_music_chord_stack",
              "MEL_music_harp_v2", "MEL_music_organ_pipes"],
    "city":  ["MEL_city_block", "MEL_city_avenue", "MEL_city_plan_courtyard",
              "MEL_city_house_cell"],
    "zen":   ["MEL_aest_zen_bonsai", "MEL_aest_zen_bamboo", "MEL_aest_zen_moss"],
    "filigree": ["MEL_filigree_core", "MEL_filigree_panel", "MEL_filigree_rail_inset"],
    "sdf":   ["MEL_pillar", "MEL_brick_wall", "MEL_aest_adv_crystals"],
}
# Family members are RESOLVED AT RUNTIME against the live registry: any listed
# id that is missing is dropped, and the slot is back-filled from the registry by
# category (preferred) then name-prefix, so the loop never skips a family silently
# and survives builder renames. See _resolve_family().
_FAMILY_CATEGORY = {
    "house": "melusina_house", "music": "music", "city": "city_gen",
    "zen": "zen_kit", "filigree": "filigree", "sdf": "experimental",
}
_FAMILY_PREFIX = {
    "house": ("MEL_mh",), "music": ("MEL_music",), "city": ("MEL_city",),
    "zen": ("MEL_aest_zen", "MEL_zen"), "filigree": ("MEL_filigree",),
    "sdf": ("MEL_pillar", "MEL_brick_wall", "MEL_aest_adv"),
}
VARIANTS_PER_BUILDER = 3
TOP_KEEP = 3          # winner genomes kept per family
MUTATE_RATE = 0.6     # probability a numeric socket is mutated
MAX_VERTS = 250_000   # reject runaway geometry (laptop budget)


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"generation": 0, "winners": {}, "family_last": None}


def save_state(st):
    os.makedirs(EVO_ROOT, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)


def family_for_generation(st):
    names = sorted(FAMILIES)
    last = st.get("family_last")
    idx = (names.index(last) + 1) % len(names) if last in names else 0
    return names[idx]


def mutate_tree_inputs(tree, rng, saved_genome=None):
    """Mutate exposed numeric group-input defaults. Returns genome dict."""
    genome = {}
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", None) != "INPUT":
            continue
        st = getattr(item, "socket_type", "")
        name = item.name
        if saved_genome and name in saved_genome:
            val = saved_genome[name]
        elif st == "NodeSocketFloat" or st == "NodeSocketInt":
            cur = getattr(item, "default_value", 0)
            if rng.random() < MUTATE_RATE:
                span = max(abs(cur), 1.0)
                val = cur + rng.uniform(-0.5, 0.5) * span
                if st == "NodeSocketInt":
                    lo = getattr(item, "min_value", 1)
                    hi = getattr(item, "max_value", 64)
                    val = max(int(lo), min(int(hi), int(round(val))))
                else:
                    lo = getattr(item, "min_value", None)
                    hi = getattr(item, "max_value", None)
                    if lo is not None:
                        val = max(float(lo), val)
                    if hi is not None:
                        val = min(float(hi), val)
                    val = round(val, 4)
            else:
                val = getattr(item, "default_value", cur)
        else:
            continue  # bool/geometry/string/vector: leave at default this gen
        try:
            item.default_value = val
        except Exception:
            continue
        genome[name] = val
    return genome


def realize_metrics(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    verts = len(me.vertices) if me else 0
    polys = len(me.polygons) if me else 0
    bbox = [0.0, 0.0, 0.0]
    if verts:
        xs = [v.co.x for v in me.vertices]
        ys = [v.co.y for v in me.vertices]
        zs = [v.co.z for v in me.vertices]
        bbox = [round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3),
                round(max(zs) - min(zs), 3)]
    if me:
        ev.to_mesh_clear()
    return verts, polys, bbox


def score_variant(verts, polys, bbox, errored):
    if errored or verts == 0:
        return 0.0
    if verts > MAX_VERTS:
        return 0.0
    import math
    vol = max(bbox[0] * bbox[1] * bbox[2], 1e-6)
    # reward moderate complexity + sane density; punish degenerate flats/runaways
    s = math.log10(max(verts, 10)) * 2.0
    s += math.log10(max(polys, 10)) * 1.0
    density = polys / max(verts, 1)
    s += 4.0 if 0.5 < density < 4.0 else 0.0
    flat = sum(1 for d in bbox if d < 0.01)
    s -= 3.0 * flat
    s -= 2.0 if vol > 10_000 else 0.0        # room-scale envelope cap
    return round(s, 3)


def thumb_render(out_png):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 480
    scene.render.resolution_y = 360
    scene.render.resolution_percentage = 100
    scene.render.filepath = out_png
    scene.render.image_settings.file_format = "PNG"
    # minimal camera framing the active object (workbench needs a camera)
    cam_ob = bpy.data.objects.get("EVO_Camera")
    if cam_ob is None:
        cam = bpy.data.cameras.new("EVO_Camera")
        cam_ob = bpy.data.objects.new("EVO_Camera", cam)
        scene.collection.objects.link(cam_ob)
    scene.camera = cam_ob
    # frame: place camera at a fixed 3/4 view around the object bbox center
    target = None
    for ob in scene.objects:
        if ob.name.startswith("EVO_") and ob.type == "MESH":
            target = ob
            break
    if target is not None:
        import mathutils
        cs = [target.matrix_world @ mathutils.Vector(c) for c in target.bound_box]
        center = sum(cs, mathutils.Vector()) / 8.0
        radius = max((v - center).length for v in cs) or 1.0
        d = radius * 2.8 + 1.0
        cam_ob.location = (center.x - d * 0.7, center.y - d * 0.7,
                           center.z + d * 0.55)
        direction = center - cam_ob.location
        rot = direction.to_track_quat("-Z", "Y")
        cam_ob.rotation_euler = rot.to_euler()
    bpy.ops.render.render(write_still=True)


def _resolve_family(family, GROUP_BUILDERS, GROUP_METADATA, rng):
    """Return >=1 live builder ids for a family: keep listed ids that exist,
    back-fill from registry by category then prefix (seeded sample for variety)."""
    ids = set(GROUP_BUILDERS)
    members = [b for b in FAMILIES[family] if b in ids]
    if members:
        return members
    cat = _FAMILY_CATEGORY.get(family)
    pool = sorted(k for k in ids if GROUP_METADATA.get(k, {}).get("category") == cat)
    if not pool:
        for pre in _FAMILY_PREFIX.get(family, ()):
            pool += [k for k in sorted(ids) if k.startswith(pre)]
    if not pool:
        return []
    k = min(len(pool), 4)
    return rng.sample(pool, k)


def run_generation():
    st = load_state()
    gen = st["generation"] + 1
    family = family_for_generation(st)
    st["family_last"] = family
    gen_dir = os.path.join(EVO_ROOT, "gen_%03d" % gen)
    os.makedirs(gen_dir, exist_ok=True)
    print("[EVO] generation %d family=%s" % (gen, family))

    from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA
    fam_rng = random.Random("%d:%s:family" % (gen, family))
    members = _resolve_family(family, GROUP_BUILDERS, GROUP_METADATA, fam_rng)
    if not members:
        print("[EVO] RESULT gen=%d family=%s scored=0 errors=0 (NO MEMBERS RESOLVED)"
              % (gen, family))
        st["generation"] = gen
        save_state(st)
        return 0
    print("[EVO]   members:", members)

    winners = st.setdefault("winners", {}).setdefault(family, [])
    winner_genomes = {w["builder"]: w.get("genome") for w in winners}
    rows = []

    for slot, bid in enumerate(members):
        fn = GROUP_BUILDERS.get(bid)
        if fn is None:
            print("[EVO]   skip %s (not in registry)" % bid)
            rows.append({"gen": gen, "family": family, "builder": bid,
                         "error": "not-registered", "score": 0.0})
            continue
        for v in range(VARIANTS_PER_BUILDER):
            rng = random.Random("%d:%s:%s:%d" % (gen, family, bid, v))
            ob_name = "EVO_%s_%d" % (bid, v)
            try:
                # winner exploitation: first variant continues best genome
                seed_genome = winner_genomes.get(bid) if v == 0 else None
                res = fn(group_name="%s_g%d_v%d" % (bid, gen, v))
                tree = res[0] if isinstance(res, (tuple, list)) else res
                genome = mutate_tree_inputs(tree, rng, seed_genome)
                me = bpy.data.meshes.new(ob_name + "_m")
                ob = bpy.data.objects.new(ob_name, me)
                bpy.context.scene.collection.objects.link(ob)
                mod = ob.modifiers.new("evo", "NODES")
                mod.node_group = tree
                verts, polys, bbox = realize_metrics(ob)
                err = None
                if verts == 0:
                    err = "empty"
                score = score_variant(verts, polys, bbox, bool(err))
                png = os.path.join(gen_dir, "%s_v%d.png" % (bid, v))
                if score > 0:
                    try:
                        thumb_render(png)
                    except Exception as e:
                        print("[EVO]   thumb fail %s: %s" % (bid, e))
                row = {"gen": gen, "family": family, "builder": bid, "variant": v,
                       "verts": verts, "polys": polys, "bbox": bbox,
                       "score": score, "error": err, "genome": genome,
                       "png": os.path.relpath(png, REPO) if os.path.exists(png) else None}
            except Exception as e:
                row = {"gen": gen, "family": family, "builder": bid, "variant": v,
                       "score": 0.0, "error": str(e)[:160]}
            rows.append(row)
            print("[EVO]   %s v%d score=%s verts=%s err=%s"
                  % (bid, v, row.get("score"), row.get("verts"), row.get("error")))
            # cleanup object so next variant starts fresh
            ob_del = bpy.data.objects.get(ob_name)
            if ob_del:
                bpy.data.objects.remove(ob_del, do_unlink=True)

    # keep top-N genomes for this family
    scored = [r for r in rows if r.get("score", 0) > 0 and "genome" in r]
    scored.sort(key=lambda r: -r["score"])
    per_builder = {}
    for r in scored:
        lst = per_builder.setdefault(r["builder"], [])
        if len(lst) < TOP_KEEP:
            lst.append({"builder": r["builder"], "score": r["score"],
                        "genome": r["genome"], "gen": gen})
    flat = [w for lst in per_builder.values() for w in lst]
    st["winners"][family] = flat[: TOP_KEEP * len(FAMILIES[family])]
    st["generation"] = gen
    save_state(st)

    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    # report
    ok = [r for r in rows if r.get("score", 0) > 0]
    lines = ["# Evolution gen %d — %s" % (gen, family),
             "",
             "- variants: %d  scored>0: %d  errors: %d"
             % (len(rows), len(ok), sum(1 for r in rows if r.get("error"))),
             "- best: %s" % (", ".join("%s=%s" % (r["builder"], r["score"])
                                      for r in scored[:5]) or "none"),
             "- thumbs: %s" % gen_dir,
             "- winners carried: %d genomes" % len(st["winners"][family]),
             "",
             "Review, then promote any winner genome manually — the loop never",
             "edits builder code or git. Promotion = param defaults worth baking.",
             ]
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("[EVO] RESULT gen=%d family=%s scored=%d errors=%d"
          % (gen, family, len(ok), sum(1 for r in rows if r.get("error"))))
    return 0


if __name__ == "__main__":
    t0 = time.time()
    sys.exit(run_generation())
