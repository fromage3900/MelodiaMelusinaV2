"""Style Genome — load, validate, apply to SurrealArchProperties."""

from __future__ import annotations

import os

from ._io import load_data, package_path
from . import atoms

_GENOME_CACHE: dict[str, dict] = {}


def _validate_genome(data: dict) -> list[str]:
    errors = []
    required = (
        "id", "verticality", "symmetry", "ornament_density",
        "structural_logic", "organic_growth", "cosmic_influence",
    )
    for key in required:
        if key not in data:
            errors.append(f"missing {key}")
        elif key != "id":
            val = data[key]
            if not isinstance(val, (int, float)) or val < 0 or val > 1:
                errors.append(f"{key} must be 0..1")
    return errors


def genome_family(genome: dict) -> str:
    """Resolve catalog family — explicit `family` field or id-prefix fallback."""
    fam = genome.get("family")
    if fam:
        return str(fam)
    gid = str(genome.get("id", ""))
    if gid.startswith("zen_"):
        return "Zen"
    if gid.startswith("gothic_"):
        return "Gothic"
    if gid.startswith("scifi_"):
        return "Sci-Fi"
    if gid.startswith("romanesque_"):
        return "Romanesque"
    if gid.startswith("venetian_"):
        return "Venetian"
    if gid.startswith("asian_"):
        return "Asian"
    if gid.startswith("brutalist_"):
        return "Brutalist"
    if gid.startswith("western_"):
        return "Western"
    if gid.startswith("art_deco_"):
        return "ArtDeco"
    if gid.startswith("art_nouveau_"):
        return "ArtNouveau"
    if gid.startswith("moorish_"):
        return "Moorish"
    if gid.startswith("renaissance_"):
        return "Renaissance"
    return "Other"


def list_genomes() -> list[str]:
    root = package_path("genomes")
    ids = []
    for name in os.listdir(root):
        if name.endswith((".json", ".yaml")):
            ids.append(os.path.splitext(name)[0])
    return sorted(set(ids))


def load_genome(genome_id: str) -> dict:
    if genome_id in _GENOME_CACHE:
        return _GENOME_CACHE[genome_id]
    data = load_data("genomes", f"{genome_id}.json")
    if not isinstance(data, dict):
        raise ValueError(f"genome {genome_id} invalid")
    errs = _validate_genome(data)
    if errs:
        raise ValueError(f"genome {genome_id}: {', '.join(errs)}")
    _GENOME_CACHE[genome_id] = data
    return data


def get_genome(genome_id: str) -> dict:
    return load_genome(genome_id)


def apply_genome(props, genome_id: str, monolith=None) -> dict:
    """Apply genome floats + prop_defaults to a SurrealArchProperties instance."""
    genome = load_genome(genome_id)
    for key in (
        "verticality", "symmetry", "ornament_density",
        "structural_logic", "organic_growth", "cosmic_influence",
    ):
        if hasattr(props, f"genome_{key}"):
            setattr(props, f"genome_{key}", float(genome[key]))
    defaults = genome.get("prop_defaults") or {}
    for key, val in defaults.items():
        if hasattr(props, key):
            try:
                setattr(props, key, val)
            except (TypeError, ValueError):
                pass
    if hasattr(props, "style_genome_id"):
        props.style_genome_id = genome_id
    seq = genome.get("sacred_sequence") or []
    if seq and hasattr(props, "arch_type"):
        first = atoms.resolve_atom(seq[0])
        if first and first.get("kit"):
            try:
                props.arch_type = first["kit"]
            except TypeError:
                pass
    recess = 0.03 + float(genome.get("ornament_density", 0.5)) * 0.05
    if hasattr(props, "gb_trim_recess"):
        props.gb_trim_recess = recess
    if monolith is not None:
        monolith._active_style_genome = genome
    return genome


def build_genome_manifest(genome: dict) -> dict:
    """Serializable Style Genome block for .world.json sidecars."""
    if not genome:
        return {}
    return {
        "id": genome.get("id"),
        "family": genome_family(genome),
        "verticality": genome.get("verticality"),
        "symmetry": genome.get("symmetry"),
        "ornament_density": genome.get("ornament_density"),
        "structural_logic": genome.get("structural_logic"),
        "organic_growth": genome.get("organic_growth"),
        "cosmic_influence": genome.get("cosmic_influence"),
        "compose_style": genome.get("compose_style"),
        "default_graph": genome.get("default_graph"),
        "grammar_id": genome.get("grammar_id"),
        "surreal_transform": genome.get("surreal_transform"),
        "torii_variant": genome.get("torii_variant"),
        "sakura_graph": genome.get("sakura_graph"),
        "sacred_sequence": list(genome.get("sacred_sequence") or []),
        "compose_roles": dict(genome.get("compose_roles") or {}),
        "resolved_compose_roles": dict(genome.get("resolved_compose_roles") or {}),
        "prop_defaults": dict(genome.get("prop_defaults") or {}),
    }


def resolve_genome_manifest(monolith, style_key: str, genome_id: str | None = None) -> dict:
    """Resolve genome DNA for world export from active genome or style defaults."""
    active = getattr(monolith, "_active_style_genome", None) if monolith is not None else None
    if active and (not genome_id or active.get("id") == genome_id):
        active_style = active.get("compose_style")
        if not style_key or not active_style or active_style == style_key:
            return build_genome_manifest(active)
    gid = genome_id
    if not gid and style_key == "ZEN_SHRINE":
        gid = "zen_shrine_v1"
    if not gid and style_key == "ASIAN_CITY":
        gid = "asian_city_v1"
    if not gid and style_key == "ASIAN_CITY_RECURSIVE":
        gid = "asian_city_recursive_v1"
    if not gid and style_key == "WESTERN_CASTLE":
        gid = "western_castle_v1"
    if not gid and style_key == "ART_DECO":
        gid = "art_deco_lobby_v1"
    if not gid and style_key == "ART_NOUVEAU":
        gid = "art_nouveau_v1"
    if not gid and style_key == "MOORISH_COURTYARD":
        gid = "moorish_courtyard_v1"
    if not gid and style_key == "RENAISSANCE_PIAZZA":
        gid = "renaissance_piazza_v1"
    if not gid and style_key == "VENETIAN_CANAL":
        gid = "venetian_canal_v1"
    if not gid and style_key == "GOTHIC_CLOISTER":
        gid = "gothic_cloister_v1"
    if not gid and style_key == "GOTHIC_CHAPTER_HOUSE":
        gid = "gothic_chapter_house_v1"
    if not gid and style_key == "GOTHIC_NAVE_CROSSING":
        gid = "gothic_nave_crossing_v1"
    if not gid and style_key == "ROMANESQUE_CLOISTER":
        gid = "romanesque_cloister_v1"
    if not gid and style_key == "ROMANESQUE_APSE":
        gid = "romanesque_apse_v1"
    if not gid and style_key == "SCIFI_DECK":
        gid = "scifi_deck_v1"
    if not gid and style_key == "BYZANTINE_BASILICA":
        gid = "byzantine_basilica_v1"
    if not gid and style_key == "BAROQUE_CHURCH":
        gid = "baroque_church_v1"
    if gid:
        try:
            return build_genome_manifest(load_genome(gid))
        except Exception:
            pass
    return {}
