"""Resonance Ecology — PCG Python Data Processor script (UE 5.8, EDITOR ONLY).

Engine contract, verified against
Engine/Plugins/PCGInterops/PCGPythonInterop/Source/PCGPythonInteropEditor/
Private/Elements/PCGPythonDataProcessor.cpp:

    data_in  : unreal.PCGDataCollection   (bridge.get_input_collection())
    data_out : unreal.PCGPythonDataBridge (add_to_collection / set_output_collection)

The node wraps this file in try/finally and deletes those names afterwards, so do
not rely on them persisting. The node is WITH_EDITOR only — at runtime it logs
"should not be used at runtime". This is an authoring-time enrichment pass, not a
runtime authority: C++ still owns gameplay truth.

Derives, per point, from position + seed only (deterministic, no side effects):
    Resonance       float  0..1
    EcologyClass    int32  0..2
    MaterialVariant int32  0..2
    ScaleBias       float  bounded
"""

INPUT_PIN = "Input"
OUTPUT_PIN = "Output"

HEIGHT_MIN = 0.0
HEIGHT_MAX = 2000.0          # cm band over which height normalises to 0..1
CLASS_EDGES = (0.33, 0.66)   # Resonance -> 3 EcologyClass bands
SCALE_BIAS_MIN = 0.75
SCALE_BIAS_MAX = 1.35
HEIGHT_WEIGHT = 0.75         # rest is deterministic positional jitter

ATTR_RESONANCE = "Resonance"
ATTR_ECOLOGY = "EcologyClass"
ATTR_VARIANT = "MaterialVariant"
ATTR_SCALE_BIAS = "ScaleBias"


def _clamp01(v):
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def _normalize(value, lo, hi):
    if hi <= lo:
        return 0.0
    return _clamp01((value - lo) / (hi - lo))


def _hash01(x, y, seed):
    """Deterministic 0..1 from integer-quantised XY and a seed. No RNG state."""
    h = (int(x) * 73856093) ^ (int(y) * 19349663) ^ (int(seed) * 83492791)
    return ((h & 0x7FFFFFFF) % 10000) / 10000.0


def derive(pos_x, pos_y, pos_z, seed, z_lo=HEIGHT_MIN, z_hi=HEIGHT_MAX):
    """Position + seed -> (resonance, ecology_class, material_variant, scale_bias).

    z_lo/z_hi default to the constant band but callers should pass the actual Z
    range of the incoming point cloud: absolute world Z is meaningless when a
    level sits at Z=38000, where every point would clamp to 1.0.
    """
    height = _normalize(pos_z, z_lo, z_hi)
    jitter = _hash01(pos_x, pos_y, seed)
    resonance = _clamp01(HEIGHT_WEIGHT * height + (1.0 - HEIGHT_WEIGHT) * jitter)

    if resonance < CLASS_EDGES[0]:
        ecology = 0
    elif resonance < CLASS_EDGES[1]:
        ecology = 1
    else:
        ecology = 2

    variant = int(jitter * 3.0) % 3
    scale_bias = SCALE_BIAS_MIN + (SCALE_BIAS_MAX - SCALE_BIAS_MIN) * resonance
    return resonance, ecology, variant, scale_bias


def process(collection, bridge, seed=0, input_pin=INPUT_PIN, output_pin=OUTPUT_PIN):
    """Enrich every PCGPointData on input_pin and emit it on output_pin.

    get_typed_inputs_by_pin_label returns (data, tags) -- the tags must be carried
    through to the emitted data or downstream selectors that key off them stop
    matching. Forwarding non-point data is deliberately NOT attempted: the bridge
    cannot marshal a base PCGData through AddToCollection ("Failed to convert
    parameter 'data'"), so this node is point-data-only by contract.
    """
    import unreal

    data_list, tag_list = collection.get_typed_inputs_by_pin_label(
        input_pin, unreal.PCGPointData
    )
    emitted = 0
    forwarded = 0

    for idx, data in enumerate(data_list):
        try:
            tags = list(tag_list[idx]) if tag_list else []
        except Exception:
            tags = []

        points = data.get_points()
        result = unreal.PCGPointData()
        # Inherit the source's metadata structure and parenting. Building a bare
        # PCGPointData and calling create_empty_metadata() produces attributes that
        # downstream PCG cannot see: the graph logs "does not have valid point
        # metadata" and accessors fail with "Attribute 'X' was not found".
        result.initialize_from_data(data)
        metadata = result.mutable_metadata()
        src_metadata = data.const_metadata()
        metadata.create_float_attribute(ATTR_RESONANCE, 0.0, True, True)
        metadata.create_integer32_attribute(ATTR_ECOLOGY, 0, False, True)
        metadata.create_integer32_attribute(ATTR_VARIANT, 0, False, True)
        metadata.create_float_attribute(ATTR_SCALE_BIAS, 1.0, True, True)

        # Normalise against this cloud's own Z range so the rule is level-agnostic.
        zs = [pt.transform.translation.z for pt in points]
        z_lo, z_hi = (min(zs), max(zs)) if zs else (HEIGHT_MIN, HEIGHT_MAX)
        if z_hi - z_lo < 1.0:
            z_lo, z_hi = HEIGHT_MIN, HEIGHT_MAX

        new_points = []
        for point in points:
            loc = point.transform.translation
            resonance, ecology, variant, scale_bias = derive(
                loc.x, loc.y, loc.z, seed, z_lo, z_hi
            )
            point.initialize_metadata(metadata, point, src_metadata)
            # Placement influence (authoring-time only). Compose with what the
            # upstream graph already authored rather than replacing it: on a unit
            # point this is identical to assignment, so nothing that fed us a
            # unit scale changes, while graphs that authored their own per-point
            # scale keep it. Density is left alone -- it is PCG's own culling
            # channel and Resonance, not density, is the semantic authority.
            xf = point.transform
            sc = xf.scale3d
            xf.scale3d = unreal.Vector(
                sc.x * scale_bias, sc.y * scale_bias, sc.z * scale_bias
            )
            point.transform = xf
            point.set_float_attribute(metadata, ATTR_RESONANCE, resonance)
            point.set_integer32_attribute(metadata, ATTR_ECOLOGY, ecology)
            point.set_integer32_attribute(metadata, ATTR_VARIANT, variant)
            point.set_float_attribute(metadata, ATTR_SCALE_BIAS, scale_bias)
            new_points.append(point)

        result.set_points(new_points)
        bridge.add_to_collection(result, output_pin, tags)
        emitted += len(new_points)

    return emitted, forwarded


# When the node executes this file, data_in / data_out are already injected.
if "data_in" in dir() and "data_out" in dir():
    _n, _fwd = process(data_in, data_out)  # noqa: F821 - engine-injected
    print("[ResonanceEcology] enriched %d points, forwarded %d non-point data" % (_n, _fwd))
