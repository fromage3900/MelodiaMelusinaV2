"""Build the website-facing technical breakdown manifest from UE evidence.

This is intentionally offline: it can run after an editor capture pass and
never invents a render as web-ready. Missing camera, trim, shader, or PCG proof
stays explicit so the site can show the next production task.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "my-site-clean"
PACKAGE = ROOT / "Saved" / "Portfolio" / "portfolio_package.json"
CAMERAS = ROOT / "Saved" / "Portfolio" / "technical_breakdown_cameras.json"
MATERIAL_AUDIT = ROOT / "Saved" / "Audit" / "material_instance_audit.json"
RENDERS = ROOT / "Saved" / "Portfolio" / "Renders" / "renders_manifest.json"
OUTPUTS = (
    SITE / "generated" / "technical" / "unreal-breakdown-manifest.json",
    ROOT / "_github_deploy" / "generated" / "technical" / "unreal-breakdown-manifest.json",
)


def read_json(path: Path) -> dict:
    """Read JSON file with error handling."""
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> int:
    """Build the technical breakdown manifest."""
    package = read_json(PACKAGE)
    cameras = read_json(CAMERAS)
    audit = read_json(MATERIAL_AUDIT)
    renders = read_json(RENDERS)

    render_cards = (
        renders.get("render_cards") or renders.get("cards") or []
    )
    camera_shots = cameras.get("shots") or []

    groups = {str(card.get("group")) for card in render_cards if isinstance(card, dict)}

    material_count = audit.get("counts", {}).get("materials_total")
    if material_count is None:
        material_count = len(package.get("materials") or [])

    slots = [
        ("shader_master", "Universal master graph", "shader_graph", "renders.breakdown"),
        ("material_instance", "Material instance family plate", "material_instance", "renders.materials"),
        ("pcg_heatmap", "PCG density and route heatmap", "pcg_heatmap", "renders.pcg"),
        ("trim_sheet", "Trim and atlas proof", "trim_sheet", "renders.breakdown"),
        ("world_shader", "In-scene shader response", "world_shader", "renders.breakdown"),
    ]

    breakdowns = []

    for shot_id, title, proof, destination in slots:
        shot = next(
            (item for item in camera_shots if item.get("id") == shot_id),
            None,
        )
        ready = bool(shot and destination.removeprefix("renders.") in groups)

        breakdowns.append({
            "id": shot_id,
            "title": title,
            "proof": proof,
            "destination": destination,
            "camera": shot.get("label") if shot else None,
            "camera_configured": bool(shot),
            "capture_present": ready,
            "status": (
                "web_ready" if ready
                else "camera_ready" if shot
                else "needs_camera"
            ),
        })

    payload = {
        "format": "melodia_technical_breakdown_manifest_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scene": package.get("scene") or cameras.get("level"),
        "camera_count": len(camera_shots),
        "material_instance_count": material_count,
        "breakdowns": breakdowns,
        "evidence": {
            "portfolio_package": str(PACKAGE),
            "camera_manifest": str(CAMERAS),
            "material_audit": str(MATERIAL_AUDIT),
            "render_manifest": str(RENDERS),
        },
        "website_contract": {
            "asset_root": "generated/assets/unreal/",
            "intake": "tools/ingest_unreal_portfolio.ps1",
            "target_pages": [
                "wix/shader-breakdowns.html",
                "wix/render-constellation.html",
            ],
        },
        "next_actions": [
            item["title"]
            for item in breakdowns
            if item["status"] != "web_ready"
        ],
    }

    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "camera_count": len(camera_shots),
                "material_instances": material_count,
                "next_actions": payload["next_actions"],
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
