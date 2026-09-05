"""Authoritative PPV and audio/cymatics contract.

This module is intentionally data-only.  It keeps the cooked-map inventory,
the gameplay certification surface, and the lookdev/regression surface
separate so a cinematic experiment cannot silently become a shipping stack.
"""
from __future__ import annotations

SEA_ABOVE = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"

# MapsToCook in Config/DefaultGame.ini.  MainMenu is packaged but is not a
# gameplay PPV certification target.
PACKAGED_SHIPPING_MAPS = (
    "/Game/Melodia/Levels/Menu/L_MelodiaMainMenu",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/ZenForestTest",
    "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
    SEA_ABOVE,
)

# Maps where the gameplay PPV must be proven in PIE and packaged runtime.
GAMEPLAY_PPV_CERTIFICATION_LEVELS = (
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
    "/Game/ZenForestTest",
    SEA_ABOVE,
)

# Non-shipping lookdev / regression maps.  They are useful for visual QA but
# are not counted as gameplay shipping coverage.
LOOKDEV_REGRESSION_LEVELS = (
    "/Game/EnvSandbox/Environments/L_FallenMoon",
    "/Game/EnvSandbox/_Template/L_Template",
)

# Compatibility alias for older scripts that still call the audited set
# SHIPPING_LEVELS.  New code should use the explicit name above.
SHIPPING_LEVELS = GAMEPLAY_PPV_CERTIFICATION_LEVELS

GRANDMASTER_OUTLINE_MATERIAL = (
    "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_Outline_Grandmaster"
)
GRANDMASTER_OUTLINE_MI = (
    "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/"
    "MI_Outline_Grandmaster_Gameplay"
)

GAMEPLAY_STACK = (
    (GRANDMASTER_OUTLINE_MI, 1.0),
    (
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/"
        "MI_MeluColorGrade_GameplayStandard",
        0.69,
    ),
    (
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/"
        "MI_MelodiaInk_GameplayStandard",
        1.0,
    ),
)

# Runtime ownership: these are read-only from the material/PPV side.
AUDIO_PALETTE = (
    "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette."
    "MPC_Melodia_Palette"
)
CYMATICS_DRIVER = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver.MPC_Cymatics_Driver"
NIAGARA_PALETTE = "/Game/EnvSandbox/VFX/MPC/NPC_Melodia_Palette.NPC_Melodia_Palette"

APPROVED_OUTLINE_REACTIVE_CHANNELS = (
    "BeatPulse",
    "BeatPhase",
    "Cymatic_EmissiveScale (bounded presentation energy only)",
)
