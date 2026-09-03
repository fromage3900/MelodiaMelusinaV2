"""Melodia Asset Passport – design-system schema for Blender render pipeline.

Writes JSON + HTML sidecars matching melodia-design-system/wix/melodia-passport-embed.html
and attaches a passport dict suitable for blender_portfolio_intake.json cards.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Iterable

_TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(_TOOLS, ".."))
SITE = os.path.join(ROOT, "my-site-clean")
PASSPORT_DIR = os.path.join(SITE, "generated", "passports")
EMBED_TEMPLATE = os.path.join(ROOT, "melodia-design-system", "wix", "melodia-passport-embed.html")
SITE_EMBED = os.path.join(SITE, "wix", "melodia-passport-embed.html")


def _fmt_int(n: int) -> str:
    """Format integer with commas."""
    return f"{n:,}"


def collect_mesh_stats(objects: Iterable[Any]) -> dict[str, int]:
    """Collect mesh statistics from Blender objects."""
    tris = 0
    mats = set()
    images = set()
    mesh_count = 0

    for obj in objects:
        if getattr(obj, "type", None) != "MESH" or not obj.data:
            continue

        mesh_count += 1
        me = obj.data

        try:
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
        except Exception:
            tris += sum(len(p.vertices) - 2 for p in me.polygons if len(p.vertices) >= 3)

        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue

            mats.add(mat.name)

            if mat.use_nodes and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        images.add(node.image.name)

    return {
        "triangles": tris,
        "materials": len(mats),
        "textures": len(images),
        "meshes": mesh_count,
    }


def build_passport(
    asset_id: str,
    project: str,
    stats: dict[str, int] | None = None,
    category: str = "Character / Stylized",
    version: str = "v1.0",
    theme: str = "dark",
    engine: str = "Blender EEVEE",
    software: str = "Blender 5.1 + Melodia Stage",
    shader: str = "Authored / Komikaze NPR",
    capture: str = "Cam_Beauty",
    extra_rows: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a passport dict."""
    passport = {
        "asset_id": asset_id,
        "project": project,
        "category": category,
        "version": version,
        "theme": theme,
        "engine": engine,
        "software": software,
        "shader": shader,
        "capture": capture,
        "created": datetime.now(timezone.utc).isoformat(),
    }

    if stats:
        passport["stats"] = stats

    if extra_rows:
        passport["extra_rows"] = extra_rows

    return passport


def _slug(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def write_passport_files(passport: dict, output_dir: str | None = None) -> dict[str, str]:
    """Write passport JSON and HTML files."""
    if output_dir is None:
        output_dir = PASSPORT_DIR

    os.makedirs(output_dir, exist_ok=True)

    asset_id = passport.get("asset_id", "unknown")
    slug = _slug(asset_id)

    paths = {}

    json_path = os.path.join(output_dir, f"{slug}_passport.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(passport, f, indent=2)
    paths["json"] = json_path

    html_path = os.path.join(output_dir, f"{slug}_passport.html")
    html = render_passport_html(passport)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    paths["html"] = html_path

    return paths


def render_passport_html(passport: dict) -> str:
    """Render passport as HTML."""
    asset_id = passport.get("asset_id", "")
    project = passport.get("project", "")
    stats = passport.get("stats", {})

    html_parts = []
    html_parts.append(f"<div class='passport'>")
    html_parts.append(f"<h2>{asset_id}</h2>")
    html_parts.append(f"<p><strong>Project:</strong> {project}</p>")

    if stats:
        html_parts.append(f"<dl>")
        for key, value in stats.items():
            html_parts.append(f"<dt>{key}</dt><dd>{_fmt_int(value)}</dd>")
        html_parts.append(f"</dl>")

    html_parts.append(f"</div>")

    return "\n".join(html_parts)


def passport_for_objects(
    asset_id: str,
    project: str,
    blender_objects: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Build passport from Blender objects."""
    stats = None
    if blender_objects:
        stats = collect_mesh_stats(blender_objects)

    return build_passport(asset_id, project, stats=stats)


def attach_passport_to_card(card: dict, passport: dict) -> dict:
    """Attach passport data to a portfolio card."""
    card["passport"] = passport
    return card


def emit_for_collection(collection_name: str) -> list[dict]:
    """Emit passports for a Blender collection."""
    return []


def emit_melusina_stage_passport(
    beauty_ref: str = "beauty void/iri interim – melusina_beauty_void_iri.png",
    stage_ref: str = "Stage EEVEE – Nikki lights – FadeDayNight",
) -> dict[str, Any]:
    """Create passport for Melusina stage setup."""
    return build_passport(
        asset_id="melusina_stage",
        project="Melusina",
        category="Stage Setup",
        software="Blender EEVEE + Melodia Stage",
        capture="Cam_Beauty",
    )


if __name__ == "__main__":
    demo = build_passport(
        asset_id="demo",
        project="Demo Asset",
        stats={
            "triangles": 12345,
            "materials": 4,
            "textures": 2,
            "meshes": 3,
        },
    )

    paths = write_passport_files(demo)

    print(
        json.dumps(
            {
                "passport": demo,
                "paths": paths,
            },
            indent=2,
        )
    )
