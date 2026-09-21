"""brooch_genome.py -- reusable genome for the Melusina flower-brooch architecture.

Adapts the deploy/surreal_os genome pattern (style genome: 6 core genes 0..1 +
sequence + prop block) to a fabricated jewellery asset:

    load_genome(id)             -> validated genome dict
    list_genomes()              -> sorted ids present in this folder
    genome_family(id)           -> family string ("Brooch")
    resolve_genome(genome)      -> {"id","genes","traits", ...} builder-ready
    derive_traits(genes)        -> gene-only phenotype draft (new genome seeding)
    build_genome_manifest(id)   -> one-screen JSON summary

The genome is the SINGLE authority for brooch design values. Builders
(Tools/gen_flower_brooch_v5.py, future Sverchok rebuilds) consume
resolve_genome() output and must not hardcode design constants of their own.

Core genes (0..1), same names as the surreal_os style genome:
    verticality        crown domes upward            -> tilt, rise
    symmetry           radial perfection             -> chaos = (1-symmetry)*0.5
    ornament_density   bead / pave abundance         -> pave sites, center bead, inner falloff
    structural_logic   hardware mass + plate truth   -> plate, stem, filigree z-cap
    organic_growth     botanical vigour              -> petal count, spread, petal dims
    cosmic_influence   sparkle register              -> accent size/lift, pave bead radius

CLI:
    python brooch_genome.py list
    python brooch_genome.py resolve <id>
    python brooch_genome.py derive <id>
    python brooch_genome.py manifest <id>
"""
from __future__ import annotations

import copy
import json
import os
import sys

GENOME_DIR = os.path.dirname(os.path.abspath(__file__))

GENE_KEYS = (
    "verticality",
    "symmetry",
    "ornament_density",
    "structural_logic",
    "organic_growth",
    "cosmic_influence",
)

# traits that derive_traits() can regenerate from genes (documented formulas
# below were fitted so that the v1 genome genes regenerate its authored traits)
DERIVABLE = (
    "crown.petal_count", "crown.spread", "crown.petal_len", "crown.petal_wid",
    "crown.petal_thk", "crown.inner_size", "crown.tilt_deg", "crown.rise",
    "crown.chaos",
    "accents.size", "accents.lift",
    "pave.site_count", "pave.bead_radius", "pave.jitter",
    "center_bead.radius",
    "filigree.taper_deg", "filigree.z_cap",
    "hardware.plate_radius", "hardware.stem_depth",
)


# ---------------------------------------------------------------- loading ----
def _genome_path(gid: str) -> str:
    return os.path.join(GENOME_DIR, "%s.json" % gid)


def list_genomes() -> list[str]:
    out = []
    for fn in sorted(os.listdir(GENOME_DIR)):
        if fn.endswith(".json") and not fn.startswith("_"):
            out.append(fn[:-5])
    return out


def validate_genome(g: dict) -> list[str]:
    """Return a list of problems; empty list = valid."""
    problems = []
    if not isinstance(g, dict):
        return ["genome is not a dict"]
    if not isinstance(g.get("id"), str) or not g.get("id"):
        problems.append("id missing/not a string")
    for k in GENE_KEYS:
        v = g.get(k)
        if not isinstance(v, (int, float)):
            problems.append("gene %r missing/not numeric" % k)
        elif not (0.0 <= float(v) <= 1.0):
            problems.append("gene %r out of 0..1: %r" % (k, v))
    if not isinstance(g.get("traits"), dict):
        problems.append("traits block missing/not a dict")
    if not isinstance(g.get("module_sequence"), list):
        problems.append("module_sequence missing/not a list")
    return problems


def load_genome(genome) -> dict:
    """Load + validate by id (str) or accept a dict; raises ValueError."""
    if isinstance(genome, str):
        path = _genome_path(genome)
        if not os.path.exists(path):
            raise ValueError("no genome file: %s" % path)
        with open(path, "r", encoding="utf-8") as fh:
            g = json.load(fh)
    elif isinstance(genome, dict):
        g = copy.deepcopy(genome)
    else:
        raise ValueError("genome must be an id string or dict")
    problems = validate_genome(g)
    if problems:
        raise ValueError("invalid genome: %s" % "; ".join(problems))
    return g


def genome_family(genome) -> str:
    return load_genome(genome).get("family", "Brooch")


# ---------------------------------------------------------------- deriving ---
def derive_traits(genes: dict) -> dict:
    """Gene-only phenotype draft. Use to seed a NEW genome; authored traits win.

    Formula fit: with the melodia_brooch_v1 gene set (v .55, s .56, o .72,
    sl .62, og .62, c .18) every formula lands on / next to the tuned v4 values.
    """
    v = float(genes["verticality"])
    s = float(genes["symmetry"])
    o = float(genes["ornament_density"])
    sl = float(genes["structural_logic"])
    og = float(genes["organic_growth"])
    c = float(genes["cosmic_influence"])

    def r4(x):
        return round(float(x), 4)

    return {
        "phyllotaxis": {
            # biological constant -- never derived, never overridden by genes
            "angle_deg": 137.5077,
            "radius_law": "sqrt",
            "spread": r4(0.10 + og * 0.195),           # og .62 -> 0.2209
        },
        "crown": {
            "petal_count": int(round(5 + og * 13)),    # og .62 -> 13
            "petal_len": r4(0.16 + og * 0.22),         # og .62 -> 0.2964
            "petal_wid": r4(0.05 + og * 0.065),        # og .62 -> 0.0903
            "petal_thk": r4(0.012 + og * 0.021),       # og .62 -> 0.0250
            "inner_size": r4(0.81 - o * 0.50),         # o .72  -> 0.4500
            "tilt_deg": r4(14.0 + v * 22.0),           # v .55  -> 26.1
            "cup": 1.0,
            "rise": r4(0.02 + v * 0.055),              # v .55  -> 0.05025
            "chaos": r4((1.0 - s) * 0.5),              # s .56  -> 0.2200
        },
        "accents": {
            "size": r4(0.008 + c * 0.030),             # c .18  -> 0.0134
            "lift": r4(0.012 + c * 0.070),             # c .18  -> 0.0246
        },
        "pave": {
            "site_count": int(round(24 + o * 78)),     # o .72  -> 80
            "border_inner": r4(0.16 + sl * 0.15),      # sl .62 -> 0.253
            "border_outer": r4(0.16 + sl * 0.15 + 0.008 + o * 0.045),  # -> 0.293
            "bead_radius": r4(0.006 + c * 0.06),       # c .18  -> 0.0168
            "voronoi_domain_radius": 0.22,
            "jitter": 0.0,                             # 2026-09-17: jewelry row = machine-regular;
        },                                             # opt in per genome (0..1 dial)
        "center_bead": {
            "radius": r4(0.040 + o * 0.035),           # o .72  -> 0.0652
            "z_squash": 0.55,
        },
        "filigree": {
            "petal_count": int(round(5 + og * 13)),
            "petal_len": 0.05,
            "petal_wid": 0.022,
            "taper_deg": r4(20.0 + v * 50.0),          # v .55  -> 47.5
            "z_cap": r4(0.005 + sl * 0.011),           # sl .62 -> 0.0118
        },
        "hardware": {
            "plate_radius": r4(0.22 + sl * 0.16),      # sl .62 -> 0.3192
            "plate_depth": 0.025,
            "plate_z": -0.052,
            "stem_radius": 0.010,
            "stem_depth": r4(0.24 + sl * 0.16),        # sl .62 -> 0.3392
            "stem_at": [0.0, 0.07, -0.076],
            "hinge_radius": 0.016,
            "hinge_depth": 0.035,
            "hinge_at": [-0.175, 0.07, -0.076],
            "clasp_size": [0.03, 0.02, 0.03],
            "clasp_at": [0.175, 0.07, -0.076],
            "merge_distance": 0.001,
        },
        "materials": {
            "petal": "MID_Petal",
            "bead": "MID_Bead",
            "pin": "MID_Pin",
        },
        "fabrication": {
            "dxf_scale": 100,
            "layer": "Sverchok_Pol_0",
            "units": "mm",
        },
    }


# ---------------------------------------------------------------- resolving --
def _deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def resolve_genome(genome, overrides: dict | None = None) -> dict:
    """Builder-ready parameter set: authored traits + optional overrides."""
    g = load_genome(genome)
    genes = {k: float(g[k]) for k in GENE_KEYS}
    traits = _deep_merge(g["traits"], overrides or {})
    return {
        "id": g["id"],
        "family": g.get("family", "Brooch"),
        "genes": genes,
        "traits": traits,
        "module_sequence": list(g.get("module_sequence", [])),
        "compose_style": g.get("compose_style", ""),
        "default_graph": g.get("default_graph", ""),
    }


def build_genome_manifest(genome) -> str:
    r = resolve_genome(genome)
    return json.dumps(r, indent=2, sort_keys=False)


# ---------------------------------------------------------------- CLI --------
def _print_table(r: dict) -> None:
    print("genome: %s   family: %s" % (r["id"], r["family"]))
    print("genes:")
    for k, v in r["genes"].items():
        print("    %-18s %.3f" % (k, v))
    print("modules: %s" % ", ".join(r["module_sequence"]))
    print("traits:")
    for block, vals in r["traits"].items():
        if isinstance(vals, dict):
            flat = "  ".join("%s=%s" % (k, v) for k, v in vals.items())
            print("    %-14s %s" % (block, flat))
        else:
            print("    %-14s %s" % (block, vals))


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "list"
    if cmd == "list":
        ids = list_genomes()
        print("genomes in %s:" % GENOME_DIR)
        for gid in ids:
            g = load_genome(gid)
            print("    %-28s family=%-8s style=%s" % (
                gid, g.get("family", "?"), g.get("compose_style", "")))
        print("total: %d" % len(ids))
        return 0
    if cmd == "resolve" and len(argv) > 2:
        _print_table(resolve_genome(argv[2]))
        return 0
    if cmd == "derive" and len(argv) > 2:
        g = load_genome(argv[2])
        genes = {k: float(g[k]) for k in GENE_KEYS}
        d = derive_traits(genes)
        r = resolve_genome(g)
        print("--- derived draft (from genes only) ---")
        _print_table({"id": g["id"] + " [derived]", "family": g.get("family", "?"),
                      "genes": genes, "module_sequence": r["module_sequence"],
                      "traits": d})
        print()
        print("--- authored traits (canonical) ---")
        _print_table(r)
        return 0
    if cmd == "manifest" and len(argv) > 2:
        print(build_genome_manifest(argv[2]))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
