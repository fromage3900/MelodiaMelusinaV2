"""Demo presentation helpers - session-scoped, no shared asset is modified.

TWO things only, both proven harmless to gameplay:

  1. The Choral Sheep is not presentation-ready -> hide him.
  2. Ambient/random audio must not run -> mute.

WHAT WAS REMOVED AND WHY (2026-10-20, after it broke the pawn):
  * Collision forcing - the preset used to set every static mesh component in
    the level to QUERY_AND_PHYSICS + BlockAll, and it added BOX hulls to 57
    mesh assets. That broke her movement and must not come back. Collision is
    an art/rig decision and belongs in the assets, not in a demo preset.
  * The PlayerStart teleport - PIE spawns the player at the editor camera
    (LastExecutedPlayModeLocation=PlayLocation_CurrentCameraLocation), but
    teleporting the pawn during PIE is a behaviour change and is not worth
    the risk in a live demo.

The sheep hide and the mute are re-applied on a timer, because PIE reloads the
map ~0.25 s in this project (Saved/SaveGames/SaveMetadata.sav is missing, so
[AscentSaveSystemEditor] reloads the current map) and a one-shot pass is undone
by the reload.

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


def _apply_now(world, first=False):
    hidden, hnotes = _hide_sheep(world)
    muted, mnotes = _mute(world)
    if first:
        _state["applied"] = [world.get_name(), hidden, muted]
        unreal.log("demo_presets: applied to {} | sheep hidden: {} | muted: {} | notes: {}".format(
            world.get_name(), hidden if hidden else "none found", muted, hnotes + mnotes))
    elif hidden:
        unreal.log("demo_presets: sheep re-hidden: {}".format(len(hidden)))


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
