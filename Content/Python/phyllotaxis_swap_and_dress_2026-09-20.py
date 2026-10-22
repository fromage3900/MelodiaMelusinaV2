"""Swap WestRim→Phyllotaxis, shrink HeroCorner PCG volumes, base-dress WestRim+EastBank."""
from __future__ import annotations
import json, math, random
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
GRAPH_DIR = "/Game/Melodia/WorldCompiler/HeroCorners"
PHYLLO = "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_PhyllotaxisGarden_Walkable"

DRESS_MESHES = [
    "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_01/S_Rock_01",
    "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_02/S_Rock_02",
    "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Small",
    "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Medium",
    "/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_01",
    "/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_02",
    "/Game/Brushify/Meshes/FloatingIslands/Dressing/Roots_01/S_Roots_01",
]

# Safer volume scales (were 3.5–4.5 → too big for Mandala/Meadow spawn)
VOL_SCALE = {
    "WestRim": (2.2, 2.2, 2.0),
    "EastBank": (2.0, 2.0, 1.8),
    "NorthDress": (2.8, 2.8, 2.2),
}


def _label(a):
    try: return a.get_actor_label() or ''
    except: return ''


def look_at(fv, tv):
    dx, dy, dz = tv.x-fv.x, tv.y-fv.y, tv.z-fv.z
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx*dx+dy*dy) or 1.0
    pitch = math.degrees(math.atan2(dz, horiz))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)


def ground_at(world, x, y, zhint=2000.0):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x,y,zhint+4000), unreal.Vector(x,y,zhint-6000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    return {'loc': t[4], 'normal': t[5], 'actor': t[9].get_actor_label() if t[9] else None}


def assign_gen(vol, graph_path, seed):
    graph = EAL.load_asset(graph_path)
    comp = vol.get_component_by_class(unreal.PCGComponent)
    if not comp or not graph:
        return False
    try:
        comp.set_graph(graph)
    except Exception:
        try:
            gi = comp.get_editor_property('graph_instance')
            if gi:
                gi.set_editor_property('graph', graph)
        except Exception:
            return False
    try:
        comp.set_editor_property('seed', seed & 0x7FFFFFFF)
    except Exception:
        pass
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    try:
        unreal.SystemLibrary.execute_console_command(world, 'pcg.FlushCache')
    except Exception:
        pass
    try:
        comp.generate(True)
        return True
    except Exception:
        return False


def swap_westrim(svc):
    dest = f"{GRAPH_DIR}/PCG_HeroCorner_WestRim"
    if EAL.does_asset_exist(dest):
        try: EAL.delete_asset(dest)
        except Exception: pass
    if not EAL.does_directory_exist(GRAPH_DIR):
        EAL.make_directory(GRAPH_DIR)
    ok = EAL.duplicate_asset(PHYLLO, dest)
    vol = next((a for a in svc.get_all_level_actors() if _label(a)=='WC_HeroCorner_WestRim_PCG'), None)
    gen = False
    if vol and ok:
        vol.set_actor_scale3d(unreal.Vector(*VOL_SCALE['WestRim']))
        gen = assign_gen(vol, dest, 90201)
    return {'duplicated': bool(ok), 'gen': gen, 'graph': dest, 'source': PHYLLO}


def shrink_volumes(svc):
    out = []
    for cid, sc in VOL_SCALE.items():
        for suffix in ('', '_Companion'):
            lab = f'WC_HeroCorner_{cid}_PCG{suffix}'
            vol = next((a for a in svc.get_all_level_actors() if _label(a)==lab), None)
            if not vol: continue
            before = vol.get_actor_scale3d()
            # companion slightly smaller
            s = sc if not suffix else (sc[0]*0.65, sc[1]*0.65, sc[2]*0.65)
            vol.set_actor_scale3d(unreal.Vector(*s))
            # regenerate
            comp = vol.get_component_by_class(unreal.PCGComponent)
            gen = False
            if comp:
                try:
                    comp.generate(True); gen = True
                except Exception:
                    pass
            after = vol.get_actor_scale3d()
            out.append({'label': lab, 'before': [before.x,before.y,before.z], 'after': [after.x,after.y,after.z], 'gen': gen})
    return out


def clear_my_dress(svc):
    n = 0
    for a in list(svc.get_all_level_actors()):
        if _label(a).startswith('WC_HeroCornerDress_'):
            svc.destroy_actor(a); n += 1
    return n


def dress_corner(svc, world, corner_id, focus, count=10):
    meshes = [(p, EAL.load_asset(p)) for p in DRESS_MESHES]
    meshes = [(p,m) for p,m in meshes if m]
    rng = random.Random(hash(corner_id) & 0xFFFFFFFF)
    spawned = []
    for i in range(count):
        ang = rng.uniform(0, math.tau)
        rad = rng.uniform(180, 900)
        x = focus[0] + math.cos(ang) * rad
        y = focus[1] + math.sin(ang) * rad
        g = ground_at(world, x, y, zhint=focus[2]+500)
        if not g: continue
        glab = g['actor'] or ''
        if not (glab.startswith('Brushify') or glab.startswith('WC_EscherWalk_')):
            continue
        if float(g['normal'].z) < 0.5:
            continue
        path, mesh = meshes[i % len(meshes)]
        loc = unreal.Vector(g['loc'].x, g['loc'].y, g['loc'].z)
        yaw = rng.uniform(0, 360)
        # SAFE scales — rocks 0.6–1.2, bushes 0.5–0.9
        if 'Rock' in path:
            sc = rng.uniform(0.55, 1.15)
        elif 'Bush' in path:
            sc = rng.uniform(0.45, 0.85)
        elif 'Root' in path:
            sc = rng.uniform(0.5, 0.9)
        else:
            sc = rng.uniform(0.5, 1.0)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0, yaw, 0))
        if not actor: continue
        name = f'WC_HeroCornerDress_{corner_id}_{i:02d}_{Path(path).name}'
        actor.set_actor_label(name)
        actor.set_actor_scale3d(unreal.Vector(sc, sc, sc))
        try:
            actor.set_folder_path(f'HeroCorners/{corner_id}/Dress')
            actor.tags = ['Portfolio', 'HeroCornerDress', f'HeroCorner.{corner_id}']
        except Exception:
            pass
        spawned.append({'label': name, 'scale': sc, 'ground': glab, 'mesh': path})
    return spawned


def capture(svc):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    uds = next((a for a in svc.get_all_level_actors() if _label(a)=='Ultra_Dynamic_Sky2'), None)
    if uds:
        for k,v in (('Animate Time of Day', False),('Time of Day',1130.0),('Cloud Coverage',2.1),
                    ('Sun Light Intensity',4.6),('Overall Intensity',1.15)):
            try: uds.set_editor_property(k,v)
            except: pass
    # hide greybox
    for a in svc.get_all_level_actors():
        lab=_label(a)
        if lab.startswith(('SM_Greybox_','SM_PM3D_Sphere3D','Houdini_')) or 'Greybox' in lab:
            a.set_is_temporarily_hidden_in_editor(True); a.set_actor_hidden_in_game(True)
    out_dir = Path(unreal.Paths.project_dir())/'Saved'/'Portfolio'/'Hero'/'MelusinaMorning'/'HeroCorners'
    out_dir.mkdir(parents=True, exist_ok=True)
    rt = unreal.RenderingLibrary.create_render_target2d(world,1920,1080,unreal.TextureRenderTargetFormat.RTF_RGBA8,unreal.LinearColor(0,0,0,1),False)
    cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0,0,0))
    shots=[]
    try:
        comp=cap.get_editor_property('capture_component2d')
        comp.set_editor_property('texture_target', rt)
        comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        for cid in ('WestRim','EastBank','MeadowChorus','NorthDress'):
            a=next((x for x in svc.get_all_level_actors() if _label(x)==f'WC_HeroCorner_{cid}_Cam'), None)
            if not a: continue
            cap.set_actor_location_and_rotation(a.get_actor_location(), a.get_actor_rotation(), False, False)
            cam=a.get_component_by_class(unreal.CameraComponent)
            fov=55.0
            if cam:
                try: fov=float(cam.get_editor_property('field_of_view'))
                except: pass
            comp.set_editor_property('fov_angle', fov)
            try:
                pps=comp.get_editor_property('post_process_settings')
                pps.set_editor_property('override_auto_exposure_bias', True)
                pps.set_editor_property('auto_exposure_bias', 1.0)
                comp.set_editor_property('post_process_settings', pps)
                comp.set_editor_property('post_process_blend_weight', 1.0)
            except: pass
            for _ in range(4):
                comp.capture_scene()
            fn=out_dir/f'hero_corner_{cid}_dress_2026-09-20.png'
            opts=unreal.ImageWriteOptions()
            opts.set_editor_property('format', unreal.DesiredImageFormat.PNG)
            opts.set_editor_property('overwrite_file', True)
            opts.set_editor_property('async_', False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace('\\','/'), opts)
            shots.append({'id':cid,'bytes':fn.stat().st_size if fn.exists() else 0})
    finally:
        cap.destroy_actor()
    return shots


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    west = swap_westrim(svc)
    vols = shrink_volumes(svc)
    cleared = clear_my_dress(svc)

    # focuses from volumes
    focuses = {}
    for cid in ('WestRim','EastBank','MeadowChorus','NorthDress'):
        vlab = 'WC_morning_rainbow_bloom_Field' if cid=='MeadowChorus' else f'WC_HeroCorner_{cid}_PCG'
        vol = next((a for a in svc.get_all_level_actors() if _label(a)==vlab), None)
        if vol:
            fl = vol.get_actor_location()
            focuses[cid] = [fl.x, fl.y, fl.z]

    dress = {}
    # Base dress priority WestRim + EastBank first (user order), light on others
    counts = {'WestRim': 12, 'EastBank': 12, 'MeadowChorus': 6, 'NorthDress': 8}
    for cid, n in counts.items():
        if cid not in focuses: continue
        dress[cid] = dress_corner(svc, world, cid, focuses[cid], count=n)

    shots = capture(svc)
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    # update lock doc note
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'west_swap': west,
        'volume_scales': vols,
        'dress_cleared': cleared,
        'dress': {k: {'n': len(v), 'sample': v[:4]} for k,v in dress.items()},
        'shots': shots,
        'saved': saved,
        'note': 'WestRim now PhyllotaxisGarden_Walkable; PCG volumes shrunk; WC_HeroCornerDress_* base dress with safe scales 0.45–1.15',
    }
    out = Path(unreal.Paths.project_dir())/'Saved'/'Audit'/'hero_corners_phyllotaxis_dress_2026-09-20.json'
    out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print('DRESS', json.dumps({
        'west': west,
        'vols': vols,
        'dress_n': {k: len(v) for k,v in dress.items()},
        'shots': shots,
        'saved': saved,
        'report': str(out),
    }, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
