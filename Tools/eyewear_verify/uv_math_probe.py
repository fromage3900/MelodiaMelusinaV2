"""Verify what UV and math nodes are actually available in this Blender build.

The plan calls for authoring UVs in-graph so shaders can be set up and packed
WITHOUT waiting on a merged geometry. This confirms:
  1. UV node availability (GeometryNodeUVUnwrap, UVProject, etc.)
  2. StoreNamedAttribute domain support (FACE vs POINT vs CORNER — needed for UV)
  3. Sine/Cosine/Atan2/Modulo/Wrap math ops
  4. Named attribute "UV" → TEXCOORD_0 roundtrip"""
import bpy

print("  blender %s" % bpy.app.version_string)

g = bpy.data.node_groups.new("probe", "GeometryNodeTree")

# --- 1. UV nodes ---
for name in ("GeometryNodeUVUnwrap", "GeometryNodeUVProject",
             "GeometryNodeUVScale", "GeometryNodeUVTranslate"):
    try:
        n = g.nodes.new(name)
        ins = ["%s:%s" % (s.name, getattr(s, "default_value", "")) for s in n.inputs]
        print("  UV  %-34s OK  %s" % (name, " | ".join(ins)[:200]))
    except Exception as exc:
        print("  UV  %-34s ABSENT (%s)" % (name, exc))

# --- 2. StoreNamedAttribute domains ---
try:
    n = g.nodes.new("GeometryNodeStoreNamedAttribute")
    for cand in ("POINT", "FACE", "CORNER", "CURVE", "INSTANCE"):
        try:
            n.domain = cand
            print("  StoreNamedAttribute domain %r OK" % cand)
        except Exception:
            print("  StoreNamedAttribute domain %r ABSENT" % cand)
except Exception as exc:
    print("  StoreNamedAttribute ABSENT: %s" % exc)

# --- 3. Math ops ---
ops = ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "POWER", "SQRT", "LOGARITHM",
       "ABSOLUTE", "MINIMUM", "MAXIMUM", "MODULO", "FLOOR", "CEILING", "ROUND",
       "SIGN", "COMPARE", "RADIANS", "DEGREES", "EXPONENT",
       "SINE", "COSINE", "TANGENT", "ARCSINE", "ARCCOSINE", "ARCTANGENT",
       "ARCTAN2", "SINH", "COSH", "TANH",
       "MULTIPLY_ADD", "PINGPONG", "SMOOTH_MIN", "SMOOTH_MAX",
       "WRAP", "FRACTION", "TRUNC", "PERCENT"]
n = g.nodes.new("ShaderNodeMath")
for op in ops:
    try:
        n.operation = op
        print("  math %s OK" % op)
    except Exception:
        pass  # silent — too many to list

# --- 4. SplineParameter factor/length ---
try:
    n = g.nodes.new("GeometryNodeSplineParameter")
    print("  SplineParameter outputs: %s" % [s.name for s in n.outputs])
except Exception as exc:
    print("  SplineParameter: %s" % exc)

# --- 5. Curve info ---
try:
    n = g.nodes.new("GeometryNodeInputCurveHandlePositions")
    print("  InputCurveHandlePositions outputs: %s" % [s.name for s in n.outputs])
except Exception as exc:
    print("  InputCurveHandlePositions: %s" % exc)

try:
    n = g.nodes.new("GeometryNodeInputTangent")
    print("  InputTangent OK")
except Exception as exc:
    print("  InputTangent: %s" % exc)

try:
    n = g.nodes.new("GeometryNodeCurveOfPoint")
    print("  CurveOfPoint OK")
except Exception as exc:
    pass

# --- 6. Position + separate XYZ available? ---
try:
    n = g.nodes.new("GeometryNodeInputPosition")
    print("  InputPosition OK")
    ns = g.nodes.new("ShaderNodeSeparateXYZ")
    print("  SeparateXYZ OK")
except Exception as exc:
    print("  %s" % exc)

# --- 7. RealizeInstances + MergeByDistance ---
for name in ("GeometryNodeRealizeInstances", "GeometryNodeMergeByDistance",
             "GeometryNodeSetMaterial", "GeometryNodeInputMaterial"):
    try:
        g.nodes.new(name)
        print("  %s OK" % name)
    except Exception as exc:
        print("  %s: %s" % (name, exc))

bpy.data.node_groups.remove(g)
print("DONE")
