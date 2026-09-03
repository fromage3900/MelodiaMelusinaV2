"""Same-camera A/B between the live PPV grade and Codex's lookdev candidates.

Created 2026-08-01 for the attachment step assigned to Claude in
Docs/Handoffs/CODEX_LOOKDEV_CANDIDATE_HANDOFF_2026-08-01.md.

Spawns a SECOND post-process volume, PPV_NikkiDream_Candidate, carrying only the
candidate blendable pair. The live PPV_NikkiDream keeps its own blendables and is
never edited -- per the candidate handoff, the current stack must not be replaced.

Why the two volumes are toggled rather than just layered: weighted blendables
ACCUMULATE across overlapping post-process volumes. If both volumes were enabled
at once you would be looking at two outline passes and two grades stacked, which
is not an A/B of anything. So exactly one of the pair is enabled at a time.

The candidate volume deliberately overrides NO native settings (bloom, vignette,
grain, fringe). Unset overrides fall through to the lower-priority volume, so the
candidate inherits the live volume's lens character and the comparison isolates
the blendable pair -- which is the thing actually being judged.

Run inside the editor (Monolith run_python), with the A/B level already open:

    import setup_ppv_candidate_ab as ab
    ab.mode("candidate")                      # look at the candidates
    ab.mode("source")                         # look at the live grade (default)
    ab.mode("candidate", profile="PortfolioHero")
    ab.mode("candidate", profile="mathcandidate")   # Codex's 8-tap algorithm
    ab.status()                               # what is enabled right now

Profiles: GameplayStandard | Narrative | PortfolioHero | mathcandidate
"""
from __future__ import annotations

SOURCE_PPV = "PPV_NikkiDream"
CANDIDATE_PPV = "PPV_NikkiDream_Candidate"

_CAND = "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles"
_GRADE = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles"

# profile -> (outline instance, grade instance).
#
# The three lookdev profiles pair an outline and a grade tuned together. "mathcandidate"
# is Codex's separate eight-tap algorithm (M_PP_StorybookOutline_MathCandidate_v2); it has
# no grade of its own, so it borrows the GameplayStandard grade deliberately -- that keeps
# the grade constant between it and the lookdev profiles, so a comparison against it
# isolates the OUTLINE and does not silently also swap the colour treatment.
PROFILE_PAIRS = {
    "GameplayStandard": (f"{_CAND}/MI_StorybookOutline_GameplayStandard",
                         f"{_GRADE}/MI_MeluColorGrade_GameplayStandard"),
    "Narrative": (f"{_CAND}/MI_StorybookOutline_Narrative",
                  f"{_GRADE}/MI_MeluColorGrade_Narrative"),
    "PortfolioHero": (f"{_CAND}/MI_StorybookOutline_PortfolioHero",
                      f"{_GRADE}/MI_MeluColorGrade_PortfolioHero"),
    "mathcandidate": (f"{_CAND}/MI_StorybookOutline_MathCandidate_v2_Standard",
                      f"{_GRADE}/MI_MeluColorGrade_GameplayStandard"),
    # Premium stack: silhouette/crease separation, analytic fwidth AA, perspective-tapered
    # width, TSR jitter compensation. Pairs with the GameplayStandard grade on purpose so
    # the grade is held constant and the A/B isolates the outline.
    "premium": (f"{_CAND}/MI_StorybookOutline_Premium_Hero",
                f"{_GRADE}/MI_MeluColorGrade_GameplayStandard"),
    # Same master as "premium", but with the Nikki magic dials actually turned up:
    # ink blur, halftone breakup, dream rim, iridescence, atmospheric depth. The locked
    # Hero profile leaves every one of those at its neutral default, so A/B-ing these two
    # isolates the new lookdev layer and nothing else.
    "dream": (f"{_CAND}/MI_StorybookOutline_Premium_Hero_Dream",
              f"{_GRADE}/MI_MeluColorGrade_GameplayStandard"),
}
PROFILES = tuple(PROFILE_PAIRS)

# Must beat the live volume. ZenForestTest's PPV_NikkiDream sits at 5.56, the
# setup script writes 10.0 elsewhere; 25 clears both with room to spare.
CANDIDATE_PRIORITY = 25.0


def _actor(unreal, label):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors() or []:
        if a.get_actor_label() == label:
            return a
    return None


def _load(unreal, path):
    return unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None


def ensure(profile: str = "GameplayStandard") -> str:
    """Create/refresh the candidate volume for a profile. Leaves it disabled."""
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

    mats, missing = [], []
    for path in PROFILE_PAIRS[profile]:
        mat = _load(unreal, path)
        (mats if mat else missing).append(mat or path)
    if missing:
        raise RuntimeError(f"missing candidate assets: {missing}")

    settings = ppv.get_editor_property("settings")
    settings.set_editor_property("weighted_blendables", unreal.WeightedBlendables(
        [unreal.WeightedBlendable(1.0, m) for m in mats]))
    ppv.set_editor_property("settings", settings)
    return profile


def mode(which: str, profile: str = "GameplayStandard", save: bool = True) -> str:
    """Enable exactly one of the two volumes. which = 'source' | 'candidate'."""
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
    msg = f"A/B mode={which} profile={profile} source_enabled={not want_candidate}"
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
