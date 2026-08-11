"""Wire triplanar single-calc slope gating into M_Master_Toon_Universal.

Builds the slope-gated mask chain on top of the existing single-calc
triplanar system (Shared macro lattice Custom node + TriplanarUVs Custom node):

  TriplanarSlopeMask (Custom HLSL, CMOT_FLOAT1)
      slope mask from vertex world normal vs world up, gated between
      TriplanarSlopeStart and TriplanarSlopeEnd (0 = flat, 1 = steep)
  TriplanarGate (Custom HLSL, CMOT_FLOAT1)
      SlopeMask * bTriplanar_Active (static bool feeds in as float)
  Multiply chain + LinearInterpolate
      lerp(A = 0, B = lattice * TriplanarUVs, Alpha = TriplanarGate)
      -> mask = 0 yields zero triplanar contribution (no visual change at default)

Idempotent: nodes already present are skipped; connections already made are
not re-made. Only ADDS nodes and ADD new connections from new nodes - never
deletes, disconnects, or rewires existing links. No parameter defaults touched.

Run in Unreal Editor (exec in the Python interpreter):
    exec(open(".../wire_triplanar_gate.py").read())
"""

import unreal

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

SLOPE_MASK_DESC = "TriplanarSlopeMask"
GATE_DESC = "TriplanarGate"
LATTICE_DESC_FRAG = "shared macro lattice"

MARK_PREFIX = "WireTriplanarGate:"

SLOPE_MASK_HLSL = """\
float upDot = abs(dot(normalize(Parameters.WorldNormal), float3(0,0,1)));
float steepness = 1.0 - upDot;
return smoothstep(SlopeStart, SlopeEnd, steepness);
"""

GATE_HLSL = """\
return SlopeMask * Active;
"""


def main():
    MEL = unreal.MaterialEditingLibrary
    con = MEL.connect_material_expressions

    def log(action):
        print(f"[WireTri] {action}")

    if not unreal.EditorAssetLibrary.does_asset_exist(MATERIAL_PATH):
        log(f"ERROR: material not found at {MATERIAL_PATH}")
        return
    mat = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
    if not mat:
        log(f"ERROR: could not load material at {MATERIAL_PATH}")
        return

    def expressions():
        return list(MEL.get_material_expressions(mat) or [])

    def custom_node(pred):
        for e in expressions():
            if type(e).__name__ != "MaterialExpressionCustom":
                continue
            try:
                desc = e.get_editor_property("description")
            except Exception:
                continue
            if desc and pred(str(desc)):
                return e
        return None

    def param_by_name(name):
        for e in expressions():
            try:
                if str(e.get_editor_property("parameter_name")) == name:
                    return e
            except Exception:
                pass
        return None

    def new_custom(desc, code, out_type, inputs, x, y):
        node = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, x, y)
        node.set_editor_property("description", desc)
        node.set_editor_property("code", code)
        node.set_editor_property("output_type", out_type)
        ins = []
        for in_name in inputs:
            ci = unreal.CustomInput()
            ci.set_editor_property("input_name", in_name)
            ins.append(ci)
        node.set_editor_property("inputs", ins)
        return node

    def find_marked(mark):
        for e in expressions():
            try:
                if str(e.get_editor_property("desc")) == MARK_PREFIX + mark:
                    return e
            except Exception:
                pass
        return None

    def mark(node, mark):
        try:
            node.set_editor_property("desc", MARK_PREFIX + mark)
        except Exception:
            log(f"WARN: could not tag {mark} node for idempotency")
    # ── 1. Anchors (must all exist - created by setup_triplanar_singlecalc) ──
    slope_start = param_by_name("TriplanarSlopeStart")
    slope_end = param_by_name("TriplanarSlopeEnd")
    active = param_by_name("bTriplanar_Active")
    lattice = custom_node(lambda d: LATTICE_DESC_FRAG in d.lower())
    tri_uvs = custom_node(lambda d: "triplanaruvs" in d.lower())

    missing = [name for name, v in (
        ("TriplanarSlopeStart", slope_start),
        ("TriplanarSlopeEnd", slope_end),
        ("bTriplanar_Active", active),
        ("Shared macro lattice node", lattice),
        ("TriplanarUVs node", tri_uvs),
    ) if v is None]
    if missing:
        log(f"ERROR: missing anchors -> {', '.join(missing)}; aborting")
        return

    # ── 2. TriplanarSlopeMask Custom HLSL ──
    slope_mask = custom_node(lambda d: "triplanarslopemask" in d.lower())
    created_slope_mask = False
    if slope_mask is None:
        slope_mask = new_custom(SLOPE_MASK_DESC, SLOPE_MASK_HLSL,
                                unreal.CustomMaterialOutputType.CMOT_FLOAT1,
                                ("SlopeStart", "SlopeEnd"), 3900, 2350)
        created_slope_mask = True
        log("created TriplanarSlopeMask Custom HLSL node")
    else:
        log("TriplanarSlopeMask already present - skipping create")

    if created_slope_mask:
        con(slope_start, "", slope_mask, "SlopeStart")
        log("wired TriplanarSlopeStart -> TriplanarSlopeMask.SlopeStart")
        con(slope_end, "", slope_mask, "SlopeEnd")
        log("wired TriplanarSlopeEnd -> TriplanarSlopeMask.SlopeEnd")

    # ── 3. TriplanarGate Custom HLSL ──
    gate = custom_node(lambda d: "triplanargate" in d.lower())
    created_gate = False
    if gate is None:
        gate = new_custom(GATE_DESC, GATE_HLSL,
                          unreal.CustomMaterialOutputType.CMOT_FLOAT1,
                          ("SlopeMask", "Active"), 4100, 2400)
        created_gate = True
        log("created TriplanarGate Custom HLSL node")
    else:
        log("TriplanarGate already present - skipping create")

    if created_gate:
        con(slope_mask, "", gate, "SlopeMask")
        log("wired TriplanarSlopeMask -> TriplanarGate.SlopeMask")
        con(active, "", gate, "Active")
        log("wired bTriplanar_Active -> TriplanarGate.Active")

    # ── 4. Gated multiply chain (lattice * TriplanarUVs) + lerp ──
    def cmot_dim(expr):
        try:
            t = expr.get_editor_property("output_type")
        except Exception:
            return 4
        s = str(t)
        if "FLOAT4" in s:
            return 4
        if "FLOAT3" in s:
            return 3
        if "FLOAT2" in s:
            return 2
        if "FLOAT1" in s or "FLOAT_1" in s:
            return 1
        return 4

    def mask_to(src, dim, x, y):
        m = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, x, y)
        m.set_editor_property("r", dim >= 1)
        m.set_editor_property("g", dim >= 2)
        m.set_editor_property("b", dim >= 3)
        m.set_editor_property("a", dim >= 4)
        con(src, "", m, "")
        return m

    lat_dim = cmot_dim(lattice)
    uv_dim = cmot_dim(tri_uvs)
    out_dim = min(lat_dim, uv_dim)

    multiply = find_marked("multiply")
    if multiply is None:
        a_src, b_src = lattice, tri_uvs
        if lat_dim != uv_dim:
            if lat_dim > uv_dim:
                a_src = mask_to(lattice, uv_dim, 4150, 2300)
            else:
                b_src = mask_to(tri_uvs, lat_dim, 4150, 2340)
        multiply = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, 4300, 2300)
        mark(multiply, "multiply")
        con(a_src, "", multiply, "A")
        con(b_src, "", multiply, "B")
        log("wired Shared macro lattice x TriplanarUVs -> Multiply")
    else:
        log("Multiply chain already present - skipping create")

    zero = find_marked("zero")
    if zero is None:
        if out_dim == 1:
            zero = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, 4300, 2460)
        elif out_dim == 2:
            zero = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant2Vector, 4300, 2460)
        elif out_dim == 3:
            zero = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, 4300, 2460)
        else:
            zero = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant4Vector, 4300, 2460)
            zero.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 0.0))
        mark(zero, "zero")
        log("created zero constant (lerp A)")
    else:
        log("zero constant already present - skipping create")

    lerp = find_marked("lerp")
    if lerp is None:
        lerp = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, 4500, 2350)
        mark(lerp, "lerp")
        con(zero, "", lerp, "A")
        con(multiply, "", lerp, "B")
        con(gate, "", lerp, "Alpha")
        log("wired lerp(A=0, B=lattice*TriplanarUVs, Alpha=TriplanarGate)")
    else:
        log("LinearInterpolate already present - skipping create")

    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    log("recompiled and saved M_Master_Toon_Universal")


if __name__ == "__main__":
    main()
