"""Demo presentation helpers - session-scoped, no shared asset is modified.

Three things the owner needs for a live screenshare / PIE demo:

  1. The Choral Sheep is not presentation-ready -> hide him.
  2. Ambient/random audio must not run -> mute.
  3. The pawn must not fall through the floor -> collision.

Applied to the PIE world at runtime, so nothing in the shared Morning level
(which has 137 external-actor packages already dirty from other lanes) is
touched, and nothing survives the PIE session.

WHY IT RE-APPLIES CONTINUOUSLY (not once):
  PIE reloads the map ~0.25 s in this project (Saved/SaveGames/SaveMetadata.sav
  is missing, so [AscentSaveSystemEditor] cannot load P0_Shorewake_Validation
  and reloads the current map). A one-shot pass therefore applies to the first
  world instance and is undone by the reload - the sheep comes back and the
  streamed-in floors lose their collision. The preset re-applies on a timer,
  and also re-places the pawn if it has fallen.

Usage (in the running editor):

    py "C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/demo_presets.py"

`install()` is idempotent. `remove()` unhooks it.
"""
import unreal

MIX_PATH = "/Game/Melodia/Audio/SM_MelodiaUserPreferences"
MASTER_CLASS = "/Engine/EngineSounds/Master"
MUSIC_CLASS = "/Engine/EngineSounds/Music"
SFX_CLASS = "/Engine/EngineSounds/SFX"

# 'ram' is deliberately absent: it is a substring of 'ca*ram*era' and hid the
# camera manager.
SHEEP_WORDS = ("sheep", "choral", "ewe", "lamb")
NEVER_HIDE = ("camera", "manager", "trigger", "player")

REAPPLY_EVERY_TICKS = 20
FALL_THRESHOLD_CM = 200.0

_state = {"world": None, "handle": None, "ticks": 0, "applied": []}


def _game_world():
    try:
        es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        return es.get_game_world()
    except Exception:
        return None


def _label(a):
    try:
        return str(a.get_actor_label() or "").lower()
    except Exception:
        return ""


def _is_sheep(a):
    name = (a.get_name() or "").lower()
    label = _label(a)
    cls = a.get_class().get_name().lower()
    for w in NEVER_HIDE:
        if w in name or w in cls:
            return False
    for w in SHEEP_WORDS:
        if w in name or w in label or w in cls:
            return True
    return False


def _hide_sheep(world):
    hidden = []
    try:
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    except Exception as e:
        return hidden, ["enumeration failed: %s" % e]
    for a in actors:
        if not _is_sheep(a):
            continue
        for fn, args in (
            ("set_actor_hidden_in_game", (True,)),
            ("set_actor_tick_enabled", (False,)),
            ("set_actor_enable_collision", (False,)),
        ):
            try:
                getattr(a, fn)(*args)
            except Exception:
                pass
        try:
            for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
                c.set_visibility(False)
                c.set_hidden_in_game(True)
        except Exception:
            pass
        try:
            for c in a.get_components_by_class(unreal.AudioComponent):
                c.set_active(False)
                c.deactivate()
        except Exception:
            pass
        try:
            for c in a.get_components_by_class(unreal.ActorComponent):
                c.deactivate()
        except Exception:
            pass
        hidden.append(a.get_name())
    return hidden, []


def _mute(world):
    """Mute through the project's own sound mix - the same mechanism as
    UMelodiaGameUserSettings::ApplyMelodiaPreferences. Runtime only."""
    mix = unreal.load_asset(MIX_PATH)
    if not mix:
        return False, ["sound mix not found"]
    notes = []
    try:
        unreal.GameplayStatics.push_sound_mix_modifier(world, mix)
    except Exception as e:
        notes.append("push: %s" % e)
    for path in (MASTER_CLASS, MUSIC_CLASS, SFX_CLASS):
        cls = unreal.load_asset(path)
        if not cls:
            notes.append("missing class %s" % path)
            continue
        try:
            unreal.GameplayStatics.set_sound_mix_class_override(world, mix, cls, 0.0, 0.05, 0.05)
        except Exception as e:
            notes.append("override %s: %s" % (path, e))
    return True, notes


def _ensure_collision(world):
    """Turn collision on for static geometry that has it switched off. The
    asset must own collision data; this enables the component."""
    fixed = []
    try:
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    except Exception as e:
        return fixed, ["enumeration failed: %s" % e]
    for a in actors:
        try:
            comps = a.get_components_by_class(unreal.ActorComponent)
        except Exception:
            continue
        for c in comps:
            cn = c.get_class().get_name().lower()
            if 'staticmesh' not in cn and 'houdini' not in cn:
                continue
            try:
                if 'NO_COLLISION' not in str(c.get_collision_enabled()):
                    continue
                c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                c.set_collision_profile_name('BlockAll')
                fixed.append(a.get_name())
            except Exception:
                pass
    return fixed, []


def _player_start(world):
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_class().get_name() in ("PlayerStart", "APlayerStart"):
            return a
    return None


def _melusina(world):
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Pawn):
        if p.get_class().get_name().startswith("BP_Melusina"):
            return p
    return None


def _place_on_player_start(world):
    """PIE spawns the player wherever the editor camera was
    (LastExecutedPlayModeLocation=PlayLocation_CurrentCameraLocation), which
    puts the camera inside the room shell. Put the pawn back on the
    PlayerStart - and keep putting it back if it falls through the floor."""
    st = _player_start(world)
    if not st:
        return None, ["no PlayerStart in level"]
    pawn = _melusina(world)
    if not pawn:
        return None, ["no pawn"]
    loc = st.get_actor_location()
    try:
        pz = pawn.get_actor_location().z
        fell = (pz - loc.z) < -FALL_THRESHOLD_CM
    except Exception:
        fell = False
    if not fell:
        return "standing", []
    try:
        pawn.set_actor_location_and_rotation(loc, st.get_actor_rotation(), False, None)
    except Exception as e:
        return None, ["teleport failed: %s" % e]
    return "respawned on PlayerStart (was below the floor)", []


def _apply_now(world, first=False):
    hidden, hnotes = _hide_sheep(world)
    muted, mnotes = _mute(world)
    coll, cnotes = _ensure_collision(world)
    spawn, snotes = _place_on_player_start(world)
    if first:
        _state["applied"] = [world.get_name(), hidden, muted, spawn, len(coll)]
        unreal.log("demo_presets: applied to {} | sheep hidden: {} | muted: {} | spawn: {} | "
                   "collision enabled on {} components | notes: {}".format(
                       world.get_name(), hidden if hidden else "none found", muted, spawn,
                       len(coll), hnotes + mnotes + cnotes + snotes))
    else:
        bits = []
        if hidden:
            bits.append("sheep re-hidden: %d" % len(hidden))
        if coll:
            bits.append("collision re-enabled: %d" % len(coll))
        if spawn and spawn.startswith("respawned"):
            bits.append(spawn)
        if bits:
            unreal.log("demo_presets: " + " | ".join(bits))


def _tick(delta):
    try:
        world = _game_world()
        if not world:
            return True
        name = world.get_name()
        if name != _state["world"]:
            _state["world"] = name
            _state["ticks"] = 0
            _apply_now(world, first=True)
        else:
            _state["ticks"] += 1
            if _state["ticks"] % REAPPLY_EVERY_TICKS == 0:
                _apply_now(world, first=False)
    except Exception as e:
        unreal.log_warning("demo_presets tick error: {}".format(e))
    return True


def install():
    """Hook the PIE watcher. Idempotent."""
    if _state["handle"] is None:
        _state["handle"] = unreal.register_slate_post_tick_callback(_tick)
        unreal.log("demo_presets: installed (PIE watcher active)")
    else:
        unreal.log("demo_presets: already installed")
    return _state["handle"]


def remove():
    """Unhook the PIE watcher."""
    if _state["handle"] is not None:
        try:
            unreal.unregister_slate_post_tick_callback(_state["handle"])
        except Exception:
            pass
        _state["handle"] = None
        _state["world"] = None
        unreal.log("demo_presets: removed")


install()
