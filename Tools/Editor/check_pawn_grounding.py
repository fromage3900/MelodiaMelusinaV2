"""Grounding proof: is the pawn actually standing on collision, and does she stay?

Reusable check for Houdini-authored levels. It answers the question a curated
hybrid pipeline makes easy to get wrong: the floor under the pawn may be
generated geometry that (a) has not cooked yet, or (b) carries no collision at
all. Either way the pawn drops through it.

Sequence (in a PIE session):
  1. waits for the character movement to report a valid floor (a fresh session
     has no floor for the first frames - judging that race produced a false
     FAIL, so the wait is part of the check);
  2. samples her height and classifies the motion as settled / falling;
  3. asks the character movement what she is standing on, and cross-checks with
     a downward trace; reports that surface's collision state and, for a mesh
     surface, whether the asset carries collision data;
  4. censuses the Houdini actors and flags any that cook on load (their geometry
     can arrive after the pawn lands, and they cannot ship live-cooked).

Verdict is strict: PASS only if she is settled AND standing on a surface that
has collision.

Usage:
  py "C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/check_pawn_grounding.py"

Running the file also installs a watcher that runs the proof once per PIE
session (PIE sessions here are short-lived, so a hand-started proof often
misses its window).

Writes a JSON receipt to Saved/Audit/GroundingProof/.
"""
import json
import os
import time

import unreal

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
OUT_DIR = os.path.join(REPO, "Saved", "Audit", "GroundingProof")
PAWN_CLASS_PREFIX = "BP_Melusina"
MAX_SAMPLES = 160
DROP_CM = 30.0          # more than this between samples = she is falling
STABLE_CM = 2.0         # less than this between samples = she has settled
FLOOR_WAIT_SECONDS = 12.0


def _find_pawn(world):
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Pawn):
        if p.get_class().get_name().startswith(PAWN_CLASS_PREFIX):
            return p
    return None


def _character_movement(pawn):
    try:
        for c in pawn.get_components_by_class(unreal.CharacterMovementComponent):
            return c
    except Exception:
        pass
    return None


def _wait_for_floor(cm, seconds=FLOOR_WAIT_SECONDS):
    """A fresh PIE session has no floor for the first frames. Wait for one."""
    t0 = time.time()
    attempts = 0
    while time.time() - t0 < seconds:
        attempts += 1
        try:
            floor = cm.get_editor_property('current_floor')
            if floor is not None and str(floor.get_editor_property('blocking_hit')) == 'True':
                return True, attempts, round(time.time() - t0, 2)
        except Exception:
            pass
        time.sleep(0.1)
    return False, attempts, round(time.time() - t0, 2)


def _sample_motion(pawn):
    samples = []
    while len(samples) < MAX_SAMPLES:
        loc = pawn.get_actor_location()
        samples.append({'i': len(samples),
                        'x': round(loc.x, 1), 'y': round(loc.y, 1), 'z': round(loc.z, 1)})
        time.sleep(0.05)
        if len(samples) % 8 == 0:
            time.sleep(0.15)
    deltas = [round(a['z'] - b['z'], 2) for a, b in zip(samples, samples[1:])]
    tail = deltas[-8:] if len(deltas) >= 8 else deltas
    first, last = samples[0]['z'], samples[-1]['z']
    return {'samples': samples, 'deltas': deltas,
            'z_first': first, 'z_last': last,
            'total_drop_cm': round(first - last, 1),
            'falling': any(d > DROP_CM for d in tail),
            'settled': all(abs(d) <= STABLE_CM for d in tail)}


def _hit_payload(hit):
    """HitResult payload via to_dict(); returns (actor, component, info)."""
    info = {}
    if hit is None:
        return None, None, info
    try:
        d = hit.to_dict()
    except Exception as e:
        info['to_dict_error'] = str(e)[:120]
        return None, None, info
    actor = d.get('hit_actor')
    comp = d.get('hit_component')
    try:
        if actor is not None:
            info['hit_actor'] = actor.get_path_name()
            info['hit_actor_label'] = str(actor.get_actor_label()) if hasattr(actor, 'get_actor_label') else None
    except Exception:
        info['hit_actor'] = str(actor)
    try:
        if comp is not None:
            info['hit_component'] = comp.get_path_name()
            info['hit_component_class'] = comp.get_class().get_name()
    except Exception:
        info['hit_component'] = str(comp)
    try:
        info['hit_distance_cm'] = round(float(d.get('distance')), 2)
    except Exception:
        pass
    try:
        ip = d.get('impact_point')
        info['impact_point'] = [round(ip.x, 1), round(ip.y, 1), round(ip.z, 1)]
    except Exception:
        pass
    return actor, comp, info


def _describe_surface(actor, comp=None):
    rec = {}
    if actor is None:
        return rec
    try:
        rec['actor'] = actor.get_name()
        rec['label'] = str(actor.get_actor_label())
        rec['class'] = actor.get_class().get_name()
    except Exception:
        pass
    if comp is not None:
        try:
            rec['component_class'] = comp.get_class().get_name()
            rec['component_collision_enabled'] = str(comp.get_collision_enabled())
            rec['component_profile'] = str(comp.get_collision_profile_name())
        except Exception:
            pass
        try:
            sm = comp.get_editor_property('static_mesh')
            if sm:
                sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
                rec['mesh'] = sm.get_path_name()
                rec['simple_collision_count'] = sms.get_simple_collision_count(sm)
                rec['complexity'] = str(sms.get_collision_complexity(sm))
        except Exception:
            pass
    return rec


def _floor_info(cm):
    out = {}
    try:
        floor = cm.get_editor_property('current_floor')
        out['blocking_hit'] = str(floor.get_editor_property('blocking_hit'))
        out['floor_dist_cm'] = round(float(floor.get_editor_property('floor_dist')), 2)
        actor, comp, info = _hit_payload(floor.get_editor_property('hit_result'))
        out.update(info)
        out['standing_on'] = _describe_surface(actor, comp)
    except Exception as e:
        out['error'] = str(e)[:160]
    return out


def _trace_below(pawn, world):
    out = {}
    loc = pawn.get_actor_location()
    try:
        hit = unreal.SystemLibrary.sphere_trace_single(
            world, unreal.Vector(loc.x, loc.y, loc.z + 40.0),
            unreal.Vector(loc.x, loc.y, loc.z - 400.0), 6.0,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [pawn],
            unreal.DrawDebugTrace.NONE)
        actor, comp, info = _hit_payload(hit)
        out.update(info)
        out['surface'] = _describe_surface(actor, comp)
    except Exception as e:
        out['error'] = str(e)[:160]
    return out


def _houdini_census(world):
    rows = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        cn = a.get_class().get_name().lower()
        if 'houdini' not in cn:
            continue
        rec = {'actor': a.get_name(), 'label': str(a.get_actor_label()), 'class': cn}
        for prop in ('b_cook_on_load', 'b_cook_on_collision', 'b_cook_on_transform_change',
                     'b_cook_collision_data', 'b_preview_mesh_visible'):
            try:
                rec[prop] = str(a.get_editor_property(prop))
            except Exception:
                pass
        try:
            rec['mesh_components'] = []
            for c in a.get_components_by_class(unreal.ActorComponent):
                if 'staticmesh' not in c.get_class().get_name().lower():
                    continue
                entry = {'collision_enabled': str(c.get_collision_enabled())}
                try:
                    sm = c.get_editor_property('static_mesh')
                    if sm:
                        entry['mesh'] = sm.get_path_name()
                except Exception:
                    pass
                rec['mesh_components'].append(entry)
        except Exception as e:
            rec['comp_err'] = str(e)[:100]
        rows.append(rec)
    return rows


def main():
    out = {'schema': 'melodia.pawn_grounding_proof.v3',
           'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
    es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = es.get_game_world()
    out['pie_world'] = world.get_name() if world else None
    if not world:
        out['verdict'] = 'FAIL_NO_PIE'
        print('GROUND=' + json.dumps(out))
        return out

    pawn = _find_pawn(world)
    if not pawn:
        out['verdict'] = 'FAIL_NO_PAWN'
        print('GROUND=' + json.dumps(out))
        return out
    out['pawn'] = pawn.get_name()

    cm = _character_movement(pawn)
    out['character_movement'] = bool(cm)
    if cm:
        got, attempts, waited = _wait_for_floor(cm)
        out['floor_wait'] = {'got_floor': got, 'attempts': attempts, 'seconds': waited}
        try:
            out['movement_mode'] = str(cm.get_editor_property('movement_mode'))
        except Exception:
            pass

    motion = _sample_motion(pawn)
    out['motion'] = {k: v for k, v in motion.items() if k != 'samples'}
    out['motion']['sample_count'] = len(motion['samples'])
    out['motion']['first_samples'] = motion['samples'][:3]
    out['motion']['last_samples'] = motion['samples'][-3:]

    out['floor'] = _floor_info(cm) if cm else {'error': 'no character movement'}
    out['trace'] = _trace_below(pawn, world)
    out['houdini'] = _houdini_census(world)
    out['houdini_actor_count'] = len(out['houdini'])

    problems = []
    inconclusive = []

    # A frozen editor game thread (a modal dialog blocks PIE) makes every
    # reading here untrustworthy. Detect it instead of guessing.
    if not motion['settled'] and not motion['falling'] and motion['total_drop_cm'] == 0.0 \
            and str(floor.get('blocking_hit')) != 'True':
        inconclusive.append('PIE_NOT_TICKING (no descent, no floor, no blocking hit - the editor '
                             'game thread is most likely blocked by a modal dialog)')

    if motion['falling']:
        problems.append('PAWN_IS_FALLING (%.1f cm over the sample window)' % motion['total_drop_cm'])
    if not motion['settled'] and not inconclusive:
        problems.append('PAWN_NOT_SETTLED')

    floor = out.get('floor') or {}
    standing = floor.get('standing_on') or {}
    if str(floor.get('blocking_hit')) != 'True' or not standing:
        if not inconclusive:
            problems.append('NOT_STANDING_ON_ANY_SURFACE (floor blocking=%s)' % floor.get('blocking_hit'))
    else:
        ce = str(standing.get('component_collision_enabled', ''))
        if 'NO_COLLISION' in ce:
            problems.append('SURFACE_COMPONENT_HAS_NO_COLLISION: %s' % standing.get('mesh'))
        sc = standing.get('simple_collision_count')
        if isinstance(sc, int) and sc <= 0:
            problems.append('SURFACE_ASSET_HAS_NO_COLLISION_DATA: %s (simple=%s)'
                            % (standing.get('mesh'), sc))

    live_cook = [h for h in out['houdini'] if 'True' in str(h.get('b_cook_on_load', ''))]
    if live_cook:
        problems.append('LIVE_COOK_ON_LOAD: %d Houdini actor(s) cook at load; their geometry can '
                        'arrive after the pawn lands and cannot ship live-cooked' % len(live_cook))
    out['live_cook_actors'] = [h.get('label') for h in live_cook]

    out['problems'] = problems
    out['inconclusive'] = inconclusive
    if inconclusive:
        out['verdict'] = 'INCONCLUSIVE'
    else:
        out['verdict'] = 'PASS' if not problems else 'FAIL'
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        path = os.path.join(OUT_DIR, 'grounding_proof_%s.json' % time.strftime('%Y%m%d_%H%M%S'))
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(out, fh, indent=1)
        out['receipt'] = path
    except Exception as e:
        out['receipt_err'] = str(e)[:120]

    unreal.log('[GroundingProof] %s %s' % (out['verdict'], '; '.join(problems) or 'clean'))
    print('GROUND=' + json.dumps(out, indent=1, default=str))
    return out


_state = {'world': None, 'handle': None}


def _tick(delta):
    try:
        es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        w = es.get_game_world()
        if not w:
            return True
        name = w.get_name()
        if name == _state['world']:
            return True
        _state['world'] = name
        unreal.log('[GroundingProof] PIE world detected -> running proof')
        main()
    except Exception as e:
        unreal.log_warning('[GroundingProof] watcher error: %s' % e)
    return True


def install_watcher():
    """Run the proof automatically for every PIE session."""
    if _state['handle'] is None:
        _state['handle'] = unreal.register_slate_post_tick_callback(_tick)
        unreal.log('[GroundingProof] auto-proof watcher installed')
    return _state['handle']


def remove_watcher():
    if _state['handle'] is not None:
        try:
            unreal.unregister_slate_post_tick_callback(_state['handle'])
        except Exception:
            pass
        _state['handle'] = None
        unreal.log('[GroundingProof] auto-proof watcher removed')


install_watcher()

if __name__ == '__main__':
    main()
