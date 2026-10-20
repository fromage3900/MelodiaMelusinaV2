"""Demo presentation helpers - session-scoped, no shared asset is modified.

Two things the owner needs during a live screenshare:

  1. The Choral Sheep is not presentation-ready -> hide him.
  2. Ambient/random audio must not run during the demo -> mute.

Both are applied to the PIE world at runtime, so nothing in the shared Morning
level (which has 137 external-actor packages already dirty from other lanes) is
touched, and nothing survives the PIE session.

Usage (in the running editor):

    py "C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/demo_presets.py"

or from Monolith / editor Python:

    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/demo_presets.py").read())
    install()

`install()` is idempotent and safe to call at any time; it applies to every
PIE session started afterwards. `remove()` unhooks it.
"""
import unreal

SHEEP_KEY = "choral"
MIX_PATH = "/Game/Melodia/Audio/SM_MelodiaUserPreferences"
MASTER_CLASS = "/Engine/EngineSounds/Master"
MUSIC_CLASS = "/Engine/EngineSounds/Music"
SFX_CLASS = "/Engine/EngineSounds/SFX"

_state = {"world": None, "handle": None, "applied": []}


def _game_world():
    try:
        es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        return es.get_game_world()
    except Exception:
        return None


def _hide_sheep(world):
    """Hide the Choral Sheep actor and stop his components (he carries the
    MelodiaCompanionComponent that drives his behaviour and sound)."""
    hidden = []
    notes = []
    try:
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    except Exception as e:
        return hidden, ["actor enumeration failed: %s" % e]
    for a in actors:
        name = (a.get_name() or "").lower()
        if SHEEP_KEY not in name and "sheep" not in name:
            continue
        try:
            a.set_actor_hidden_in_game(True)
        except Exception as e:
            notes.append("hidden flag: %s" % e)
        try:
            a.set_actor_tick_enabled(False)
        except Exception as e:
            notes.append("tick: %s" % e)
        try:
            a.set_actor_enable_collision(False)
        except Exception as e:
            notes.append("collision: %s" % e)
        try:
            for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
                c.set_visibility(False)
                c.set_hidden_in_game(True)
        except Exception as e:
            notes.append("mesh visibility: %s" % e)
        try:
            for c in a.get_components_by_class(unreal.ActorComponent):
                c.deactivate()
        except Exception as e:
            notes.append("deactivate: %s" % e)
        hidden.append(a.get_name())
    return hidden, notes


def _mute(world):
    """Mute everything through the project's own sound mix (same mechanism as
    UMelodiaGameUserSettings::ApplyMelodiaPreferences). Runtime only - nothing
    is written to the saved user settings."""
    mix = unreal.load_asset(MIX_PATH)
    if not mix:
        return False, ["sound mix not found: %s" % MIX_PATH]
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


def _frame_camera(world):
    """PIE opens wherever the editor camera was (LastExecutedPlayModeLocation =
    PlayLocation_CurrentCameraLocation), which is usually inside geometry, and
    the spawn is then inside the room shell. Put the pawn back on the level's
    PlayerStart so the gameplay camera frames her normally.

    No camera hijack: a static cine camera would lose her the moment she moves.
    """
    notes = []
    starts = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_class().get_name() in ("PlayerStart", "APlayerStart"):
            starts.append(a)
    if not starts:
        return None, ["no PlayerStart in level"]
    pawn = None
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Pawn):
        if p.get_class().get_name().startswith("BP_Melusina"):
            pawn = p
            break
    if not pawn:
        for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Pawn):
            pawn = p
            break
    if not pawn:
        return None, ["no pawn"]
    st = starts[0]
    loc = st.get_actor_location()
    rot = st.get_actor_rotation()
    try:
        pawn.set_actor_location_and_rotation(loc, rot, False, None)
        teleported = True
    except Exception as e:
        teleported = False
        notes.append("teleport failed: %s" % e)
    return "{} -> {}".format(pawn.get_name(), st.get_name()), notes


def _apply_once():
    world = _game_world()
    if not world:
        return
    name = world.get_name()
    if name == _state["world"]:
        return
    _state["world"] = name
    hidden, hnotes = _hide_sheep(world)
    muted, mnotes = _mute(world)
    cam, cnotes = _frame_camera(world)
    _state["applied"] = [name, hidden, muted, cam]
    unreal.log("demo_presets: applied to {} | sheep hidden: {} | muted: {} | spawn: {} | notes: {}".format(
        name, hidden if hidden else "none found", muted, cam, hnotes + mnotes + cnotes))


def _tick(delta):
    try:
        _apply_once()
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
