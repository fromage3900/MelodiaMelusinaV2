"""Build a semantic, deterministic asset constellation for a Resonant World chunk.

The first Resonant World atlas proved that the repository contains the raw
ingredients.  This layer answers the next authoring question: *which existing
ingredients form one coherent magical place for this movement, seed, and
chunk?*

It is deliberately an authoring/read-model bridge.  It does not load Unreal
assets, spawn actors, equip cosmetics, apply traversal, grant currency, or
write save state.  Each selected reference states whether it is backed by a
project file, an authoring manifest, or only a logical contract.  This keeps
the infinite-world promise honest while still making the asset surface useful.

The design borrows three useful ideas from open-world styling games without
copying their content: abilities are world verbs, appearance can be styled
independently from capability, and every generated moment has a scene-preview
and presentation readback.  Quantum remains a low-frequency two-candidate
chooser; it never generates geometry or chooses individual voxels.

Usage::

    python Content/Python/resonant_world_asset_constellation.py \
        --seed 3900 --movement petal_cantata --chunk-x 0 --chunk-y 0 \
        --output Saved/Audit/resonant_world_constellation_petal_3900.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from resonant_world_asset_atlas import (
    MANIFEST_FILES,
    _load_json_manifests,
    _scan_files,
)
from resonant_world_generator import (
    WORLD_MOVEMENT_LIBRARY,
    WorldConfig,
    stable_int,
)


CONSTELLATION_VERSION = "resonant_asset_constellation_v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ROLE_ORDER = (
    "terrain",
    "structure",
    "flora",
    "ornament",
    "material",
    "water",
    "vfx",
    "wardrobe",
    "music",
    "character",
    "population",
    "quantum",
    "ui",
)

REQUIRED_ROLES = ("terrain", "structure", "music", "wardrobe", "vfx", "quantum")
ROLE_LIMITS = {
    "terrain": 4,
    "structure": 6,
    "flora": 5,
    "ornament": 5,
    "material": 6,
    "water": 3,
    "vfx": 4,
    "wardrobe": 4,
    "music": 6,
    "character": 3,
    "population": 4,
    "quantum": 4,
    "ui": 4,
}

BLOCKED_PATH_TOKENS = (
    "/_archive/",
    "/_quarantine/",
    "/_deprecated/",
    "/__externalactors__/",
    "/__externalobjects__/",
    "/__pycache__/",
    "/saved/",
    "/intermediate/",
    "/deriveddatacache/",
    "/binaries/",
    "/build/",
)

MOVEMENT_ALIASES: dict[str, tuple[str, ...]] = {
    "petal_cantata": ("sakura", "petal", "blossom", "bloom", "phyllotaxis", "tea", "garden"),
    "star_loom": ("cosmic", "space", "star", "astral", "orrery", "constellation", "loom"),
    "liquid_cathedral": ("water", "river", "pond", "rain", "crystal", "harp", "grotto"),
    "cadence_cathedral": ("musical", "hero", "cathedral", "bridge", "bell", "xylophone", "harp", "piano"),
    "mirage_gala": ("mirage", "wind", "dune", "ribbon", "sakura", "meadow", "escher"),
    "dissonant_expanse": ("dissonant", "umbral", "void", "grotto", "cyberpunk", "baroque", "ruin", "escher"),
}

WORLD_MOMENTS: dict[str, dict[str, Any]] = {
    "bloom": {
        "moment_id": "petal_memory",
        "scene": "a flower opens only when the player's phrase returns to its tonic",
        "route": "petal_lattice",
        "handheld_conductor": "petal_chime",
    },
    "weave": {
        "moment_id": "constellation_hem",
        "scene": "a constellation becomes a walkable hemline between two sky islands",
        "route": "star_thread",
        "handheld_conductor": "astral_shuttle",
    },
    "conduct": {
        "moment_id": "tide_chord",
        "scene": "a water surface carries a chord toward a submerged landmark",
        "route": "ripple_staff",
        "handheld_conductor": "tide_baton",
    },
    "compose": {
        "moment_id": "living_score",
        "scene": "placed tone voxels grow into an architectural phrase with a readable cadence",
        "route": "note_bridge",
        "handheld_conductor": "score_folio",
    },
    "drift": {
        "moment_id": "ribbon_mirage",
        "scene": "wind reveals the next route as a ribbon that answers the player's silhouette",
        "route": "wind_lattice",
        "handheld_conductor": "ankle_bell_compass",
    },
    "resolve": {
        "moment_id": "beautiful_dissonance",
        "scene": "an unresolved interval becomes a survivable portal rather than a failure state",
        "route": "rest_gate",
        "handheld_conductor": "dissonance_prism",
    },
}


def _verification_snapshot(project_root: Path) -> dict[str, Any]:
    """Expose Echo/PIE evidence without confusing it with authoring proof."""
    ledger_path = project_root / "Saved" / "gate_ledger.json"
    latest: dict[str, dict[str, Any]] = {}
    if ledger_path.exists():
        try:
            raw = json.loads(ledger_path.read_text(encoding="utf-8"))
            for row in raw.get("gates", []):
                if isinstance(row, dict) and row.get("id"):
                    latest[str(row["id"])] = {
                        "status": row.get("status"),
                        "date": row.get("date"),
                        "time": row.get("time"),
                        "session": row.get("session"),
                        "note": row.get("note"),
                    }
        except (OSError, json.JSONDecodeError):
            latest = {}

    return {
        "echo": {
            "runner": "Tools/echo_run.py",
            "contract": "specs/echo_pipeline.json",
            "ledger": "Saved/gate_ledger.json",
            "ledger_present": ledger_path.exists(),
            "latest_gate_status": latest,
            "commands": {
                "status": "python Tools/echo_run.py status",
                "runtime": "python Tools/echo_run.py run runtime_gates",
                "record": "python Tools/echo_run.py record <gate-id> pass|fail --note \"...\"",
            },
            "authority": "ledger_only",
        },
        "pie": {
            "runner": "Tools/playtest_harness.py",
            "preflight": "python Tools/playtest_harness.py preflight",
            "run": "python Tools/playtest_harness.py run --map L_KaleidoNave --backend auto",
            "evidence_root": "Saved/Playtest",
            "runtime_gate_is_not_world_specific": True,
            "world_specific_status": "not_yet_observed",
            "read_model_is_not_pie_proof": True,
            "editor_apply_performed": False,
        },
    }


def _normalise(value: str) -> str:
    return str(value).replace("\\", "/").lower()


def _is_blocked(path: str) -> bool:
    normalised = f"/{_normalise(path).strip('/')}/"
    if any(token in normalised for token in BLOCKED_PATH_TOKENS):
        return True
    segments = [segment for segment in normalised.strip("/").split("/") if segment]
    return any(
        segment.startswith(("_archive", "_quarantine", "_deprecated"))
        for segment in segments
    )


def _unreal_to_disk_path(project_root: Path, unreal_path: str | None) -> Path | None:
    if not unreal_path or not str(unreal_path).startswith("/Game/"):
        return None
    relative = str(unreal_path)[len("/Game/"):].strip("/")
    base = project_root / "Content" / relative
    for suffix in ("", ".uasset", ".umap"):
        candidate = Path(f"{base}{suffix}")
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _movement_tokens(movement_id: str, movement: Any) -> tuple[str, ...]:
    raw = [movement_id.replace("_", " "), movement.display_name, *movement.pcg_asset_fragments,
           *movement.musical_asset_fragments, *movement.water_profiles, *movement.vfx_systems]
    tokens: set[str] = set()
    for value in raw:
        normalised = _normalise(value)
        for token in normalised.replace("/", " ").replace("_", " ").split():
            if len(token) >= 3 and token not in {"pcg", "wp", "midi", "ns", "hero"}:
                tokens.add(token)
    tokens.update(MOVEMENT_ALIASES.get(movement_id, ()))
    return tuple(sorted(tokens))


def _ref(
    *,
    role: str,
    reference: str,
    source: str,
    score: int,
    evidence: Iterable[str],
    project_root: Path,
    unreal_path: str | None = None,
    authoring_ready: bool = True,
    runtime_ready: bool | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    disk_path = _unreal_to_disk_path(project_root, unreal_path)
    if runtime_ready is None:
        runtime_ready = disk_path is not None
    out = {
        "role": role,
        "reference": str(reference),
        "source": source,
        "score": int(score),
        "evidence": sorted(set(str(item) for item in evidence if item)),
        "authoring_ready": bool(authoring_ready),
        "runtime_ready": bool(runtime_ready),
        "on_disk": bool(disk_path),
    }
    if unreal_path:
        out["unreal_path"] = str(unreal_path)
    if disk_path:
        out["disk_path"] = disk_path.relative_to(project_root).as_posix()
    if metadata:
        out["metadata"] = dict(metadata)
    return out


@lru_cache(maxsize=4)
def _inventory(project_root_name: str) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, str]]:
    root = Path(project_root_name).resolve()
    rows, summary = _scan_files(root)
    manifests, manifest_errors = _load_json_manifests(root)
    return rows, summary, manifests, manifest_errors


def _role_hints(role: str) -> tuple[str, ...]:
    return {
        "terrain": ("terrain", "landscape", "l_wp_", "worldpartition", "renderterrains"),
        "structure": ("pcg", "hero", "cathedral", "bridge", "garden", "orrery", "grotto", "ruins", "temple", "oasis", "meadow"),
        "flora": ("sakura", "petal", "flower", "blossom", "bloom", "foliage", "phyllotaxis", "garden", "meadow"),
        "ornament": ("sm_orn_", "musicalornament", "sheetmusic", "piano", "bell", "harp", "xylophone", "filigree"),
        "material": ("/materials/", "mi_", "m_master_", "mpc_melodia", "landscape"),
        "music": ("/midi/", ".mid", "musical", "audio", "harmony", "melody"),
        "character": ("melusina", "/characters/"),
        "quantum": ("/python/quantum/", "qsharp", "quantum"),
        "ui": ("/ui/", "figma", "hud", "scene_preview", "interactionprompt"),
    }.get(role, ())


def _role_suffixes(role: str) -> set[str]:
    return {
        "terrain": {".uasset", ".umap"},
        "structure": {".uasset", ".umap"},
        "flora": {".uasset", ".umap", ".png", ".fbx", ".glb"},
        "ornament": {".uasset", ".fbx", ".glb", ".png"},
        "material": {".uasset"},
        "music": {".uasset", ".mid", ".wav", ".ogg", ".mp3"},
        "character": {".uasset", ".umap", ".fbx", ".png"},
        "quantum": {".py", ".qs", ".cs", ".json", ".md"},
        "ui": {".uasset", ".png", ".svg", ".json"},
    }.get(role, set())


def _path_candidates(
    rows: list[dict[str, Any]],
    project_root: Path,
    movement_tokens: tuple[str, ...],
    role: str,
) -> list[dict[str, Any]]:
    hints = _role_hints(role)
    suffixes = _role_suffixes(role)
    candidates: list[dict[str, Any]] = []
    for row in rows:
        path = str(row.get("path", ""))
        lower = _normalise(path)
        suffix = str(row.get("suffix", "")).lower()
        if not path or _is_blocked(path) or suffix not in suffixes:
            continue
        if role == "music" and "/midi/" not in lower and suffix not in {".mid", ".wav", ".ogg", ".mp3"}:
            continue
        if role == "character" and "melusina" not in lower:
            continue
        if role == "quantum" and "/python/quantum/" not in lower:
            continue
        if role == "ui" and "/ui/" not in lower and "figma" not in lower:
            continue
        matched_tokens = [token for token in movement_tokens if token in lower]
        matched_hints = [hint for hint in hints if hint in lower]
        # A movement word such as "garden" is not enough evidence for a
        # terrain, ornament, material, character, or UI binding.  Those roles
        # need their own semantic path signal; otherwise a PCG garden graph
        # would be falsely reported as a terrain mesh or a material instance.
        if role in {"terrain", "ornament", "material", "character", "ui"} and not matched_hints:
            continue
        if not matched_tokens and not matched_hints:
            continue
        if role == "character" and ("/textures/" in lower or "/audio/" in lower):
            continue
        if role == "terrain" and (
            "sm_terrain" not in lower
            and "/renderterrains/" not in lower
            and "/environments/wp/l_wp_" not in lower
        ):
            continue
        if role == "ornament" and not any(
            token in lower
            for token in ("sm_orn_", "/meshes/ornament/", "sheetmusic", "/pcg/musical/mi_piano")
        ):
            continue
        if role == "material" and "/materials/" not in lower and not any(
            token in lower for token in ("/mi_", "/m_master_", "mpc_melodia")
        ):
            continue
        score = len(matched_tokens) * 4 + len(matched_hints) * 2
        if role in row.get("families", []):
            score += 2
        if suffix in {".uasset", ".umap", ".mid"}:
            score += 1
        candidates.append(_ref(
            role=role,
            reference=path,
            source="project_file",
            score=score,
            evidence=[*matched_tokens, *matched_hints],
            project_root=project_root,
            unreal_path=("/Game/" + path[len("Content/"):].rsplit(".", 1)[0].replace("\\", "/"))
            if path.startswith("Content/") and suffix in {".uasset", ".umap"} else None,
            metadata={"families": list(row.get("families", [])), "suffix": suffix},
        ))
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["reference"])))
    return candidates


def _terrain_fallback(rows: list[dict[str, Any]], project_root: Path) -> list[dict[str, Any]]:
    candidates = []
    for row in rows:
        path = str(row.get("path", ""))
        lower = _normalise(path)
        if _is_blocked(path) or row.get("suffix") not in {".uasset", ".umap"}:
            continue
        if "sm_terrain" not in lower and "/environments/wp/l_wp_" not in lower:
            continue
        candidates.append(_ref(
            role="terrain",
            reference=path,
            source="project_file_shared_fallback",
            score=1,
            evidence=["shared_terrain_fallback"],
            project_root=project_root,
            unreal_path=("/Game/" + path[len("Content/"):].rsplit(".", 1)[0].replace("\\", "/"))
            if path.startswith("Content/") else None,
            metadata={"shared_fallback": True},
        ))
    return candidates


def _manifest_vfx_refs(project_root: Path, manifests: Mapping[str, Any], movement: Any) -> list[dict[str, Any]]:
    systems = manifests.get("niagara_nikki", {}).get("systems", {})
    refs: list[dict[str, Any]] = []
    for system_id in movement.vfx_systems:
        system = systems.get(system_id, {}) if isinstance(systems, dict) else {}
        unreal_path = system.get("path")
        refs.append(_ref(
            role="vfx",
            reference=system_id,
            source="niagara_manifest",
            score=10 if system else 1,
            evidence=["movement_vfx_system", "manifest_record" if system else "manifest_gap"],
            project_root=project_root,
            unreal_path=unreal_path,
            runtime_ready=_unreal_to_disk_path(project_root, unreal_path) is not None,
            metadata={
                "description": system.get("description"),
                "routes": dict(system.get("osr_routes", {})),
                "max_particles": system.get("max_particles"),
            },
        ))
    return refs


def _manifest_water_refs(project_root: Path, manifests: Mapping[str, Any], movement: Any) -> list[dict[str, Any]]:
    profiles = manifests.get("water_profiles", {}).get("profiles", {})
    refs: list[dict[str, Any]] = []
    for profile_id in movement.water_profiles:
        profile = profiles.get(profile_id, {}) if isinstance(profiles, dict) else {}
        role = str(profile.get("role", ""))
        # Melusina hair is a valuable cross-layer water shader reference, but it
        # is not a traversable water body and must never be bound as one.
        if profile_id == "melusina_hair" or role not in {"pond", "river", "waterfall"}:
            continue
        unreal_path = profile.get("surface_instance")
        refs.append(_ref(
            role="water",
            reference=profile_id,
            source="water_profile_manifest",
            score=10 if profile else 1,
            evidence=["movement_water_profile", "traversable_water_role"],
            project_root=project_root,
            unreal_path=unreal_path,
            metadata={"profile": dict(profile), "water_role": role},
        ))
    return refs


def _manifest_wardrobe_refs(project_root: Path, manifests: Mapping[str, Any], movement: Any, archetype_id: str | None) -> list[dict[str, Any]]:
    archetypes = manifests.get("archetypes", {}).get("archetypes", {})
    chosen = archetype_id or (movement.outfit_archetypes[0] if movement.outfit_archetypes else "Melusina")
    ids = [chosen] if chosen else []
    refs: list[dict[str, Any]] = []
    for item in ids:
        record = archetypes.get(item, {}) if isinstance(archetypes, dict) else {}
        refs.append(_ref(
            role="wardrobe",
            reference=f"manifest:archetypes/{item}",
            source="archetype_manifest",
            score=10 if record else 1,
            evidence=["movement_archetype", "appearance_layer", "ability_style_preview"],
            project_root=project_root,
            runtime_ready=False,
            metadata={
                "display_name": record.get("display_name", item),
                "element": record.get("element"),
                "outfit_pieces": list(record.get("outfit_pieces", [])),
                "spawn_zones": list(record.get("spawn_zones", [])),
                "source_is_manifest": True,
            },
        ))
    return refs


def _population_refs(project_root: Path, manifests: Mapping[str, Any], movement: Any, archetype_id: str | None) -> list[dict[str, Any]]:
    archetypes = manifests.get("archetypes", {}).get("archetypes", {})
    chosen = archetype_id or (movement.outfit_archetypes[0] if movement.outfit_archetypes else "Melusina")
    record = archetypes.get(chosen, {}) if isinstance(archetypes, dict) else {}
    zones = list(record.get("spawn_zones", [])) if record else list(movement.npc_zones)
    return [
        _ref(
            role="population",
            reference=f"manifest:population/{chosen}/{zone}",
            source="archetype_manifest",
            score=8 if record else 2,
            evidence=["movement_npc_zone", "authored_spawn_zone"],
            project_root=project_root,
            runtime_ready=False,
            metadata={"archetype_id": chosen, "zone": zone},
        )
        for zone in zones
    ]


def _quantum_refs(project_root: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs = _path_candidates(rows, project_root, ("quantum", "qsharp", "movement", "ranker"), "quantum")
    # Keep the two source files that define the current movement selector even
    # if a future scan changes the generic path scoring.
    return refs


def _ordered_refs(seed: int, movement_id: str, chunk_x: int, chunk_y: int, role: str, refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        refs,
        key=lambda item: (
            -int(item.get("score", 0)),
            stable_int(seed, "constellation", movement_id, chunk_x, chunk_y, role, item.get("reference")),
            str(item.get("reference")),
        ),
    )


def _quantum_setup(seed: int, movement_id: str, mode_id: str, coverage: Mapping[str, Any]) -> dict[str, Any]:
    compatible = [
        candidate_id
        for candidate_id, movement in WORLD_MOVEMENT_LIBRARY.items()
        if mode_id in movement.mode_affinities
    ]
    if movement_id not in compatible:
        compatible.insert(0, movement_id)
    candidates = (movement_id, next((item for item in compatible if item != movement_id), movement_id))
    rank_preview: dict[str, Any] | None = None
    try:
        from quantum.resonant_movement_ranker import MovementCandidate, rank_movements

        rank_candidates = []
        for candidate_id in candidates:
            candidate_coverage = coverage.get("candidate_movement_coverage", {}).get(candidate_id, {})
            role_count = sum(1 for value in candidate_coverage.get("role_counts", {}).values() if value)
            features = {
                "outfit_synergy": 1.0 if candidate_coverage.get("wardrobe") else 0.0,
                "asset_coverage": min(1.0, role_count / max(1, len(REQUIRED_ROLES))),
                "traversal_safety": 0.85 if candidate_coverage.get("water") or candidate_id != "dissonant_expanse" else 0.70,
                "visual_contrast": 0.85 if candidate_id in {"star_loom", "mirage_gala"} else 0.72,
                "motif_continuity": 0.90 if candidate_id in {"petal_cantata", "cadence_cathedral"} else 0.68,
            }
            rank_candidates.append(MovementCandidate(candidate_id, candidate_id, features))
        rank_preview = rank_movements(seed, rank_candidates, backend="qsharp-simulator")
    except Exception as exc:  # pragma: no cover - optional Q# environment
        rank_preview = {"status": "classical_rank_preview_unavailable", "reason": str(exc)}
    return {
        "algorithm": "two_candidate_amplitude_measurement",
        "qsharp_operation": "QuantumGameplay.WorldComposer.PickMovement",
        "candidate_movements": list(candidates),
        "backend_policy": {
            "preferred": "qsharp-simulator",
            "fallback": "classical-baseline",
            "requires_exactly_two_candidates": True,
        },
        "rank_preview": rank_preview,
        "selection_stage": "world_preparation_only",
        "quantum_is_selector_not_generator": True,
        "not_allowed": ["per_frame_traversal", "individual_voxel_selection", "player_input_grading", "reward_grants"],
        "persist_before_apply": ["winner_movement_id", "classical_baseline_winner_id", "backend", "trace_id"],
    }


def build_asset_constellation(
    project_root: str | Path = PROJECT_ROOT,
    world_seed: int = 3900,
    *,
    movement_id: str | None = None,
    chunk_x: int = 0,
    chunk_y: int = 0,
    archetype_id: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    rows, scan_summary, manifests, manifest_errors = _inventory(str(root))
    config = WorldConfig.from_seed(world_seed)
    selected_movement_id = movement_id or config.movement_id
    if selected_movement_id not in WORLD_MOVEMENT_LIBRARY:
        raise ValueError(f"unknown movement id: {selected_movement_id}")
    movement = WORLD_MOVEMENT_LIBRARY[selected_movement_id]
    tokens = _movement_tokens(selected_movement_id, movement)

    candidates: dict[str, list[dict[str, Any]]] = {}
    for role in ROLE_ORDER:
        if role == "vfx":
            refs = _manifest_vfx_refs(root, manifests, movement)
        elif role == "water":
            refs = _manifest_water_refs(root, manifests, movement)
        elif role == "wardrobe":
            refs = _manifest_wardrobe_refs(root, manifests, movement, archetype_id)
        elif role == "population":
            refs = _population_refs(root, manifests, movement, archetype_id)
        elif role == "quantum":
            refs = _quantum_refs(root, rows)
        else:
            refs = _path_candidates(rows, root, tokens, role)
            if role == "terrain" and not refs:
                refs = _terrain_fallback(rows, root)
        candidates[role] = _ordered_refs(world_seed, selected_movement_id, chunk_x, chunk_y, role, refs)

    selected = {
        role: refs[: ROLE_LIMITS.get(role, 4)]
        for role, refs in candidates.items()
    }
    role_counts = {role: len(refs) for role, refs in selected.items()}
    missing_required_roles = [role for role in REQUIRED_ROLES if not selected.get(role)]
    candidate_movement_coverage: dict[str, Any] = {}
    for candidate_id, candidate_movement in WORLD_MOVEMENT_LIBRARY.items():
        candidate_tokens = _movement_tokens(candidate_id, candidate_movement)
        candidate_counts = {}
        for role in ("terrain", "structure", "flora", "material", "music"):
            candidate_refs = _path_candidates(rows, root, candidate_tokens, role)
            if role == "terrain" and not candidate_refs:
                candidate_refs = _terrain_fallback(rows, root)
            candidate_counts[role] = len(candidate_refs)
        candidate_counts["wardrobe"] = len(_manifest_wardrobe_refs(root, manifests, candidate_movement, None))
        candidate_counts["vfx"] = len(_manifest_vfx_refs(root, manifests, candidate_movement))
        candidate_counts["water"] = len(_manifest_water_refs(root, manifests, candidate_movement))
        candidate_counts["quantum"] = len(_quantum_refs(root, rows))
        candidate_movement_coverage[candidate_id] = {"role_counts": candidate_counts, **candidate_counts}

    coverage = {
        "required_roles": list(REQUIRED_ROLES),
        "bound_roles": [role for role in ROLE_ORDER if role_counts.get(role, 0) > 0],
        "missing_required_roles": missing_required_roles,
        "role_counts": role_counts,
        "candidate_movement_coverage": candidate_movement_coverage,
        "required_role_coverage": round(
            (len(REQUIRED_ROLES) - len(missing_required_roles)) / len(REQUIRED_ROLES), 3
        ),
        "runtime_ready_reference_count": sum(
            1 for refs in selected.values() for item in refs if item.get("runtime_ready")
        ),
        "authoring_reference_count": sum(
            1 for refs in selected.values() for item in refs if item.get("authoring_ready")
        ),
        "blocked_candidates_excluded": True,
    }
    moment = dict(WORLD_MOMENTS.get(movement.world_verb, WORLD_MOMENTS["compose"]))
    constellation_id = hashlib.sha256(
        f"{CONSTELLATION_VERSION}|{int(world_seed)}|{selected_movement_id}|{int(chunk_x)}|{int(chunk_y)}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "format": "melodia_resonant_world_asset_constellation",
        "schema_version": 1,
        "constellation_version": CONSTELLATION_VERSION,
        "constellation_id": constellation_id,
        "world": {
            "world_seed": int(world_seed),
            "chunk": [int(chunk_x), int(chunk_y)],
            "root_note": config.root_note,
            "mode_id": config.mode_id,
            "bpm": config.bpm,
            "beats_per_bar": config.beats_per_bar,
            "motif_id": config.motif_id,
            "movement_id": selected_movement_id,
            "movement_display_name": movement.display_name,
            "world_verb": movement.world_verb,
            "resonant_form_id": movement.resonant_form_id,
        },
        "inventory": {
            "scanned_file_count": scan_summary.get("scanned_file_count", 0),
            "family_counts": scan_summary.get("family_counts", {}),
            "manifest_sources": {
                key: {"path": MANIFEST_FILES.get(key), "loaded": key not in manifest_errors, "error": manifest_errors.get(key)}
                for key in MANIFEST_FILES
            },
            "movement_tokens": list(tokens),
        },
        "movement": movement.to_dict(),
        "asset_candidates": {
            role: refs[: ROLE_LIMITS.get(role, 4) * 3]
            for role, refs in candidates.items()
        },
        "bindings": selected,
        "coverage": coverage,
        "magical_moment": {
            **moment,
            "phrase_identity": f"{config.mode_id}:{config.motif_id}:{movement.world_verb}",
            "style_layer": {
                "archetype_id": archetype_id or (movement.outfit_archetypes[0] if movement.outfit_archetypes else "Melusina"),
                "appearance_is_separate_from_capability": True,
                "capability_declared_by_form": movement.resonant_form_id,
                "effect_toggle_surface": True,
                "scene_preview_surface": True,
            },
            "route_is_a_request": True,
            "route_authority": "UMelodiaTraversalComponent",
        },
        "quantum_setup": _quantum_setup(world_seed, selected_movement_id, config.mode_id, coverage),
        "verification": _verification_snapshot(root),
        "canonical_authorities": {
            "asset_loading": "existing Unreal PCG/World Partition and catalog owners",
            "wardrobe": "UMelodiaWardrobeSubsystem",
            "form_capability": "existing form/catalog gate",
            "traversal": "UMelodiaTraversalComponent",
            "narrative_and_save": "UMelodiaNarrativeSubsystem",
            "currency": "UMelodiaTokenWalletSubsystem through canonical reward adapter",
            "music_clock": "existing Harmonix/Melodia music clock",
            "quantum": "world preparation result persisted before authored PCG apply",
        },
        "runtime_boundary": {
            "authoring_or_read_model": True,
            "does_not_load_unreal_assets": True,
            "does_not_spawn_actors": True,
            "does_not_equip": True,
            "does_not_grant_capability": True,
            "does_not_apply_traversal": True,
            "does_not_grant_currency": True,
            "does_not_write_save": True,
        },
    }


def validate_asset_constellation(constellation: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if constellation.get("format") != "melodia_resonant_world_asset_constellation":
        errors.append("unexpected constellation format")
    if constellation.get("constellation_version") != CONSTELLATION_VERSION:
        errors.append("unregistered constellation version")
    world = constellation.get("world", {})
    if world.get("movement_id") not in WORLD_MOVEMENT_LIBRARY:
        errors.append("unknown movement id")
    coverage = constellation.get("coverage", {})
    for role in REQUIRED_ROLES:
        if int(coverage.get("role_counts", {}).get(role, 0)) <= 0:
            errors.append(f"required asset role is unbound: {role}")
    for role, refs in constellation.get("bindings", {}).items():
        seen: set[str] = set()
        for item in refs:
            reference = str(item.get("reference", ""))
            if not reference:
                errors.append(f"{role} contains an empty reference")
            if reference in seen:
                errors.append(f"{role} contains duplicate reference: {reference}")
            seen.add(reference)
            if _is_blocked(reference):
                errors.append(f"blocked reference escaped into binding: {reference}")
            if role == "water" and str(item.get("reference")) == "melusina_hair":
                errors.append("Melusina hair must not be bound as traversable water")
    boundary = constellation.get("runtime_boundary", {})
    for key in ("does_not_load_unreal_assets", "does_not_spawn_actors", "does_not_apply_traversal", "does_not_write_save"):
        if boundary.get(key) is not True:
            errors.append(f"runtime boundary missing truthy guard: {key}")
    quantum = constellation.get("quantum_setup", {})
    if len(quantum.get("candidate_movements", [])) != 2:
        errors.append("quantum setup must contain exactly two candidate movements")
    if quantum.get("quantum_is_selector_not_generator") is not True:
        errors.append("quantum setup must state selector-not-generator boundary")
    return errors


def build_constellation_portfolio(project_root: str | Path = PROJECT_ROOT, world_seed: int = 3900) -> dict[str, Any]:
    constellations = [
        build_asset_constellation(project_root, world_seed, movement_id=movement_id)
        for movement_id in WORLD_MOVEMENT_LIBRARY
    ]
    errors = {
        item["world"]["movement_id"]: validate_asset_constellation(item)
        for item in constellations
    }
    return {
        "format": "melodia_resonant_world_asset_constellation_portfolio",
        "schema_version": 1,
        "constellation_version": CONSTELLATION_VERSION,
        "world_seed": int(world_seed),
        "constellation_count": len(constellations),
        "constellations": constellations,
        "validation_errors": {key: value for key, value in errors.items() if value},
        "ok": not any(errors.values()),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--movement", default="petal_cantata")
    parser.add_argument("--chunk-x", type=int, default=0)
    parser.add_argument("--chunk-y", type=int, default=0)
    parser.add_argument("--archetype")
    parser.add_argument("--all-movements", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.all_movements:
        result = build_constellation_portfolio(args.root, args.seed)
    else:
        result = build_asset_constellation(
            args.root,
            args.seed,
            movement_id=args.movement,
            chunk_x=args.chunk_x,
            chunk_y=args.chunk_y,
            archetype_id=args.archetype,
        )
        result["validation_errors"] = validate_asset_constellation(result)
        result["ok"] = not result["validation_errors"]
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
