"""Dreamprint — candidate PPV A/B: live stack vs live stack + M_PP_MelodiaInk.

Spawns PPV_Dreamprint_Candidate (unbound, priority 25 — beats PPV_NikkiDream).
The candidate carries the SAME approved outline+grade (GameplayStandard weights)
PLUS the Dreamprint ink layer on top, so the A/B isolates the ink stack exactly.
Exactly one of the two volumes is enabled at a time (weighted blendables
accumulate across overlapping volumes — both on means double-outline, not A/B).

Run in-editor (Monolith run_python):

    import setup_dreamprint_ab as ab
    ab.ensure("GameplayStandard")     # create/refresh candidate volume
    ab.mode("candidate", "PortfolioHero")   # look at Dreamprint
    ab.mode("source")                 # back to the live locked look
    ab.status()
"""
from __future__ import annotations

SOURCE_PPV = "PPV_NikkiDream"
CANDIDATE_PPV = "PPV_Dreamprint_Candidate"
CANDIDATE_PRIORITY = 25.0

_CAND = "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles"
_GRADE = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles"
_INK = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles"

INK_PROFILES = {
    "GameplayStandard": "MI_MelodiaInk_GameplayStandard",
    "Narrative": "MI_MelodiaInk_Narrative",
    "PortfolioHero": "MI_MelodiaInk_PortfolioHero",
}
PROFILES = tuple(INK_PROFILES)


def _actor(unreal, label):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors() or []:
        if a.get_actor_label() == label:
            return a
    return None


def _load(unreal, path):
    return unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None


def ensure(profile: str = "GameplayStandard") -> str:
    import unreal
    if profile not in PROFILES:
        raise ValueError(f"profile must be one of {PROFILES}, got {profile!r}")

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ppv = _actor(unreal, CANDIDATE_PPV)
    if ppv is None:
        ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
        ppv.set_actor_label(CANDIDATE_PPV)
    ppv.set_editor_property("unbound", True)
    ppv.set_editor_property("priority", CANDIDATE_PRIORITY)

    stack = [
        (f"{_CAND}/MI_StorybookOutline_GameplayStandard", 1.0),
        (f"{_GRADE}/MI_MeluColorGrade_GameplayStandard", 0.69),
        (f"{_INK}/{INK_PROFILES[profile]}", 1.0),
    ]
    mats, missing = [], []
    for path, weight in stack:
        mat = _load(unreal, path)
        if mat:
            mats.append((weight, mat))
        else:
            missing.append(path)
    if missing:
        raise RuntimeError(f"missing candidate assets: {missing}")

    settings = ppv.get_editor_property("settings")
    settings.set_editor_property("weighted_blendables", unreal.WeightedBlendables(
        [unreal.WeightedBlendable(w, m) for w, m in mats]))
    ppv.set_editor_property("settings", settings)
    return profile


def mode(which: str, profile: str = "GameplayStandard", save: bool = True) -> str:
    import unreal
    if which not in ("source", "candidate"):
        raise ValueError("which must be 'source' or 'candidate'")
    ensure(profile)
    src = _actor(unreal, SOURCE_PPV)
    cand = _actor(unreal, CANDIDATE_PPV)
    want_candidate = which == "candidate"
    if src is not None:
        src.set_editor_property("enabled", not want_candidate)
    cand.set_editor_property("enabled", want_candidate)
    if save:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    msg = f"A/B mode={which} profile={profile} ink={INK_PROFILES[profile]}"
    print(msg)
    return msg


def status() -> str:
    import unreal
    out = []
    for label in (SOURCE_PPV, CANDIDATE_PPV):
        a = _actor(unreal, label)
        if a is None:
            out.append(f"{label}: ABSENT")
            continue
        names = []
        try:
            wb = a.get_editor_property("settings").get_editor_property("weighted_blendables")
            for e in (wb.get_editor_property("array") if wb else []) or []:
                obj = e.get_editor_property("object")
                if obj:
                    names.append(obj.get_name())
        except Exception as exc:
            names = [f"<{exc}>"]
        out.append(f"{label}: enabled={a.get_editor_property('enabled')} "
                   f"priority={a.get_editor_property('priority')} blendables={names}")
    msg = "\n".join(out)
    print(msg)
    return msg


if __name__ == "__main__":
    ensure()
    status()