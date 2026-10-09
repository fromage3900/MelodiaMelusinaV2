#!/usr/bin/env python3
"""Melodia World Compiler -- deterministic offline compiler for seed-driven worlds.

Contract: Docs/WorldGen/WORLD_COMPILER_CONTRACT.md
Recipe schema: specs/schemas/world_recipe.v1.schema.json
Bundle schema: specs/schemas/world_compiler_bundle.v1.schema.json

    python Tools/world_compiler.py compile recipes/morning_rainbow_bloom.v1.json
    python Tools/world_compiler.py validate recipes/morning_rainbow_bloom.v1.json
    python Tools/world_compiler.py show Saved/WorldCompiler/morning_rainbow_bloom_3900

The compiler is a thin orchestrator over existing modules:

    identity  -> Content/Python/resonant_world_generator.py      (reused)
    terrain   -> Tools/terrain_handoff.py                        (reused, optional)
    ecology   -> this file (radial Chladni band field + clearance masks)   NEW
    dressing  -> recipe species table (+ resonant_world_asset_constellation when --constellation)
    signal    -> byte-level lane check against the two MPC assets (read-only)
    chapter   -> Tools/scaffold_chapter.py                       (reused, optional)
    bundle    -> this file + Tools/evidence_envelope.py           NEW

Hard rules (see contract section 8): never ``import unreal``; never edit PCG
graph structure; never write to an MPC; same recipe + same compiler version
=> byte-identical tables and manifest SHA.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import io
import json
import math
import sys
from pathlib import Path
from typing import Any

COMPILER_VERSION = "world_compiler_v1.0"
ROOT = Path(__file__).resolve().parents[1]
CONTENT_PY = ROOT / "Content" / "Python"
for _p in (str(ROOT / "Tools"), str(CONTENT_PY)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resonant_world_generator as rwg  # noqa: E402  (reused identity module)
import harmonic_terrain as ht  # noqa: E402  (optional harmony stage)

try:
    from pcg.resonance_ecology_processor import derive as _resonance_derive  # noqa: E402
except Exception:  # pragma: no cover - fallback keeps the compiler runnable
    _resonance_derive = None

POINT_COLUMNS = [
    "point_id", "x", "y", "z", "yaw", "scale", "species_id", "variant_id", "band", "mode_n", "mode_m",
    "cluster_id", "hue_seed", "wind_phase", "wind_response", "sparkle_response", "hero_weight",
    "height_class", "density_class", "Resonance", "EcologyClass", "MaterialVariant", "ScaleBias",
    # NOTE: UE FNames are case-insensitive, so no column may differ from another only by case
    # ("Scale" vs "scale" collided in the DataTable -> the vector column read back the float).
    "mesh", "material", "StemMaterial", "Position", "Rotation", "Scale3D",
    # v2 horizon fields (additive; v1 consumers ignore these)
    "horizon_distance", "sky_exposure", "silhouette_weight", "atmospheric_depth",
]
FX_COLUMNS = [
    "anchor_id", "fx_kind", "band", "x", "y", "z", "hue_seed", "spawn_multiplier", "bounds_cm",
    "system", "material_instance",
]
GOLDEN_ANGLE = 2.399963229728653
PARASTICHY = 13
FLOAT_FMT = "{:.3f}"


# ----------------------------------------------------------------------------- helpers

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _f(value: float) -> str:
    text = FLOAT_FMT.format(float(value))
    return "0.000" if text == "-0.000" else text


def _u(seed: int, *parts: object) -> float:
    """Deterministic 0..1 for a recipe coordinate (NMS-style sub-seeding)."""
    return rwg.stable_float(seed, "world_compiler", *parts)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def _soft_path(game_path: str) -> str:
    """'/Game/A/B' -> '/Game/A/B.B' (UE soft object path form)."""
    if not game_path or "." in game_path.rsplit("/", 1)[-1]:
        return game_path
    return f"{game_path}.{game_path.rsplit('/', 1)[-1]}"


def _stage(status: str, module: str = "", note: str = "", errors: list[str] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"status": status}
    if module:
        out["module"] = module
    if note:
        out["note"] = note
    if errors:
        out["errors"] = errors
    return out


# ----------------------------------------------------------------------------- recipe

def load_recipe(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    recipe = json.loads(raw.decode("utf-8"))
    return recipe, raw


def validate_recipe(recipe: dict[str, Any]) -> list[str]:
    """Schema validation via jsonschema when available, plus semantic checks."""
    errors: list[str] = []
    schema_path = ROOT / "specs" / "schemas" / "world_recipe.v1.schema.json"
    try:
        import jsonschema  # type: ignore

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for err in sorted(validator.iter_errors(recipe), key=lambda e: list(e.path)):
            loc = "/".join(str(p) for p in err.path) or "<root>"
            errors.append(f"schema: {loc}: {err.message}")
    except ImportError:
        for key in ("schema", "recipe_id", "world_seed", "identity", "place", "field", "species", "palette", "signal"):
            if key not in recipe:
                errors.append(f"missing required key: {key}")
        if recipe.get("schema") != "melodia.world_recipe.v1":
            errors.append("schema must be melodia.world_recipe.v1")
    if errors:
        return errors

    field = recipe["field"]
    bands = recipe["palette"]["bands"]
    if len(bands) != field["band_count"]:
        errors.append(f"palette.bands has {len(bands)} entries but field.band_count is {field['band_count']}")
    modes = (field.get("chladni") or {}).get("modes")
    if modes is not None and len(modes) != field["band_count"]:
        errors.append(f"field.chladni.modes has {len(modes)} entries but field.band_count is {field['band_count']}")
    for band_index, band in enumerate(bands):
        if not band["label"].startswith(f"B{band_index}_"):
            errors.append(f"palette.bands[{band_index}].label must start with B{band_index}_")
    mode_id = recipe["identity"].get("mode_id")
    if mode_id and mode_id not in rwg.MODE_LIBRARY:
        errors.append(f"identity.mode_id {mode_id} not in MODE_LIBRARY")
    movement_id = recipe["identity"].get("movement_id")
    if movement_id and movement_id not in rwg.WORLD_MOVEMENT_LIBRARY:
        errors.append(f"identity.movement_id {movement_id} not in WORLD_MOVEMENT_LIBRARY")
    for text in json.dumps(recipe).split('"'):
        if len(text) > 2 and text[1] == ":" and text[2] in "\\/":
            errors.append(f"workstation path in recipe: {text}")
    weights = sum(s["weight"] for s in recipe["species"])
    if weights <= 0:
        errors.append("species weights must sum to > 0")
    known_species = {s["species_id"] for s in recipe["species"]}
    for arc in (field.get("trail_arcs") or []):
        if arc.get("species_id") not in known_species:
            errors.append(f"field.trail_arcs species {arc.get('species_id')!r} is not a recipe species")
    if recipe.get("harmony") is not None:
        errors.extend(ht.validate(recipe["harmony"]))
    beauty = recipe.get("beauty")
    if beauty is not None:
        for key in ("sender_name", "render_target", "sender_bp"):
            if not beauty.get(key):
                errors.append(f"beauty.{key} is required when recipe.beauty is present")
        name = beauty.get("sender_name") or ""
        if name and (not name[0].isalpha() or not name.replace("_", "").isalnum()):
            errors.append(f"beauty.sender_name {name!r} must match ^[A-Za-z][A-Za-z0-9_]*$")
        for key in ("render_target", "sender_bp"):
            path = beauty.get(key) or ""
            if path and not path.startswith("/Game/"):
                errors.append(f"beauty.{key} {path!r} must be a /Game/ path")
        for key in ("width", "height"):
            dim = beauty.get(key)
            if dim is not None and (not isinstance(dim, int) or isinstance(dim, bool) or dim < 1):
                errors.append(f"beauty.{key} must be a positive integer")
    return errors


# ----------------------------------------------------------------------------- identity

def stage_identity(recipe: dict[str, Any]) -> dict[str, Any]:
    ident = recipe.get("identity", {})
    config = rwg.WorldConfig.from_seed(
        recipe["world_seed"],
        root_pitch_class=ident.get("root_pitch_class"),
        mode_id=ident.get("mode_id"),
        bpm=ident.get("bpm"),
    )
    if ident.get("movement_id"):
        config = dataclasses.replace(config, movement_id=ident["movement_id"])
    cx, cy = ident.get("chunk", [0, 0])
    chunk = rwg.chunk_manifest(config, int(cx), int(cy), include_voxels=False)
    return {
        "generator_version": rwg.GENERATOR_VERSION,
        "world": config.to_dict(),
        "chunk": chunk,
        "world_partition_chunk_size_cm": rwg.WORLD_PARTITION_CHUNK_SIZE_CM,
    }


# ----------------------------------------------------------------------------- ecology

@dataclasses.dataclass
class Clearance:
    circles: list[dict[str, Any]]
    capsules: list[dict[str, Any]]

    @classmethod
    def from_recipe(cls, recipe: dict[str, Any]) -> "Clearance":
        c = (recipe.get("place") or {}).get("clearance") or {}
        return cls(list(c.get("circles") or []), list(c.get("capsules") or []))

    def blocked(self, x: float, y: float) -> str | None:
        for circle in self.circles:
            cx, cy = circle["center_cm"]
            if math.hypot(x - cx, y - cy) < circle["radius_cm"]:
                return circle["label"]
        for cap in self.capsules:
            if _segment_distance(x, y, cap["a_cm"], cap["b_cm"]) < cap["radius_cm"]:
                return cap["label"]
        return None

    def hero_weight(self, x: float, y: float, falloff_cm: float) -> float:
        best = 0.0
        for circle in self.circles:
            cx, cy = circle["center_cm"]
            d = math.hypot(x - cx, y - cy) - circle["radius_cm"]
            if falloff_cm <= 0:
                continue
            best = max(best, _clamp01(1.0 - d / falloff_cm))
        return best


def _segment_distance(px: float, py: float, a: list[float], b: list[float]) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(px - ax, py - ay)
    t = _clamp01(((px - ax) * dx + (py - ay) * dy) / length_sq)
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def chladni(u: float, v: float, n: int, m: int) -> float:
    """Square-plate Chladni figure on unit coordinates u,v in [0,1]; nodal lines at 0."""
    return math.cos(n * math.pi * u) * math.cos(m * math.pi * v) - math.cos(m * math.pi * u) * math.cos(n * math.pi * v)


def _pick_species(recipe: dict[str, Any], r: float) -> dict[str, Any]:
    species = recipe["species"]
    total = sum(s["weight"] for s in species)
    acc = 0.0
    for s in species:
        acc += s["weight"] / total
        if r <= acc:
            return s
    return species[-1]


def _glitter_brightness(recipe: dict[str, Any]) -> tuple[list[float], str]:
    """(brightness_steps, glitter mi_prefix) for the palette.glitter lane.

    Absent/empty -> ([1.0], prefix-or-""): every MI keeps its canonical
    `{mi_prefix}{label}` name and every point references it, so pre-shade
    recipes compile byte-identical.
    """
    glitter = recipe["palette"].get("glitter") or {}
    steps = list(glitter.get("brightness_steps") or [1.0])
    return steps, str(glitter.get("mi_prefix") or "")


def _glitter_mi_name(mi_prefix: str, label: str, brightness: float) -> str:
    """Canonical name for brightness == 1.0 (existing MIs keep working);
    `_L<pct>` suffix otherwise (BRT70 reads darker, BRT140 hotter)."""
    if brightness == 1.0:
        return f"{mi_prefix}{label}"
    return f"{mi_prefix}{label}_L{int(round(brightness * 100.0))}"


def _wind_suffixes(recipe: dict[str, Any], wind: dict[str, Any]) -> list[str]:
    """Ordered unique mesh_mi_suffixes across species on the wind prefix.

    Lets every band MI variant the points reference (e.g. tall cards with
    their own atlas) carry the lane's tint/response/overrides. No suffixed
    species -> [""] -> legacy seven MIs, byte-identical.
    """
    prefix = wind.get("mi_prefix") or ""
    seen: list[str] = []
    for s in recipe["species"]:
        if prefix and s.get("band_mi_prefix") != prefix:
            continue
        for sfx in (s.get("mesh_mi_suffixes") or []):
            if sfx not in seen:
                seen.append(sfx)
    return seen or [""]


def stage_ecology(recipe: dict[str, Any], identity: dict[str, Any]) -> dict[str, Any]:
    seed = int(recipe["world_seed"])
    rid = recipe["recipe_id"]
    field = recipe["field"]
    place = recipe["place"]
    ax, ay, az = place["anchor_cm"]
    z = az + float(place.get("up_axis_offset_cm", 4.0))
    clearance = Clearance.from_recipe(recipe)
    band_count = int(field["band_count"])
    r0 = float(field["inner_radius_cm"])
    width = float(field["band_width_cm"])
    density = float(field["density_per_m2"])
    golden = float(field.get("phyllotaxis_angle_rad", GOLDEN_ANGLE))
    jitter = float(field.get("radial_jitter_cm", 18.0))
    s_lo, s_hi = field.get("scale_range", [0.5, 1.1])
    # Per-species scale_range overrides the field default (a species without one
    # keeps the legacy global behavior). Pre-glitter recipes pin the field value
    # on every species, so outputs stay byte-identical; see the recipe.
    chl = field.get("chladni") or {}
    modes = chl.get("modes") or [[2 + b, 3 + b] for b in range(band_count)]
    threshold = float(chl.get("threshold", 0.35))
    outer_radius = r0 + width * band_count
    plate = float(chl.get("plate_size_cm", outer_radius * 2.0 + 200.0))
    hero_falloff = float(field.get("hero_falloff_cm", 600.0))
    bands_palette = recipe["palette"]["bands"]
    chunk_seed = int(identity["chunk"]["stable_seed"])
    ground = load_ground_mask(recipe)
    up = float(place.get("up_axis_offset_cm", 4.0))
    # optional angular sector [center_deg, half_width_deg]: concentrate the phyllotaxis where ground exists
    sector = field.get("sector_deg")
    sector_frac = 1.0 if not sector else _clamp01(float(sector[1]) / 180.0)

    points: list[dict[str, Any]] = []
    band_rows: list[dict[str, Any]] = []
    removed_clearance = 0
    removed_chladni = 0
    removed_ground = 0
    point_id = 0

    for b in range(band_count):
        r_in = r0 + b * width
        r_out = r_in + width
        area_m2 = math.pi * (r_out * r_out - r_in * r_in) / 10_000.0 * sector_frac
        n_target = max(1, int(round(area_m2 * density)))
        phase = _u(seed, rid, "band_phase", b) * 2.0 * math.pi
        n, m = int(modes[b][0]), int(modes[b][1])
        kept = 0
        for i in range(n_target):
            t = (i + 0.5) / n_target
            r = math.sqrt(r_in * r_in + t * (r_out * r_out - r_in * r_in))
            r += _lerp(-jitter, jitter, _u(seed, rid, "jitter", b, i))
            theta = phase + i * golden
            if sector:
                # fold the golden-angle sweep into the sector so the spiral stays low-discrepancy
                span = 2.0 * math.radians(float(sector[1]))
                theta = math.radians(float(sector[0])) - span / 2.0 + (theta % (2.0 * math.pi)) / (2.0 * math.pi) * span
            x = ax + r * math.cos(theta)
            y = ay + r * math.sin(theta)
            if ground is not None:
                gz = ground.ground_z(x, y)
                if gz is None:
                    removed_ground += 1
                    continue
                z = gz + up
            u = _clamp01((x - ax) / plate + 0.5)
            v = _clamp01((y - ay) / plate + 0.5)
            fig = abs(chladni(u, v, n, m))
            weight = 1.0 - _clamp01(fig)
            keep_p = max(threshold, weight * weight)
            if _u(seed, rid, "chladni_keep", b, i) > keep_p:
                removed_chladni += 1
                continue
            if clearance.blocked(x, y):
                removed_clearance += 1
                continue
            species = _pick_species(recipe, _u(seed, rid, "species", b, i))
            # palette.active_lane picks which band-MI family the 'material' column names.
            # A species-level band_mi_prefix wins (glitter/detail families); otherwise the
            # wind lane prefix applies when active, else the (legacy) species prefix.
            # For all pre-glitter recipes the flower prefix equals the wind prefix and
            # dressing species carry no prefix, so outputs are byte-identical.
            wind_lane = recipe["palette"].get("wind") or {}
            material_prefix = (species.get("band_mi_prefix")
                               or (wind_lane.get("mi_prefix") if recipe["palette"].get("active_lane") == "wind" and wind_lane
                                   else ""))
            meshes = list(species.get("meshes") or [species["mesh"]])
            variants = int(species.get("variants", len(meshes) if species.get("meshes") else 3))
            variant_id = rwg.stable_int(seed, "world_compiler", rid, "variant", b, i) % variants
            # species.mesh_mi_suffixes (parallel to meshes) picks each mesh's own band MI, e.g. "_Tall"
            # so a card mesh gets the band MI that carries its texture atlas.
            mesh_mi_suffixes = list(species.get("mesh_mi_suffixes") or [])
            bri_steps, glitter_prefix = _glitter_brightness(recipe)
            bri = 1.0
            if material_prefix and glitter_prefix and material_prefix == glitter_prefix and len(bri_steps) > 1:
                bri = float(bri_steps[rwg.stable_int(seed, "world_compiler", rid, "shade", b, i) % len(bri_steps)])
                band_mi = _glitter_mi_name(material_prefix, bands_palette[b]['label'], bri)
            else:
                band_mi = (f"{material_prefix}{bands_palette[b]['label']}"
                           f"{mesh_mi_suffixes[variant_id % len(meshes)] if mesh_mi_suffixes else ''}")
            if _resonance_derive is not None:
                resonance, ecology_class, material_variant, scale_bias = _resonance_derive(
                    x, y, r, chunk_seed, z_lo=r0, z_hi=outer_radius
                )
            else:  # pragma: no cover
                resonance = _u(seed, rid, "res", b, i)
                ecology_class = 0 if resonance < 0.33 else (1 if resonance < 0.66 else 2)
                material_variant = int(resonance * 3) % 3
                scale_bias = 0.75 + 0.6 * resonance
            height_class = int(species.get("height_class", 1))
            density_class = 2 if weight > 0.66 else (1 if weight > 0.33 else 0)
            hero_w = clearance.hero_weight(x, y, hero_falloff)
            # v2 horizon fields (additive; computed from radial distance + height_class)
            horizon_dist = r  # radial distance from anchor = proxy for horizon distance
            sky_exp = _clamp01(0.3 + 0.5 * height_class + 0.2 * (1.0 - density_class / 2.0))
            silhouette_w = _clamp01(0.2 + 0.6 * height_class + 0.2 * weight)
            atmo_depth = _clamp01(horizon_dist / (outer_radius * 2.0))
            sp_lo, sp_hi = species.get("scale_range", [s_lo, s_hi])
            scale = _lerp(float(sp_lo), float(sp_hi), _u(seed, rid, "scale", b, i)) * (0.85 + 0.15 * hero_w)
            # Flat-lay (fairy dust): species opt into lying at light-catching
            # angles. Absent keys -> pitch 0.000, the legacy Rotation string.
            pitch_base = float(species.get("pitch_deg", 0.0))
            pitch_jit = float(species.get("pitch_jitter_deg", 0.0))
            pitch = pitch_base + _lerp(-pitch_jit, pitch_jit, _u(seed, rid, "pitch", b, i)) if pitch_jit else pitch_base
            yaw_deg = _u(seed, rid, "yaw", b, i) * 360.0
            points.append({
                "point_id": point_id,
                "x": x, "y": y, "z": z,
                "yaw": yaw_deg,
                "scale": scale,
                "species_id": species["species_id"],
                "variant_id": variant_id,
                "band": b,
                "mode_n": n, "mode_m": m,
                "cluster_id": i % PARASTICHY,
                "hue_seed": _clamp01((b + 0.5) / band_count + _lerp(-0.04, 0.04, _u(seed, rid, "hue", b, i))),
                "wind_phase": _u(seed, rid, "wind_phase", b, i),
                "wind_response": _lerp(0.55, 1.0, _u(seed, rid, "wind_resp", b, i)) * (1.0 if height_class else 0.7),
                "sparkle_response": _clamp01(0.2 + 0.6 * resonance),
                "hero_weight": hero_w,
                "height_class": height_class,
                "density_class": density_class,
                "Resonance": resonance,
                "EcologyClass": ecology_class,
                "MaterialVariant": b,  # band index selects the band MI in the spawner
                "ScaleBias": scale_bias,
                # Soft object paths so PCGMeshSelectorByAttribute + material-override-by-attribute
                # make the owner's template graph fully data-driven (no per-species graph edits).
                "mesh": _soft_path(meshes[variant_id % len(meshes)]),
                "material": _soft_path(band_mi) if material_prefix else "",
                "StemMaterial": (
                    _soft_path(band_mi)
                    if species.get("stem_material") == "__band__" and material_prefix
                    else (_soft_path(species["stem_material"]) if species.get("stem_material") else "")
                ),
                # UE struct-typed mirrors so PCG's Load Data Table maps them to $Position/$Rotation/$Scale directly.
                "Position": f"(X={_f(x)},Y={_f(y)},Z={_f(z)})",
                "Rotation": f"(Pitch={_f(pitch)},Yaw={_f(yaw_deg)},Roll=0.000)",
                "Scale3D": f"(X={_f(scale)},Y={_f(scale)},Z={_f(scale)})",
                # v2 horizon fields
                "horizon_distance": _f(horizon_dist),
                "sky_exposure": _f(sky_exp),
                "silhouette_weight": _f(silhouette_w),
                "atmospheric_depth": _f(atmo_depth),
            })
            point_id += 1
            kept += 1
        band_rows.append({
            "band": b,
            "label": bands_palette[b]["label"],
            "tint": bands_palette[b]["tint"],
            "inner_radius_cm": r_in,
            "outer_radius_cm": r_out,
            "mode_n": n, "mode_m": m,
            "target_count": n_target,
            "point_count": kept,
        })

    # Trail arcs (fairy-dust spill trails): deliberate arcs, not phyllotaxis.
    # cluster_id >= 900 marks trail rows (normal range is [0, PARASTICHY)).
    # Absent `field.trail_arcs` -> zero rows, byte-identical output.
    for a, arc in enumerate(recipe["field"].get("trail_arcs") or []):
        tracer = next(s for s in recipe["species"] if s["species_id"] == arc["species_id"])
        tmeshes = list(tracer.get("meshes") or [tracer["mesh"]])
        tvariants = int(tracer.get("variants", len(tmeshes) if tracer.get("meshes") else 3))
        tprefix = tracer.get("band_mi_prefix") or ""
        t_lo, t_hi = tracer.get("scale_range", [s_lo, s_hi])
        tpitch = float(tracer.get("pitch_deg", 0.0))
        tpitch_jit = float(tracer.get("pitch_jitter_deg", 0.0))
        tcount = int(arc["count"])
        twidth = float(arc.get("width_cm", 40.0))
        trad = float(arc["radius_cm"])
        tcenter = math.radians(float(arc["angle_center_deg"]))
        tspan = math.radians(float(arc["span_deg"]))
        for k in range(tcount):
            t = (k + 0.5) / tcount
            ang = tcenter + (t - 0.5) * tspan + _lerp(-0.06, 0.06, _u(seed, rid, "tangle", a, k))
            rr = trad + _lerp(-twidth, twidth, _u(seed, rid, "trad", a, k))
            x = ax + rr * math.cos(ang)
            y = ay + rr * math.sin(ang)
            if ground is not None:
                gz = ground.ground_z(x, y)
                if gz is None:
                    removed_ground += 1
                    continue
                z = gz + up
            if clearance.blocked(x, y):
                removed_clearance += 1
                continue
            tb = min(band_count - 1, max(0, int((rr - r0) // width)))
            tn, tm = int(modes[tb][0]), int(modes[tb][1])
            tvariant = rwg.stable_int(seed, "world_compiler", rid, "tvariant", a, k) % tvariants
            tsuffixes = list(tracer.get("mesh_mi_suffixes") or [])
            bri_steps, glitter_prefix = _glitter_brightness(recipe)
            if tprefix and glitter_prefix and tprefix == glitter_prefix and len(bri_steps) > 1:
                tbri = float(bri_steps[rwg.stable_int(seed, "world_compiler", rid, "tshade", a, k) % len(bri_steps)])
                tband_mi = _glitter_mi_name(tprefix, bands_palette[tb]['label'], tbri)
            else:
                tband_mi = f"{tprefix}{bands_palette[tb]['label']}{tsuffixes[tvariant % len(tsuffixes)] if tsuffixes else ''}"
            tyaw = _u(seed, rid, "tyaw", a, k) * 360.0
            tpitch_k = tpitch + _lerp(-tpitch_jit, tpitch_jit, _u(seed, rid, "tpitch", a, k)) if tpitch_jit else tpitch
            tscale = _lerp(float(t_lo), float(t_hi), _u(seed, rid, "tscale", a, k))
            thero = clearance.hero_weight(x, y, hero_falloff)
            tscale *= 0.85 + 0.15 * thero
            if _resonance_derive is not None:
                tres, teclass, _, tscale_bias = _resonance_derive(x, y, rr, chunk_seed, z_lo=r0, z_hi=outer_radius)
            else:  # pragma: no cover
                tres = _u(seed, rid, "tres", a, k)
                teclass = 0 if tres < 0.33 else (1 if tres < 0.66 else 2)
                tscale_bias = 0.75 + 0.6 * tres
            theight = int(tracer.get("height_class", 1))
            points.append({
                "point_id": point_id,
                "x": x, "y": y, "z": z,
                "yaw": tyaw,
                "scale": tscale,
                "species_id": tracer["species_id"],
                "variant_id": tvariant,
                "band": tb,
                "mode_n": tn, "mode_m": tm,
                "cluster_id": 900 + a,
                "hue_seed": _clamp01((tb + 0.5) / band_count + _lerp(-0.04, 0.04, _u(seed, rid, "thue", a, k))),
                "wind_phase": _u(seed, rid, "twind_phase", a, k),
                "wind_response": _lerp(0.55, 1.0, _u(seed, rid, "twind_resp", a, k)) * (1.0 if theight else 0.7),
                "sparkle_response": _clamp01(0.2 + 0.6 * tres),
                "hero_weight": thero,
                "height_class": theight,
                "density_class": 2,
                "Resonance": tres,
                "EcologyClass": teclass,
                "MaterialVariant": tb,
                "ScaleBias": tscale_bias,
                "mesh": _soft_path(tmeshes[tvariant % len(tmeshes)]),
                "material": _soft_path(tband_mi) if tprefix else "",
                "StemMaterial": (
                    _soft_path(tband_mi)
                    if tracer.get("stem_material") == "__band__" and tprefix
                    else (_soft_path(tracer["stem_material"]) if tracer.get("stem_material") else "")
                ),
                "Position": f"(X={_f(x)},Y={_f(y)},Z={_f(z)})",
                "Rotation": f"(Pitch={_f(tpitch_k)},Yaw={_f(tyaw)},Roll=0.000)",
                "Scale3D": f"(X={_f(tscale)},Y={_f(tscale)},Z={_f(tscale)})",
                # v2 horizon fields (trail arcs)
                "horizon_distance": _f(rr),
                "sky_exposure": _f(_clamp01(0.3 + 0.5 * theight + 0.2 * (1.0 - 2.0 / 2.0))),
                "silhouette_weight": _f(_clamp01(0.2 + 0.6 * theight + 0.2 * thero)),
                "atmospheric_depth": _f(_clamp01(rr / (outer_radius * 2.0))),
            })
            point_id += 1
            band_rows[tb]["point_count"] += 1

    anchors, fx_removed = _fx_anchors(recipe, band_rows, clearance, az + up, ground=ground, sector=sector)
    return {
        "points": points,
        "bands": band_rows,
        "fx_anchors": anchors,
        "outer_radius_cm": outer_radius,
        "plate_size_cm": plate,
        "removed_by_clearance": removed_clearance,
        "removed_by_chladni": removed_chladni,
        "removed_by_ground": removed_ground,
        "ground_mask": None if ground is None else {"plantable_cells": len(ground.cells), "plantable_area_m2": round(ground.area_m2(), 1)},
        "sector_deg": sector,
        "fx_removed_by_clearance": fx_removed,
    }


def _load_fx_pack(recipe: dict[str, Any]) -> dict[str, Any] | None:
    fx = recipe.get("fx") or {}
    pack = fx.get("pack")
    if not pack:
        return None
    path = ROOT / pack
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _fx_anchors(recipe: dict[str, Any], bands: list[dict[str, Any]], clearance: Clearance, z: float, *,
                ground: "GroundMask | None" = None, sector: list[float] | None = None) -> tuple[list[dict[str, Any]], int]:
    fx = recipe.get("fx") or {}
    if not fx:
        return [], 0

    def in_sector(angle: float) -> float:
        if not sector:
            return angle
        span = 2.0 * math.radians(float(sector[1]))
        return math.radians(float(sector[0])) - span / 2.0 + (angle % (2.0 * math.pi)) / (2.0 * math.pi) * span
    seed = int(recipe["world_seed"])
    rid = recipe["recipe_id"]
    ax, ay, _ = recipe["place"]["anchor_cm"]
    pack = _load_fx_pack(recipe) or {"systems": []}
    systems = {s["id"]: s for s in pack.get("systems", [])}
    bounds = float(fx.get("bounds_cm", 400))
    wind = fx.get("wind_dir", [1.0, 0.0])
    wl = math.hypot(*wind) or 1.0
    wind = [wind[0] / wl, wind[1] / wl]
    removed = 0
    anchors: list[dict[str, Any]] = []

    def place(kind: str, band: int, radius: float, angle: float, hue: float, mult: float) -> None:
        nonlocal removed
        sysrec = systems.get(kind, {})
        for attempt in range(16):
            a = in_sector(angle + attempt * math.radians(37.0))
            x = ax + radius * math.cos(a)
            y = ay + radius * math.sin(a)
            if clearance.blocked(x, y):
                continue
            zz = z
            if ground is not None:
                gz = ground.ground_z(x, y)
                if gz is None and kind != "mist":  # mist may hover over the water edge
                    continue
                zz = (gz if gz is not None else z - 4.0) + 4.0
            mi = sysrec.get("material_instance") or (f"{sysrec.get('material_instance_prefix', '')}{band}" if band >= 0 else "")
            anchors.append({
                "anchor_id": f"fx_{kind}_{band if band >= 0 else 'x'}_{len([q for q in anchors if q['fx_kind'] == kind])}",
                "fx_kind": kind,
                "band": band,
                "x": x, "y": y, "z": zz + (60.0 if kind in ("petal", "pollen") else 10.0),
                "hue_seed": hue,
                "spawn_multiplier": mult,
                "bounds_cm": float(sysrec.get("fixed_bounds_cm", bounds)),
                "system": sysrec.get("target", ""),
                "material_instance": mi,
            })
            return
        removed += 1

    per_band = fx.get("anchors_per_band") or {}
    for row in bands:
        b = row["band"]
        mid_r = (row["inner_radius_cm"] + row["outer_radius_cm"]) * 0.5
        base_angle = _u(seed, rid, "fx_angle", b) * 2.0 * math.pi
        hue = (b + 0.5) / max(1, len(bands))
        for kind, count in per_band.items():
            for k in range(int(count)):
                place(kind, b, mid_r, base_angle + k * math.pi, hue, 1.0)
    inner = bands[0]["inner_radius_cm"] if bands else 260.0
    for k in range(int(fx.get("mist_anchors", 0))):
        place("mist", -1, inner + 40.0, _u(seed, rid, "mist_angle", k) * 2.0 * math.pi, 0.0, 1.0)
    outer = bands[-1]["outer_radius_cm"] if bands else 1500.0
    for k in range(int(fx.get("windfront_anchors", 0))):
        upwind = math.atan2(-wind[1], -wind[0])
        place("windfront", -1, max(inner + 80.0, outer - 400.0), upwind + k * math.radians(25.0), 0.0, 1.0)
    return anchors, removed


# ----------------------------------------------------------------------------- dressing / signal / terrain / chapter

def stage_dressing(recipe: dict[str, Any], ecology: dict[str, Any], *, constellation: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    palette = recipe["palette"]
    species_rows = []
    for s in recipe["species"]:
        prefix = s.get("band_mi_prefix")
        species_rows.append({
            "species_id": s["species_id"],
            "mesh": s["mesh"],
            "meshes": list(s.get("meshes") or [s["mesh"]]),
            "weight": s["weight"],
            "variants": int(s.get("variants", len(s["meshes"]) if s.get("meshes") else 3)),
            "height_class": int(s.get("height_class", 1)),
            "band_material_instances": [f"{prefix}{band['label']}" for band in palette["bands"]] if prefix else [],
        })
    wind = palette.get("wind") or {}
    band_count = len(palette["bands"])
    table = {
        "schema": "melodia.world_compiler_dressing.v1",
        "parent_master": palette.get("parent_master"),
        "tint_parameter": palette.get("tint_parameter", "BaseTint"),
        "active_lane": palette.get("active_lane", "static"),
        "bands": [{"band": b["band"], "label": b["label"], "tint": b["tint"],
                   "material_instance": f"{recipe['species'][0].get('band_mi_prefix', '')}{b['label']}"} for b in ecology["bands"]],
        # Wind hue-reveal family: same seven tints, parented to a master that already binds
        # MF_MelodiaWindHueReveal and reads the palette Wind* lanes. Undriven == natural albedo.
        # Mesh-variant suffixes (e.g. "_Tall" cards carrying their own atlas) expand the
        # lane so every band MI the points reference gets tint/response/overrides.
        # Species without suffixes -> [""] -> legacy seven, byte-identical.
        "wind_lane": ({
            "parent": wind["parent"],
            "tint_parameter": wind.get("tint_parameter", "MelodiaWindRevealTint"),
            "hue_seed_parameter": wind.get("hue_seed_parameter", "MelodiaWindHueSeed"),
            "response_parameter": wind.get("response_parameter", "MelodiaWindResponse"),
            "response": float(wind.get("response", 1.0)),
            "scalar_overrides": dict(wind.get("scalar_overrides") or {}),
            "static_switches_off": list(wind.get("static_switches_off") or []),
            "texture_overrides": dict(wind.get("texture_overrides") or {}),
            "bands": [{"band": b["band"], "label": b["label"], "tint": b["tint"],
                       "hue_seed": (b["band"] + 0.5) / band_count,
                       "material_instance": f"{wind['mi_prefix']}{b['label']}{sfx}"}
                      for b in ecology["bands"] for sfx in _wind_suffixes(recipe, wind)],
        } if wind else None),
        # Glitter detail family: same seven tints on the glitter master, expanded by
        # brightness_steps (default [1.0] -> one MI per band, legacy names).
        # brightness == 1.0 keeps the canonical `{mi_prefix}{label}` MI; other
        # steps get `_L<pct>` suffixes with pre-scaled tints (the UE forge
        # writes lane tints verbatim, so scaling happens here, once).
        # Parent scalars/switches stay untouched.
        "glitter_lane": ({
            "parent": glitter["parent"],
            "tint_parameters": list(glitter.get("tint_parameters") or ["FastLayerColor", "MidLayerColor", "DeepLayerColor"]),
            "shade_steps": list(glitter.get("shade_steps") or [1.0]),
            "scalar_overrides": dict(glitter.get("scalar_overrides") or {}),
            "brightness_steps": list(glitter.get("brightness_steps") or [1.0]),
            "bands": [{"band": b["band"], "label": b["label"],
                       "tint": [min(4.0, c * step) for c in b["tint"]],
                       "brightness": step,
                       "material_instance": _glitter_mi_name(glitter['mi_prefix'], b['label'], step)}
                      for b in ecology["bands"] for step in (glitter.get("brightness_steps") or [1.0])],
        } if (glitter := palette.get("glitter")) else None),
        "species": species_rows,
        "packer_attributes": ["hue_seed", "Resonance", "wind_response", "sparkle_response"],
        "source": "recipe",
    }
    note = "species/band table from recipe"
    status = "PASS"
    if constellation:
        try:
            import resonant_world_asset_constellation as rwac  # noqa: E402

            ident = recipe.get("identity", {})
            cx, cy = ident.get("chunk", [0, 0])
            table["constellation"] = rwac.build_asset_constellation(
                ROOT, int(recipe["world_seed"]), movement_id=ident.get("movement_id"), chunk_x=int(cx), chunk_y=int(cy)
            )
            table["source"] = "recipe+constellation"
            note = "species/band table from recipe; asset constellation attached (machine-dependent inventory)"
        except Exception as exc:  # pragma: no cover
            note = f"constellation unavailable: {exc}"
            status = "EXPECTED_FAIL"
    return table, _stage(status, "recipe species table" + (" + resonant_world_asset_constellation" if constellation else ""), note)


def _uasset_for(game_path: str) -> Path:
    rel = game_path.replace("/Game/", "Content/", 1)
    return ROOT / (rel + ".uasset")


def stage_signal(recipe: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    sig = recipe["signal"]
    checks = []
    errors = []
    for role, key in (("driver", "driver_mpc"), ("source", "source_mpc")):
        path = _uasset_for(sig[key])
        exists = path.exists()
        data = path.read_bytes() if exists else b""
        lfs_pointer = data.startswith(b"version https://git-lfs.github.com/spec/v1")
        lanes = sig["lanes"] if role == "driver" else [lane.replace("Cymatic_", "") for lane in sig["lanes"] if lane.startswith("Cymatic_Wind")]
        for lane in lanes:
            present = (lane.encode("ascii") in data) if exists and not lfs_pointer else None
            status = "PASS" if present else ("SKIPPED" if present is None else "FAIL")
            if status == "FAIL":
                errors.append(f"{role} MPC lacks lane {lane}")
            checks.append({"mpc": sig[key], "role": role, "lane": lane, "status": status,
                           "note": "" if present is not None else ("asset missing" if not exists else "LFS pointer; hydrate to check")})
    mf = sig.get("material_function")
    mf_exists = _uasset_for(mf).exists() if mf else None
    bindings = {
        "schema": "melodia.world_compiler_signal_bindings.v1",
        "writer": "UMelodiaCymaticsWriterSubsystem (only driver writer); palette writer is UMelodiaAudioReactivePresentationSubsystem",
        "source_mpc": sig["source_mpc"],
        "driver_mpc": sig["driver_mpc"],
        "material_function": mf,
        "material_function_present": mf_exists,
        "lane_checks": checks,
        "consumers": {
            "band_material_instances": {"reads": sig["lanes"], "via": "parent master collection-parameter nodes; MF_MelodiaWindHueReveal consumes WindDir/WindStrength inputs"},
            "instance_custom_data": {"hue_seed": "MF_MelodiaWindHueReveal.PerInstanceHueSeed", "wind_response": "MF_MelodiaWindHueReveal.ResponseAmount", "Resonance": "Cymatic emissive scale weight"},
            "niagara": "specs/niagara/morning_hero_fx_pack.v1.json materials[].mpc_lanes",
        },
        "rule": "compiler never writes a collection parameter",
    }
    status = "FAIL" if errors else ("PASS" if all(c["status"] == "PASS" for c in checks) else "SKIPPED")
    return bindings, _stage(status, "byte-level lane check", f"{sum(c['status']=='PASS' for c in checks)}/{len(checks)} lanes present", errors or None)


@dataclasses.dataclass
class GroundMask:
    """Nearest-cell lookup over a line-trace grid written by world_compiler_ue.py probe_ground."""
    step: float
    cells: dict[tuple[int, int], float]  # (ix, iy) -> ground z for plantable cells only
    origin: tuple[float, float]
    total_cells: int

    @classmethod
    def from_probe(cls, doc: dict[str, Any], z_lo: float, z_hi: float, exclude_classes: set[str]) -> "GroundMask":
        step = float(doc["step_cm"])
        cx, cy = doc["center_cm"]
        radius = float(doc["radius_cm"])
        ox, oy = cx - radius, cy - radius
        cells: dict[tuple[int, int], float] = {}
        for x, y, z, _label, acls in doc["rows"]:
            lab = str(_label or "")
            # Bedroom kit floors and the rejected grass shelf are never plantable,
            # even if they fall inside walkable_z.
            if lab.startswith("WC_DellFloor") or lab.startswith("WC_EscherWalk") or "classic_arch" in lab.lower():
                continue
            if "Sphere3D" in lab or lab.startswith("SM_PM3D"):
                continue
            if lab and not lab.startswith("BrushifyIsland_"):
                continue
            if z is None or not (z_lo <= z <= z_hi) or (acls in exclude_classes):
                continue
            cells[(int(round((x - ox) / step)), int(round((y - oy) / step)))] = float(z)
        return cls(step, cells, (ox, oy), len(doc["rows"]))

    def ground_z(self, x: float, y: float) -> float | None:
        ix = int(round((x - self.origin[0]) / self.step))
        iy = int(round((y - self.origin[1]) / self.step))
        return self.cells.get((ix, iy))

    def area_m2(self) -> float:
        return len(self.cells) * (self.step * self.step) / 10_000.0


def load_ground_mask(recipe: dict[str, Any]) -> GroundMask | None:
    terrain = recipe.get("terrain") or {}
    if terrain.get("kind") != "ground_probe":
        return None
    path = ROOT / terrain["probe"]
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    z_lo, z_hi = terrain.get("walkable_z_cm") or [-1e9, 1e9]
    return GroundMask.from_probe(doc, float(z_lo), float(z_hi), set(terrain.get("exclude_actor_classes") or []))


def stage_terrain(recipe: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    terrain = recipe.get("terrain")
    if terrain and terrain.get("kind") == "ground_probe":
        try:
            mask = load_ground_mask(recipe)
            doc = json.loads((ROOT / terrain["probe"]).read_text(encoding="utf-8-sig"))
            info = {"kind": "ground_probe", "probe": terrain["probe"], "level": doc.get("level"), "recorded_at_utc": doc.get("recorded_at_utc"),
                    "cells": mask.total_cells, "plantable_cells": len(mask.cells), "plantable_area_m2": round(mask.area_m2(), 1),
                    "walkable_z_cm": terrain.get("walkable_z_cm"), "exclude_actor_classes": terrain.get("exclude_actor_classes") or [],
                    "probe_radius_cm": terrain.get("probe_radius_cm"), "probe_step_cm": terrain.get("probe_step_cm"),
                    "hit_classes": doc.get("classes")}
            status = "PASS" if mask.cells else "FAIL"
            return info, _stage(status, "Content/Python/world_compiler_ue.py:probe_ground", f"{len(mask.cells)} plantable cells / {mask.total_cells}",
                                None if mask.cells else ["ground probe has no plantable cells"])
        except Exception as exc:
            return {"kind": "ground_probe", "probe": terrain.get("probe"), "error": str(exc)}, _stage("FAIL", "ground_probe", "", [str(exc)])
    if not terrain or not terrain.get("handoff"):
        return None, _stage("SKIPPED", "Tools/terrain_handoff.py", "recipe.terrain is null")
    try:
        import terrain_handoff as th  # noqa: E402

        doc, _ = th._load_doc(str(ROOT / terrain["handoff"]))
        unified = th.convert_document(doc)
        problems = th.validate_handoff(unified)
        status = "PASS" if not problems else "FAIL"
        return {"handoff": terrain["handoff"], "unified": unified, "problems": problems}, _stage(status, "Tools/terrain_handoff.py", "", problems or None)
    except Exception as exc:
        return {"handoff": terrain["handoff"], "error": str(exc)}, _stage("FAIL", "Tools/terrain_handoff.py", "", [str(exc)])


def stage_chapter(recipe: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    chapter = recipe.get("chapter")
    if not chapter or not chapter.get("chapter"):
        return None, _stage("SKIPPED", "Tools/scaffold_chapter.py", "recipe.chapter is null")
    if not chapter.get("create"):
        return {"chapter": chapter["chapter"], "created": False}, _stage("PASS", "Tools/scaffold_chapter.py", "reference only; create=false")
    try:
        import scaffold_chapter as sc  # noqa: E402

        target = sc.scaffold(chapter["chapter"])
        return {"chapter": chapter["chapter"], "created": True, "path": str(target.relative_to(ROOT)).replace("\\", "/")}, _stage("PASS", "Tools/scaffold_chapter.py")
    except FileExistsError as exc:
        return {"chapter": chapter["chapter"], "created": False, "note": str(exc)}, _stage("PASS", "Tools/scaffold_chapter.py", "already exists")
    except Exception as exc:
        return {"chapter": chapter["chapter"], "error": str(exc)}, _stage("FAIL", "Tools/scaffold_chapter.py", "", [str(exc)])


# ----------------------------------------------------------------------------- beauty feed

# Canon live-lookdev contract (CURRENT_STATE.md): one Spout2 sender name for the
# whole project. The compiler enforces the name and emits the feed contract; the
# UE lane (Content/Python/world_compiler_ue.py `beauty` step) proves the assets live.
BEAUTY_CANON = {
    "sender_name": "UE_Beauty",
    "render_target": "/Game/Melodia/Lookdev/RT_UE_Beauty",
    "sender_bp": "/Game/Melodia/Lookdev/BP_UE_BeautySender",
    "width": 1920,
    "height": 1080,
    "capture_source": "SCS_FinalColorLDR",
    "startup_policy": "Editor_Game",
    "plugin": {
        "name": "Spout2_DX12",
        "version": "2.1.1",
        "source": "https://github.com/GPUbrainStorm/UE5_Spout2_DX12",
    },
}


def stage_beauty(recipe: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Optional live beauty-feed contract. Absent => no tables (bundles byte-identical)."""
    beauty = recipe.get("beauty")
    if not beauty:
        return None, _stage("SKIPPED", "Tools/world_compiler.py:stage_beauty", "recipe.beauty absent")
    errors: list[str] = []
    cfg = {**{k: v for k, v in BEAUTY_CANON.items() if k != "plugin"}, **beauty}
    if cfg["sender_name"] != BEAUTY_CANON["sender_name"]:
        errors.append(
            f"beauty.sender_name {cfg['sender_name']!r} is not the canon name "
            f"{BEAUTY_CANON['sender_name']!r}: one sender name per project, no second beauty writer"
        )
    assets: dict[str, dict[str, Any]] = {}
    for role, key in (("render_target", "render_target"), ("sender_actor", "sender_bp")):
        uasset = _uasset_for(cfg[key])
        present = uasset.exists()
        assets[role] = {"path": cfg[key], "uasset": str(uasset.relative_to(ROOT)).replace("\\", "/"), "present": present}
        if not present:
            errors.append(f"beauty.{key} missing on disk: {cfg[key]}")
    feed = {
        "schema": "melodia.beauty_feed.v1",
        "sender_name": cfg["sender_name"],
        "render_target": _soft_path(cfg["render_target"]),
        "sender_bp": _soft_path(cfg["sender_bp"]),
        "width": int(cfg["width"]),
        "height": int(cfg["height"]),
        "capture_source": cfg["capture_source"],
        "startup_policy": cfg["startup_policy"],
        "plugin": BEAUTY_CANON["plugin"],
        "assets": assets,
        "live_verify": "Content/Python/world_compiler_ue.py `beauty` step (RT dims + sender wiring + plugin reflected); TD lookdev_comp Spout In proves frames",
    }
    status = "FAIL" if errors else "PASS"
    note = f"sender {cfg['sender_name']} {cfg['width']}x{cfg['height']} via {cfg['sender_bp']}"
    return feed, _stage(status, "Tools/world_compiler.py:stage_beauty", note, errors or None)


# ----------------------------------------------------------------------------- structures

SLOT_COLUMNS = [
    "slot_uid", "slot_id", "ring", "index", "builder_id", "preset", "x", "y", "z", "yaw",
    "footprint_w_cm", "footprint_d_cm", "interior", "roof_type", "mesh", "material",
]
CURVE_COLUMNS = [
    "curve_uid", "curve_id", "kind", "index", "x", "y", "z", "yaw", "scale", "builder_id", "mesh", "material",
]


def _mandala_slots(structures: dict[str, Any]) -> list[dict[str, Any]]:
    """n-fold rings of slots around the layout centre; yaw faces outward/centre/tangent."""
    layout = structures["layout"]
    cx, cy, cz = layout["center_cm"]
    order = int(layout.get("order", 1))
    base = math.radians(float(layout.get("rotation_deg", 0.0)))
    kit = structures.get("kit", {}).get("ue_path", "")
    rows: list[dict[str, Any]] = []
    for ring_index, ring in enumerate(layout["rings"]):
        slot = structures["slots"][ring["slot"]]
        count = int(ring.get("count", order))
        radius = float(ring["radius_cm"])
        phase = math.radians(float(ring.get("phase_deg", 0.0)))
        for i in range(count):
            a = base + phase + 2.0 * math.pi * i / count
            x, y = cx + radius * math.cos(a), cy + radius * math.sin(a)
            facing = slot.get("face", "center")
            yaw_rad = a + (math.pi if facing == "center" else 0.0 if facing == "outward" else math.pi / 2.0)
            fw, fd = slot.get("footprint_cm", [0.0, 0.0])
            rows.append({
                "slot_uid": f"R{ring_index}_{i:02d}", "slot_id": ring["slot"], "ring": ring_index, "index": i,
                "builder_id": slot["builder_id"], "preset": slot.get("preset", ""),
                "x": x, "y": y, "z": float(cz), "yaw": math.degrees(yaw_rad) % 360.0,
                "footprint_w_cm": float(fw), "footprint_d_cm": float(fd),
                "interior": int(bool(slot.get("interior", False))),
                "roof_type": (slot.get("roof") or {}).get("type", ""),
                # Interchange GLB import lays each kit piece out as <kit>/SM_<slot>/StaticMeshes/SM_<slot>
                "mesh": _soft_path(slot.get("mesh") or (f"{kit}/SM_{ring['slot']}/StaticMeshes/SM_{ring['slot']}" if kit else "")),
                "material": _soft_path(slot.get("material_instance", "")),
            })
    return rows


def _catenary(p0: tuple[float, float, float], p1: tuple[float, float, float], sag: float, n: int) -> list[tuple[float, float, float]]:
    """Hanging chain between two equal-height-ish points; a from bisection on a*cosh(L/2a)-a = sag."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    span = math.hypot(x1 - x0, y1 - y0)
    if span < 1e-3 or sag <= 0.0:
        return [(_lerp(x0, x1, t), _lerp(y0, y1, t), _lerp(z0, z1, t)) for t in (i / n for i in range(n + 1))]
    lo, hi = 1e-3, 1e7
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid * math.cosh(span / (2.0 * mid)) - mid > sag:
            lo = mid
        else:
            hi = mid
    a = 0.5 * (lo + hi)
    pts = []
    for i in range(n + 1):
        t = i / n
        s = (t - 0.5) * span
        drop = a * math.cosh(span / (2.0 * a)) - a * math.cosh(s / a)
        pts.append((_lerp(x0, x1, t), _lerp(y0, y1, t), _lerp(z0, z1, t) - drop))
    return pts


def _sample_count(length_cm: float, sample_cm: float) -> int:
    return max(2, int(math.ceil(length_cm / max(sample_cm, 1.0))))


def _curve_rows(structures: dict[str, Any], slots: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    layout = structures["layout"]
    cx, cy, cz = layout["center_cm"]
    rows: list[dict[str, Any]] = []

    def emit(curve_id: str, kind: str, pts: list[tuple[float, float, float]], decor: dict[str, Any]) -> None:
        for i, (x, y, z) in enumerate(pts):
            nx, ny = (pts[i + 1][0], pts[i + 1][1]) if i + 1 < len(pts) else (x + (x - pts[i - 1][0]), y + (y - pts[i - 1][1]))
            rows.append({
                "curve_uid": f"{curve_id}_{i:03d}", "curve_id": curve_id, "kind": kind, "index": i,
                "x": x, "y": y, "z": z, "yaw": math.degrees(math.atan2(ny - y, nx - x)) % 360.0,
                "scale": float(decor.get("scale", 1.0)),
                "builder_id": decor.get("builder_id", ""), "mesh": _soft_path(decor.get("mesh", "")),
                "material": _soft_path(decor.get("material_instance", "")),
            })

    for w_index, walk in enumerate(structures.get("walkways", [])):
        sample = float(walk.get("sample_cm", 100.0))
        kind = walk["kind"]
        cid = walk.get("walkway_id", f"walk{w_index}")
        if kind == "ring":
            r = float(walk["radius_cm"])
            n = _sample_count(2.0 * math.pi * r, sample)
            pts = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), cz) for i in range(n + 1)]
        elif kind == "spoke":
            r0, r1 = float(walk["inner_radius_cm"]), float(walk["radius_cm"])
            pts = []
            for k in range(int(layout.get("order", 1))):
                a = math.radians(float(layout.get("rotation_deg", 0.0)) + float(walk.get("phase_deg", 0.0))) + 2 * math.pi * k / int(layout.get("order", 1))
                n = _sample_count(r1 - r0, sample)
                emit(f"{cid}_{k}", "spoke", [(cx + _lerp(r0, r1, i / n) * math.cos(a), cy + _lerp(r0, r1, i / n) * math.sin(a), cz) for i in range(n + 1)], walk)
            continue
        else:  # spiral: golden log spiral, rising rise_cm over turns
            r0, r1 = float(walk["inner_radius_cm"]), float(walk["radius_cm"])
            turns = float(walk.get("turns", 1.0))
            n = _sample_count(math.pi * (r0 + r1) * turns, sample)
            pts = []
            for i in range(n + 1):
                t = i / n
                a = 2 * math.pi * turns * t
                r = r0 * (r1 / r0) ** t
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a), cz + float(walk.get("rise_cm", 0.0)) * t))
        emit(cid, kind, pts, walk)

    for decor in structures.get("decor", []):
        curve = decor["curve"]
        kind = curve["kind"]
        sample = float(curve.get("sample_cm", 60.0))
        did = decor["decor_id"]
        if kind == "lissajous":
            ra, rb = float(curve.get("a", 3)), float(curve.get("b", 2))
            delta = math.radians(float(curve.get("delta_deg", 90.0)))
            R = float(curve["radius_cm"])
            h, amp = float(curve.get("height_cm", 0.0)), float(curve.get("z_amp_cm", 0.0))
            n = _sample_count(2 * math.pi * R * max(ra, rb), sample)
            pts = [(cx + R * math.sin(ra * t + delta), cy + R * math.sin(rb * t), cz + h + amp * math.sin((ra + rb) * t))
                   for t in (2 * math.pi * i / n for i in range(n + 1))]
            emit(did, kind, pts, decor)
        elif kind == "catenary":
            ring = int(curve.get("ring", 0))
            ring_slots = [s for s in slots if s["ring"] == ring]
            attach = float(curve.get("attach_height_cm", 300.0))
            for k, s0 in enumerate(ring_slots):
                s1 = ring_slots[(k + 1) % len(ring_slots)]
                if len(ring_slots) < 2 or (s1 is s0):
                    break
                p0, p1 = (s0["x"], s0["y"], s0["z"] + attach), (s1["x"], s1["y"], s1["z"] + attach)
                span = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                sag = float(curve.get("sag_cm", 0.0)) or span * float(curve.get("sag_ratio", 0.08))
                emit(f"{did}_{k}", kind, _catenary(p0, p1, sag, _sample_count(span, sample)), decor)
        elif kind == "phyllotaxis":
            count = int(curve["count"])
            r0, r1 = float(curve.get("inner_radius_cm", 0.0)), float(curve["radius_cm"])
            ang = float(curve.get("angle_rad", GOLDEN_ANGLE))
            pts = []
            for i in range(count):
                t = math.sqrt((i + 0.5) / count)
                r = _lerp(r0, r1, t)
                a = i * ang + _u(seed, did, i) * 1e-3
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a), cz))
            emit(did, kind, pts, decor)
    return rows


def stage_structures(recipe: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Mandala slots + walkway/decor curves + Blender GN bake jobs. Optional: absent => no tables."""
    structures = recipe.get("structures")
    if not structures:
        return None, [], [], _stage("SKIPPED", "Tools/world_compiler.py:stage_structures", "recipe.structures absent")
    errors = [f"layout.rings[{i}].slot '{r['slot']}' not in slots" for i, r in enumerate(structures["layout"]["rings"])
              if r["slot"] not in structures["slots"]]
    if errors:
        return None, [], [], _stage("FAIL", "Tools/world_compiler.py:stage_structures", "", errors)
    slots = _mandala_slots(structures)
    curves = _curve_rows(structures, slots, int(recipe["world_seed"]))
    kit = structures.get("kit", {})
    bake = {
        "schema": "melodia.structures_bake.v1",
        "note": "Blender 5.2 + melodia_gn registry; export GLB, Interchange-import, save packages (no automated FBX)",
        "kit_ue_path": kit.get("ue_path", ""),
        "export": kit.get("export", "glb"),
        "slots": {sid: {k: v for k, v in slot.items() if k not in ("face",)} for sid, slot in sorted(structures["slots"].items())},
        "decor": [{"decor_id": d["decor_id"], "builder_id": d.get("builder_id", ""), "curve_kind": d["curve"]["kind"],
                   "curve_ids": sorted({c["curve_id"] for c in curves if c["curve_id"].startswith(d["decor_id"])})}
                  for d in structures.get("decor", [])],
    }
    note = f"{len(slots)} slots, {len({c['curve_id'] for c in curves})} curves ({len(curves)} samples)"
    return bake, slots, curves, _stage("PASS", "Tools/world_compiler.py:stage_structures", note)


def _biome_point(pid: int, b: dict[str, Any], labels: list[str]) -> dict[str, Any]:
    """A harmony biome sample as a points.csv row, so the existing PointField graph + S_WorldCompilerPoint spawn it."""
    spec, k = b["spec"], b["mesh_index"]
    band = min(b["band"], len(labels) - 1)
    if "band_mi_prefix" in spec:
        suffix = (spec.get("mi_suffixes") or [""] * len(spec["meshes"]))[k]
        mat = f"{spec['band_mi_prefix']}{labels[band]}{suffix}"
    else:
        mat = spec["materials"][k]
    x, y, z, s = b["x"], b["y"], b["z"], b["scale"]
    height_class = {"basin": 0, "meadow": 0, "cliff": 1, "crest": 2}[b["biome"]]
    return {
        "point_id": pid, "x": x, "y": y, "z": z, "yaw": b["yaw"], "scale": s,
        "species_id": f"harmony_{b['biome']}", "variant_id": k, "band": band, "mode_n": 0, "mode_m": 0,
        "cluster_id": ht.BIOMES.index(b["biome"]), "hue_seed": _clamp01((band + 0.5) / len(labels) + (b["hue"] - 0.5) * 0.08),
        "wind_phase": b["hue"], "wind_response": 0.85 if height_class == 0 else 0.0,
        "sparkle_response": _clamp01(0.2 + 0.6 * b["resonance"]), "hero_weight": b["resonance"],
        "height_class": height_class, "density_class": 1, "Resonance": b["resonance"],
        "EcologyClass": ht.BIOMES.index(b["biome"]), "MaterialVariant": band, "ScaleBias": 1.0,
        "mesh": _soft_path(spec["meshes"][k]), "material": _soft_path(mat), "StemMaterial": _soft_path(mat),
        "Position": f"(X={_f(x)},Y={_f(y)},Z={_f(z)})",
        "Rotation": f"(Pitch={_f(b['pitch'])},Yaw={_f(b['yaw'])},Roll=0.000)",
        "Scale3D": f"(X={_f(s)},Y={_f(s)},Z={_f(s)})",
        "horizon_distance": _f(0.0), "sky_exposure": _f(_clamp01(1.0 - b["slope"])),
        "silhouette_weight": _f(b["resonance"]), "atmospheric_depth": _f(0.0),
    }


def stage_harmony(recipe: dict[str, Any], identity: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Chords carve valleys, arpeggios raise ridges. Optional: absent => no tables."""
    harmony = recipe.get("harmony")
    if not harmony:
        return None, _stage("SKIPPED", "Tools/harmonic_terrain.py", "recipe.harmony absent")
    mode = rwg.MODE_LIBRARY[identity["world"]["mode_id"]]
    out = ht.compile_harmony(harmony, seed=int(recipe["world_seed"]), anchor=recipe["place"]["anchor_cm"],
                             scale_intervals=list(mode.intervals), rand=_u)
    for row in out["nodes"]:
        row["Position"] = ht.vec(row["Position"], _f)
    for row in out["edges"]:
        row["Start"], row["End"] = ht.vec(row["Start"], _f), ht.vec(row["End"], _f)
    labels = [b["label"] for b in recipe["palette"]["bands"]]
    out["points"] = [_biome_point(pid, row, labels) for pid, row in enumerate(out.pop("biomes"))]
    c = out["meta"]["counts"]
    note = (f"{c['chords']} chords -> {c['valley_features']} valley features, {c['peaks']} peaks / {c['ridges']} ridges, "
            f"z {out['meta']['z_min_cm']:.0f}..{out['meta']['z_max_cm']:.0f} cm")
    return out, _stage("PASS", "Tools/harmonic_terrain.py", note)


# ----------------------------------------------------------------------------- bundle

def _csv_bytes(columns: list[str], rows: list[dict[str, Any]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        out = []
        for col in columns:
            val = row[col]
            out.append(_f(val) if isinstance(val, float) else str(val))
        writer.writerow(out)
    return buf.getvalue().encode("utf-8")


def _json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def compile_recipe(recipe_path: Path, *, out_root: Path | None = None, constellation: bool = False, write_envelope: bool = True) -> dict[str, Any]:
    recipe, raw = load_recipe(recipe_path)
    errors = validate_recipe(recipe)
    if errors:
        raise ValueError("recipe invalid:\n  " + "\n  ".join(errors))
    compile_id = f"{recipe['recipe_id']}_{int(recipe['world_seed'])}"
    out_dir = (out_root or (ROOT / "Saved" / "WorldCompiler")) / compile_id
    out_dir.mkdir(parents=True, exist_ok=True)

    stages: dict[str, dict[str, Any]] = {}
    identity = stage_identity(recipe)
    stages["identity"] = _stage("PASS", "Content/Python/resonant_world_generator.py", f"movement {identity['world']['movement_id']}, mode {identity['world']['mode_id']}")
    terrain, stages["terrain"] = stage_terrain(recipe)
    ecology = stage_ecology(recipe, identity)
    eco_errors = [f"band {b['band']} has zero points" for b in ecology["bands"] if b["point_count"] == 0]
    stages["ecology"] = _stage("FAIL" if eco_errors else "PASS", "Tools/world_compiler.py:stage_ecology",
                               f"{len(ecology['points'])} points, {len(ecology['fx_anchors'])} fx anchors", eco_errors or None)
    dressing, stages["dressing"] = stage_dressing(recipe, ecology, constellation=constellation)
    signal, stages["signal"] = stage_signal(recipe)
    chapter, stages["chapter"] = stage_chapter(recipe)
    bake, slot_rows, curve_rows, structures_stage = stage_structures(recipe)
    if recipe.get("structures"):
        stages["structures"] = structures_stage
    beauty, beauty_stage = stage_beauty(recipe)
    if recipe.get("beauty"):
        stages["beauty"] = beauty_stage
    harmony, harmony_stage = stage_harmony(recipe, identity)
    if recipe.get("harmony"):
        stages["harmony"] = harmony_stage

    files: dict[str, bytes] = {
        "points.csv": _csv_bytes(POINT_COLUMNS, ecology["points"]),
        "fx_anchors.csv": _csv_bytes(FX_COLUMNS, ecology["fx_anchors"]),
        "dressing_table.json": _json_bytes(dressing),
        "signal_bindings.json": _json_bytes(signal),
        "identity.json": _json_bytes(identity),
    }
    if terrain is not None:
        files["terrain.json"] = _json_bytes(terrain)
    if chapter is not None:
        files["chapter.json"] = _json_bytes(chapter)
    if bake is not None:
        files["structure_slots.csv"] = _csv_bytes(SLOT_COLUMNS, slot_rows)
        files["structure_curves.csv"] = _csv_bytes(CURVE_COLUMNS, curve_rows)
        files["structures_bake.json"] = _json_bytes(bake)
    if beauty is not None:
        files["beauty_feed.json"] = _json_bytes(beauty)
    if harmony is not None:
        files["harmony_nodes.csv"] = _csv_bytes(ht.NODE_COLUMNS, harmony["nodes"])
        files["harmony_edges.csv"] = _csv_bytes(ht.EDGE_COLUMNS, harmony["edges"])
        files["harmony_height.r16"] = harmony["r16"]
        files["harmony.json"] = ht.to_json(harmony["meta"])
        if harmony["points"]:
            files["harmony_points.csv"] = _csv_bytes(POINT_COLUMNS, harmony["points"])
    for name, data in files.items():
        (out_dir / name).write_bytes(data)

    table_shape = {
        "points.csv": (len(ecology["points"]), POINT_COLUMNS),
        "fx_anchors.csv": (len(ecology["fx_anchors"]), FX_COLUMNS),
        "structure_slots.csv": (len(slot_rows), SLOT_COLUMNS),
        "structure_curves.csv": (len(curve_rows), CURVE_COLUMNS),
        **({"harmony_nodes.csv": (len(harmony["nodes"]), ht.NODE_COLUMNS),
            "harmony_edges.csv": (len(harmony["edges"]), ht.EDGE_COLUMNS),
            "harmony_points.csv": (len(harmony["points"]), POINT_COLUMNS)} if harmony is not None else {}),
    }
    tables = {
        name: {
            "path": name,
            "sha256": _sha256_bytes(data),
            "rows": table_shape.get(name, (1, None))[0],
            **({"columns": table_shape[name][1]} if name in table_shape else {}),
        }
        for name, data in files.items()
    }
    hard_fail = any(s["status"] == "FAIL" for k, s in stages.items() if k in ("identity", "ecology", "dressing"))
    soft_fail = any(s["status"] == "FAIL" for s in stages.values())
    stages["bundle"] = _stage("PASS", "Tools/world_compiler.py:compile_recipe", f"{len(files)} tables")
    manifest = {
        "schema": "melodia.world_compiler_bundle.v1",
        "compiler_version": COMPILER_VERSION,
        "compile_id": compile_id,
        "recipe_id": recipe["recipe_id"],
        "world_seed": int(recipe["world_seed"]),
        "recipe_sha256": _sha256_bytes(raw),
        "status": "FAIL" if hard_fail else ("EXPECTED_FAIL" if soft_fail else "PASS"),
        "stages": stages,
        "identity": {"movement_id": identity["world"]["movement_id"], "mode_id": identity["world"]["mode_id"],
                     "root_note": identity["world"]["root_note"], "bpm": identity["world"]["bpm"],
                     "chunk_stable_seed": identity["chunk"]["stable_seed"], "motif_id": identity["chunk"]["motif_id"]},
        "place": {
            "level": recipe["place"]["level"],
            "anchor_cm": recipe["place"]["anchor_cm"],
            "clearance_applied": {"circles": len(Clearance.from_recipe(recipe).circles), "capsules": len(Clearance.from_recipe(recipe).capsules)},
            "outer_radius_cm": ecology["outer_radius_cm"],
            "plate_size_cm": ecology["plate_size_cm"],
            "sector_deg": ecology["sector_deg"],
            "ground_mask": ecology["ground_mask"],
        },
        "terrain": terrain,
        "bands": [{**b, "material_instance": dressing["bands"][b["band"]]["material_instance"]} for b in ecology["bands"]],
        "tables": tables,
        "counts": {
            "points_total": len(ecology["points"]),
            "points_removed_by_clearance": ecology["removed_by_clearance"],
            "points_removed_by_chladni": ecology["removed_by_chladni"],
            "points_removed_by_ground": ecology["removed_by_ground"],
            "fx_anchors_total": len(ecology["fx_anchors"]),
            "fx_anchors_removed_by_clearance": ecology["fx_removed_by_clearance"],
        },
        "ue_lane": {
            "data_table": f"/Game/Melodia/WorldCompiler/DT_{recipe['recipe_id']}_Points",
            "row_struct": "/Game/Melodia/WorldCompiler/S_WorldCompilerPoint",
            "pcg_template_graph": "/Game/Melodia/WorldCompiler/PCG_WorldCompiler_PointField",
            "pcg_volume_label": f"WC_{recipe['recipe_id']}_Field",
            "actor_tag": f"WorldCompiler.{compile_id}",
            "fx_pack": (recipe.get("fx") or {}).get("pack", ""),
            # Positional: index == static-mesh material slot. Slot 0 (stem) is overridden with the
            # neutral StemMaterial column so the band MI in 'material' lands on slot 1 (petals).
            "material_override_attributes": (
                ["StemMaterial", "material"] if any(s.get("stem_material") for s in recipe["species"]) else ["material"]
            ),
            **({"structures": {
                "slot_data_table": f"/Game/Melodia/WorldCompiler/DT_{recipe['recipe_id']}_StructureSlots",
                "curve_data_table": f"/Game/Melodia/WorldCompiler/DT_{recipe['recipe_id']}_StructureCurves",
                "pcg_template_graph": "/Game/Melodia/WorldCompiler/PCG_WorldCompiler_Structures",
                "control_actor_class": "/Game/EnvSandbox/PCG/Universal/BP_MelodiaPCGControl",
                "kit_ue_path": (recipe["structures"].get("kit") or {}).get("ue_path", ""),
            }} if bake is not None else {}),
            **({"beauty_feed": {
                "sender_name": beauty["sender_name"],
                "render_target": beauty["render_target"],
                "sender_bp": beauty["sender_bp"],
                "width": beauty["width"],
                "height": beauty["height"],
                "capture_source": beauty["capture_source"],
                "startup_policy": beauty["startup_policy"],
                "plugin": beauty["plugin"]["name"],
            }} if beauty is not None else {}),
            **({"harmony": {
                "node_row_struct": "/Game/Melodia/WorldCompiler/S_WorldCompilerHarmonyNode",
                "edge_row_struct": "/Game/Melodia/WorldCompiler/S_WorldCompilerHarmonyEdge",
                "node_data_table": f"/Game/Melodia/WorldCompiler/DT_{recipe['recipe_id']}_HarmonyNodes",
                "edge_data_table": f"/Game/Melodia/WorldCompiler/DT_{recipe['recipe_id']}_HarmonyEdges",
                "pcg_template_graph": "/Game/Melodia/WorldCompiler/PCG_WorldCompiler_HarmonicRidges",
                "pcg_volume_label": f"WC_{recipe['recipe_id']}_Ridges",
                "points_data_table": f"/Game/Melodia/WorldCompiler/DT_{recipe['recipe_id']}_HarmonyPoints",
                "points_row_struct": "/Game/Melodia/WorldCompiler/S_WorldCompilerPoint",
                "biome_volume_label": f"WC_{recipe['recipe_id']}_Biomes",
                "landscape_import": harmony["meta"]["ue_landscape_import"],
            }} if harmony is not None else {}),
        },
        "notes": [
            "compiler never imports unreal; UE lane is Content/Python/world_compiler_ue.py",
            "template graph is owner-authored and reads the fixed DataTable path; Python only fills rows",
            "MaterialVariant == band index; 'mesh'/'material' soft paths drive PCGMeshSelectorByAttribute",
        ],
    }
    manifest_bytes = _json_bytes(manifest)
    (out_dir / "manifest.json").write_bytes(manifest_bytes)
    manifest["manifest_sha256"] = _sha256_bytes(manifest_bytes)

    if write_envelope:
        try:
            import evidence_envelope as ev  # noqa: E402

            envelope = ev.make_envelope(
                kind="static",
                status="pass" if manifest["status"] in ("PASS", "EXPECTED_FAIL") else "fail",
                producer="Tools/world_compiler.py",
                check_name="world_compiler.compile",
                check_status="pass" if manifest["status"] == "PASS" else ("hold" if manifest["status"] == "EXPECTED_FAIL" else "fail"),
                note=f"{compile_id}: {manifest['counts']['points_total']} points, manifest sha {manifest['manifest_sha256'][:12]}",
                gate_id="world_compiler.offline",
                subject={"compile_id": compile_id, "recipe": str(recipe_path.relative_to(ROOT)).replace("\\", "/") if recipe_path.is_relative_to(ROOT) else recipe_path.name},
                artifacts=[str((out_dir / n).relative_to(ROOT)).replace("\\", "/") for n in list(files) + ["manifest.json"]],
            )
            ev.write_envelope(envelope, out_dir / "evidence_envelope.json")
        except Exception as exc:  # pragma: no cover
            (out_dir / "evidence_envelope.error.txt").write_text(str(exc), encoding="utf-8")

    manifest["out_dir"] = str(out_dir)
    return manifest


# ----------------------------------------------------------------------------- CLI

def _print_summary(manifest: dict[str, Any]) -> None:
    print(f"compile_id : {manifest['compile_id']}   status {manifest['status']}   {manifest['compiler_version']}")
    print(f"identity   : {manifest['identity']}")
    print(f"out_dir    : {manifest.get('out_dir', '')}")
    print(f"manifest   : sha {manifest.get('manifest_sha256', '')[:16]}")
    for name, stage in manifest["stages"].items():
        print(f"  {name:9} {stage['status']:14} {stage.get('note', '')}")
    print(f"{'band':>4} {'label':12} {'r_in':>7} {'r_out':>7} {'mode':>6} {'target':>7} {'kept':>6}")
    for b in manifest["bands"]:
        print(f"{b['band']:>4} {b['label']:12} {b['inner_radius_cm']:>7.0f} {b['outer_radius_cm']:>7.0f} {b['mode_n']}x{b['mode_m']:<4} {b['target_count']:>7} {b['point_count']:>6}")
    c = manifest["counts"]
    print(f"points {c['points_total']}  (clearance -{c['points_removed_by_clearance']}, chladni -{c['points_removed_by_chladni']}, ground -{c['points_removed_by_ground']})  fx anchors {c['fx_anchors_total']} (-{c['fx_anchors_removed_by_clearance']})")
    for name, t in manifest["tables"].items():
        print(f"  {name:22} rows {t['rows']:>6}  sha {t['sha256'][:16]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_compile = sub.add_parser("compile", help="compile a recipe into Saved/WorldCompiler/<compile_id>/")
    p_compile.add_argument("recipe", type=Path)
    p_compile.add_argument("--out-root", type=Path, default=None)
    p_compile.add_argument("--constellation", action="store_true", help="attach resonant_world_asset_constellation (machine-dependent)")
    p_compile.add_argument("--no-envelope", action="store_true")
    p_compile.add_argument("--json", action="store_true", help="print the manifest as JSON")
    p_validate = sub.add_parser("validate", help="validate a recipe against the schema and semantic rules")
    p_validate.add_argument("recipe", type=Path)
    p_show = sub.add_parser("show", help="summarise an existing bundle")
    p_show.add_argument("bundle_dir", type=Path)
    args = parser.parse_args(argv)

    if args.cmd == "validate":
        recipe, _ = load_recipe(args.recipe)
        errors = validate_recipe(recipe)
        print("\n".join(errors) if errors else f"recipe OK: {recipe['recipe_id']} seed {recipe['world_seed']}")
        return 1 if errors else 0
    if args.cmd == "show":
        manifest = json.loads((args.bundle_dir / "manifest.json").read_text(encoding="utf-8"))
        manifest["out_dir"] = str(args.bundle_dir)
        manifest["manifest_sha256"] = _sha256_file(args.bundle_dir / "manifest.json")
        _print_summary(manifest)
        return 0
    manifest = compile_recipe(args.recipe, out_root=args.out_root, constellation=args.constellation, write_envelope=not args.no_envelope)
    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        _print_summary(manifest)
    return 0 if manifest["status"] in ("PASS", "EXPECTED_FAIL") else 1


if __name__ == "__main__":
    raise SystemExit(main())
