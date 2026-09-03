"""Project authority policy used by the static atlas.

This module contains decisions from PROJECT.md and the Orchestra contracts.  It
does not inspect or import Unreal or production Python modules.  Classification
overrides are deliberately small: source discovery supplies the nodes and
reachability evidence; policy only says what role a discovered node is allowed
to play.
"""

from __future__ import annotations

from dataclasses import dataclass


SCHEMA_VERSION = 2
CLASSIFICATIONS = (
    "CANONICAL",
    "ADAPTER",
    "PRESENTATION",
    "AUTHORING",
    "PROTOTYPE",
    "MERGE",
    "DEAD_CANDIDATE",
    "UNKNOWN",
)

CORE_DOMAINS = (
    "narrative",
    "battle",
    "rhythm",
    "party",
    "save",
    "progression",
    "wardrobe",
    "traversal",
    "ui",
    "music_world",
    "economy",
    "tooling",
)

SCAN_ROOTS = (
    "Source/BS_GodFile/MelodiaIntegration",
    "Source/BS_GodFile/Piano",
    "Plugins/MelodiaCore",
    "Plugins/MelodiaWardrobe",
    "Plugins/QuillScript",
    "Content/Python/gmm",
    "Tools",
    "specs",
)

TEXT_EXTENSIONS = frozenset(
    {
        ".h", ".hpp", ".cpp", ".cs", ".py", ".json", ".md", ".ini",
        ".uplugin", ".qsc", ".toml", ".yaml", ".yml",
    }
)

IGNORED_PARTS = frozenset(
    {"__pycache__", "Intermediate", "Binaries", ".git", ".pytest_cache"}
)


DOMAIN_OWNERS = {
    "narrative": "QuillScript; UMelodiaNarrativeSubsystem is the sole integration seam",
    "battle": "TurnBased JRPG template (turns, targeting, damage, results)",
    "rhythm": "UMelodiaRhythmCombatSubsystem; UMelodiaMusicClockSubsystem owns beat time",
    "party": "TurnBased JRPG template (party and units)",
    "save": "TurnBased JRPG BP_JRPGSaveGame; NarrativeRecord is an adapted fragment",
    "progression": "QuillScript-authored narrative progression plus stock JRPG mechanics, committed through UMelodiaNarrativeSubsystem",
    "wardrobe": "UMelodiaWardrobeSubsystem and wardrobe catalog contract",
    "traversal": "UMelodiaTraversalComponent with one IMelodiaTraversalCapabilityProvider",
    "ui": "One writer per surface: stock BP_BattleUI for commands and UMelodiaUIBridgeSubsystem for Melodia battle presentation",
    "music_world": "APCGHeroMusicGraphHost emits; UMelodiaNarrativeSubsystem commits consequences; reactivity remains presentation",
    "economy": "TurnBased JRPG inventory/save authority; wardrobe acquisition may adapt through UMelodiaWardrobeGachaSubsystem",
    "tooling": "Repository tooling and manifests; never runtime gameplay authority",
}


DOMAIN_KEYWORDS = {
    "save": ("save", "persist", "checkpoint", "slot"),
    "wardrobe": ("wardrobe", "outfit", "cosmetic", "garment", "clothing", "gacha"),
    "traversal": ("traversal", "glide", "swim", "dash", "locomotion", "watergameplay"),
    "rhythm": ("rhythm", "beat", "musicclock", "timing", "highway"),
    "battle": ("battle", "combat", "encounter", "enemy", "damage", "arena", "skill", "roguelike"),
    "party": ("party", "companion", "unitbootstrap", "unit"),
    "ui": ("widget", "hud", "overlay", "ui", "presentation", "minimap"),
    "music_world": ("music", "piano", "phrase", "pcg", "reactivity", "audio", "osc", "worldchallenge"),
    "economy": ("wallet", "token", "currency", "entitlement", "reward", "economy"),
    "progression": ("progression", "openingflow", "quest", "persona", "bond", "social", "objective", "stateanchor"),
    "narrative": ("narrative", "quill", "dialogue", "story", "conversation"),
}


@dataclass(frozen=True)
class Override:
    classification: str
    domain: str
    verdict: str
    owner: str | None = None
    confidence: float = 0.98


# Only load-bearing or especially misleading symbols are overridden.  Other
# candidates are classified mechanically from module, base class, and name.
SYMBOL_OVERRIDES = {
    "UQuillscriptSubsystem": Override(
        "CANONICAL", "narrative", "Absolute authored narrative and dialogue authority.",
        "QuillScript", 1.0,
    ),
    "UMelodiaNarrativeSubsystem": Override(
        "ADAPTER", "narrative", "Keep as the single Quill-to-stock integration and NarrativeRecord boundary.",
        confidence=1.0,
    ),
    "UMelodiaExternalJRPGBridgeSubsystem": Override(
        "ADAPTER", "battle", "Keep as the narrow reflection adapter to the stock JRPG battle lifecycle.",
        confidence=1.0,
    ),
    "UMelodiaRhythmCombatSubsystem": Override(
        "CANONICAL", "rhythm", "Keep as the sole timing-grade path layered over stock JRPG commands.",
        confidence=1.0,
    ),
    "UMelodiaMusicClockSubsystem": Override(
        "CANONICAL", "rhythm", "Keep as the sole Harmonix/Quartz beat authority.",
        confidence=1.0,
    ),
    "UMelodiaJRPGPresentationRhythmComponent": Override(
        "PRESENTATION", "rhythm", "Keep as presentation/telemetry; it must not own damage or turns.",
    ),
    "UMelodiaRhythmHUDWidget": Override(
        "PRESENTATION", "ui", "Live rhythm presentation used by the canonical rhythm subsystem.",
    ),
    "UMelodiaRhythmReactivitySubsystem": Override(
        "PRESENTATION", "music_world", "Keep as material/OSC presentation bus; never combat authority.",
    ),
    "UMelodiaRhythmExecutionComponent": Override(
        "DEAD_CANDIDATE", "rhythm", "Retire after proving no shipping caller; do not merge its combat execution path.",
        confidence=0.96,
    ),
    "UMelodiaBattleInputComponent": Override(
        "DEAD_CANDIDATE", "rhythm", "Its game-mode-owned remap is not the documented live BP_BattleUI input seam.",
        confidence=0.96,
    ),
    "UMelodiaBattleSession": Override(
        "MERGE", "battle", "Competing battle authority: harvest presentation/data only, then disable and retire the executor.",
        confidence=1.0,
    ),
    "UMelodiaSaveGameSubsystem": Override(
        "MERGE", "save", "Competing save API despite quarantine comments; migrate required fragments to the canonical stock slot, then retire.",
        confidence=1.0,
    ),
    "UMelodiaSaveGame": Override(
        "MERGE", "save", "Parallel native save object; migrate any required fragment to the canonical stock JRPG slot, then retire.",
        confidence=1.0,
    ),
    "UMelodiaSaveRecoverySubsystem": Override(
        "ADAPTER", "save", "Recovery adapter around the canonical stock save path; it must not become a second slot authority.",
    ),
    "UMelodiaOpeningFlowSubsystem": Override(
        "MERGE", "progression", "Move unique opening state into Quill/Narrative transactions and remove independent persistence/quest writes.",
        confidence=1.0,
    ),
    "UMelodiaPartySubsystem": Override(
        "MERGE", "party", "Competing exploration-party state; migrate shipping consumers to the stock JRPG party authority.",
        confidence=1.0,
    ),
    "AMelodiaQuestManagerBase": Override(
        "MERGE", "progression", "Legacy quest actor with independent mutation/reachability; converge unique state into Quill/Narrative transactions.",
        confidence=0.99,
    ),
    "UMelodiaProgressionComponent": Override(
        "MERGE", "progression", "Independent progression state holder; retain no shipping mutation authority outside Narrative.",
        confidence=0.98,
    ),
    "UMelodiaPersonaSubsystem": Override(
        "PROTOTYPE", "progression", "Quest/equipment facade only; not evidence of a calendar/social-loop authority.",
        confidence=0.99,
    ),
    "UMelodiaJRPGPartyBootstrapSubsystem": Override(
        "ADAPTER", "party", "Keep only as an idempotent stock-party bootstrap adapter.",
    ),
    "UMelodiaSaveSlotLibrary": Override(
        "ADAPTER", "save", "Canonical stock BP_JRPGSaveGame adapter surface.",
        confidence=1.0,
    ),
    "UMelodiaWardrobeSubsystem": Override(
        "CANONICAL", "wardrobe", "Sole wardrobe state and traversal-capability provider.",
        confidence=1.0,
    ),
    "UMelodiaWardrobeComponent": Override(
        "ADAPTER", "wardrobe", "Pawn-facing wardrobe visual/state mirror; mutation remains subsystem-owned.",
    ),
    "UMelodiaWardrobeGachaSubsystem": Override(
        "ADAPTER", "economy", "Wardrobe acquisition adapter; must not become a parallel general inventory/save authority.",
    ),
    "UMelodiaOutfitComponent": Override(
        "DEAD_CANDIDATE", "wardrobe", "Compatibility outfit holder superseded by MelodiaWardrobe.",
        confidence=0.98,
    ),
    "UMelodiaTraversalComponent": Override(
        "CANONICAL", "traversal", "Current movement executor; refactor internally into explicit states without introducing another traversal authority.",
        confidence=1.0,
    ),
    "IMelodiaTraversalCapabilityProvider": Override(
        "ADAPTER", "traversal", "Single-provider capability seam between wardrobe and traversal.",
        confidence=1.0,
    ),
    "UMelodiaUIBridgeSubsystem": Override(
        "CANONICAL", "ui", "Sole Melodia battle-widget lifecycle owner; stock BP_BattleUI retains command input.",
        confidence=1.0,
    ),
    "UMelodiaJRPGBattleOverlaySubsystem": Override(
        "DEAD_CANDIDATE", "ui", "Retired compatibility observer; current source creates no widgets.",
        confidence=1.0,
    ),
    "UMelodiaPCGNarrativeChallengeBridgeComponent": Override(
        "ADAPTER", "music_world", "Existing music-key-to-Narrative transaction adapter; live attachment remains runtime-only proof.",
        confidence=1.0,
    ),
    "UMelodiaPCGWaterGameplayBridgeComponent": Override(
        "ADAPTER", "music_world", "Physical water response adapter for the existing piano emitter.",
    ),
    "UMelodiaTokenWalletSubsystem": Override(
        "MERGE", "economy", "Has independent currency state/save coupling; reconcile with the stock inventory/save authority.",
        confidence=0.98,
    ),
    "AQuillscriptInterpreter": Override(
        "CANONICAL", "narrative", "QuillScript interpreter owns authored dialogue execution and choice flow.",
        "QuillScript", 1.0,
    ),
    "APCGHeroMusicGraphHost": Override(
        "CANONICAL", "music_world", "Canonical played-phrase scorer and world-challenge event emitter.",
        confidence=1.0,
    ),
    "UMelusinaSorrowSeamComponent": Override(
        "PRESENTATION", "music_world", "Presentation-only veil driver; reads Narrative/MPC state without combat, traversal, or save mutation.",
        confidence=1.0,
    ),
}


PATH_OVERRIDES = (
    (
        "Content/Python/gmm/",
        Override(
            "PROTOTYPE",
            "tooling",
            "Standalone Python gameplay/read-model prototype; it must not be treated as shipping authority.",
            "Repository tooling and prototypes; never runtime gameplay authority",
            0.97,
        ),
    ),
    (
        "Tools/",
        Override(
            "AUTHORING",
            "tooling",
            "Offline authoring, audit, orchestration, or verification surface.",
            confidence=0.95,
        ),
    ),
    (
        "specs/",
        Override(
            "AUTHORING",
            "tooling",
            "Data contract or authored manifest; not runtime proof by itself.",
            confidence=0.94,
        ),
    ),
)


DUPLICATE_CLUSTER_HINTS = {
    "combat_executors": (
        "UMelodiaBattleSession",
        "module:Content/Python/gmm/game/battle_manager.py",
        "module:Content/Python/gmm/main.py",
    ),
    "save_owners": (
        "UMelodiaSaveGameSubsystem",
        "UMelodiaSaveSlotLibrary",
        "module:Content/Python/gmm/game/save_manager.py",
        "module:Content/Python/gmm/game/player_state.py",
    ),
    "narrative_progression": (
        "UMelodiaNarrativeSubsystem",
        "UMelodiaOpeningFlowSubsystem",
        "UMelodiaPersonaSubsystem",
    ),
    "wardrobe_state": (
        "UMelodiaWardrobeSubsystem",
        "UMelodiaWardrobeComponent",
        "UMelodiaOutfitComponent",
    ),
    "rhythm_execution": (
        "UMelodiaRhythmCombatSubsystem",
        "UMelodiaRhythmExecutionComponent",
        "UMelodiaBattleInputComponent",
        "module:Content/Python/gmm/game/rhythm_clock.py",
    ),
    "battle_ui": (
        "UMelodiaUIBridgeSubsystem",
        "UMelodiaJRPGBattleOverlaySubsystem",
        "UMelodiaRhythmHUDWidget",
        "module:Content/Python/gmm/ui/battle_gui.py",
    ),
    "economy_state": (
        "UMelodiaTokenWalletSubsystem",
        "UMelodiaWardrobeGachaSubsystem",
        "module:Content/Python/gmm/game/tokens.py",
    ),
}


RETIREMENT_SEQUENCE = (
    {
        "order": 1,
        "action": "Freeze the authority contract and generate this atlas in CI/offline review.",
        "reason": "Prevents new callers from landing while competing systems are migrated.",
    },
    {
        "order": 2,
        "action": "Prove and then disable shipping creation/reachability for UMelodiaBattleSession.",
        "reason": "Stock JRPG must remain the only turn/damage/result executor; harvest presentation/data only.",
    },
    {
        "order": 3,
        "action": "Move required MelodiaSaveGameSubsystem fragments into the stock BP_JRPGSaveGame adapter and retire its public Save/Load API.",
        "reason": "One canonical slot must restore all shipping state without dual-save drift.",
    },
    {
        "order": 4,
        "action": "Reduce OpeningFlow to a Quill/Narrative projection and remove direct quest-manager mutation.",
        "reason": "Narrative progression needs one transaction owner rather than synchronization between state machines.",
    },
    {
        "order": 5,
        "action": "Replace wardrobe calls to RestoreNarrativeRecord with narrow grant/equip/unequip transactions.",
        "reason": "An outfit mutation must not replay Quill and water load-time restore effects.",
    },
    {
        "order": 6,
        "action": "Refactor UMelodiaTraversalComponent internally into movement state, resources, sensors, input, and presentation.",
        "reason": "Improve state validity while retaining one traversal executor and one capability provider.",
    },
    {
        "order": 7,
        "action": "Delete compatibility observers/components only after static callers and live Blueprint reachability are both proven absent.",
        "reason": "Source absence is not Blueprint or asset absence; deletion remains an owner/runtime gate.",
    },
)


DOCUMENT_DRIFT = (
    {
        "topic": "battle_overlay",
        "document_claim": "The 2026-08-20 contract says UMelodiaJRPGBattleOverlaySubsystem creates a second set of battle widgets.",
        "current_code": "Current header calls it a retired compatibility observer and current cpp creates no widgets.",
        "status": "STALE_DOC",
        "citations": (
            ("Docs/ORCHESTRA_CONTRACT_2026-08-20.md", "currently violated"),
            ("Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGBattleOverlaySubsystem.h", "Retired presentation observer"),
        ),
    },
    {
        "topic": "music_world_key",
        "document_claim": "The 2026-08-20 contract labels the Piano-to-Narrative edge unwired.",
        "current_code": "UMelodiaPCGNarrativeChallengeBridgeComponent now binds OnPatternCompleted and calls CommitWorldChallenge; live attachment is still unproven statically.",
        "status": "IMPLEMENTED_NOT_LIVE_PROVEN",
        "citations": (
            ("Docs/ORCHESTRA_CONTRACT_2026-08-20.md", "NOT WIRED"),
            ("Source/BS_GodFile/MelodiaIntegration/MelodiaPCGNarrativeChallengeBridgeComponent.cpp", "CommitWorldChallenge"),
        ),
    },
    {
        "topic": "wardrobe_restore_coupling",
        "document_claim": "Wardrobe is presented as a bounded capability/presentation owner.",
        "current_code": "Grant/equip/unequip call RestoreNarrativeRecord, which also restores water state and persistent Quill variables.",
        "status": "CURRENT_CODE_RISK",
        "citations": (
            ("Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeSubsystem.cpp", "RestoreNarrativeRecord"),
            ("Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp", "RestorePersistentQuillVariables"),
        ),
    },
)
