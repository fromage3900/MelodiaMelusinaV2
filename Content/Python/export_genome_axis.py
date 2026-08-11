"""Export genome axis steps from architectural_atoms.yaml for Figma visualization.

Reads deploy/surreal_os/architectural_atoms.yaml and emits a JSON fragment
containing ordered axis steps for the StyleGenomeAxisDiagram Figma component.

Output:
    Saved/Portfolio/Metadata/genome_axis.json

Run (standalone):
    python Content/Python/export_genome_axis.py
    python Content/Python/export_genome_axis.py --genome ZEN_SHRINE_AXIS

Run (in-editor):
    py Content/Python/export_genome_axis.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ATOMS_YAML = PROJECT_ROOT / "deploy" / "surreal_os" / "architectural_atoms.yaml"
OUT_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "Metadata" / "genome_axis.json"

# Fallback genome order when no explicit axis sequence is defined in YAML
_DEFAULT_AXIS = ["GB_ZEN_TORII", "GB_ZEN_SANDO", "GB_ZEN_KAIRO", "GB_ZEN_HAIDEN"]

# Color map matching Figma FIGMA_COMPONENT_SPECS.md §StyleGenomeAxisDiagram
_GENOME_TYPE_COLORS = {
    "gate":      "#C4A882",
    "path":      "#8BAE8A",
    "corridor":  "#7A9BBF",
    "platform":  "#B5846A",
    "courtyard": "#C2A87E",
}


def _load_yaml(path: Path) -> dict:
    """Load YAML using stdlib or fall back to manual minimal parser for simple cases."""
    try:
        import yaml  # type: ignore
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        pass
    # Minimal fallback: parse top-level keys and nested dicts (good enough for atoms)
    data: dict = {}
    current_key: str | None = None
    with path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.lstrip().startswith("#"):
                continue
            if not line.startswith(" ") and ":" in stripped:
                current_key = stripped.split(":", 1)[0].strip()
                data[current_key] = {}
            elif current_key and ":" in stripped:
                k, _, v = stripped.strip().partition(":")
                data[current_key][k.strip()] = v.strip().strip('"').strip("'")
    return data


def _count_snaps(atom_data: dict) -> int:
    """Estimate snap count from atom dict."""
    snaps = atom_data.get("snaps") or atom_data.get("snap_count") or atom_data.get("connections") or {}
    if isinstance(snaps, dict):
        return len(snaps)
    if isinstance(snaps, list):
        return len(snaps)
    if isinstance(snaps, int):
        return snaps
    return 0


def _infer_type(atom_id: str, atom_data: dict) -> str:
    """Infer the visual type of an atom from its id or data."""
    atom_type = (atom_data.get("type") or atom_data.get("category") or "").lower()
    if atom_type in _GENOME_TYPE_COLORS:
        return atom_type
    id_lower = atom_id.lower()
    if any(k in id_lower for k in ("torii", "gate", "mon")):
        return "gate"
    if any(k in id_lower for k in ("sando", "path", "walk")):
        return "path"
    if any(k in id_lower for k in ("kairo", "corridor", "cloister")):
        return "corridor"
    if any(k in id_lower for k in ("haiden", "honden", "platform", "stage")):
        return "platform"
    if any(k in id_lower for k in ("karesansui", "garden", "courtyard")):
        return "courtyard"
    return "path"


def build_genome_axis(genome_filter: str | None = None) -> dict:
    """Parse architectural_atoms.yaml and produce ordered axis steps."""
    if not ATOMS_YAML.exists():
        print(f"[GenomeAxis] WARNING: {ATOMS_YAML} not found — using built-in defaults")
        atoms_raw: dict = {}
    else:
        atoms_raw = _load_yaml(ATOMS_YAML)

    # Discover genome-level axis sequence if defined
    axis_key = genome_filter or "ZEN_SHRINE_AXIS"
    axis_sequence: list[str] = []
    if "genomes" in atoms_raw and axis_key in atoms_raw["genomes"]:
        genome_def = atoms_raw["genomes"][axis_key]
        axis_sequence = genome_def.get("axis") or genome_def.get("rooms") or []
    elif "axes" in atoms_raw and axis_key in atoms_raw["axes"]:
        axis_sequence = atoms_raw["axes"][axis_key]

    if not axis_sequence:
        # Fall back to filtering atoms whose id contains the genome prefix
        prefix = genome_filter.replace("_AXIS", "").replace("_SHRINE", "") if genome_filter else "ZEN"
        axis_sequence = [
            k for k in atoms_raw.keys()
            if k.startswith(f"GB_{prefix}") and not k.startswith("GB_ZEN_GARDEN")
        ]
    if not axis_sequence:
        axis_sequence = _DEFAULT_AXIS

    steps: list[dict] = []
    for atom_id in axis_sequence:
        atom_data = atoms_raw.get(atom_id, {})
        atom_type = _infer_type(atom_id, atom_data)
        label = (
            atom_data.get("label")
            or atom_data.get("display_name")
            or atom_id.replace("GB_ZEN_", "").replace("_", " ").title()
        )
        steps.append({
            "id": atom_id,
            "label": label,
            "type": atom_type,
            "color": _GENOME_TYPE_COLORS.get(atom_type, "#888888"),
            "snap_count": _count_snaps(atom_data),
            "description": atom_data.get("description") or "",
        })

    return {
        "genome": axis_key,
        "axis_steps": steps,
        "step_count": len(steps),
    }


def write_genome_axis(genome_filter: str | None = None) -> Path:
    """Build and write genome_axis.json; return the path."""
    result = build_genome_axis(genome_filter)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "export_genome_axis.py",
        "ok": True,
        "project_root": str(PROJECT_ROOT),
        "genome": result,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[GenomeAxis] wrote {OUT_PATH} ({result['step_count']} steps)")
    return OUT_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description="Export genome axis steps for Figma visualization.")
    parser.add_argument("--genome", default=None, help="Genome axis key (default: ZEN_SHRINE_AXIS)")
    args = parser.parse_args()
    write_genome_axis(genome_filter=args.genome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
