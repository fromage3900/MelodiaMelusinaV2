"""BS_GodFile EnvSandbox Niagara starter library.

USAGE
-----
In-editor (Output Log):
  py Content/Python/setup_niagara_library.py

Headless (UnrealEditor-Cmd):
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_niagara_library.py"

With live editor + UnrealMCP (port 55557), the script prefers MCP create_niagara_system /
create_atmospheric_fx â€” same path the agent uses. Re-run safely; existing assets are skipped.

LIBRARY LAYOUT
--------------
/Game/EnvSandbox/VFX/
  MPC/                 MPC_Magical (henshin driver for materials + BP/Sequencer sync)
  Systems/Universal/   reusable portfolio environment systems
  Systems/Ambient/     NS_FairyDust, NS_ConstellationTwinkle, NS_EmberMotes
  Systems/Sakura/      NS_Sakura* (6-system kit; full build via setup_sakura_niagara.py)
  Systems/Magical/     NS_MagicalHenshinBurst, NS_MagicTrail
  _Showcase/           optional L_VFX_Showcase (spawn grid when --showcase)

THEME ALIGNMENT (material work plan)
------------------------------------
| System                  | Material cousins              | Notes |
| NS_FairyDust            | MI_Universal_Fairy*           | soft hanging sparkles |
| NS_ConstellationTwinkle | MI_Universal_Constellation    | slow twinkle field |
| NS_EmberMotes           | MI_Universal_Warm* / campfire | warm floating dust |
| NS_Uni_MistSheet        | landscape / water pillars     | depth fog sheet for cliffs, ponds, ruins |
| NS_Uni_Fireflies        | Nikki / magical families      | readable stylized night-life layer |
| NS_Uni_LeafDrift        | forest / zen / autumn biomes  | non-Sakura leaf drift |
| NS_Uni_WaterMist        | MI_GrandWater_*               | pond, river, waterfall atomization |
| NS_Uni_DustShafts       | stone / trimsheet interiors   | temple, ruin, cathedral dust beams |
| NS_Uni_PollenSparkle    | meadow / flower fields        | soft botanical sparkle |
| NS_Uni_RainRipples      | water / wetness materials     | stylized rain surface accents |
| NS_Uni_GroundWisps      | forest floor / graveyard      | low fog and magical ground wisps |
| NS_SakuraPetals         | MI_Sakura_Blossom             | canopy drift for L_SakuraPath |
| NS_SakuraGroundPetals   | MI_Sakura_Petals              | fallen petals â€” see setup_sakura_niagara.py |
| NS_SakuraDreamSparkle   | MI_Sakura_Blossom             | Nikki air shimmer under canopy |
| NS_SakuraLanternMotes   | MI_Sakura_Lantern             | warm motes at stone lantern |
| NS_SakuraPondShimmer    | MI_Sakura_Water               | pond surface sparkle |
| NS_SakuraPetalGust      | MI_Sakura_Petals              | wind gust burst (one-shot) |
| NS_MagicalHenshinBurst  | MagicalTransform on Universal | one-shot burst; drive User.Burst via Sequencer |
| NS_MagicTrail           | M_PP_ToonOutline / storybook  | ribbon trail; tune in Niagara after spawn |

MPC / AUDIO WIRING (optional, manual in BP)
-------------------------------------------
- MPC_Magical.MagicalTransform  -> material henshin wipe (setup_master_universal.py)
- MPC_Melodia_Palette.BeatPhase -> bind to NS_FairyDust User.SpawnRate or emissive pulse
- Trigger NS_MagicalHenshinBurst from Sequencer Niagara track when MagicalTransform keyframes

SPAWN / TEST
------------
1. Run this script with editor open.
2. Open /Game/EnvSandbox/VFX/_Showcase/L_VFX_Showcase (if --showcase) or drag systems from Content Browser.
3. Place NS_SakuraPetals under blossom canopy; scale box location to tree bounds.
4. PIE: verify particles compile (no stack errors in Niagara editor).

HEADLESS / NO MCP
-----------------
NiagaraToolset_System edit APIs are not on the Python class in UE 5.8. Without UnrealMCP
(editor open, port 55557), missing systems duplicate NS_FairyDust or NS_EmberMotes as scaffolds.
Delete a .uasset and re-run with the editor live for proper templates (Fountain, Burst, Ribbon).

POST-RUN TUNING (expected)
--------------------------
Templates are starting points. Assign sprite materials (T_Spark / _AssetLibrary/Magical motifs),
tint colors to match MI presets, and expose User.* params before cinematic lock.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import material_lib as lib
except ModuleNotFoundError:
    lib = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "niagara_library_build.json"
LOG_PATH = PROJECT_ROOT / "Saved" / "Logs" / "niagara_library.log"

VFX_ROOT = "/Game/EnvSandbox/VFX"
MPC_DIR = f"{VFX_ROOT}/MPC"
SYSTEMS_AMBIENT = f"{VFX_ROOT}/Systems/Ambient"
SYSTEMS_UNIVERSAL = f"{VFX_ROOT}/Systems/Universal"
SYSTEMS_SAKURA = f"{VFX_ROOT}/Systems/Sakura"
SYSTEMS_MAGICAL = f"{VFX_ROOT}/Systems/Magical"
SHOWCASE_DIR = f"{VFX_ROOT}/_Showcase"
PROBE_DIR = f"{VFX_ROOT}/_Probe"

MPC_MAGICAL = "MPC_Magical"
MPC_AUDIO_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

NIAGARA_EMITTER_ROOT = "/Niagara/DefaultAssets/Templates/Emitters"
MCP_HOST = "127.0.0.1"
MCP_PORT = 55557

ENGINE_SYSTEM_TEMPLATES: dict[str, list[str]] = {
    "Fountain": [
        "/Niagara/DefaultAssets/Templates/Systems/FountainLightweight.FountainLightweight",
        "/Niagara/DefaultAssets/Templates/Systems/FountainLightweight",
        "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight",
    ],
    "HangingParticulates": [
        "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight",
        "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight",
        "/Niagara/DefaultAssets/DefaultSystem.DefaultSystem",
    ],
    "OmnidirectionalBurst": [
        "/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst",
        "/Niagara/DefaultAssets/Templates/Systems/RadialBurst",
        "/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst.DirectionalBurst",
    ],
    "LocationBasedRibbon": [
        "/Niagara/DefaultAssets/Templates/Systems/AttributeReaderTrails.AttributeReaderTrails",
        "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight",
    ],
    "floating_dust": [
        "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight",
        "/Niagara/DefaultAssets/DefaultSystem.DefaultSystem",
    ],
}

TEMPLATE_NAME_HINTS: dict[str, tuple[str, ...]] = {
    "Fountain": ("FountainLightweight", "Fountain", "MinimalLightweight"),
    "HangingParticulates": ("HangingParticulates", "MinimalLightweight", "DefaultSystem"),
    "OmnidirectionalBurst": ("RadialBurst", "DirectionalBurst", "Burst"),
    "LocationBasedRibbon": ("AttributeReaderTrails", "Ribbon", "Trails"),
    "floating_dust": ("MinimalLightweight", "FloatingDust", "DefaultSystem"),
}


@dataclass(frozen=True)
class NiagaraSystemSpec:
    name: str
    folder: str
    template_emitter: str | None = None
    atmospheric_preset: str | None = None
    theme: str = ""
    paired_materials: tuple[str, ...] = ()
    user_params: tuple[str, ...] = ()


SYSTEMS: tuple[NiagaraSystemSpec, ...] = (
    NiagaraSystemSpec(
        "NS_FairyDust",
        SYSTEMS_AMBIENT,
        f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        theme="fairy sparkle ambient",
        paired_materials=("MI_Universal_FairyStars", "MI_Universal_FairyFirefly"),
        user_params=("User.SpawnRate", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_ConstellationTwinkle",
        SYSTEMS_AMBIENT,
        f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        theme="celestial twinkle field",
        paired_materials=("MI_Universal_Constellation", "MI_Universal_MidnightGalaxy"),
        user_params=("User.SpawnRate", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_EmberMotes",
        SYSTEMS_AMBIENT,
        atmospheric_preset="floating_dust",
        theme="warm ember motes",
        paired_materials=("MI_Universal_CopperWarm", "MI_Universal_GoldLeaf"),
        user_params=("User.SpawnRate",),
    ),
    NiagaraSystemSpec(
        "NS_Uni_MistSheet",
        SYSTEMS_UNIVERSAL,
        atmospheric_preset="floating_dust",
        theme="universal depth mist for cliffs, ponds, ruins, and forest thresholds",
        paired_materials=("MI_Landscape_CoastalCliff", "MI_GrandWater_ShorelinePond"),
        user_params=("User.SpawnRate", "User.Color", "User.WindStrength", "User.LayerHeight"),
    ),
    NiagaraSystemSpec(
        "NS_Uni_Fireflies",
        SYSTEMS_UNIVERSAL,
        f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        theme="stylized firefly points for night forest and magical look-dev",
        paired_materials=("MI_Show_FairyHearts", "MI_Show_NikkiHero"),
        user_params=("User.SpawnRate", "User.Color", "User.PulseSpeed"),
    ),
    NiagaraSystemSpec(
        "NS_Uni_LeafDrift",
        SYSTEMS_UNIVERSAL,
        f"{NIAGARA_EMITTER_ROOT}/Fountain",
        theme="generic leaf drift for forest, autumn, zen, and ruin biomes",
        paired_materials=("MI_Show_ForestFoliage", "MI_Zen_MossGarden"),
        user_params=("User.SpawnRate", "User.WindStrength", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_Uni_WaterMist",
        SYSTEMS_UNIVERSAL,
        atmospheric_preset="floating_dust",
        theme="water atomization for ponds, rivers, waterfalls, and shoreline contact",
        paired_materials=("MI_GrandWater_RiverClear", "MI_GrandWater_WaterfallSheet"),
        user_params=("User.SpawnRate", "User.Color", "User.SourceWidth"),
    ),
    NiagaraSystemSpec(
        "NS_Uni_DustShafts",
        SYSTEMS_UNIVERSAL,
        f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        theme="interior dust shafts for temple, ruin, cathedral, and trimsheet showcases",
        paired_materials=("MI_Show_StoneCliff", "MI_Baroque_CathedralSurreal"),
        user_params=("User.SpawnRate", "User.Color", "User.BeamLength"),
    ),
    NiagaraSystemSpec(
        "NS_Uni_PollenSparkle",
        SYSTEMS_UNIVERSAL,
        f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        theme="botanical pollen sparkle for meadows, flower fields, and hero asset reveals",
        paired_materials=("MI_Show_CherryBlossom", "MI_Zen_BambooMist"),
        user_params=("User.SpawnRate", "User.Color", "User.PulseSpeed"),
    ),
    NiagaraSystemSpec(
        "NS_Uni_RainRipples",
        SYSTEMS_UNIVERSAL,
        f"{NIAGARA_EMITTER_ROOT}/OmnidirectionalBurst",
        theme="stylized water and wet-ground ripple accents for rainy portfolio shots",
        paired_materials=("MI_Show_ElementHydro", "MI_GrandWater_PondStylized"),
        user_params=("User.SpawnRate", "User.RippleScale", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_Uni_GroundWisps",
        SYSTEMS_UNIVERSAL,
        atmospheric_preset="floating_dust",
        theme="low magical ground wisps for forest floor, shrine, graveyard, and ruin scenes",
        paired_materials=("MI_Show_InkWash", "MI_Zen_MoonlitGarden"),
        user_params=("User.SpawnRate", "User.Color", "User.LayerHeight"),
    ),    NiagaraSystemSpec(
        "NS_SakuraPetals",
        SYSTEMS_SAKURA,
        f"{NIAGARA_EMITTER_ROOT}/Fountain",
        theme="sakura petal drift",
        paired_materials=("MI_Sakura_Blossom", "MI_Sakura_Petal"),
        user_params=("User.SpawnRate", "User.WindStrength", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_SakuraGroundPetals",
        SYSTEMS_SAKURA,
        atmospheric_preset="floating_dust",
        theme="fallen petals on path",
        paired_materials=("MI_Sakura_Petals",),
        user_params=("User.SpawnRate", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_SakuraDreamSparkle",
        SYSTEMS_SAKURA,
        f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        theme="Nikki air shimmer under canopy",
        paired_materials=("MI_Sakura_Blossom",),
        user_params=("User.SpawnRate", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_SakuraLanternMotes",
        SYSTEMS_SAKURA,
        atmospheric_preset="floating_dust",
        theme="warm motes at stone lantern",
        paired_materials=("MI_Sakura_Lantern",),
        user_params=("User.SpawnRate", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_SakuraPondShimmer",
        SYSTEMS_SAKURA,
        f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        theme="pond surface sparkle",
        paired_materials=("MI_Sakura_Water",),
        user_params=("User.SpawnRate", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_SakuraPetalGust",
        SYSTEMS_SAKURA,
        f"{NIAGARA_EMITTER_ROOT}/OmnidirectionalBurst",
        theme="wind gust burst",
        paired_materials=("MI_Sakura_Petals",),
        user_params=("User.BurstScale", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_MagicalHenshinBurst",
        SYSTEMS_MAGICAL,
        f"{NIAGARA_EMITTER_ROOT}/OmnidirectionalBurst",
        theme="magical-girl henshin burst",
        paired_materials=("MI_Universal_FairyHearts", "MI_Universal_DreamyPastel"),
        user_params=("User.BurstScale", "User.Color"),
    ),
    NiagaraSystemSpec(
        "NS_MagicTrail",
        SYSTEMS_MAGICAL,
        f"{NIAGARA_EMITTER_ROOT}/LocationBasedRibbon",
        theme="outline-adjacent magic trail",
        paired_materials=("MI_Universal_HoloFabric", "MI_Universal_IridescentShell"),
        user_params=("User.RibbonWidth", "User.Color"),
    ),
)

PROBE_ASSETS = (
    f"{PROBE_DIR}/NS_TestProbe",
    f"{PROBE_DIR}/NS_ToolsetProbe",
    f"{PROBE_DIR}/NS_ToolsetProbe2",
)


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def _ensure_vfx_folders() -> None:
    import unreal

    for path in (
        VFX_ROOT,
        MPC_DIR,
        SYSTEMS_AMBIENT,
        SYSTEMS_UNIVERSAL,
        SYSTEMS_SAKURA,
        SYSTEMS_MAGICAL,
        SHOWCASE_DIR,
    ):
        lib.ensure_directory(path)


def _mcp_ping(retries: int = 5, delay_sec: float = 1.0) -> bool:
    import time

    for attempt in range(retries):
        try:
            resp = _mcp_call("ping", {}, timeout=5.0)
            if resp.get("result", {}).get("message") == "pong" or resp.get("status") == "success":
                return True
        except OSError:
            pass
        if attempt + 1 < retries:
            time.sleep(delay_sec)
    return False


def _template_key(spec: NiagaraSystemSpec) -> str:
    if spec.atmospheric_preset:
        return spec.atmospheric_preset
    if spec.template_emitter:
        return spec.template_emitter.rsplit("/", 1)[-1].split(".", 1)[0]
    return "DefaultSystem"


def _discover_engine_templates(key: str) -> list[str]:
    import unreal

    hints = TEMPLATE_NAME_HINTS.get(key, (key,))
    static = list(ENGINE_SYSTEM_TEMPLATES.get(key, []))
    found: list[str] = []
    try:
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        ar.search_all_assets(True)
        filt = unreal.ARFilter(
            class_names=["NiagaraSystem"],
            package_paths=["/Niagara"],
            recursive_paths=True,
        )
        for data in ar.get_assets(filt):
            name = str(data.asset_name)
            if not any(h.lower() in name.lower() for h in hints):
                continue
            pkg = str(data.package_name)
            for candidate in (f"{pkg}.{name}", pkg):
                if unreal.EditorAssetLibrary.does_asset_exist(candidate):
                    found.append(candidate)
    except Exception as exc:
        unreal.log_warning(f"[VFX] template registry scan: {exc}")

    merged: list[str] = []
    for path in static + found:
        if path not in merged:
            merged.append(path)
    return merged


def _create_from_engine_system(spec: NiagaraSystemSpec) -> str:
    import unreal

    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception:
        pass

    path = _asset_path(spec.folder, spec.name)
    key = _template_key(spec)
    for src in _discover_engine_templates(key):
        if not unreal.EditorAssetLibrary.does_asset_exist(src):
            continue
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)
        dup = unreal.EditorAssetLibrary.duplicate_asset(src, path)
        if dup:
            unreal.log(f"[VFX] built {path} from engine template {src}")
            return path
    raise RuntimeError(f"No engine NiagaraSystem template for {spec.name} (key={key})")


def _duplicate_seed(spec: NiagaraSystemSpec) -> str:
    import unreal

    path = _asset_path(spec.folder, spec.name)
    try:
        return _create_from_engine_system(spec)
    except Exception as engine_exc:
        unreal.log_warning(f"[VFX] engine template failed for {spec.name}: {engine_exc}")

    if spec.atmospheric_preset:
        seed = _asset_path(SYSTEMS_AMBIENT, "NS_EmberMotes")
    elif spec.template_emitter and "Ribbon" in spec.template_emitter:
        seed = _asset_path(SYSTEMS_AMBIENT, "NS_FairyDust")
    elif spec.template_emitter and "Burst" in spec.template_emitter:
        seed = _asset_path(SYSTEMS_AMBIENT, "NS_FairyDust")
    elif spec.template_emitter and "Fountain" in spec.template_emitter:
        seed = _asset_path(SYSTEMS_AMBIENT, "NS_FairyDust")
    else:
        seed = _asset_path(SYSTEMS_AMBIENT, "NS_FairyDust")

    if not unreal.EditorAssetLibrary.does_asset_exist(seed):
        raise RuntimeError(f"No seed asset to duplicate: {seed}")

    dup = unreal.EditorAssetLibrary.duplicate_asset(seed, path)
    if not dup:
        raise RuntimeError(f"duplicate_asset failed {seed} -> {path}")
    unreal.log_warning(
        f"[VFX] duplicated {path} from {seed} (re-tune emitter stack; MCP/editor preferred for templates)"
    )
    return path


def _mcp_call(command: str, params: dict, timeout: float = 120.0) -> dict:
    payload = json.dumps({"command": command, "params": params}) + "\n"
    with socket.create_connection((MCP_HOST, MCP_PORT), timeout=timeout) as sock:
        sock.sendall(payload.encode("utf-8"))
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    line = data.split(b"\n", 1)[0].decode("utf-8", errors="replace")
    return json.loads(line)


def _create_via_mcp(spec: NiagaraSystemSpec) -> str:
    path = _asset_path(spec.folder, spec.name)
    if spec.atmospheric_preset:
        resp = _mcp_call(
            "create_atmospheric_fx",
            {
                "system_name": spec.name,
                "preset": spec.atmospheric_preset,
                "destination_path": spec.folder,
            },
        )
    else:
        resp = _mcp_call(
            "create_niagara_system",
            {
                "system_name": spec.name,
                "destination_path": spec.folder,
                "template_emitter_path": spec.template_emitter,
            },
        )
    result = resp.get("result", resp)
    if not result.get("success"):
        raise RuntimeError(f"MCP failed for {spec.name}: {resp}")
    return result.get("system_path", path)


def _create_via_toolset(spec: NiagaraSystemSpec) -> str:
    import unreal

    path = _asset_path(spec.folder, spec.name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log(f"[VFX] reusing {path}")
        return path

    if spec.atmospheric_preset:
        return _create_atmospheric_in_ue(spec)

    template_path = spec.template_emitter
    if not template_path:
        raise RuntimeError(f"No template for {spec.name}")

    # NiagaraToolset_System edit APIs are not bound on the Python class in UE 5.8;
    # prefer MCP or duplicate an existing portfolio system as scaffold.
    if not hasattr(unreal.NiagaraToolset_System, "add_emitter"):
        return _duplicate_seed(spec)

    template_emitter = unreal.load_asset(template_path)
    if not template_emitter:
        raise RuntimeError(f"Failed to load emitter template: {template_path}")

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.NiagaraSystemFactoryNew()
    system = asset_tools.create_asset(spec.name, spec.folder, unreal.NiagaraSystem, factory)
    if not system:
        raise RuntimeError(f"Failed to create NiagaraSystem {spec.name}")

    toolset = unreal.NiagaraToolset_System
    emitter_name = f"{spec.name}_Emitter"
    toolset.add_emitter(system, template_emitter, emitter_name)
    system.request_compile(False)
    try:
        system.wait_for_compile_complete()
    except Exception as exc:
        unreal.log_warning(f"[VFX] compile wait skipped for {spec.name}: {exc}")

    lib.save_package(system)
    unreal.log(f"[VFX] built {path} from {template_path}")
    return path


def _create_atmospheric_in_ue(spec: NiagaraSystemSpec) -> str:
    """Floating-dust preset: prefer MCP; in-editor fallback duplicates NS_EmberMotes or uses HangingParticulates."""
    import unreal

    path = _asset_path(spec.folder, spec.name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log(f"[VFX] reusing {path}")
        return path

    seed = _asset_path(SYSTEMS_AMBIENT, "NS_EmberMotes")
    if spec.name != "NS_EmberMotes" and unreal.EditorAssetLibrary.does_asset_exist(seed):
        dup = unreal.EditorAssetLibrary.duplicate_asset(seed, path)
        if dup:
            unreal.log(f"[VFX] duplicated atmospheric {path} from {seed}")
            return path

    unreal.log_warning(
        f"[VFX] atmospheric preset '{spec.atmospheric_preset}' needs MCP or existing NS_EmberMotes; "
        f"falling back to HangingParticulates for {spec.name}"
    )
    return _create_via_toolset(
        NiagaraSystemSpec(
            spec.name,
            spec.folder,
            f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
            theme=spec.theme,
            paired_materials=spec.paired_materials,
            user_params=spec.user_params,
        )
    )


def build_mpc_magical() -> str:
    import unreal

    lib.ensure_directory(MPC_DIR)
    path = _asset_path(MPC_DIR, MPC_MAGICAL)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialParameterCollectionFactoryNew()

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mpc = unreal.load_asset(path)
        unreal.log(f"[VFX] reusing {path}")
    else:
        mpc = asset_tools.create_asset(MPC_MAGICAL, MPC_DIR, unreal.MaterialParameterCollection, factory)
        if not mpc:
            raise RuntimeError(f"Failed to create {MPC_MAGICAL}")

    scalars = [
        ("MagicalTransform", 0.0),
        ("BurstIntensity", 0.0),
        ("SparklePulse", 0.0),
    ]
    for param_name, default in scalars:
        try:
            param = unreal.CollectionScalarParameter()
            param.default_value = default
            param.parameter_name = param_name
            mpc.add_scalar_parameter(param)
        except Exception as exc:
            unreal.log_warning(f"[VFX] MPC scalar {param_name}: {exc}")

    lib.save_package(mpc)
    unreal.log(f"[VFX] MPC ready {path}")
    return path


def cleanup_probe_assets() -> list[str]:
    import unreal

    removed: list[str] = []
    for path in PROBE_ASSETS:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            if unreal.EditorAssetLibrary.delete_asset(path):
                removed.append(path)
    if removed:
        unreal.log(f"[VFX] removed probe assets: {removed}")
    return removed


def spawn_showcase_level() -> str:
    """Place all library systems in a review grid on L_VFX_Showcase."""
    import unreal

    level_path = f"{SHOWCASE_DIR}/L_VFX_Showcase"
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.new_level(level_path)

    col = 0
    for spec in SYSTEMS:
        sys_path = _asset_path(spec.folder, spec.name)
        if not unreal.EditorAssetLibrary.does_asset_exist(sys_path):
            unreal.log_warning(f"[VFX] showcase skip missing {sys_path}")
            continue
        system = unreal.load_asset(sys_path)
        if not system:
            continue
        loc = unreal.Vector(col * 450.0, 0.0, 120.0)
        actor = eas.spawn_actor_from_class(unreal.NiagaraActor, loc, unreal.Rotator(0, 0, 0))
        if actor:
            actor.set_actor_label(spec.name)
            comp = actor.get_niagara_component()
            comp.set_asset(system)
            comp.activate(True)
        col += 1

    les.save_current_level()
    unreal.log(f"[VFX] showcase level {level_path}")
    return level_path


def build_all(*, showcase: bool = False, prefer_mcp: bool = True) -> dict:
    import unreal

    unreal.log("=== EnvSandbox Niagara library build ===")
    _ensure_vfx_folders()
    mpc_path = build_mpc_magical()
    removed = cleanup_probe_assets()

    use_mcp = prefer_mcp and _mcp_ping()
    if use_mcp:
        unreal.log("[VFX] using UnrealMCP (port 55557)")
    else:
        unreal.log("[VFX] using NiagaraToolset_System in-editor")

    built: list[dict] = []
    errors: list[dict] = []

    for spec in SYSTEMS:
        path = _asset_path(spec.folder, spec.name)
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                unreal.log(f"[VFX] skip existing {path}")
                built.append({"name": spec.name, "path": path, "status": "existing"})
                continue
            if use_mcp:
                out_path = _create_via_mcp(spec)
            else:
                out_path = _create_via_toolset(spec)
            built.append(
                {
                    "name": spec.name,
                    "path": out_path,
                    "status": "created",
                    "theme": spec.theme,
                    "materials": list(spec.paired_materials),
                }
            )
        except Exception as exc:
            unreal.log_error(f"[VFX] FAILED {spec.name}: {exc}")
            errors.append({"name": spec.name, "error": str(exc)})

    showcase_path = None
    if showcase and not errors:
        try:
            showcase_path = spawn_showcase_level()
        except Exception as exc:
            unreal.log_warning(f"[VFX] showcase failed: {exc}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpc_magical": mpc_path,
        "mpc_audio_optional": MPC_AUDIO_PATH,
        "used_mcp": use_mcp,
        "built": built,
        "errors": errors,
        "removed_probes": removed,
        "showcase_level": showcase_path,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"[VFX] report -> {REPORT_PATH}")
    unreal.log(f"=== VFX BUILD COMPLETE ({len(built)} ok, {len(errors)} errors) ===")
    return report


def _run_headless(showcase: bool) -> int:
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    args = (PROJECT_ROOT / "Content" / "Python" / "setup_niagara_library.py").as_posix()
    if showcase:
        args += " --showcase"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={args}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={LOG_PATH}",
    ]
    print(f"Niagara library build -> {LOG_PATH}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


def main() -> int:
    showcase = "--showcase" in sys.argv
    if _in_ue():
        report = build_all(showcase=showcase)
        return 1 if report.get("errors") else 0
    return _run_headless(showcase)


if __name__ == "__main__":
    raise SystemExit(main())




