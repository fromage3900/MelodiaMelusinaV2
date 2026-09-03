"""Sakura Dream Niagara kit for L_SakuraPath — six systems + sprite material + MPC driver.

Run full plan (prerequisites + rebuild + spawn + validate):
  py Content/Python/run_sakura_niagara_plan.py
  py Content/Python/run_sakura_niagara_plan.py --rebuild

Run kit only:
  py Content/Python/setup_sakura_niagara.py
  py Content/Python/setup_sakura_niagara.py --rebuild
  py Content/Python/setup_sakura_niagara.py --spawn-only

Headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_sakura_niagara_plan.py"
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import material_lib as lib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sakura_niagara_build.json"
LOG_PATH = PROJECT_ROOT / "Saved" / "Logs" / "sakura_niagara.log"

VFX_ROOT = "/Game/EnvSandbox/VFX"
VFX_MAT_DIR = f"{VFX_ROOT}/Materials"
MPC_DIR = f"{VFX_ROOT}/MPC"
SYSTEMS_SAKURA = f"{VFX_ROOT}/Systems/Sakura"
SYSTEMS_AMBIENT = f"{VFX_ROOT}/Systems/Ambient"
SYSTEMS_MAGICAL = f"{VFX_ROOT}/Systems/Magical"

LEVEL = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"
MPC_SAKURA = "MPC_SakuraDream"
MASTER_SPRITE = "M_Niagara_SakuraSprite"
NIAGARA_EMITTER_ROOT = "/Niagara/DefaultAssets/Templates/Emitters"

MCP_HOST = "127.0.0.1"
MCP_PORTS = (55557, 55558)  # UnrealMCP (EpicUnrealMCPBridge)
MONOLITH_URL = "http://127.0.0.1:9316/mcp"
_active_mcp_port: int | None = None
_active_mcp_backend: str | None = None  # "unreal" | "monolith"

# Palette from setup_sakura_instances.py (linear 0-1)
COLORS = {
    "petal_pink": (1.0, 0.74, 0.84, 1.0),
    "petal_scatter": (1.0, 0.78, 0.86, 1.0),
    "dream_tint": (1.0, 0.80, 0.90, 1.0),
    "lantern_warm": (1.0, 0.78, 0.45, 1.0),
    "water_iridescence": (0.80, 0.70, 0.95, 1.0),
}

MPC_SCALARS = [
    ("WindStrength", 0.3),
    ("GustTrigger", 0.0),
    ("SparklePulse", 0.0),
    ("PetalDensity", 1.0),
]

SPRITE_INSTANCES = [
    {
        "name": "MI_Niagara_Petal",
        # Literal petal shapes first; zen wave/circle reads as blossom accent in drift
        "texture": [
            "/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal",
            "/Game/Sakura/T_Sakura_Blossom.T_Sakura_Blossom",
            "jro:zen07",
            "jro:zen03",
        ],
        "base_color": COLORS["petal_scatter"],
        "emissive": 1.2,
        "opacity": 0.85,
    },
    {
        "name": "MI_Niagara_Sparkle",
        # Nikki shimmer + zen wave glyph (same family as MI_Zen_InkWash)
        "texture": [
            "jro:zen07",
            "jro:zen01",
            "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
            "/Game/Alphas_Sparkles/T_Spark_Glow.T_Spark_Glow",
        ],
        "base_color": COLORS["dream_tint"],
        "emissive": 2.5,
        "opacity": 0.7,
    },
    {
        "name": "MI_Niagara_Mote",
        # Lantern motes: zen circle + soft bokeh fallback
        "texture": [
            "jro:zen03",
            "jro:zen01",
            "/Game/Alphas_Sparkles/T_Spark_Bokeh.T_Spark_Bokeh",
            "/Game/Alphas_Sparkles/T_Spark_Dot.T_Spark_Dot",
        ],
        "base_color": COLORS["lantern_warm"],
        "emissive": 1.8,
        "opacity": 0.6,
    },
    {
        "name": "MI_Niagara_Pond",
        # Koi pond: sand ripples / stone garden motifs
        "texture": [
            "jro:zen35",
            "jro:zen30",
            "jro:zen07",
            "/Game/Alphas_Sparkles/T_Spark_Glow.T_Spark_Glow",
        ],
        "base_color": COLORS["water_iridescence"],
        "emissive": 1.4,
        "opacity": 0.45,
    },
    {
        "name": "MI_Niagara_Gust",
        # Wind gust accent: bamboo + petal mix
        "texture": [
            "/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal",
            "jro:zen23",
            "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
        ],
        "base_color": COLORS["petal_scatter"],
        "emissive": 1.5,
        "opacity": 0.8,
    },
]


@dataclass(frozen=True)
class SakuraSystemSpec:
    name: str
    template_emitter: str | None = None
    atmospheric_preset: str | None = None
    seed_system: str | None = None
    sprite_material: str = "MI_Niagara_Petal"
    user_params: tuple[tuple[str, str, object], ...] = ()
    theme: str = ""


SAKURA_SYSTEMS: tuple[SakuraSystemSpec, ...] = (
    SakuraSystemSpec(
        "NS_SakuraPetals",
        template_emitter=f"{NIAGARA_EMITTER_ROOT}/Fountain",
        seed_system=f"{SYSTEMS_AMBIENT}/NS_FairyDust",
        sprite_material="MI_Niagara_Petal",
        user_params=(
            ("User.SpawnRate", "float", 120.0),
            ("User.WindStrength", "float", 0.35),
            ("User.Color", "color", {"R": 1.0, "G": 0.74, "B": 0.84, "A": 1.0}),
        ),
        theme="canopy petal drift",
    ),
    SakuraSystemSpec(
        "NS_SakuraPetals_v2",
        template_emitter=f"{NIAGARA_EMITTER_ROOT}/Fountain",
        seed_system=f"{SYSTEMS_SAKURA}/NS_SakuraPetals",
        sprite_material="MI_Niagara_Petal",
        user_params=(
            ("User.SpawnRate", "float", 180.0),
            ("User.WindStrength", "float", 0.42),
            ("User.Color", "color", {"R": 1.0, "G": 0.76, "B": 0.86, "A": 1.0}),
        ),
        theme="canopy petal drift v2 (authoritative)",
    ),
    SakuraSystemSpec(
        "NS_SakuraGroundPetals",
        atmospheric_preset="floating_dust",
        seed_system=f"{SYSTEMS_AMBIENT}/NS_EmberMotes",
        sprite_material="MI_Niagara_Petal",
        user_params=(
            ("User.SpawnRate", "float", 40.0),
            ("User.Color", "color", {"R": 0.95, "G": 0.72, "B": 0.80, "A": 0.85}),
        ),
        theme="fallen petals on path",
    ),
    SakuraSystemSpec(
        "NS_SakuraDreamSparkle",
        template_emitter=f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        seed_system=f"{SYSTEMS_AMBIENT}/NS_FairyDust",
        sprite_material="MI_Niagara_Sparkle",
        user_params=(
            ("User.SpawnRate", "float", 25.0),
            ("User.Color", "color", {"R": 1.0, "G": 0.80, "B": 0.90, "A": 1.0}),
        ),
        theme="Nikki air shimmer",
    ),
    SakuraSystemSpec(
        "NS_SakuraLanternMotes",
        atmospheric_preset="floating_dust",
        seed_system=f"{SYSTEMS_AMBIENT}/NS_EmberMotes",
        sprite_material="MI_Niagara_Mote",
        user_params=(
            ("User.SpawnRate", "float", 18.0),
            ("User.Color", "color", {"R": 1.0, "G": 0.78, "B": 0.45, "A": 1.0}),
        ),
        theme="lantern warm motes",
    ),
    SakuraSystemSpec(
        "NS_SakuraPondShimmer",
        template_emitter=f"{NIAGARA_EMITTER_ROOT}/HangingParticulates",
        seed_system=f"{SYSTEMS_AMBIENT}/NS_ConstellationTwinkle",
        sprite_material="MI_Niagara_Pond",
        user_params=(
            ("User.SpawnRate", "float", 12.0),
            ("User.Color", "color", {"R": 0.80, "G": 0.70, "B": 0.95, "A": 0.6}),
        ),
        theme="pond surface sparkle",
    ),
    SakuraSystemSpec(
        "NS_SakuraPetalGust",
        template_emitter=f"{NIAGARA_EMITTER_ROOT}/OmnidirectionalBurst",
        seed_system=f"{SYSTEMS_MAGICAL}/NS_MagicalHenshinBurst",
        sprite_material="MI_Niagara_Gust",
        user_params=(
            ("User.BurstScale", "float", 1.0),
            ("User.Color", "color", {"R": 1.0, "G": 0.76, "B": 0.86, "A": 1.0}),
        ),
        theme="wind gust burst",
    ),
)

ENGINE_SYSTEM_TEMPLATES: dict[str, list[str]] = {
    "Fountain": [
        "/Niagara/DefaultAssets/Templates/Systems/FountainLightweight.FountainLightweight",
        "/Niagara/DefaultAssets/Templates/Systems/FountainLightweight",
        "/Niagara/DefaultAssets/Templates/Systems/Fountain.Fountain",
        "/Niagara/DefaultAssets/Templates/Systems/Fountain",
        "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight",
    ],
    "HangingParticulates": [
        "/Niagara/DefaultAssets/Templates/Systems/HangingParticulates.HangingParticulates",
        "/Niagara/DefaultAssets/Templates/Systems/HangingParticulates",
        "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight",
        "/Niagara/DefaultAssets/DefaultSystem.DefaultSystem",
    ],
    "OmnidirectionalBurst": [
        "/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst",
        "/Niagara/DefaultAssets/Templates/Systems/RadialBurst",
        "/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst.DirectionalBurst",
        "/Niagara/DefaultAssets/Templates/Systems/OmnidirectionalBurst.OmnidirectionalBurst",
    ],
    "floating_dust": [
        "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight",
        "/Niagara/DefaultAssets/DefaultSystem.DefaultSystem",
    ],
}

TEMPLATE_NAME_HINTS: dict[str, tuple[str, ...]] = {
    "Fountain": ("FountainLightweight", "Fountain", "MinimalLightweight"),
    "HangingParticulates": ("HangingParticulates", "MinimalLightweight", "DefaultSystem"),
    "OmnidirectionalBurst": ("RadialBurst", "DirectionalBurst", "OmnidirectionalBurst", "Burst"),
    "floating_dust": ("MinimalLightweight", "FloatingDust", "DefaultSystem"),
}


def _template_key(spec: SakuraSystemSpec) -> str:
    if spec.atmospheric_preset:
        return spec.atmospheric_preset
    if spec.template_emitter:
        return spec.template_emitter.rsplit("/", 1)[-1].split(".", 1)[0]
    return "DefaultSystem"


def _cleanup_stub_assets() -> list[str]:
    import unreal

    removed: list[str] = []
    content = PROJECT_ROOT / "Content"
    for rel in (
        "EnvSandbox/VFX/Systems/Ambient",
        "EnvSandbox/VFX/Systems/Magical",
        "EnvSandbox/VFX/Systems/Sakura",
        "EnvSandbox/VFX/MPC/MPC_Magical.uasset",
        "Sakura",
    ):
        target = content / rel
        if target.is_file() and target.stat().st_size < 512:
            asset_path = "/Game/" + rel.replace("\\", "/").replace(".uasset", "")
            name = target.stem
            full = f"{asset_path}.{name}" if not asset_path.endswith(name) else f"/Game/{rel.replace('.uasset','').replace(chr(92),'/')}.{name}"
            if unreal.EditorAssetLibrary.does_asset_exist(full) and unreal.EditorAssetLibrary.delete_asset(full):
                removed.append(full)
            target.unlink(missing_ok=True)
            removed.append(str(target))
        elif target.is_dir():
            for uasset in target.rglob("*.uasset"):
                if uasset.stat().st_size < 512:
                    rel_path = uasset.relative_to(content).as_posix()
                    stem = uasset.stem
                    folder = "/Game/" + rel_path.rsplit("/", 1)[0]
                    full = f"{folder}/{stem}.{stem}"
                    if unreal.EditorAssetLibrary.does_asset_exist(full):
                        if unreal.EditorAssetLibrary.delete_asset(full):
                            removed.append(full)
                    uasset.unlink(missing_ok=True)
                    removed.append(str(uasset))
    return removed


# Hand-tune checklist (Niagara Editor) — applied automatically where Python allows.
SAKURA_TUNING_NOTES: dict[str, list[str]] = {
    "NS_SakuraPetals": [
        "Spawn: box ~1200x800x400 above canopy; mixed petal/blossom sub-image",
        "Forces: curl noise wind + light gravity; SpriteRotationRate flutter",
        "Assign MI_Niagara_Petal on sprite renderer (Python cannot bind in UE 5.8)",
        "GPU sim if spawn rate > ~2k",
    ],
    "NS_SakuraPetals_v2": [
        "Authoritative canopy system — prefer over NS_SakuraPetals",
        "Spawn: box aligned to trunk bounds from scene anchors",
        "Bind WindStrength + GustTrigger from MPC_SakuraDream",
        "Assign MI_Niagara_Petal; tune curl noise in Niagara Editor",
    ],
    "NS_SakuraGroundPetals": [
        "Spawn: flat box along path Y=0-30; higher density under tree positions",
        "Motion: slow horizontal drift, short lifetime, desaturated pink",
        "Assign MI_Niagara_Petal; lower emissive than canopy",
    ],
    "NS_SakuraDreamSparkle": [
        "Sparse volume under canopy; sine scale/opacity pulse",
        "Bind SparklePulse from MPC_SakuraDream to emissive if exposed",
        "Assign MI_Niagara_Sparkle; size 2-6",
    ],
    "NS_SakuraLanternMotes": [
        "Small sphere spawn at lantern; ~30 motes, slow rise",
        "Assign MI_Niagara_Mote; gold (1.0, 0.78, 0.45)",
    ],
    "NS_SakuraPondShimmer": [
        "Flat box 400x300 over pond; minimal motion, twinkle only",
        "Assign MI_Niagara_Pond; cool pastel, very low opacity",
        "Pairs with MI_GrandWater_SakuraPond (WaterRoughness ~0.09, MagicalIntensity ~0.42)",
    ],
    "NS_SakuraPetalGust": [
        "One-shot burst 40-80 petals; User.BurstScale or MPC GustTrigger",
        "Assign MI_Niagara_Gust; optional 15-30s auto-loop for demo",
    ],
}


CANOPY_SYSTEM_LEGACY = "NS_SakuraPetals"
CANOPY_SYSTEM_V2 = "NS_SakuraPetals_v2"
PETAL_SYSTEMS = (CANOPY_SYSTEM_V2, "NS_SakuraGroundPetals", "NS_SakuraPetalGust")
TRUNK_FALLOFF_RADIUS_UU = 420.0


def canonical_canopy_system() -> str:
    import unreal

    v2_path = _asset_path(SYSTEMS_SAKURA, CANOPY_SYSTEM_V2)
    if unreal.EditorAssetLibrary.does_asset_exist(v2_path):
        return CANOPY_SYSTEM_V2
    return CANOPY_SYSTEM_LEGACY


def _spawn_anchors_from_scene(eas) -> dict:
    import unreal

    trunks: list[tuple[float, float, float]] = []
    canopy_center = None
    pond_center = None
    for actor in eas.get_all_level_actors() or []:
        label = actor.get_actor_label()
        loc = actor.get_actor_location()
        if label.startswith("Trunk_"):
            trunks.append((loc.x, loc.y, loc.z))
        if label.startswith("Trunk_") and canopy_center is None:
            canopy_center = (loc.x, loc.y, loc.z + 420.0)
        tags = list(getattr(actor, "tags", []) or [])
        if "PCG_Pond" in tags or "KoiPond" in label:
            pond_center = (loc.x, loc.y, loc.z + 8.0)
    if canopy_center is None:
        canopy_center = (400.0, 200.0, 420.0)
    return {
        "canopy": {"location": list(canopy_center), "trunks": trunks, "source": "scene"},
        "pond": {"location": list(pond_center or (600.0, -400.0, 8.0)), "source": "scene"},
    }


def _resolve_level_spawns(eas) -> list[dict]:
    anchors = _spawn_anchors_from_scene(eas)
    canopy_loc = tuple(anchors["canopy"]["location"])
    resolved: list[dict] = []
    for spawn in LEVEL_SPAWNS:
        entry = dict(spawn)
        if spawn["label"] == "VFX_SakuraCanopy":
            entry["system"] = canonical_canopy_system()
            entry["location"] = canopy_loc
            entry["anchor_source"] = anchors["canopy"]["source"]
        elif spawn["label"] == "VFX_PondShimmer":
            entry["location"] = tuple(anchors["pond"]["location"])
            entry["anchor_source"] = anchors["pond"]["source"]
        resolved.append(entry)
    return resolved


def _probe_mpc_material_bindings() -> dict[str, bool]:
    import unreal

    master_path = f"{VFX_MAT_DIR}/{MASTER_SPRITE}.{MASTER_SPRITE}"
    result = {name: False for name, _ in MPC_SCALARS}
    if not unreal.EditorAssetLibrary.does_asset_exist(master_path):
        return result
    mat = unreal.load_asset(master_path)
    if not mat:
        return result
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if not expr or "CollectionParameter" not in type(expr).__name__:
            continue
        try:
            pname = str(expr.get_editor_property("parameter_name") or "")
            if pname in result:
                result[pname] = True
        except Exception:
            pass
    return result


def _probe_system_mpc_exposure(system, spec: SakuraSystemSpec) -> dict:
    exposed = {p[0]: False for p in spec.user_params}
    for name in ("WindStrength", "GustTrigger", "PetalDensity"):
        if name in exposed or any(name in p[0] for p in spec.user_params):
            exposed[name] = True
    return {"user_params": exposed, "mpc_note": "Bind MPC_SakuraDream in Niagara Editor for live wind"}


LEVEL_SPAWNS = [
    {
        "label": "VFX_SakuraCanopy",
        "system": CANOPY_SYSTEM_V2,
        "location": (400.0, 200.0, 420.0),
        "scale": (3.0, 2.5, 1.5),
        "auto_activate": True,
    },
    {
        "label": "VFX_SakuraSparkle",
        "system": "NS_SakuraDreamSparkle",
        "location": (200.0, 100.0, 350.0),
        "scale": (2.5, 2.0, 1.8),
        "auto_activate": True,
    },
    {
        "label": "VFX_SakuraGround",
        "system": "NS_SakuraGroundPetals",
        "location": (0.0, 0.0, 20.0),
        "scale": (8.0, 6.0, 0.3),
        "auto_activate": True,
    },
    {
        "label": "VFX_LanternMotes",
        "system": "NS_SakuraLanternMotes",
        "location": (-600.0, 360.0, 95.0),
        "scale": (0.8, 0.8, 0.8),
        "auto_activate": True,
    },
    {
        "label": "VFX_PondShimmer",
        "system": "NS_SakuraPondShimmer",
        "location": (600.0, -400.0, 8.0),
        "scale": (4.0, 3.0, 0.2),
        "auto_activate": True,
    },
    {
        "label": "VFX_PetalGust",
        "system": "NS_SakuraPetalGust",
        "location": (400.0, 200.0, 300.0),
        "scale": (1.5, 1.5, 1.5),
        "auto_activate": False,
    },
]


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def _monolith_ping(timeout: float = 5.0) -> bool:
    try:
        import monolith_mcp_client as mono

        return mono.ping(timeout=timeout)
    except Exception:
        return False


def _monolith_call(command: str, params: dict) -> dict:
    import monolith_mcp_client as mono

    if command == "ping":
        return {"result": {"message": "pong"}} if mono.ping() else {"error": "monolith offline"}

    if command == "create_niagara_system":
        actions = (
            "create_system_from_emitter",
            "duplicate_emitter_to_system",
            "create_niagara_system",
        )
        payload = {
            "system_name": params.get("system_name"),
            "destination_path": params.get("destination_path"),
            "template_emitter_path": params.get("template_emitter_path"),
            "template_path": params.get("template_emitter_path"),
        }
        last_err = None
        for action in actions:
            try:
                result = mono.niagara_query(action, **{k: v for k, v in payload.items() if v})
                return {"result": {"success": True, "system_path": result.get("system_path") or result.get("path"), **result}}
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"Monolith niagara_query create failed: {last_err}")

    if command == "create_atmospheric_fx":
        actions = ("create_atmospheric_fx", "create_floating_dust", "create_system_from_preset")
        payload = {
            "system_name": params.get("system_name"),
            "destination_path": params.get("destination_path"),
            "preset": params.get("preset"),
        }
        last_err = None
        for action in actions:
            try:
                result = mono.niagara_query(action, **{k: v for k, v in payload.items() if v})
                return {"result": {"success": True, **result}}
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"Monolith atmospheric create failed: {last_err}")

    if command == "spawn_niagara_system":
        try:
            result = mono.niagara_query("spawn_system", **params)
            return {"result": {"success": True, **result}}
        except Exception:
            result = mono.editor_query("spawn_niagara_actor", **params)
            return {"result": {"success": True, **result}}

    if command == "set_niagara_parameter":
        try:
            result = mono.niagara_query(
                "set_user_parameter",
                actor_name=params.get("actor_name"),
                parameter_name=params.get("parameter_name"),
                parameter_type=params.get("parameter_type"),
                value=params.get("value"),
            )
            return {"result": {"success": True, **result}}
        except Exception:
            result = mono.niagara_query("set_parameter", **params)
            return {"result": {"success": True, **result}}

    raise RuntimeError(f"Monolith bridge: unsupported command {command}")


def _mcp_call(command: str, params: dict, timeout: float = 120.0) -> dict:
    global _active_mcp_backend
    if _active_mcp_backend == "monolith":
        return _monolith_call(command, params)

    global _active_mcp_port
    port = _active_mcp_port or MCP_PORTS[0]
    payload = json.dumps({"command": command, "params": params}) + "\n"
    with socket.create_connection((MCP_HOST, port), timeout=timeout) as sock:
        sock.sendall(payload.encode("utf-8"))
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    line = data.split(b"\n", 1)[0].decode("utf-8", errors="replace")
    return json.loads(line)


def _mcp_ping(retries: int = 3, delay_sec: float = 1.0) -> bool:
    import time

    global _active_mcp_port, _active_mcp_backend

    for port in MCP_PORTS:
        for attempt in range(retries):
            try:
                _active_mcp_port = port
                _active_mcp_backend = "unreal"
                resp = _mcp_call("ping", {}, timeout=5.0)
                if resp.get("result", {}).get("message") == "pong" or resp.get("status") == "success":
                    return True
            except OSError:
                pass
            if attempt + 1 < retries:
                time.sleep(delay_sec)

    for attempt in range(retries):
        if _monolith_ping(timeout=5.0):
            _active_mcp_port = None
            _active_mcp_backend = "monolith"
            return True
        if attempt + 1 < retries:
            time.sleep(delay_sec)

    _active_mcp_port = None
    _active_mcp_backend = None
    return False


def _ensure_dirs() -> None:
    for path in (VFX_ROOT, VFX_MAT_DIR, MPC_DIR, SYSTEMS_SAKURA):
        lib.ensure_directory(path)


def _run_prerequisites() -> dict:
    import unreal

    results: dict = {}
    try:
        import portfolio_alpha_paths as alpha

        for rel, dest in alpha.IMPORT_FROM_LIBRARY:
            if "Sakura" not in rel:
                continue
            stem = Path(rel).stem
            game_path = f"{dest}/{stem}.{stem}"
            if unreal.EditorAssetLibrary.does_asset_exist(game_path):
                unreal.EditorAssetLibrary.delete_asset(game_path)
        results["alpha_imports"] = alpha.ensure_alpha_imports()
    except Exception as exc:
        unreal.log_warning(f"[SakuraVFX] alpha import: {exc}")
        results["alpha_imports_error"] = str(exc)

    parent = f"{lib.MASTER_DIR}/M_Master_Toon_Universal.M_Master_Toon_Universal"
    if unreal.EditorAssetLibrary.does_asset_exist(parent):
        try:
            import setup_sakura_instances as sakura_mi

            sakura_mi.build()
            results["sakura_instances"] = "built"
        except Exception as exc:
            unreal.log_warning(f"[SakuraVFX] sakura instances: {exc}")
            results["sakura_instances_error"] = str(exc)
    else:
        results["sakura_instances"] = "skipped (master missing)"

    level_name = LEVEL.rsplit("/", 1)[-1]
    level_exists = unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.{level_name}")
    if not level_exists:
        try:
            import setup_sakura_scene

            setup_sakura_scene.build()
            results["sakura_scene"] = "built"
        except Exception as exc:
            unreal.log_warning(f"[SakuraVFX] sakura scene: {exc}")
            results["sakura_scene_error"] = str(exc)
    else:
        results["sakura_scene"] = "existing"
    return results


def build_mpc_sakura_dream() -> str:
    import unreal

    path = _asset_path(MPC_DIR, MPC_SAKURA)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialParameterCollectionFactoryNew()

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mpc = unreal.load_asset(path)
        unreal.log(f"[SakuraVFX] reusing {path}")
    else:
        mpc = asset_tools.create_asset(MPC_SAKURA, MPC_DIR, unreal.MaterialParameterCollection, factory)
        if not mpc:
            raise RuntimeError(f"Failed to create {MPC_SAKURA}")
        for param_name, default in MPC_SCALARS:
            try:
                param = unreal.CollectionScalarParameter()
                param.default_value = default
                param.parameter_name = param_name
                mpc.add_scalar_parameter(param)
            except Exception as exc:
                unreal.log_warning(f"[SakuraVFX] MPC add {param_name}: {exc}")

    lib.save_package(mpc)
    unreal.log(f"[SakuraVFX] MPC ready {path}")
    return path


def build_niagara_sprite_material(*, force: bool = False) -> str:
    import unreal

    path = _asset_path(VFX_MAT_DIR, MASTER_SPRITE)
    material = None
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.load_asset(path)
        if material and not force:
            unreal.log(f"[SakuraVFX] reusing sprite material {path}")
            return path
        if material and force:
            lib.clear_material_graph(material)

    if not material:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material = asset_tools.create_asset(
            MASTER_SPRITE, VFX_MAT_DIR, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not material:
        raise RuntimeError(f"Failed to create {MASTER_SPRITE}")

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    tex = lib.texture_param(material, "SpriteTexture", "Sprite", -900, 0, desc="Alpha sprite mask")
    base = lib.vector_param(
        material, "BaseColor", "Sprite", (1.0, 0.78, 0.86, 1.0), -900, 160, desc="Tint multiply"
    )
    emissive_strength = lib.scalar_param(
        material, "EmissiveStrength", "Sprite", 1.5, -900, 280, desc="Bloom pickup"
    )
    opacity_scalar = lib.scalar_param(material, "Opacity", "Sprite", 0.85, -900, 400)
    soft_fade = lib.scalar_param(
        material, "SoftDepthFade", "Sprite", 200.0, -900, 520, desc="Depth fade distance"
    )

    tex_rgb = lib.create_expression(material, unreal.MaterialExpressionComponentMask, -640, 0)
    tex_rgb.set_editor_property("r", True)
    tex_rgb.set_editor_property("g", True)
    tex_rgb.set_editor_property("b", True)
    tex_rgb.set_editor_property("a", False)
    lib.connect(tex, "", tex_rgb, "")

    tex_a = lib.create_expression(material, unreal.MaterialExpressionComponentMask, -640, 120)
    tex_a.set_editor_property("r", False)
    tex_a.set_editor_property("g", False)
    tex_a.set_editor_property("b", False)
    tex_a.set_editor_property("a", True)
    lib.connect(tex, "", tex_a, "")

    color_mul = lib.create_expression(material, unreal.MaterialExpressionMultiply, -420, 40)
    lib.connect(tex_rgb, "", color_mul, "A")
    lib.connect(base, "", color_mul, "B")

    emissive = lib.create_expression(material, unreal.MaterialExpressionMultiply, -200, 40)
    lib.connect(color_mul, "", emissive, "A")
    lib.connect(emissive_strength, "", emissive, "B")

    mpc_asset = f"{MPC_DIR}/{MPC_SAKURA}.{MPC_SAKURA}"
    if unreal.EditorAssetLibrary.does_asset_exist(mpc_asset):
        sparkle_mpc = lib.collection_scalar(material, MPC_DIR + "/" + MPC_SAKURA, "SparklePulse", -640, 320)
        density_mpc = lib.collection_scalar(material, MPC_DIR + "/" + MPC_SAKURA, "PetalDensity", -640, 440)
        sparkle_boost = lib.create_expression(material, unreal.MaterialExpressionMultiply, -420, 320)
        lib.connect(sparkle_mpc, "", sparkle_boost, "A")
        half = lib.create_expression(material, unreal.MaterialExpressionConstant, -640, 400)
        half.set_editor_property("r", 0.5)
        lib.connect(half, "", sparkle_boost, "B")
        emissive_pulse = lib.create_expression(material, unreal.MaterialExpressionAdd, -200, 120)
        lib.connect(emissive, "", emissive_pulse, "A")
        lib.connect(sparkle_boost, "", emissive_pulse, "B")
        emissive = emissive_pulse
        opacity_density = lib.create_expression(material, unreal.MaterialExpressionMultiply, -420, 480)
        lib.connect(opacity_scalar, "", opacity_density, "A")
        density_clamp = lib.create_expression(material, unreal.MaterialExpressionClamp, -640, 520)
        lib.connect(density_mpc, "", density_clamp, "Input")
        density_clamp.set_editor_property("min", 0.1)
        density_clamp.set_editor_property("max", 1.0)
        lib.connect(density_clamp, "", opacity_density, "B")
        opacity_scalar = opacity_density

    alpha_mul = lib.create_expression(material, unreal.MaterialExpressionMultiply, -420, 200)
    lib.connect(tex_a, "", alpha_mul, "A")
    lib.connect(opacity_scalar, "", alpha_mul, "B")

    try:
        fade = lib.create_expression(material, unreal.MaterialExpressionDepthFade, -200, 200)
        fade.set_editor_property("fade_distance", 200.0)
        lib.connect(alpha_mul, "", fade, "Opacity")
        opacity_out = fade
    except Exception:
        opacity_out = alpha_mul

    rough = lib.scalar_param(material, "RoughnessConst", "Sprite", 1.0, -420, 320)
    lib.connect(emissive, "", material, "EmissiveColor")
    lib.connect(opacity_out, "", material, "Opacity")
    lib.connect(rough, "", material, "Roughness")

    unreal.MaterialEditingLibrary.recompile_material(material)
    lib.save_package(material)
    unreal.log(f"[SakuraVFX] built sprite material {path}")
    return path


def _resolve_sprite_texture(candidates: list[str] | str) -> list[str]:
    """Expand jro:* keys to Japanese ornament paths from portfolio_alpha_paths."""
    import portfolio_alpha_paths as alpha

    if isinstance(candidates, str):
        candidates = [candidates]
    resolved: list[str] = []
    for item in candidates:
        if item.startswith("jro:"):
            key = item.split(":", 1)[1]
            paths = alpha.JAPANESE_ORNAMENT_MASKS.get(key, [])
            resolved.extend(paths if isinstance(paths, list) else [paths])
        else:
            resolved.append(item)
    return resolved


def build_sprite_instances() -> list[str]:
    import unreal

    parent = _asset_path(VFX_MAT_DIR, MASTER_SPRITE)
    if not unreal.EditorAssetLibrary.does_asset_exist(parent):
        build_niagara_sprite_material()

    made: list[str] = []
    for spec in SPRITE_INSTANCES:
        mi = lib.create_material_instance(spec["name"], VFX_MAT_DIR, parent)
        tex_candidates = _resolve_sprite_texture(spec["texture"])
        wired = lib.set_instance_texture(mi, "SpriteTexture", tex_candidates)
        if not wired:
            unreal.log_warning(f"[SakuraVFX] no texture resolved for {spec['name']}: {tex_candidates}")
        else:
            unreal.log(f"[SakuraVFX] {spec['name']} -> {wired}")
        lib.set_instance_vector(mi, "BaseColor", spec["base_color"])
        lib.set_instance_scalar(mi, "EmissiveStrength", spec["emissive"])
        lib.set_instance_scalar(mi, "Opacity", spec["opacity"])
        lib.save_package(mi)
        made.append(spec["name"])
    unreal.log(f"[SakuraVFX] sprite instances: {made}")
    return made


def _create_via_mcp(spec: SakuraSystemSpec) -> str:
    path = _asset_path(SYSTEMS_SAKURA, spec.name)
    if spec.atmospheric_preset:
        resp = _mcp_call(
            "create_atmospheric_fx",
            {
                "system_name": spec.name,
                "preset": spec.atmospheric_preset,
                "destination_path": SYSTEMS_SAKURA,
            },
        )
    else:
        resp = _mcp_call(
            "create_niagara_system",
            {
                "system_name": spec.name,
                "destination_path": SYSTEMS_SAKURA,
                "template_emitter_path": spec.template_emitter,
            },
        )
    result = resp.get("result", resp)
    if not result.get("success"):
        raise RuntimeError(f"MCP failed for {spec.name}: {resp}")
    return result.get("system_path", path)


def _discover_engine_templates(key: str) -> list[str]:
    """Registry scan for NiagaraSystem templates matching template key hints."""
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
            pkg = str(data.package_name)
            name = str(data.asset_name)
            if not any(h.lower() in name.lower() for h in hints):
                continue
            for candidate in (f"{pkg}.{name}", pkg):
                if unreal.EditorAssetLibrary.does_asset_exist(candidate):
                    found.append(candidate)
    except Exception as exc:
        unreal.log_warning(f"[SakuraVFX] template registry scan: {exc}")

    merged: list[str] = []
    for path in static + found:
        if path not in merged:
            merged.append(path)
    return merged


def _create_from_engine_system(spec: SakuraSystemSpec) -> str:
    import unreal

    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception:
        pass

    path = _asset_path(SYSTEMS_SAKURA, spec.name)
    key = _template_key(spec)
    candidates = _discover_engine_templates(key)

    for src in candidates:
        if not unreal.EditorAssetLibrary.does_asset_exist(src):
            continue
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)
        dup = unreal.EditorAssetLibrary.duplicate_asset(src, path)
        if dup:
            unreal.log(f"[SakuraVFX] built {path} from engine template {src}")
            return path
    raise RuntimeError(f"No engine NiagaraSystem template for {spec.name} (key={key})")


def _ensure_portfolio_seeds() -> None:
    """Bootstrap ambient/magical seeds if the sakura kit duplicates from portfolio library."""
    import unreal

    required = (
        _asset_path(SYSTEMS_AMBIENT, "NS_FairyDust"),
        _asset_path(SYSTEMS_AMBIENT, "NS_EmberMotes"),
        _asset_path(SYSTEMS_MAGICAL, "NS_MagicalHenshinBurst"),
    )
    if all(unreal.EditorAssetLibrary.does_asset_exist(path) for path in required):
        return
    try:
        import setup_niagara_library as nlib

        nlib.build_all(showcase=False, prefer_mcp=_mcp_ping(retries=1))
    except Exception as exc:
        unreal.log_warning(f"[SakuraVFX] portfolio seed bootstrap: {exc}")


def _duplicate_seed(spec: SakuraSystemSpec) -> str:
    import unreal

    path = _asset_path(SYSTEMS_SAKURA, spec.name)
    try:
        return _create_from_engine_system(spec)
    except Exception as engine_exc:
        unreal.log_warning(f"[SakuraVFX] engine template failed for {spec.name}: {engine_exc}")

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)

    seeds: list[str] = []
    if spec.seed_system:
        seeds.append(spec.seed_system)
    seeds.extend(
        [
            f"{SYSTEMS_AMBIENT}/NS_FairyDust",
            f"{SYSTEMS_AMBIENT}/NS_EmberMotes",
            f"{SYSTEMS_AMBIENT}/NS_ConstellationTwinkle",
            f"{SYSTEMS_MAGICAL}/NS_MagicalHenshinBurst",
        ]
    )

    for seed in seeds:
        seed_name = seed.rsplit("/", 1)[-1]
        seed_full = seed if seed.endswith(f".{seed_name}") else f"{seed}.{seed_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(seed_full):
            continue
        dup = unreal.EditorAssetLibrary.duplicate_asset(seed_full, path)
        if dup:
            unreal.log_warning(f"[SakuraVFX] duplicated {path} from portfolio seed {seed_full}")
            return path

    raise RuntimeError(f"No seed or engine template for {spec.name}")


def _delete_system(name: str) -> bool:
    import unreal

    path = _asset_path(SYSTEMS_SAKURA, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.delete_asset(path)
    return False


def create_sakura_systems(*, rebuild: bool = False, prefer_mcp: bool = True) -> list[dict]:
    import unreal

    if rebuild:
        for spec in SAKURA_SYSTEMS:
            if _delete_system(spec.name):
                unreal.log(f"[SakuraVFX] deleted for rebuild: {spec.name}")

    _ensure_portfolio_seeds()

    use_mcp = prefer_mcp and _mcp_ping()
    if use_mcp:
        unreal.log("[SakuraVFX] using UnrealMCP for system creation")
    else:
        unreal.log("[SakuraVFX] MCP unavailable — duplicating ambient/magical seeds")

    built: list[dict] = []
    for spec in SAKURA_SYSTEMS:
        path = _asset_path(SYSTEMS_SAKURA, spec.name)
        try:
            if rebuild:
                _delete_system(spec.name)
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                unreal.log(f"[SakuraVFX] reusing {path}")
                built.append({"name": spec.name, "path": path, "status": "existing"})
                continue
            if use_mcp:
                out = _create_via_mcp(spec)
                status = "created_mcp"
            else:
                out = _duplicate_seed(spec)
                status = "created_duplicate"
            built.append(
                {
                    "name": spec.name,
                    "path": out,
                    "status": status,
                    "theme": spec.theme,
                    "template": spec.template_emitter or spec.atmospheric_preset,
                }
            )
        except Exception as exc:
            unreal.log_error(f"[SakuraVFX] FAILED {spec.name}: {exc}")
            built.append({"name": spec.name, "path": path, "status": "error", "error": str(exc)})
    return built


def _assign_sprite_material(system, material_path: str) -> bool:
    import unreal

    if not unreal.EditorAssetLibrary.does_asset_exist(material_path):
        return False
    material = unreal.load_asset(material_path)
    if not material:
        return False

    assigned = False
    toolset = getattr(unreal, "NiagaraToolset_System", None)
    if toolset:
        for method in (
            "set_renderer_material",
            "SetRendererMaterial",
            "set_sprite_renderer_material",
        ):
            if hasattr(toolset, method):
                try:
                    getattr(toolset, method)(system, material)
                    assigned = True
                    break
                except Exception:
                    pass
            try:
                toolset.call_method(method, system, material)
                assigned = True
                break
            except Exception:
                pass

    editor_lib = getattr(unreal, "NiagaraEditorLibrary", None)
    if editor_lib:
        for call in (
            lambda: editor_lib.set_renderer_material(system, material),
            lambda: editor_lib.set_renderer_material(system, material, 0, 0),
            lambda: editor_lib.set_system_sprite_material(system, material),
        ):
            try:
                call()
                assigned = True
                break
            except Exception:
                pass

    try:
        handles = system.get_emitter_handles()
        for handle in handles:
            emitter = handle.get_instance()
            if not emitter:
                continue
            props = emitter.get_editor_property("renderer_properties")
            if not props:
                continue
            for prop in props:
                try:
                    prop.set_editor_property("material", material)
                    assigned = True
                except Exception:
                    try:
                        prop.set_editor_property("material_interface", material)
                        assigned = True
                    except Exception:
                        pass
    except Exception as exc:
        unreal.log_warning(f"[SakuraVFX] renderer material assign: {exc}")

    if assigned:
        system.request_compile(False)
        try:
            system.wait_for_compile_complete()
        except Exception:
            pass
        lib.save_package(system)
    return assigned


def _mcp_set_actor_params(actor_label: str, spec: SakuraSystemSpec) -> list[str]:
    import unreal

    if not _mcp_ping(retries=1):
        return []
    set_ok: list[str] = []
    for param_name, param_type, value in spec.user_params:
        try:
            if param_type == "float":
                payload = float(value)
                ptype = "float"
            elif param_type == "color" and isinstance(value, dict):
                payload = value
                ptype = "color"
            else:
                continue
            resp = _mcp_call(
                "set_niagara_parameter",
                {
                    "actor_name": actor_label,
                    "parameter_name": param_name,
                    "parameter_type": ptype,
                    "value": payload,
                },
            )
            if resp.get("result", resp).get("success", True):
                set_ok.append(param_name)
        except Exception as exc:
            unreal.log_warning(f"[SakuraVFX] MCP param {actor_label}.{param_name}: {exc}")
    return set_ok


def _mcp_spawn_actor(spawn: dict, system_folder: str) -> bool:
    import unreal

    if not _mcp_ping(retries=1):
        return False
    sys_name = spawn["system"]
    sys_path = f"{system_folder}/{sys_name}"
    try:
        resp = _mcp_call(
            "spawn_niagara_system",
            {
                "actor_name": spawn["label"],
                "system_path": sys_path,
                "location": list(spawn["location"]),
                "rotation": [0, 0, 0],
                "scale": list(spawn["scale"]),
                "auto_activate": spawn.get("auto_activate", True),
            },
        )
        return bool(resp.get("result", resp).get("success", True))
    except Exception as exc:
        unreal.log_warning(f"[SakuraVFX] MCP spawn {spawn['label']}: {exc}")
        return False


def tune_sakura_systems(*, sync_level_actors: bool = True) -> list[dict]:
    import unreal

    tuned: list[dict] = []
    spawn_by_system = {s["system"]: s["label"] for s in LEVEL_SPAWNS}
    level_actors: dict[str, object] = {}
    if sync_level_actors:
        level_name = LEVEL.rsplit("/", 1)[-1]
        if unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.{level_name}"):
            les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
            eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            les.load_level(LEVEL)
            for actor in eas.get_all_level_actors():
                label = actor.get_actor_label()
                if label in {s["label"] for s in LEVEL_SPAWNS}:
                    level_actors[label] = actor

    for spec in SAKURA_SYSTEMS:
        path = _asset_path(SYSTEMS_SAKURA, spec.name)
        entry = {
            "name": spec.name,
            "material_assigned": False,
            "params_set": [],
            "hand_tune": SAKURA_TUNING_NOTES.get(spec.name, []),
        }
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            entry["error"] = "missing"
            tuned.append(entry)
            continue

        system = unreal.load_asset(path)
        if not system:
            entry["error"] = "load failed"
            tuned.append(entry)
            continue

        mat_path = _asset_path(VFX_MAT_DIR, spec.sprite_material)
        entry["material_assigned"] = _assign_sprite_material(system, mat_path)
        entry["material_manual"] = not entry["material_assigned"]

        comp_path = f"{path}.{spec.name}"
        for param_name, param_type, value in spec.user_params:
            try:
                if param_type == "float":
                    unreal.NiagaraFunctionLibrary.set_float_parameter(comp_path, param_name, float(value))
                elif param_type == "color" and isinstance(value, dict):
                    color = unreal.LinearColor(
                        value.get("R", 1.0),
                        value.get("G", 1.0),
                        value.get("B", 1.0),
                        value.get("A", 1.0),
                    )
                    unreal.NiagaraFunctionLibrary.set_color_parameter(comp_path, param_name, color)
                entry["params_set"].append(param_name)
            except Exception:
                pass

        actor_label = spawn_by_system.get(spec.name)
        actor = level_actors.get(actor_label) if actor_label else None
        if actor:
            _set_actor_niagara_params(actor, spec)
            entry["actor_params_synced"] = actor_label

        tuned.append(entry)
        unreal.log(
            f"[SakuraVFX] tuned {spec.name}: mat={entry['material_assigned']} "
            f"params={entry['params_set']} actor={entry.get('actor_params_synced')}"
        )
    return tuned


def _set_actor_niagara_params(actor, spec: SakuraSystemSpec) -> None:
    import unreal

    comp = actor.get_component_by_class(unreal.NiagaraComponent)
    if not comp:
        return
    for param_name, param_type, value in spec.user_params:
        try:
            if param_type == "float":
                comp.set_niagara_variable_float(param_name, float(value))
            elif param_type == "color" and isinstance(value, dict):
                comp.set_niagara_variable_linear_color(
                    param_name,
                    unreal.LinearColor(
                        value.get("R", 1.0),
                        value.get("G", 1.0),
                        value.get("B", 1.0),
                        value.get("A", 1.0),
                    ),
                )
        except Exception as exc:
            unreal.log_warning(f"[SakuraVFX] actor param {param_name}: {exc}")


def spawn_sakura_vfx_on_level(*, use_mcp: bool = True) -> list[str]:
    import unreal

    level_path = LEVEL
    level_name = LEVEL.rsplit("/", 1)[-1]
    full_level = f"{level_path}.{level_name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(full_level):
        unreal.log_error(f"[SakuraVFX] level missing: {full_level}")
        return []

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level(level_path)

    spec_by_name = {s.name: s for s in SAKURA_SYSTEMS}
    spawned: list[str] = []
    mcp_ok = use_mcp and _mcp_ping(retries=1)

    for spawn in _resolve_level_spawns(eas):
        label = spawn["label"]
        sys_name = spawn["system"]
        sys_path = _asset_path(SYSTEMS_SAKURA, sys_name)
        if not unreal.EditorAssetLibrary.does_asset_exist(sys_path):
            unreal.log_warning(f"[SakuraVFX] skip spawn — missing {sys_path}")
            continue

        if mcp_ok:
            for actor in list(eas.get_all_level_actors()):
                if actor.get_actor_label() == label:
                    eas.destroy_actor(actor)
            if _mcp_spawn_actor(spawn, SYSTEMS_SAKURA):
                spec = spec_by_name.get(sys_name)
                if spec:
                    _mcp_set_actor_params(label, spec)
                spawned.append(label)
                unreal.log(f"[SakuraVFX] MCP spawned {label}")
                continue

        existing = None
        for actor in eas.get_all_level_actors():
            if actor.get_actor_label() == label:
                existing = actor
                break

        system = unreal.load_asset(sys_path)
        if not system:
            continue

        if existing:
            actor = existing
            comp = actor.get_component_by_class(unreal.NiagaraComponent)
            if comp:
                comp.set_asset(system)
                comp.set_auto_activate(spawn.get("auto_activate", True))
                if spawn.get("auto_activate", True):
                    comp.activate(True)
            spec = spec_by_name.get(sys_name)
            if spec:
                _set_actor_niagara_params(actor, spec)
            spawned.append(label)
            unreal.log(f"[SakuraVFX] updated actor {label}")
            continue

        loc = unreal.Vector(*spawn["location"])
        actor = eas.spawn_actor_from_class(unreal.NiagaraActor, loc, unreal.Rotator(0, 0, 0))
        if not actor:
            continue
        actor.set_actor_label(label)
        actor.set_actor_scale3d(unreal.Vector(*spawn["scale"]))
        comp = actor.get_component_by_class(unreal.NiagaraComponent)
        if not comp:
            unreal.log_warning(f"[SakuraVFX] no NiagaraComponent on {label}")
            continue
        comp.set_asset(system)
        comp.set_auto_activate(spawn.get("auto_activate", True))
        if spawn.get("auto_activate", True):
            comp.activate(True)
        spec = spec_by_name.get(sys_name)
        if spec:
            _set_actor_niagara_params(actor, spec)
        spawned.append(label)
        unreal.log(f"[SakuraVFX] spawned {label} @ {spawn['location']}")

    les.save_current_level()
    return spawned


def build_sakura_showcase_level() -> str:
    """Sakura-only review grid at /Game/EnvSandbox/VFX/_Showcase/L_VFX_SakuraShowcase."""
    import unreal

    showcase_dir = f"{VFX_ROOT}/_Showcase"
    level_path = f"{showcase_dir}/L_VFX_SakuraShowcase"
    lib.ensure_directory(showcase_dir)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.new_level(level_path)

    col = 0
    for spec in SAKURA_SYSTEMS:
        sys_path = _asset_path(SYSTEMS_SAKURA, spec.name)
        if not unreal.EditorAssetLibrary.does_asset_exist(sys_path):
            continue
        system = unreal.load_asset(sys_path)
        if not system:
            continue
        loc = unreal.Vector(col * 500.0, 0.0, 150.0)
        actor = eas.spawn_actor_from_class(unreal.NiagaraActor, loc, unreal.Rotator(0, 0, 0))
        if actor:
            actor.set_actor_label(spec.name)
            comp = actor.get_component_by_class(unreal.NiagaraComponent)
            comp.set_asset(system)
            comp.activate(True)
            _set_actor_niagara_params(actor, spec)
        col += 1

    les.save_current_level()
    unreal.log(f"[SakuraVFX] showcase level {level_path}")
    return level_path


def build_all(*, rebuild: bool = False, spawn: bool = True, skip_prereq: bool = False) -> dict:
    import unreal

    unreal.log("=== Sakura Dream Niagara build ===")
    _ensure_dirs()
    removed_stubs = _cleanup_stub_assets()

    prereq = {} if skip_prereq else _run_prerequisites()
    mpc_path = build_mpc_sakura_dream()
    sprite_mat = build_niagara_sprite_material()
    sprite_instances = build_sprite_instances()
    systems = create_sakura_systems(rebuild=rebuild)
    tuned = tune_sakura_systems()
    spawned = []
    if spawn:
        try:
            spawned = spawn_sakura_vfx_on_level(use_mcp=_mcp_ping(retries=1))
        except Exception as exc:
            unreal.log_error(f"[SakuraVFX] spawn failed: {exc}")
            spawned = []

    validation = {}
    try:
        validation = __import__("validate_sakura_niagara").run_validation()
    except Exception as exc:
        validation = {"error": str(exc)}

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "used_mcp": _mcp_ping(retries=1),
        "mcp_backend": _active_mcp_backend,
        "mcp_port": _active_mcp_port,
        "prerequisites": prereq,
        "removed_stub_assets": removed_stubs,
        "mpc_sakura_dream": mpc_path,
        "sprite_material": sprite_mat,
        "sprite_instances": sprite_instances,
        "systems": systems,
        "tuned": tuned,
        "spawned_actors": spawned,
        "validation": validation,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"[SakuraVFX] report -> {REPORT_PATH}")
    unreal.log("=== Sakura Dream Niagara COMPLETE ===")
    return report


def _run_headless(*args: str) -> int:
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    script = (PROJECT_ROOT / "Content" / "Python" / "setup_sakura_niagara.py").as_posix()
    if args:
        script += " " + " ".join(args)
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={script}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={LOG_PATH}",
    ]
    print(f"Sakura Niagara build -> {LOG_PATH}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


def main() -> int:
    rebuild = "--rebuild" in sys.argv
    spawn_only = "--spawn-only" in sys.argv
    skip_prereq = "--skip-prereq" in sys.argv

    if _in_ue():
        if spawn_only:
            spawned = spawn_sakura_vfx_on_level()
            print(f"SAKURA_VFX_SPAWNED {spawned}")
            return 0
        report = build_all(rebuild=rebuild, spawn=True, skip_prereq=skip_prereq)
        errors = [s for s in report.get("systems", []) if s.get("status") == "error"]
        return 1 if errors else 0

    extra = []
    if rebuild:
        extra.append("--rebuild")
    if spawn_only:
        extra.append("--spawn-only")
    if skip_prereq:
        extra.append("--skip-prereq")
    return _run_headless(*extra)


if __name__ == "__main__":
    raise SystemExit(main())
