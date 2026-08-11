from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _project_root() -> Path:
    # Content/Python/envui/paths.py -> Content/Python/envui -> Content/Python -> Content -> ProjectRoot
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class EnvUIPaths:
    project_root: Path
    saved_dir: Path
    portfolio_dir: Path
    material_previews_dir: Path
    previews_manifest: Path
    audit_dir: Path
    material_audit_json: Path


def get_paths() -> EnvUIPaths:
    root = _project_root()
    saved = root / "Saved"
    portfolio = saved / "Portfolio"
    material_previews = portfolio / "MaterialPreviews"
    audit_dir = saved / "Audit"
    return EnvUIPaths(
        project_root=root,
        saved_dir=saved,
        portfolio_dir=portfolio,
        material_previews_dir=material_previews,
        previews_manifest=material_previews / "previews_manifest.json",
        audit_dir=audit_dir,
        material_audit_json=audit_dir / "material_instance_audit.json",
    )

