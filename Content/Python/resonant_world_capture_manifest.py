"""Build a read-only visual-evidence manifest for Resonant World captures.

The score and asset constellation describe what a generated musical world should
be.  This module describes how that world is allowed to appear in a portfolio
capture.  It deliberately does not render, open Unreal, copy images, or publish
to the webfront.  Instead it joins each canonical lookdev slot to:

* the deterministic movement/score/constellation that motivates the shot;
* absolute source paths for the existing project assets;
* an intended camera, lighting, and material state; and
* locally observed PNG evidence with a conservative visual-review verdict.

An exact target filename is never treated as publishable by filename alone.
Clean-frame approval remains a human/lookdev decision, and the manifest marks
missing, unreviewed, or rejected evidence without inventing a placeholder.

Usage::

    python Content/Python/resonant_world_capture_manifest.py \
        --seed 3900 --output Saved/Audit/resonant_world_capture_manifest_3900.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from resonant_world_asset_constellation import (
    build_asset_constellation,
    validate_asset_constellation,
)
from resonant_world_score import build_resonant_score, validate_resonant_score


CAPTURE_MANIFEST_VERSION = "resonant_world_capture_manifest_v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_CANDIDATES_PER_TARGET = 24
SCAN_DIRECTORIES = ("Saved", "Exports", "Products")
RENDER_TEST_NAMESPACE = "/Game/_PROJECT/Levels/RenderTests/"

# Findings reported by the render-only lookdev lane.  These are intentionally
# rejection records, not approval shortcuts: a filename can be useful evidence
# while still being disqualified from webfront intake.
KNOWN_REVIEW_FINDINGS: dict[str, tuple[str, str]] = {
    "l_render_sakuradream_beauty_raw.png": (
        "rejected_runtime_evidence",
        "Lookdev review rejected this SakuraDream PIE capture: black/checker frames and post-marker Error/Ensure matches were observed.",
    ),
}


# These are the four named slots requested by the overnight lookdev lane.  The
# recipes are intentions, not claims that the current editor state already
# satisfies them.
CAPTURE_TARGETS: tuple[dict[str, Any], ...] = (
    {
        "target_id": "niagara_sakura_ambience",
        "movement_id": "petal_cantata",
        "filename": "breakdown_niagara_sakura_ambience_1920x1080.png",
        "resolution": [1920, 1080],
        "camera_intent": "clean standalone SakuraDream traversal pocket: low forward three-quarter view, route readable from foreground to blossom landmark",
        "lighting_state": "soft Sakura dusk key with cool water fill, restrained bloom, readable midtones, no editor viewport overlays",
        "material_state": "MI_Sakura_Blossom and MI_WaterV7_SakuraPond corrected in their instances; validate blossom translucency, pond reflection, and Niagara sparkle in-world",
        "asset_roles": ["terrain", "flora", "water", "ornament", "vfx", "music"],
        "search_tokens": ["sakura", "blossom", "pond", "niagara", "petal"],
        "reject_if": [
            "editor chrome, frustums, debug icons, or selection outlines are visible",
            "the frame is an empty greybox or an unlit gradient rather than a readable world pocket",
            "preview geometry or material-grid cards are used as the in-world shot",
        ],
    },
    {
        "target_id": "zen_shrine_axis_route_proof",
        "movement_id": "star_loom",
        "filename": "pcg_zen_shrine_axis_route_proof_1920x1080.png",
        "resolution": [1920, 1080],
        "camera_intent": "clean axial establishing frame: shrine landmark and generated musical route share one vanishing line",
        "lighting_state": "celestial blue hour with a warm shrine accent, controlled exposure, route readable without PCG debug visualization",
        "material_state": "use the resolved star-loom structure, ornament, material, and music bindings; show authored surface contrast rather than generator diagnostics",
        "asset_roles": ["terrain", "structure", "ornament", "material", "music", "vfx"],
        "search_tokens": ["zen", "shrine", "axis", "pcg", "star", "loom"],
        "reject_if": [
            "PCG debug points, bounds, splines, labels, or editor chrome are visible",
            "the route cannot be read against a real landmark or surface",
            "the capture is a placeholder gradient or an empty test platform",
        ],
    },
    {
        "target_id": "baroque_escher_ornament",
        "movement_id": "dissonant_expanse",
        "filename": "breakdown_baroque_escher_ornament_1920x1080.png",
        "resolution": [1920, 1080],
        "camera_intent": "hero ornament breakdown in context: rose-window/Escher circulation gesture framed with enough negative space to read the recursive silhouette",
        "lighting_state": "ink-blue ambient with ivory and wine-gold edge accents, high local contrast, no clipped white ornament highlights",
        "material_state": "ebony/ivory musical accents and authored baroque ornament materials; surface response should be legible at the hero distance",
        "asset_roles": ["structure", "ornament", "material", "terrain", "music", "vfx"],
        "search_tokens": ["baroque", "escher", "ornament", "rosewindow", "rose_window", "dissonant"],
        "reject_if": [
            "the ornament is isolated as an unlit preview card rather than shown in a world composition",
            "wireframe, bounds, gizmos, or debug text are visible",
            "white clipping or an empty background hides the recursive silhouette",
        ],
    },
    {
        "target_id": "nikki_surface_polish",
        "movement_id": "petal_cantata",
        "filename": "materials_nikki_surface_polish_2048x2048.png",
        "resolution": [2048, 2048],
        "camera_intent": "clean material passport: close surface read with one hero material family and restrained supporting swatches, no editor UI",
        "lighting_state": "large soft key, cool rim, neutral exposure, gentle specular separation for satin, water, ebony, and ivory",
        "material_state": "Infinity-Nikki-inspired polish target: pearlescent bloom, clear but controlled wetness, satin cloth response, and ebony/ivory contrast; candidate state until visual A/B approval",
        "asset_roles": ["material", "water", "flora", "ornament", "structure"],
        "search_tokens": ["material", "surface", "nikki", "sakura", "water", "piano", "ivory", "ebony", "constellation"],
        "reject_if": [
            "preview geometry, diagnostic cards, editor chrome, or debug labels are visible",
            "the sample is black/white clipped, unlit, or too blurred to read surface response",
            "the image is a before-state or an unapproved candidate presented as final polish",
        ],
    },
)


def _normalise(value: str) -> str:
    return str(value).replace("\\", "/").lower()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _png_dimensions(path: Path) -> list[int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
        if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
            return None
        width, height = struct.unpack(">II", header[16:24])
        return [int(width), int(height)]
    except (OSError, struct.error):
        return None


def _is_blocked_scan_path(path: Path) -> bool:
    blocked = {
        ".git",
        "binaries",
        "build",
        "deriveddatacache",
        "intermediate",
        "node_modules",
        "__pycache__",
        "_archive",
        "_deprecated",
        "_quarantine",
    }
    return any(part.lower() in blocked for part in path.parts)


def _iter_pngs(project_root: Path) -> Iterable[Path]:
    seen: set[str] = set()
    for directory_name in SCAN_DIRECTORIES:
        directory = project_root / directory_name
        if not directory.is_dir():
            continue
        for path in directory.rglob("*.png"):
            if _is_blocked_scan_path(path) or not path.is_file():
                continue
            key = _normalise(str(path.resolve()))
            if key in seen:
                continue
            seen.add(key)
            yield path


def _candidate_verdict(path: Path, target: Mapping[str, Any]) -> tuple[str, str]:
    lower = _normalise(str(path))
    filename = path.name
    known = KNOWN_REVIEW_FINDINGS.get(filename.lower())
    if known:
        return known
    expected = str(target["filename"])
    if filename == expected:
        return (
            "exact_target_unverified",
            "Exact target filename exists; clean-frame visual approval is still required.",
        )
    if "lookdevlane3" in lower and "rendertest_pie" in lower:
        return (
            "rejected_preview",
            "Observed PIE frame is retained as diagnostic evidence, not a clean standalone capture.",
        )
    if any(token in lower for token in ("before", "raw", "debug", "wireframe", "frustum", "overlay")):
        return (
            "rejected_preview",
            "Filename identifies a before/raw/debug/overlay state; it cannot be promoted as final lookdev evidence.",
        )
    if "lookdevlane3" in lower and any(token in lower for token in ("material", "shadowfix", "clamp", "water")):
        return (
            "rejected_preview",
            "Observed material preview is useful A/B evidence but still contains preview/debug presentation risk.",
        )
    return (
        "unreviewed_candidate",
        "Candidate matches the target search vocabulary but has no recorded clean-frame approval.",
    )


def _find_candidates(project_root: Path, target: Mapping[str, Any]) -> list[dict[str, Any]]:
    tokens = tuple(str(item).lower() for item in target.get("search_tokens", ()))
    rows: list[tuple[float, Path]] = []
    for path in _iter_pngs(project_root):
        searchable = _normalise(f"{path.name} {path.parent}")
        if not any(token in searchable for token in tokens):
            continue
        try:
            modified = path.stat().st_mtime
        except OSError:
            continue
        rows.append((modified, path))
    rows.sort(key=lambda item: (-item[0], str(item[1])))
    candidates: list[dict[str, Any]] = []
    for _, path in rows[:MAX_CANDIDATES_PER_TARGET]:
        verdict, note = _candidate_verdict(path, target)
        dimensions = _png_dimensions(path)
        candidates.append(
            {
                "absolute_path": str(path.resolve()),
                "relative_path": path.resolve().relative_to(project_root.resolve()).as_posix(),
                "filename": path.name,
                "dimensions": dimensions,
                "sha256": _sha256(path),
                "observed_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "verdict": verdict,
                "note": note,
                "matches_target_resolution": dimensions == list(target["resolution"]),
            }
        )
    return candidates


def _absolute_disk_path(project_root: Path, value: str | None) -> str | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = project_root / path
    return str(path.resolve()) if path.exists() else None


def _source_asset_refs(
    project_root: Path,
    constellation: Mapping[str, Any],
    roles: Iterable[str],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    bindings = constellation.get("bindings", {})
    for role in roles:
        for item in bindings.get(role, []):
            if not isinstance(item, Mapping):
                continue
            reference = str(item.get("reference", ""))
            if reference in seen:
                continue
            seen.add(reference)
            refs.append(
                {
                    "role": role,
                    "reference": reference,
                    "unreal_path": item.get("unreal_path"),
                    "absolute_path": _absolute_disk_path(project_root, item.get("disk_path")),
                    "runtime_ready": bool(item.get("runtime_ready")),
                    "source": item.get("source"),
                    "evidence": list(item.get("evidence", [])),
                }
            )
    return refs


def _build_target_manifest(
    project_root: Path,
    world_seed: int,
    chunk_x: int,
    chunk_y: int,
    target: Mapping[str, Any],
) -> dict[str, Any]:
    movement_id = str(target["movement_id"])
    constellation = build_asset_constellation(
        project_root,
        world_seed,
        movement_id=movement_id,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
    )
    score = build_resonant_score(
        world_seed,
        movement_id=movement_id,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
        project_root=project_root,
    )
    constellation_errors = validate_asset_constellation(constellation)
    score_errors = validate_resonant_score(score)
    candidates = _find_candidates(project_root, target)
    exact = [item for item in candidates if item["filename"] == target["filename"]]
    if exact:
        status = "exact_target_unverified"
    elif candidates:
        status = "observed_candidates_not_publishable"
    else:
        status = "missing_clean_capture"
    return {
        "target_id": target["target_id"],
        "status": status,
        "movement_id": movement_id,
        "score_id": score.get("score_id"),
        "constellation_id": constellation.get("constellation_id"),
        "output_filename": target["filename"],
        "output_path": str((project_root / "Saved" / "Screenshots" / "ResonantWorld" / target["filename"]).resolve()),
        "resolution": list(target["resolution"]),
        "camera_intent": target["camera_intent"],
        "lighting_state": target["lighting_state"],
        "material_state": target["material_state"],
        "asset_roles": list(target["asset_roles"]),
        "source_asset_refs": _source_asset_refs(project_root, constellation, target["asset_roles"]),
        "observed_candidates": candidates,
        "clean_frame_requirements": {
            "editor_chrome_free": None,
            "frustums_and_debug_icons_free": None,
            "white_clipping_free": None,
            "empty_gradient_free": None,
            "preview_geometry_free": None,
            "visual_approval": "required",
            "reject_if": list(target["reject_if"]),
        },
        "validation": {
            "score_errors": score_errors,
            "constellation_errors": constellation_errors,
            "source_asset_count": len(_source_asset_refs(project_root, constellation, target["asset_roles"])),
        },
        "materialization": {"performed": False, "writes_project_state": False},
    }


def build_capture_manifest(
    world_seed: int = 3900,
    *,
    movement_id: str | None = None,
    chunk_x: int = 0,
    chunk_y: int = 0,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the four-slot visual evidence contract without mutating state."""
    root = Path(project_root).resolve() if project_root else PROJECT_ROOT
    requested = str(movement_id or "all")
    targets = [
        target
        for target in CAPTURE_TARGETS
        if requested in ("", "all", "*") or str(target["movement_id"]) == requested
    ]
    if not targets:
        raise ValueError(f"unknown capture movement id: {requested}")
    records = [
        _build_target_manifest(root, int(world_seed), int(chunk_x), int(chunk_y), target)
        for target in targets
    ]
    return {
        "format": "melodia_resonant_world_capture_manifest",
        "schema_version": 1,
        "capture_manifest_version": CAPTURE_MANIFEST_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "world": {
            "seed": int(world_seed),
            "chunk": [int(chunk_x), int(chunk_y)],
            "movement_scope": requested,
        },
        "render_map_contract": {
            "namespace": RENDER_TEST_NAMESPACE,
            "write_scope": "isolated render-only map",
            "allowed": [RENDER_TEST_NAMESPACE],
            "forbidden": [
                "/Game/Melodia/Environments/WP/L_WP_SakuraDream",
                "Headquarters BFG",
                "source graphs",
                "gameplay maps",
                "save/gameplay state",
            ],
        },
        "targets": records,
        "verification": {
            "target_count": len(records),
            "exact_target_count": sum(item["status"] == "exact_target_unverified" for item in records),
            "clean_approved_count": sum(item["status"] == "publishable" for item in records),
            "clean_capture_pending_count": sum(item["status"] != "publishable" for item in records),
            "missing_clean_capture_count": sum(item["status"] != "publishable" for item in records),
            "observed_but_not_publishable_count": sum(item["status"] == "observed_candidates_not_publishable" for item in records),
            "publish_policy": "never promote a placeholder or an unreviewed/debug frame",
            "scan_directories": [str((root / item).resolve()) for item in SCAN_DIRECTORIES if (root / item).is_dir()],
        },
        "runtime_boundary": {
            "read_model_only": True,
            "does_not_render": True,
            "does_not_touch_gameplay_maps": True,
            "does_not_copy_images": True,
            "does_not_publish_webfront": True,
            "does_not_load_unreal_assets": True,
            "does_not_write_save": True,
        },
        "materialization": {"performed": False, "writes_project_state": False},
    }


def validate_capture_manifest(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("format") != "melodia_resonant_world_capture_manifest":
        errors.append("unexpected capture manifest format")
    if manifest.get("capture_manifest_version") != CAPTURE_MANIFEST_VERSION:
        errors.append("unregistered capture manifest version")
    targets = list(manifest.get("targets", []))
    if not targets:
        errors.append("capture manifest has no targets")
    for target in targets:
        if not target.get("output_filename", "").endswith(".png"):
            errors.append(f"target has no PNG output filename: {target.get('target_id')}")
        resolution = target.get("resolution", [])
        if len(resolution) != 2 or any(int(value) <= 0 for value in resolution):
            errors.append(f"target has invalid resolution: {target.get('target_id')}")
        if target.get("status") == "publishable":
            requirements = target.get("clean_frame_requirements", {})
            if requirements.get("visual_approval") != "approved":
                errors.append(f"publishable target lacks visual approval: {target.get('target_id')}")
        if target.get("materialization", {}).get("writes_project_state") is not False:
            errors.append(f"capture target crossed the read-only boundary: {target.get('target_id')}")
    boundary = manifest.get("runtime_boundary", {})
    for key in ("read_model_only", "does_not_render", "does_not_publish_webfront", "does_not_write_save"):
        if boundary.get(key) is not True:
            errors.append(f"runtime boundary missing {key}")
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--movement", default="all")
    parser.add_argument("--chunk-x", type=int, default=0)
    parser.add_argument("--chunk-y", type=int, default=0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = build_capture_manifest(
        args.seed,
        movement_id=args.movement,
        chunk_x=args.chunk_x,
        chunk_y=args.chunk_y,
    )
    errors = validate_capture_manifest(manifest)
    manifest["validation_errors"] = errors
    manifest["ok"] = not errors
    encoded = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
