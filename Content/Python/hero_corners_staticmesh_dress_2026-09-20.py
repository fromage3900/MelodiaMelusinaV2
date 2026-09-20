"""HeroCorner static mesh set-dress per Material Artist recipe 2026-09-20."""
from __future__ import annotations
import json, math, random
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary

MESHES = {
    'Rock_03': '/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_03/S_Rock_03',
    'Rock_04': '/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_04/S_Rock_04',
    'Rock_05': '/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_05/S_Rock_05',
    'Overgrowth_01': '/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_01',
    'Overgrowth_02': '/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_02',
    'Bush_S': '/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Small',
    'Bush_M': '/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Medium',
    'Mossy_01': '/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_01',
    'Mossy_02': '/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_02',
    'Mossy_03': '/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_03',
    'Shamrock_01': '/Game/Megascans/3D_Plants/PurpleShamrock/SM_PurpleShamrock_01',
    'Shamrock_02': '/Game/Megascans/3D_Plants/PurpleShamrock/SM_PurpleShamrock_02',
    'Shamrock_03': '/Game/Megascans/3D_Plants/PurpleShamrock/SM_PurpleShamrock_03',
    'GhostCore': '/Game/EnvSandbox/Meshes/SurrealFlora/GhostLotus_GlowCore',
    'GhostReceptacle': '/Game/EnvSandbox/Meshes/SurrealFlora/GhostLotus_Receptacle',
}

# Per-corner recipes: list of mesh keys + count targets
RECIPES = {
    'WestRim': {
        'seed': 202609201,
        'count': 6,
        'keys': ['Rock_03', 'Rock_04', 'Rock_05', 'Overgrowth_01', 'Overgrowth_02', 'Rock_04'],
        'rad': (220, 780),
        'scale': {
            'Rock': (0.55, 1.15), 'Overgrowth': (0.5, 0.95), 'default': (0.5, 1.0),
        },
    },
    'EastBank': {
        'seed': 202609202,
        'count': 7,
        'keys': ['Overgrowth_01', 'Bush_S', 'Bush_M', 'Shamrock_01', 'Shamrock_02', 'Overgrowth_02', 'Bush_S'],
        'rad': (180, 720),
        'scale': {
            'Bush': (0.45, 0.85), 'Overgrowth': (0.5, 0.9), 'Shamrock': (0.6, 1.2), 'default': (0.5, 1.0),
        },
    },
    'MeadowChorus': {
        'seed': 202609203,
        'count': 6,
        'keys': ['Mossy_01', 'Mossy_02', 'Shamrock_01', 'Shamrock_03', 'GhostCore', 'Mossy_01'],
        'rad': (350, 1100),
        'scale': {
            'Mossy': (0.5, 1.1), 'Shamrock': (0.55, 1.15), 'Ghost': (0.35, 0.7), 'default': (0.5, 1.0),
        },
    },
    'NorthDress': {
        'seed': 202609204,
        'count': 8,
        'keys': ['Mossy_02', 'Mossy_03', 'Shamrock_02', 'Shamrock_03', 'GhostReceptacle', 'Mossy_02', 'Shamrock_01', 'Mossy_03'],
        'rad': (200, 950),
        'scale': {
            'Mossy': (0.55, 1.2), 'Shamrock': (0.55, 1.2), 'Ghost': (0.35, 0.75), 'default': (0.5, 1.1),
        },
        'accept_any_solid': True,  # NorthDress often not Brushify
    },
}

FOCUS_VOL = {
    'WestRim': 'WC_HeroCorner_WestRim_PCG',
    'EastBank': 'WC_HeroCorner_EastBank_PCG',
    'MeadowChorus': 'WC_morning_rainbow_bloom_Field',
    'NorthDress': 'WC_HeroCorner_NorthDress_PCG',
}


def _label(a):
    try: return a.get_actor_label() or ''
    except: return ''


def ground_at(world, x, y, zhint):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, zhint + 5000), unreal.Vector(x, y, zhint - 8000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    return {'loc': t[4], 'normal': t[5], 'actor': t[9].get_actor_label() if t[9] else None, 'class': t[9].get_class().get_name() if t[9] else None}


def mesh_bottom_offset(mesh, scale):
    """Push actor up so mesh bottom sits on impact (local Z min * scale)."""
    try:
        box = mesh.get_bounding_box()
        zmin = float(box.min.z)
        return -zmin * scale  # if zmin negative, lift by |zmin|*scale
    except Exception:
        return 0.0


def scale_for(key, recipe, rng):
    ranges = recipe['scale']
    for prefix, rngv in ranges.items():
        if prefix != 'default' and key.startswith(prefix.replace('_', '')):
            pass
    # match by substring
    for tag, (lo, hi) in ranges.items():
        if tag == 'default':
            continue
        if tag.lower() in key.lower() or key.startswith(tag):
            return rng.uniform(lo, hi)
    lo, hi = ranges.get('default', (0.5, 1.0))
    return rng.uniform(lo, hi)


def material_slots(actor):
    slots = []
    try:
        for c in actor.get_components_by_class(unreal.StaticMeshComponent) or []:
            try:
                n = c.get_num_materials()
            except Exception:
                n = 0
            for i in range(n):
                try:
                    m = c.get_material(i)
                    slots.append(m.get_path_name() if m else None)
                except Exception:
                    slots.append(None)
    except Exception:
        pass
    return slots


def clear_prior_dress(svc):
    removed = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith('WC_HeroDress_') or lab.startswith('WC_HeroCornerDress_'):
            if svc.destroy_actor(a):
                removed.append(lab)
    return removed


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    # resolve meshes
    resolved = {}
    missing = []
    for k, p in MESHES.items():
        if EAL.does_asset_exist(p):
            resolved[k] = EAL.load_asset(p)
        else:
            missing.append(p)

    removed = clear_prior_dress(svc)
    placed = []
    per_corner = {}

    for corner, recipe in RECIPES.items():
        vlab = FOCUS_VOL[corner]
        vol = next((a for a in svc.get_all_level_actors() if _label(a) == vlab), None)
        if not vol:
            per_corner[corner] = {'error': f'missing volume {vlab}', 'actors': []}
            continue
        fl = vol.get_actor_location()
        focus = [fl.x, fl.y, fl.z]
        rng = random.Random(recipe['seed'])
        keys = recipe['keys']
        r0, r1 = recipe['rad']
        actors = []
        attempts = 0
        i = 0
        while len(actors) < recipe['count'] and attempts < recipe['count'] * 12:
            attempts += 1
            key = keys[len(actors) % len(keys)]
            mesh = resolved.get(key)
            if not mesh:
                # skip missing key
                if len(actors) >= recipe['count']:
                    break
                # advance by trying next key once
                key = keys[(len(actors) + attempts) % len(keys)]
                mesh = resolved.get(key)
                if not mesh:
                    continue
            ang = rng.uniform(0, math.tau)
            rad = rng.uniform(r0, r1)
            x = focus[0] + math.cos(ang) * rad
            y = focus[1] + math.sin(ang) * rad
            g = ground_at(world, x, y, focus[2] + 800)
            if not g:
                continue
            glab = g['actor'] or ''
            gcls = g['class'] or ''
            ok_ground = (
                glab.startswith('Brushify') or glab.startswith('WC_EscherWalk_')
                or 'Landscape' in gcls or glab.startswith('Landscape')
            )
            if recipe.get('accept_any_solid') and float(g['normal'].z) >= 0.55:
                ok_ground = True
            if not ok_ground:
                continue
            if float(g['normal'].z) < 0.55:
                continue
            sc = scale_for(key, recipe, rng)
            sc = max(0.45, min(1.35, sc))
            z_off = mesh_bottom_offset(mesh, sc)
            loc = unreal.Vector(g['loc'].x, g['loc'].y, g['loc'].z + z_off)
            yaw = rng.uniform(0, 360)
            actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
                mesh, loc, unreal.Rotator(0, yaw, 0))
            if not actor:
                continue
            mesh_name = Path(MESHES[key]).name
            name = f'WC_HeroDress_{corner}_{len(actors):02d}_{mesh_name}'
            actor.set_actor_label(name)
            actor.set_actor_scale3d(unreal.Vector(sc, sc, sc))
            try:
                actor.set_folder_path(f'HeroCorners/{corner}/SetDress')
                actor.tags = ['Portfolio', 'HeroCorner', 'SetDress', f'HeroCorner.{corner}']
            except Exception:
                pass
            rec = {
                'label': name,
                'corner': corner,
                'mesh': MESHES[key],
                'loc': [loc.x, loc.y, loc.z],
                'scale': sc,
                'yaw': yaw,
                'ground': glab,
                'ground_class': gcls,
                'normal_z': float(g['normal'].z),
                'materials': material_slots(actor),
            }
            actors.append(rec)
            placed.append(rec)
            i += 1
        per_corner[corner] = {'focus': focus, 'spawned': len(actors), 'attempts': attempts, 'actors': actors}

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        'schema': 'melodia.hero_corners_staticmesh_dress.v1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'removed_prior': removed,
        'missing_meshes': missing,
        'resolved_keys': sorted(resolved.keys()),
        'corners': per_corner,
        'total_placed': len(placed),
        'level_saved': saved,
        'do_not_touch': ['PCG graphs/volumes', 'HeroCorner cams', 'PPV_NikkiDream', 'NS_Morning_*', 'MI_RainbowSpeedTree_*'],
        'awaiting': 'Material Artist MI tune/green before recapture',
    }
    out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'hero_corners_staticmesh_dress_2026-09-20.json'
    out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print('HERODRESS ' + json.dumps({
        'total': len(placed),
        'per': {k: v.get('spawned') for k, v in per_corner.items()},
        'missing': missing,
        'saved': saved,
        'report': str(out),
    }, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
