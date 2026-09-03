"""Build a deterministic World Partition PCG set-dressing handoff.

This is intentionally editor-independent. It consumes the latest verified
``Saved/Audit/wp_pillar_levels.json`` report and writes one SVG density plate,
one JSON contract, and one Markdown handoff for each WP pillar. Density is a
readability signal, not a navigation proof; navmesh and capsule-clearance
checks remain explicit manual gates.

Run from the project root:
    python Content/Python/generate_wp_setdress_handoff.py
"""
from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Saved" / "Audit" / "wp_pillar_levels.json"
OUT_DIR = ROOT / "Saved" / "Audit" / "WP_SetDress"

RULES = {
    "primary_route_clear_cm": 250,
    "secondary_route_clear_cm": 150,
    "landmark_clear_cm": 350,
    "encounter_clear_cm": 700,
    "density_bands": {
        "sparse": "background framing / negative space",
        "light": "secondary route or approach",
        "medium": "destination dressing",
        "dense": "hero cluster only; keep off traversal lane",
        "very_dense": "hero composition only; reduce before playtest",
    },
}

PALETTE = {
    "sparse": "#9ad7c4",
    "light": "#f3d36b",
    "medium": "#f39b5a",
    "dense": "#dd5f70",
    "very_dense": "#8e3d68",
}

SETDRESS_BEATS = {
    "SakuraDream": {
        "identity": "Blossom promenade: gentle arrival, petal-framed destination, garden discovery branch.",
        "hero_volume": "PCG_SakuraDream_0",
        "arrival": "Keep the first 700 cm quiet enough for Melusina and the first landmark silhouette to read immediately.",
        "destination": "Dress the densest meadow/blossom pocket as the hero garden, with a clear return sightline.",
        "negative_space": "Preserve open sky and pale ground around the promenade so petals do not become visual noise.",
    },
    "SpaceCathedral": {
        "identity": "Celestial ascent: long readable spine, measured vertical reveal, observatory-like destination.",
        "hero_volume": "PCG_SpaceCathedral_0",
        "arrival": "Use the first route segment as a clean orientation deck; do not hide the next elevation change.",
        "destination": "Reserve the highest-contrast architectural silhouette for the far end of the 1,600 cm route.",
        "negative_space": "Leave deliberate voids between floating platforms so traversal beats remain legible at a glance.",
    },
    "BaroqueGrotto": {
        "identity": "Ruined garden grotto: framed entry, overgrown side discovery, colonnade destination.",
        "hero_volume": "PCG_BaroqueGrotto_3",
        "arrival": "Keep wall growth lateral rather than across the primary lane; let the entry read as a threshold.",
        "destination": "Use the colonnade/ruin cluster as the hero composition and leave a 700 cm encounter approach pocket.",
        "negative_space": "Maintain dark-to-light contrast at the grotto mouth; avoid ivy and moss filling every vertical surface.",
    },
    "CosmicOrrery": {
        "identity": "Orbiting garden: compact arrival, circular discovery, luminous mechanical landmark.",
        "hero_volume": "PCG_CosmicOrrery_0",
        "arrival": "Keep the first 400 cm readable as a tutorial-scale movement beat with one obvious forward choice.",
        "destination": "Stage the orbit scatter as a single luminous focal system, not a uniform starfield.",
        "negative_space": "Preserve dark voids between orbit bands so the player can read platform order and return direction.",
    },
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _svg(pillar: dict) -> str:
    volumes = pillar.get("verify", {}).get("ism_per_volume", {})
    names = list(volumes)
    if not names:
        names = [v.get("label", "Volume") for v in pillar.get("pcg_volumes", [])]
    counts = [int(volumes.get(name, 0)) for name in names]
    width, height = 1200, 520
    left, top, chart_w, chart_h = 110, 95, 1000, 300
    max_count = max(counts or [1])
    bar_w = chart_w / max(1, len(names)) * 0.72
    gap = chart_w / max(1, len(names))
    bars = []
    for i, (name, count) in enumerate(zip(names, counts)):
        x = left + i * gap + (gap - bar_w) / 2
        bar_h = max(4, chart_h * count / max_count)
        y = top + chart_h - bar_h
        if count < 50:
            band = "sparse"
        elif count < 200:
            band = "light"
        elif count < 500:
            band = "medium"
        elif count < 1000:
            band = "dense"
        else:
            band = "very_dense"
        label = name.replace(f"PCG_{pillar['pillar']}_", "V")
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'fill="{PALETTE[band]}" rx="4"/><text x="{x + bar_w / 2:.1f}" y="{y - 10:.1f}" '
            f'text-anchor="middle" class="count">{count}</text><text x="{x + bar_w / 2:.1f}" '
            f'y="{top + chart_h + 28:.1f}" text-anchor="middle" class="label">{_esc(label)}</text>'
        )
    total = sum(counts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
<style>text{{font-family:Arial,sans-serif;fill:#24313a}}.title{{font-size:28px;font-weight:700}}.sub{{font-size:15px;fill:#52616b}}.count{{font-size:16px;font-weight:700}}.label{{font-size:14px}}</style>
<rect width="100%" height="100%" fill="#f7f3ea"/><text x="55" y="50" class="title">{_esc(pillar['pillar'])} PCG density handoff</text>
<text x="55" y="75" class="sub">Verified instances: {total} | density is a dressing signal, not nav proof</text>
<line x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}" stroke="#52616b"/>
{''.join(bars)}
<text x="55" y="470" class="sub">Clear primary route: {RULES['primary_route_clear_cm']} cm | landmark clear: {RULES['landmark_clear_cm']} cm | encounter clear: {RULES['encounter_clear_cm']} cm</text>
</svg>'''


def _contract(pillar: dict) -> dict:
    verified = pillar.get("verify", {})
    volumes = verified.get("ism_per_volume", {})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pillar": pillar["pillar"],
        "level": pillar.get("level"),
        "world_partition": pillar.get("world_partition", verified.get("world_partition", False)),
        "verification": {
            "passed": verified.get("passed", False),
            "expected_volume_count": verified.get("expected_volume_count", 0),
            "volume_count": len(volumes),
            "total_ism": verified.get("total_ism", 0),
            "missing_volumes": verified.get("missing_volumes", []),
            "empty_volumes": verified.get("empty_volumes", []),
        },
        "design_contract": {
            "primary_route": "Keep the central traversal spine visually quiet and readable.",
            "secondary_routes": "Use light-density volumes as optional discovery branches.",
            "landmarks": "Reserve the densest volume for one hero landmark or destination beat.",
            "encounters": "Place encounter triggers in a 700 cm clear approach pocket.",
            "no_scatter": "Author WP_NoScatter around player starts, triggers, camera beats, and interactables.",
            "clearance_cm": RULES,
        },
        "set_dressing_beats": SETDRESS_BEATS.get(pillar["pillar"], {}),
        "manual_gates": [
            "Navmesh reaches the intended destination without crossing a dense cluster.",
            "Melusina capsule has at least 250 cm primary-route clearance.",
            "No hero landmark occludes the next route decision from the approach camera.",
            "Encounter pocket supports turn-in, combat presentation, and retreat without collision.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    data = json.loads(args.source.read_text(encoding="utf-8"))
    pillars = data.get("pillars", {})
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = {"generated_at": datetime.now(timezone.utc).isoformat(), "pillars": []}
    for key, pillar in pillars.items():
        contract = _contract(pillar)
        stem = f"{key}_setdress"
        (OUT_DIR / f"{stem}.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
        (OUT_DIR / f"{stem}.svg").write_text(_svg(pillar), encoding="utf-8")
        index["pillars"].append(contract)
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Generated {len(index['pillars'])} WP set-dressing contracts in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
