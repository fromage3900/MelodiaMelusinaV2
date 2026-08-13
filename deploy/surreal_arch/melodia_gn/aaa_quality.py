"""AAA quality standards document + audit snapshot for the Melodia GN library.

Read-only data module: no register_builder calls, no node graph. Consumed by
agents and dashboards to track the P0-P3 quality roadmap against the live
registry (set_dressing, pcg_integration, water, ribbon, instruments).
"""

from __future__ import annotations

import re

PARAM_NAMING_CONVENTIONS = {
    "R": "radius",
    "radii": "radius",
    "bore_r": "bore_radius",
    "freq": "base_freq",
    "frequency": "base_freq",
    "omega": "base_omega",
    "amp": "amplitude",
    "magnitude": "amplitude",
    "n": "count",
    "num": "count",
    "res": "resolution",
    "dir": "direction",
    "pos": "position",
    "loc": "position",
    "col": "color",
    "sz": "size",
    "len": "length",
}

QUALITY_GATES = {
    "mesh_quality": "Non-manifold edges, shade-smooth + normal recalculation.",
    "parameter_variety": "6-15 meaningful parameters with art-direction intent.",
    "preset_system": "2-3 curated presets per builder + JSON export.",
    "output_quality": "Export-ready topology, clean normals.",
    "pipeline_integration": "Themed attribute sockets (water_*, mn_*) + PCG tag outputs.",
    "documentation": "STUDIO_LABELS entry + Input/Curves/Attributes/Output frames.",
    "cross_builder_consistency": "Standardized parameter naming across all builders.",
    "regression_gate": "GN tree fingerprint + regression-test compatibility.",
}


def aaq_quality_checklist(builder_name: str) -> dict:
    """Return the gate checklist for one builder, all gates OPEN by default."""
    return {
        "builder": builder_name,
        "gates": {gate: {"passed": False, "note": note} for gate, note in QUALITY_GATES.items()},
    }


_MEL_SNAKE_RE = re.compile(r"^MEL_[a-z][a-z0-9_]*$")


def naming_convention_audit(registered: list[str]) -> dict:
    """Audit builder ids: MEL_ prefix then snake_case rest (letters, digits, underscores).

    Short ids such as MEL_arch / MEL_column / MEL_gazebo are valid. Do not
    require a category segment or a second underscore. Do not rename builders
    to satisfy an older MEL_<cat>_<name> rule.
    """
    bad = []
    for bid in registered:
        if not bid.startswith("MEL_"):
            bad.append((bid, "missing MEL_ prefix"))
        elif not _MEL_SNAKE_RE.fullmatch(bid):
            bad.append((bid, "rest after MEL_ is not snake_case"))
    return {
        "total": len(registered),
        "conforming": len(registered) - len(bad),
        "non_conforming": bad,
        "convention_map": PARAM_NAMING_CONVENTIONS,
    }


def aaq_roadmap() -> dict:
    """P0-P3 AAA quality roadmap with estimated durations."""
    return {
        "phase": [
            {
                "name": "P0 - Quick Wins",
                "duration": "2 weeks",
                "goals": [
                    "Standardize parameter naming across all builders (PARAM_NAMING_CONVENTIONS).",
                    "STUDIO_LABELS frame descriptions on every builder.",
                    "2-3 preset JSON configs for the most-used builders.",
                    "Run naming_convention_audit and publish the migration list.",
                ],
            },
            {
                "name": "P1 - Quality Infrastructure",
                "duration": "2 weeks",
                "goals": [
                    "Mesh topology cleanup guide for boolean-heavy builders.",
                    "Themed attribute sockets on water/instrument/ribbon builders.",
                    "Preset export pipeline for all builders.",
                    "Mesh quality validation script template.",
                ],
            },
            {
                "name": "P2 - Automation",
                "duration": "2 weeks",
                "goals": [
                    "Fingerprint-based regression across the GN library.",
                    "Automated quality gate in the registration pipeline.",
                    "Builder quality score dashboard.",
                    "Full parameter documentation for every builder.",
                ],
            },
            {
                "name": "P3 - Polish",
                "duration": "8 weeks",
                "goals": [
                    "Final quality gate pass across the whole library.",
                    "Release AAA-quality builder pack v1.0.",
                    "Update agent documentation and onboarding guides.",
                ],
            },
        ],
        "total_estimated_weeks": 14,
        "critical_path": [
            "Parameter naming standardization",
            "STUDIO_LABELS audit",
            "Preset system implementation",
            "Mesh quality cleanup guides",
            "Themed attribute sockets",
        ],
    }


BUILDER_PRIORITY = {
    "high": [
        "MEL_effect_magic", "MEL_music_harmonic", "MEL_escher_waterfall",
        "MEL_nikki_quarter", "MEL_sky_observatory", "MEL_recursive_castle_spire",
    ],
    "medium": [
        "MEL_music_treble_clef", "MEL_music_note_head", "MEL_filigree_spiral",
        "MEL_effect_wave", "MEL_escher_belvedere", "MEL_escher_penrose_stairs",
        "MEL_castle_assembler", "MEL_harmonic_orb", "MEL_water_them_gazebo",
        "MEL_music_them_gazebo",
    ],
    "low": [
        "MEL_water_gerstner", "MEL_water_ripples", "MEL_water_foam",
        "MEL_water_current_markers", "MEL_brass_pipe", "MEL_reed_body",
        "MEL_bell_chime", "MEL_ribbon_curve", "MEL_violin_bow",
        "MEL_lissajous_ribbon", "MEL_closed_ribbon", "MEL_water_them_structure",
        "MEL_music_them_structure", "MEL_material_crosswalk",
        "MEL_water_them_fountain", "MEL_water_them_bridge",
        "MEL_music_them_bandstand", "MEL_pcg_water_tags_v2", "MEL_music_staff",
        "MEL_column",
    ],
}

AUDIT_REPORT = {
    "document_title": "Melodia GN AAA Quality Standards",
    "mode": "read-only snapshot (no code mutation)",
    "quality_gates": QUALITY_GATES,
    "roadmap": aaq_roadmap(),
    "priority": BUILDER_PRIORITY,
}