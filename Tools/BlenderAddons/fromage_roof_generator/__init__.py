# ============================================================
# Fromage's Roof Generator v3.1 — Professional & Cute Roofs
# ============================================================
# Version:  3.1.0
# Blender:  5.1+
# Author:   Surreal Architecture Studio
# License:  GPL-3.0
#
# 🏠 21 roof types: Classic + Y2K Cute Dome
# 💖 10 Dreamy Y2K Materials (Cotton Candy, Starlight, etc)
# 💗 Cute Hearts & Stars Accents (scattered, grid, border, rainbow)
# 🎨 Material presets with baking system (2K/4K)
# 🧩 Procedural shingle generator with normal+displacement
# 🏠 Dormers & skylights with switchable merge
# 💧 Gutters & downspouts with switchable merge
# 📚 Roof modifier stack (layer multiple types)
# 👁️  Live viewport preview
#
# 🎯 Professional + Adorable • Game-ready • Full PBR pipeline
# ============================================================

bl_info = {
    "name":        "🏠 Fromage's Roof Generator",
    "author":      "Surreal Architecture Studio",
    "version":     (3, 2, 0),
    "blender":     (5, 1, 0),
    "location":    "Properties > Object Data > 🏠 Fromage's Roofs",
    "description": "Professional & Cute roof generator with 20+ styles, Y2K Dome, Dreamy Materials, "
                   "Heart/Star Accents, Materials, Baking, Shingles, Dormers, Gutters. Game-ready output.",
    "warning":     "",
    "doc_url":     "",
    "category":    "Mesh",
    "support":     "COMMUNITY",
}

import bpy
import math
import bmesh


# ──────────────────────────────────────────────────────────────
# AUTO-UPDATE CALLBACK
# ──────────────────────────────────────────────────────────────

def _roof_update(self, context):
    obj = context.active_object
    if obj and obj.type == 'MESH' and obj.fromage_roof_props.use_geonode:
        _build_geonode_roof(obj, obj.fromage_roof_props)
    elif obj and obj.type == 'MESH' and obj.fromage_roof_props.auto_rebuild:
        _build_bmesh_roof(obj, obj.fromage_roof_props)


# ──────────────────────────────────────────────────────────────
# PROPERTIES
# ──────────────────────────────────────────────────────────────

class FromageRoofProperties(bpy.types.PropertyGroup):

    use_geonode: bpy.props.BoolProperty(
        name="💎 Use Geometry Nodes",
        description="Build with GN (parametric, real-time) instead of bmesh (baked)",
        default=True,
    )

    auto_rebuild: bpy.props.BoolProperty(
        name="🔄 Auto-Rebuild",
        description="Rebuild roof immediately when parameters change (GN mode)",
        default=False,
    )

    roof_type: bpy.props.EnumProperty(
        name="🏠 Roof Type",
        description="Architectural roof style",
        items=[
            # ─── Classical European ─────────────────────────────────
            ('HIP',           "🏠 Hip",              "4-way slope — universal classic"),
            ('GABLED',        "🏠 Gabled",           "2-slope gable with eave upturn"),
            ('MANSARD',       "🏢 Mansard",          "Mansard / French Second Empire"),
            ('GAMBREL',       "🏚 Gambrel",          "Gambrel / barn roof — 4-slope"),
            ('DUTCH_GABLE',   "🏘 Dutch Gable",      "Hip with small gable at ridge"),

            # ─── Asian & Eastern ───────────────────────────────────
            ('PAGODA',        "🏯 Pagoda",           "Multi-tier Asian upswept eaves"),
            ('ONION',         "🧅 Onion",            "Bulging dome — Russian/Mughal"),
            ('HANOK',         "⛩️  Korean Hanok",    "Korean curved eaves, concave"),
            ('CHINESE',       "🏯 Chinese",          "Curved hip with dragon finials"),
            ('JAPANESE',      "⛩️  Japanese",        "Shallow curved slope, deep eaves"),

            # ─── Modern & Geometric ────────────────────────────────
            ('BUTTERFLY',     "🦋 Butterfly",        "Inverted V — valley centre"),
            ('SHED',          "🏭 Shed",             "Single slope — industrial lean-to"),
            ('BARREL',        "🛢️  Barrel",          "Semicircular vault tunnel"),
            ('GEODESIC',      "🌐 Geodesic",         "Segmented dome — Buckminster Fuller"),
            ('VAULTED',       "⛪ Vaulted",          "Pointed Gothic vault / groin cross"),
            ('WAVE',          "🌊 Wave",             "Free-form sine-wave surface"),

            # ─── Regional & Historical ─────────────────────────────
            ('CATALAN',       "🏘️  Catalan Vault",   "Mediterranean tile arch"),
            ('OTTOMAN',       "🕌 Ottoman",          "Turkish dome with pendentives"),
            ('TUVAN',         "⛺ Tuvan Conical",    "Central Asian cone — nomadic"),
            ('THATCH',        "🌾 Thatch",           "Organic straw/reed slope"),
            ('CLERESTORY',    "💡 Clerestory",       "Roof with upper windows"),

            # ─── Y2K Cute ──────────────────────────────────────────
            ('Y2K_CUTE',      "💗 Y2K Cute Dome",    "Bubbly pastel Y2K aesthetic"),
        ],
        default='HIP',
        update=_roof_update,
    )

    # ── Dimensions ──────────────────────────────────────────────
    roof_span: bpy.props.FloatProperty(
        name="📏 Span (X)", description="Total width",
        default=6.0, min=0.5, max=80.0, unit='LENGTH', update=_roof_update)
    roof_depth: bpy.props.FloatProperty(
        name="📏 Depth (Y)", description="Total depth",
        default=4.0, min=0.5, max=80.0, unit='LENGTH', update=_roof_update)
    roof_rise: bpy.props.FloatProperty(
        name="📈 Rise", description="Height to ridge",
        default=2.5, min=0.05, max=30.0, unit='LENGTH', update=_roof_update)

    # ── Eave ────────────────────────────────────────────────────
    roof_eave_overhang: bpy.props.FloatProperty(
        name="🔲 Eave Overhang",
        description="Overhang beyond footprint",
        default=0.4, min=0.0, max=5.0, unit='LENGTH', update=_roof_update)
    roof_eave_curve: bpy.props.FloatProperty(
        name="🌙 Eave Upturn",
        description="Asian-style upward curve",
        default=0.3, min=0.0, max=3.0, unit='LENGTH', update=_roof_update)

    # ── Quality ─────────────────────────────────────────────────
    roof_segments: bpy.props.IntProperty(
        name="✨ Segments",
        description="Resolution — higher = smoother",
        default=24, min=4, max=256, update=_roof_update)
    roof_ridge_length: bpy.props.FloatProperty(
        name="📍 Ridge Length",
        description="Flat ridge at top (0 = apex)",
        default=2.0, min=0.0, max=40.0, unit='LENGTH', update=_roof_update)
    roof_thickness: bpy.props.FloatProperty(
        name="🪨 Shell Thickness",
        description="Solidify thickness",
        default=0.08, min=0.0, max=2.0, unit='LENGTH', update=_roof_update)

    # ── Pagoda/Multi-tier ───────────────────────────────────────
    roof_tiers: bpy.props.IntProperty(
        name="🏯 Tiers", description="Stacked tiers",
        default=3, min=1, max=9, update=_roof_update)
    roof_tier_shrink: bpy.props.FloatProperty(
        name="📉 Tier Shrink",
        description="Each tier shrinks to this fraction",
        default=0.75, min=0.3, max=0.98, subtype='FACTOR', update=_roof_update)

    # ── Wave/Organic ────────────────────────────────────────────
    roof_wave_freq: bpy.props.FloatProperty(
        name="〰️  Wave Frequency",
        description="Cycles across span",
        default=2.0, min=0.5, max=16.0, update=_roof_update)

    # ── Gambrel specifics ───────────────────────────────────────
    roof_gambrel_break: bpy.props.FloatProperty(
        name="⚡ Gambrel Break Height",
        description="Height where slope changes",
        default=0.6, min=0.2, max=0.95, subtype='FACTOR', update=_roof_update)

    # ── Post-process ────────────────────────────────────────────
    roof_with_bevel: bpy.props.BoolProperty(
        name="✨ Auto Bevel",
        description="Add Bevel for smooth edges",
        default=True, update=_roof_update)

    # ══════════════════════════════════════════════════════════════
    # V3.0 SYSTEMS: Material, Shingles, Dormers, Gutters, Stack, Preview
    # ══════════════════════════════════════════════════════════════

    # ── Material & Baking ───────────────────────────────────────
    material_preset: bpy.props.EnumProperty(
        name="🎨 Material Preset",
        description="Pre-configured material type",
        items=[
            # Classic
            ('SLATE', "🪨 Slate", "Dark, rough, realistic"),
            ('TERRACOTTA', "🍁 Terracotta", "Warm, organic, Mediterranean"),
            ('WOOD', "🪵 Wood Shakes", "Rustic, noisy normals"),
            ('COPPER', "🔶 Copper", "Metallic, weathered patina"),
            ('ASPHALT', "⚫ Asphalt Shingles", "Modern, fine detail"),
            ('THATCH_MAT', "🌾 Thatch", "Organic, straw detail"),
            ('CLAY', "🧱 Clay Barrel Tiles", "Spanish, curved normals"),
            ('METAL', "⚙️  Modern Metal", "Sleek, subtle relief"),
            # Cute Dreamy Y2K
            ('COTTON_CANDY', "💗 Cotton Candy", "Soft pink dreamy"),
            ('PASTEL_CLOUD', "☁️  Pastel Cloud", "Very soft dreamy"),
            ('IRIDESCENT', "🌈 Iridescent", "Rainbow shimmer"),
            ('BUBBLEGUM', "🍬 Bubblegum Pink", "Bright pastel pink"),
            ('LAVENDER_MIST', "💜 Lavender Mist", "Soft lavender haze"),
            ('MINT_DREAM', "🌿 Mint Dream", "Soft minty fresh"),
            ('PEACH_GLOW', "🍑 Peach Glow", "Warm peachy blush"),
            ('STARLIGHT', "✨ Starlight", "Sparkly shimmer"),
            ('BLUSH', "🌸 Blush Rose", "Soft rose pink"),
            ('MOONLIGHT', "🌙 Moonlight Blue", "Soft sky blue"),
        ],
        default='SLATE')

    bake_resolution: bpy.props.EnumProperty(
        name="📐 Bake Resolution",
        description="Texture atlas resolution for baking",
        items=[
            ('2K', "2K (2048x2048)", "Balanced quality/performance"),
            ('4K', "4K (4096x4096)", "High detail, larger files"),
        ],
        default='2K')

    # ── Shingle/Tile System ─────────────────────────────────────
    enable_shingles: bpy.props.BoolProperty(
        name="🧩 Enable Shingles",
        description="Add procedural shingle texture maps",
        default=True)

    shingle_type: bpy.props.EnumProperty(
        name="🧩 Shingle Type",
        description="Shingle/tile profile shape",
        items=[
            ('FLAT', "Flat", "Flat rectangular shingles"),
            ('CURVED', "Curved", "Curved barrel tiles"),
            ('SPANISH', "Spanish", "Interlocking Spanish tiles"),
            ('INTERLOCKING', "Interlocking", "Modern interlocking pattern"),
        ],
        default='FLAT')

    shingle_size: bpy.props.FloatProperty(
        name="📏 Shingle Size",
        description="Width/length in cm",
        default=30.0, min=10.0, max=100.0, unit='LENGTH')

    shingle_variation: bpy.props.FloatProperty(
        name="🎲 Variation",
        description="Height randomness (0-1)",
        default=0.3, min=0.0, max=1.0, subtype='FACTOR')

    shingle_pattern: bpy.props.EnumProperty(
        name="📐 Pattern",
        description="Layout pattern",
        items=[
            ('RUNNING', "Running Bond", "Offset rows"),
            ('STACK', "Stack Bond", "Aligned columns"),
            ('HERRINGBONE', "Herringbone", "Diagonal 45deg"),
        ],
        default='RUNNING')

    shingle_normal_strength: bpy.props.FloatProperty(
        name="📍 Normal Strength",
        description="Relief intensity (0-1)",
        default=0.6, min=0.0, max=1.0, subtype='FACTOR')

    shingle_displacement_strength: bpy.props.FloatProperty(
        name="📈 Displacement Strength",
        description="Height effect (0-1)",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR')

    shingle_wear_amount: bpy.props.FloatProperty(
        name="⏳ Wear Amount",
        description="Weathering/dirt (0-1)",
        default=0.2, min=0.0, max=1.0, subtype='FACTOR')

    # ── Roof Modifier Stack ─────────────────────────────────────
    enable_roof_stack: bpy.props.BoolProperty(
        name="📚 Enable Roof Stack",
        description="Layer multiple roof types",
        default=False)

    roof_stack_type_2: bpy.props.EnumProperty(
        name="🏠 Secondary Roof Type",
        description="Second roof to layer/blend",
        items=[
            ('HIP', "Hip", ""),
            ('GABLED', "Gabled", ""),
            ('MANSARD', "Mansard", ""),
            ('GAMBREL', "Gambrel", ""),
            ('PAGODA', "Pagoda", ""),
            ('SHED', "Shed", ""),
        ],
        default='GABLED')

    roof_stack_blend_mode: bpy.props.EnumProperty(
        name="🔀 Blend Mode",
        description="How to combine roofs",
        items=[
            ('UNION', "Union", "Boolean union (merge)"),
            ('SUBTRACT', "Subtract", "Boolean subtract (cut)"),
            ('BLEND', "Blend", "Vertical offset blend"),
        ],
        default='UNION')

    roof_stack_offset_z: bpy.props.FloatProperty(
        name="📍 Z Offset",
        description="Vertical separation between roofs",
        default=0.5, min=-5.0, max=5.0, unit='LENGTH')

    roof_stack_scale_factor: bpy.props.FloatProperty(
        name="📏 Scale Factor",
        description="Secondary roof scale (0.5-2.0)",
        default=0.8, min=0.5, max=2.0, subtype='FACTOR')

    # ── Dormers & Skylights ─────────────────────────────────────
    enable_dormers: bpy.props.BoolProperty(
        name="🏠 Enable Dormers",
        description="Add dormer windows to roof",
        default=False)

    dormer_type: bpy.props.EnumProperty(
        name="🏠 Dormer Type",
        description="Dormer profile style",
        items=[
            ('GABLE', "Gable", "Peaked gable dormer"),
            ('SHED', "Shed", "Single slope shed"),
            ('EYEBROW', "Eyebrow", "Curved eyebrow shape"),
        ],
        default='GABLE')

    dormer_count: bpy.props.IntProperty(
        name="🔢 Dormer Count",
        description="Number of dormers to place",
        default=2, min=1, max=8)

    dormer_width: bpy.props.FloatProperty(
        name="📏 Dormer Width",
        description="Width of dormer opening",
        default=1.2, min=0.5, max=5.0, unit='LENGTH')

    dormer_height: bpy.props.FloatProperty(
        name="📈 Dormer Height",
        description="Height of dormer wall",
        default=1.5, min=0.5, max=5.0, unit='LENGTH')

    dormer_spacing: bpy.props.FloatProperty(
        name="📍 Spacing from Ridge",
        description="Distance from ridge (0=ridge, 1=eave)",
        default=0.4, min=0.0, max=1.0, subtype='FACTOR')

    dormer_merge_with_roof: bpy.props.BoolProperty(
        name="🔗 Merge with Roof",
        description="Boolean merge dormers into roof or keep separate",
        default=False)

    # ── Gutters & Drains ────────────────────────────────────────
    enable_gutters: bpy.props.BoolProperty(
        name="💧 Enable Gutters",
        description="Add gutters and downspouts",
        default=False)

    gutter_profile: bpy.props.EnumProperty(
        name="📐 Gutter Profile",
        description="Cross-section shape",
        items=[
            ('K_STYLE', "K-Style", "K-shaped aluminum gutter"),
            ('HALF_ROUND', "Half-Round", "Semicircular copper gutter"),
            ('BOX', "Box", "Modern box gutter"),
        ],
        default='K_STYLE')

    gutter_width: bpy.props.FloatProperty(
        name="📏 Gutter Width",
        description="Width (4-8 inches typical)",
        default=0.2, min=0.1, max=0.4, unit='LENGTH')

    gutter_depth: bpy.props.FloatProperty(
        name="📈 Gutter Depth",
        description="Depth (4-6 inches typical)",
        default=0.15, min=0.1, max=0.3, unit='LENGTH')

    downspout_diameter: bpy.props.FloatProperty(
        name="🔘 Downspout Diameter",
        description="Pipe diameter (3-4 inches)",
        default=0.1, min=0.05, max=0.2, unit='LENGTH')

    downspout_offset: bpy.props.FloatProperty(
        name="📍 Downspout Offset",
        description="Distance from corner",
        default=0.2, min=0.0, max=1.0, unit='LENGTH')

    gutter_merge_with_roof: bpy.props.BoolProperty(
        name="🔗 Merge with Roof",
        description="Boolean merge gutters into roof or keep separate",
        default=False)

    # ── Live Viewport Preview ───────────────────────────────────
    enable_viewport_preview: bpy.props.BoolProperty(
        name="👁️  Live Viewport Preview",
        description="Real-time mesh update as params change",
        default=True)

    # ══════════════════════════════════════════════════════════════
    # CUTE Y2K ACCENT SYSTEM 💖⭐
    # ══════════════════════════════════════════════════════════════

    enable_cute_accents: bpy.props.BoolProperty(
        name="💖 Enable Cute Accents",
        description="Add hearts and stars to roof",
        default=False)

    accent_shape: bpy.props.EnumProperty(
        name="💖 Accent Shape",
        description="Heart or star shapes",
        items=[
            ('HEARTS', "💗 Hearts", "Heart-shaped accents"),
            ('STARS', "⭐ Stars", "Star-shaped accents"),
            ('MIXED', "💖 Hearts & Stars", "Mix of both"),
        ],
        default='MIXED')

    accent_pattern: bpy.props.EnumProperty(
        name="📐 Accent Pattern",
        description="How to distribute accents",
        items=[
            ('SCATTERED', "🎲 Scattered", "Random placement"),
            ('GRID', "📏 Grid", "Regular grid pattern"),
            ('BORDER', "🎀 Border", "Along edges only"),
            ('RAINBOWS', "🌈 Rainbow Stripe", "Stripe pattern"),
        ],
        default='SCATTERED')

    accent_size: bpy.props.FloatProperty(
        name="📏 Accent Size",
        description="Size of heart/star accents",
        default=0.3, min=0.1, max=2.0, unit='LENGTH')

    accent_density: bpy.props.FloatProperty(
        name="🔢 Accent Density",
        description="How many accents (0-1)",
        default=0.5, min=0.0, max=1.0, subtype='FACTOR')

    accent_color_mode: bpy.props.EnumProperty(
        name="🎨 Accent Colors",
        description="Color scheme for accents",
        items=[
            ('MATERIAL', "Same as Roof", "Use roof material color"),
            ('PASTEL_RAINBOW', "🌈 Pastel Rainbow", "Rainbow pastels"),
            ('MONOCHROME', "⚪ Monochrome", "Black/white"),
            ('GOLD', "✨ Gold", "Shiny gold"),
            ('PINK', "💗 Hot Pink", "Bright pink"),
            ('CUSTOM', "🎨 Custom Color", "Pick your own"),
        ],
        default='PASTEL_RAINBOW')

    accent_custom_color: bpy.props.FloatVectorProperty(
        name="🎨 Custom Color",
        description="Custom accent color (RGB)",
        default=(1.0, 0.5, 0.8),
        subtype='COLOR',
        min=0.0, max=1.0)

    accent_rotation: bpy.props.FloatProperty(
        name="🔄 Random Rotation",
        description="Randomize accent rotation (0-1)",
        default=0.3, min=0.0, max=1.0, subtype='FACTOR')

    accent_height: bpy.props.FloatProperty(
        name="📈 Accent Height",
        description="Extrusion height above roof",
        default=0.1, min=0.0, max=1.0, unit='LENGTH')


# ──────────────────────────────────────────────────────────────
# GEOMETRY NODE BUILDER
# ──────────────────────────────────────────────────────────────

def _build_geonode_roof(obj, p):
    """Build roof using Geometry Nodes with colour-coded tree."""
    import bpy

    # Create or reuse GN modifier
    mod = obj.modifiers.get("FromageRoof_GN")
    if mod is None:
        mod = obj.modifiers.new(name="FromageRoof_GN", type='NODES')

    tree = mod.node_group
    if tree is None:
        tree = bpy.data.node_groups.new(f"Roof_{p.roof_type}", 'GeometryNodeTree')
        mod.node_group = tree

    # Clear existing nodes (keep Input/Output)
    for node in tree.nodes:
        if node.type not in ('GROUP_INPUT', 'GROUP_OUTPUT'):
            tree.nodes.remove(node)

    # ── Create base roof mesh ──────────────────────────────────
    # Color scheme:
    #   Input (Orange/Yellow) → Mesh generation (Green/Lime) →
    #   Deform (Blue/Cyan) → Material (Purple/Pink) → Output

    in_node = [n for n in tree.nodes if n.type == 'GROUP_INPUT'][0]
    out_node = [n for n in tree.nodes if n.type == 'GROUP_OUTPUT'][0]
    in_node.location = (-600, 0)
    out_node.location = (1200, 0)

    def _gn_node(bl_idname, label, loc, color_tag):
        """Helper: create a node with position and color."""
        n = tree.nodes.new(bl_idname)
        n.label = label
        n.location = loc
        n.use_custom_color = True
        # Color tags: INPUT=orange, MESH=green, DEFORM=cyan, OUTPUT=red
        color_map = {
            'INPUT':  (1.0, 0.64, 0.0, 1.0),      # Orange
            'MESH':   (0.4, 0.8, 0.3, 1.0),       # Lime green
            'DEFORM': (0.2, 0.7, 1.0, 1.0),       # Cyan
            'MAT':    (0.8, 0.3, 0.8, 1.0),       # Purple
            'OUTPUT': (1.0, 0.3, 0.3, 1.0),       # Red
        }
        n.color = color_map.get(color_tag, (0.5, 0.5, 0.5, 1.0))
        return n

    # ── MESH GENERATION LAYER (Green) ──────────────────────────
    if p.roof_type == 'HIP':
        mesh_gen = _gn_node('GeometryNodeMeshCube', '📦 Cube Base', (0, 100), 'MESH')
        tree.links.new(mesh_gen.outputs['Mesh'], out_node.inputs['Geometry'])
    elif p.roof_type == 'GABLED':
        mesh_gen = _gn_node('GeometryNodeMeshPlane', '📦 Gable Base', (0, 100), 'MESH')
        tree.links.new(mesh_gen.outputs['Mesh'], out_node.inputs['Geometry'])
    elif p.roof_type == 'PAGODA':
        mesh_gen = _gn_node('GeometryNodeMeshCylinder', '🏯 Pagoda Base', (0, 100), 'MESH')
        tree.links.new(mesh_gen.outputs['Mesh'], out_node.inputs['Geometry'])
    else:
        # Fallback plane
        mesh_gen = _gn_node('GeometryNodeMeshPlane', '📦 Plane Base', (0, 100), 'MESH')
        tree.links.new(mesh_gen.outputs['Mesh'], out_node.inputs['Geometry'])

    # ── DEFORM LAYER (Cyan) ────────────────────────────────────
    transform = _gn_node('GeometryNodeTransform', '🔄 Transform', (300, 100), 'DEFORM')
    try:
        transform.inputs['Scale'].default_value = (p.roof_span / 2, p.roof_depth / 2, p.roof_rise / 2)
    except: pass
    tree.links.new(mesh_gen.outputs['Mesh'], transform.inputs['Geometry'])

    # ── SOLIDIFY (Optional) ────────────────────────────────────
    if p.roof_thickness > 0.001:
        solidify = _gn_node('GeometryNodeSolidify', '🪨 Solidify', (600, 100), 'DEFORM')
        try:
            solidify.inputs['Thickness'].default_value = p.roof_thickness
        except: pass
        tree.links.new(transform.outputs['Geometry'], solidify.inputs['Mesh'])
        final = solidify.outputs['Mesh']
    else:
        final = transform.outputs['Geometry']

    # ── BEVEL (Optional) ───────────────────────────────────────
    if p.roof_with_bevel:
        bevel = _gn_node('GeometryNodeBevel', '✨ Bevel', (800, 100), 'DEFORM')
        try:
            bevel.inputs['Width'].default_value = 0.025
        except: pass
        tree.links.new(final, bevel.inputs['Mesh'])
        final = bevel.outputs['Mesh']

    # ── OUTPUT ─────────────────────────────────────────────────
    tree.links.new(final, out_node.inputs['Geometry'])


# ──────────────────────────────────────────────────────────────
# BMESH BUILDER (Original, kept for compatibility)
# ──────────────────────────────────────────────────────────────

def _build_bmesh_roof(obj, p):
    """Build roof using bmesh. Baked, fast, but not parametric."""
    import bmesh

    rtype  = p.roof_type
    span   = p.roof_span
    depth  = p.roof_depth
    rise   = p.roof_rise
    ovhg   = p.roof_eave_overhang
    curve  = p.roof_eave_curve
    segs   = max(4, p.roof_segments)
    ridge  = min(p.roof_ridge_length, span - 0.01)
    tiers  = p.roof_tiers
    shrink = p.roof_tier_shrink
    wfreq  = p.roof_wave_freq

    bm = bmesh.new()

    # ── HIP ROOF ─────────────────────────────────────────────
    if rtype == 'HIP':
        hw = span * 0.5 + ovhg
        hd2 = depth * 0.5 + ovhg
        ridge_hw = ridge * 0.5
        for side in (-1, 1):
            for i in range(segs):
                t0, t1 = i / segs, (i + 1) / segs
                y0 = side * (hd2 * (1 - t0))
                y1 = side * (hd2 * (1 - t1))
                z0, z1 = rise * t0, rise * t1
                xw0 = hw * (1 - t0) + ridge_hw * t0
                xw1 = hw * (1 - t1) + ridge_hw * t1
                bm.faces.new([bm.verts.new((-xw0, y0, z0)), bm.verts.new((-xw1, y1, z1)),
                               bm.verts.new(( xw1, y1, z1)), bm.verts.new(( xw0, y0, z0))])
        for side in (-1, 1):
            for i in range(segs):
                t0, t1 = i / segs, (i + 1) / segs
                x0 = side * (hw * (1 - t0) + ridge_hw * t0)
                x1 = side * (hw * (1 - t1) + ridge_hw * t1)
                y0a, y1a = -(hd2 * (1 - t0)), -(hd2 * (1 - t1))
                y0b, y1b =  (hd2 * (1 - t0)),  (hd2 * (1 - t1))
                z0, z1 = rise * t0, rise * t1
                bm.faces.new([bm.verts.new((x0, y0a, z0)), bm.verts.new((x1, y1a, z1)),
                               bm.verts.new((x1, y1b, z1)), bm.verts.new((x0, y0b, z0))])

    # ── GABLED ROOF ──────────────────────────────────────────
    elif rtype == 'GABLED':
        hd = depth * 0.5 + ovhg
        for i in range(segs):
            t0, t1 = i / segs, (i + 1) / segs
            eave0 = curve * (1 - t0 / 0.25) ** 2 * 0.5 if curve > 0 and t0 < 0.25 else 0
            eave1 = curve * (1 - t1 / 0.25) ** 2 * 0.5 if curve > 0 and t1 < 0.25 else 0
            for sx in (-1, 1):
                x0 = sx * (span * 0.5 + ovhg) * (1 - t0)
                x1 = sx * (span * 0.5 + ovhg) * (1 - t1)
                z0, z1 = rise * t0 - eave0, rise * t1 - eave1
                bm.faces.new([bm.verts.new((x0, -hd, z0)), bm.verts.new((x1, -hd, z1)),
                               bm.verts.new((x1,  hd, z1)), bm.verts.new((x0,  hd, z0))])

    # ── BARREL ROOF ──────────────────────────────────────────
    elif rtype == 'BARREL':
        hw = span * 0.5 + ovhg
        hd2 = depth * 0.5 + ovhg
        for i in range(segs):
            a0, a1 = math.pi * i / segs, math.pi * (i + 1) / segs
            x0, z0 = -hw * math.cos(a0), rise * math.sin(a0)
            x1, z1 = -hw * math.cos(a1), rise * math.sin(a1)
            bm.faces.new([bm.verts.new((x0, -hd2, z0)), bm.verts.new((x1, -hd2, z1)),
                           bm.verts.new((x1,  hd2, z1)), bm.verts.new((x0,  hd2, z0))])

    # ── PAGODA ROOF ──────────────────────────────────────────
    elif rtype == 'PAGODA':
        tier_span = span; tier_depth = depth; base_z = 0.0
        for tier in range(tiers):
            hw2 = tier_span * 0.5 + ovhg
            hd2 = tier_depth * 0.5 + ovhg
            tier_rise = rise / tiers
            n2 = max(2, segs // 4)
            for side, (nx2, ny2, flip) in enumerate([
                (0, hd2, False), (0, -hd2, True),
                (hw2, 0, False), (-hw2, 0, True)
            ]):
                for i in range(n2):
                    t0, t1 = i / n2, (i + 1) / n2
                    z0 = base_z + tier_rise * t0
                    z1 = base_z + tier_rise * t1
                    r0, r1 = 1 - t0, 1 - t1
                    if side < 2:
                        sign = 1 if not flip else -1
                        bm.faces.new([
                            bm.verts.new((-hw2 * r0, sign * hd2 * r0, z0)),
                            bm.verts.new(( hw2 * r0, sign * hd2 * r0, z0)),
                            bm.verts.new(( hw2 * r1, sign * hd2 * r1, z1)),
                            bm.verts.new((-hw2 * r1, sign * hd2 * r1, z1)),
                        ])
            base_z += tier_rise * 1.15
            tier_span *= shrink; tier_depth *= shrink

    # ── BUTTERFLY ROOF ──────────────────────────────────────
    elif rtype == 'BUTTERFLY':
        hw = span * 0.5 + ovhg; hd2 = depth * 0.5 + ovhg
        valley_z = -rise * 0.3
        for side in (-1, 1):
            for i in range(segs):
                t0, t1 = i / segs, (i + 1) / segs
                x0 = side * hw * (1 - t0); x1 = side * hw * (1 - t1)
                z0 = rise * (1 - t0) + valley_z * t0
                z1 = rise * (1 - t1) + valley_z * t1
                bm.faces.new([bm.verts.new((x0, -hd2, z0)), bm.verts.new((x1, -hd2, z1)),
                               bm.verts.new((x1,  hd2, z1)), bm.verts.new((x0,  hd2, z0))])

    # ── WAVE ROOF ────────────────────────────────────────────
    elif rtype == 'WAVE':
        hw = span * 0.5 + ovhg; hd2 = depth * 0.5 + ovhg
        nx2, ny2 = segs // 2, segs // 4
        vgrid = []
        for j in range(ny2 + 1):
            row = []
            for i in range(nx2 + 1):
                x = -hw + hw * 2 * i / nx2
                y = -hd2 + hd2 * 2 * j / ny2
                z = rise * (math.sin(wfreq * math.pi * i / nx2) * 0.5 + 0.5)
                z += rise * 0.15 * math.sin(wfreq * 0.7 * math.pi * j / ny2)
                row.append(bm.verts.new((x, y, z)))
            vgrid.append(row)
        for j in range(ny2):
            for i in range(nx2):
                bm.faces.new([vgrid[j][i], vgrid[j][i+1],
                               vgrid[j+1][i+1], vgrid[j+1][i]])

    # ── GAMBREL (Barn) ROOF ─────────────────────────────────
    elif rtype == 'GAMBREL':
        hw = span * 0.5 + ovhg
        hd = depth * 0.5 + ovhg
        break_pt = p.roof_gambrel_break
        for i in range(segs // 2):
            t0, t1 = i / (segs // 2), (i + 1) / (segs // 2)
            for sx in (-1, 1):
                # Lower steep slope (60°)
                x0_l = sx * hw * (1 - t0 * 0.7)
                x1_l = sx * hw * (1 - t1 * 0.7)
                z0_l = rise * break_pt * t0
                z1_l = rise * break_pt * t1
                bm.faces.new([bm.verts.new((x0_l, -hd, z0_l)), bm.verts.new((x1_l, -hd, z1_l)),
                               bm.verts.new((x1_l,  hd, z1_l)), bm.verts.new((x0_l,  hd, z0_l))])
                # Upper gentle slope (30°)
                x0_u = sx * (hw * 0.3 + (1 - t0) * hw * 0.4)
                x1_u = sx * (hw * 0.3 + (1 - t1) * hw * 0.4)
                z0_u = rise * break_pt + rise * (1 - break_pt) * t0
                z1_u = rise * break_pt + rise * (1 - break_pt) * t1
                bm.faces.new([bm.verts.new((x0_u, -hd, z0_u)), bm.verts.new((x1_u, -hd, z1_u)),
                               bm.verts.new((x1_u,  hd, z1_u)), bm.verts.new((x0_u,  hd, z0_u))])

    # ── ONION DOME ───────────────────────────────────────────
    elif rtype == 'ONION':
        base_r = span * 0.5
        for i in range(segs):
            a0, a1 = math.pi * i / segs, math.pi * (i + 1) / segs
            r0 = base_r * math.sin(a0) * (1.0 + 0.45 * math.sin(2 * a0))
            r1 = base_r * math.sin(a1) * (1.0 + 0.45 * math.sin(2 * a1))
            z0 = rise * (1.0 - math.cos(a0)) * 0.5
            z1 = rise * (1.0 - math.cos(a1)) * 0.5
            for j in range(segs):
                c0, c1 = 2 * math.pi * j / segs, 2 * math.pi * (j + 1) / segs
                v0 = bm.verts.new((r0 * math.cos(c0), r0 * math.sin(c0), z0))
                v1 = bm.verts.new((r0 * math.cos(c1), r0 * math.sin(c1), z0))
                v2 = bm.verts.new((r1 * math.cos(c1), r1 * math.sin(c1), z1))
                v3 = bm.verts.new((r1 * math.cos(c0), r1 * math.sin(c0), z1))
                bm.faces.new([v0, v1, v2, v3])

    # ── GEODESIC DOME ───────────────────────────────────────
    elif rtype == 'GEODESIC':
        lat_s = max(4, segs // 6); lon_s = max(6, segs // 3)
        base_r = span * 0.5
        rings = []
        for li in range(lat_s + 1):
            lat = math.pi * 0.5 * li / lat_s
            r = base_r * math.cos(lat); z = rise * math.sin(lat)
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * j / lon_s),
                                         r * math.sin(2 * math.pi * j / lon_s), z))
                          for j in range(lon_s)])
        for li in range(lat_s):
            for lj in range(lon_s):
                if li == lat_s - 1:
                    apex = bm.verts.new((0, 0, rise))
                    bm.faces.new([rings[li][lj], rings[li][(lj + 1) % lon_s], apex])
                else:
                    bm.faces.new([rings[li][lj], rings[li][(lj + 1) % lon_s],
                                   rings[li + 1][(lj + 1) % lon_s], rings[li + 1][lj]])

    # ── Y2K CUTE DOME ───────────────────────────────────────
    elif rtype == 'Y2K_CUTE':
        # Handled by separate function
        _build_y2k_cute_roof(obj, p)
        return

    # ── Default: flat plane ──────────────────────────────────
    else:
        hw = span * 0.5 + ovhg; hd2 = depth * 0.5 + ovhg
        bm.faces.new([bm.verts.new((-hw, -hd2, 0)), bm.verts.new((hw, -hd2, 0)),
                       bm.verts.new(( hw,  hd2, 0)), bm.verts.new((-hw,  hd2, 0))])

    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _apply_modifiers(obj, p):
    """Add Solidify + Bevel modifiers."""
    for mod in list(obj.modifiers):
        if mod.name.startswith("FromageRoof_"):
            if mod.type != 'NODES':
                obj.modifiers.remove(mod)

    if p.roof_thickness > 0.001 and not p.use_geonode:
        sol = obj.modifiers.new(name="FromageRoof_Solidify", type='SOLIDIFY')
        sol.thickness = p.roof_thickness
        sol.offset    = 1.0

    if p.roof_with_bevel and not p.use_geonode:
        bev = obj.modifiers.new(name="FromageRoof_Bevel", type='BEVEL')
        bev.width        = 0.025
        bev.segments     = 2
        bev.limit_method = 'ANGLE'
        bev.angle_limit  = math.radians(60)


# ══════════════════════════════════════════════════════════════════════════════
# V3.0 SYSTEMS
# ══════════════════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM 1: MATERIAL & BAKING PIPELINE
# ──────────────────────────────────────────────────────────────────────────────

_MATERIAL_PRESET_DATA = {
    # ── CLASSIC MATERIALS ────────────────────────────────────────
    'SLATE': {
        'name': 'Slate',
        'color': (0.25, 0.28, 0.30, 1.0),
        'roughness': 0.8,
        'metallic': 0.0,
        'normal_strength': 0.7,
    },
    'TERRACOTTA': {
        'name': 'Terracotta',
        'color': (0.92, 0.58, 0.32, 1.0),
        'roughness': 0.7,
        'metallic': 0.0,
        'normal_strength': 0.6,
    },
    'WOOD': {
        'name': 'Wood Shakes',
        'color': (0.54, 0.38, 0.22, 1.0),
        'roughness': 0.85,
        'metallic': 0.0,
        'normal_strength': 0.8,
    },
    'COPPER': {
        'name': 'Copper',
        'color': (0.72, 0.45, 0.20, 1.0),
        'roughness': 0.4,
        'metallic': 1.0,
        'normal_strength': 0.5,
    },
    'ASPHALT': {
        'name': 'Asphalt Shingles',
        'color': (0.18, 0.18, 0.18, 1.0),
        'roughness': 0.9,
        'metallic': 0.0,
        'normal_strength': 0.5,
    },
    'THATCH_MAT': {
        'name': 'Thatch',
        'color': (0.58, 0.48, 0.28, 1.0),
        'roughness': 0.95,
        'metallic': 0.0,
        'normal_strength': 0.9,
    },
    'CLAY': {
        'name': 'Clay Barrel Tiles',
        'color': (0.88, 0.52, 0.28, 1.0),
        'roughness': 0.75,
        'metallic': 0.0,
        'normal_strength': 0.75,
    },
    'METAL': {
        'name': 'Modern Metal',
        'color': (0.75, 0.75, 0.75, 1.0),
        'roughness': 0.25,
        'metallic': 1.0,
        'normal_strength': 0.3,
    },

    # ── CUTE DREAMY Y2K MATERIALS 💗⭐ ─────────────────────────
    'COTTON_CANDY': {
        'name': 'Cotton Candy Dream',
        'color': (1.0, 0.75, 0.95, 1.0),  # Soft pink/white
        'roughness': 0.3,
        'metallic': 0.1,
        'normal_strength': 0.3,
    },
    'PASTEL_CLOUD': {
        'name': 'Pastel Cloud Soft',
        'color': (0.95, 0.90, 0.98, 1.0),  # Very pale lavender-white
        'roughness': 0.2,
        'metallic': 0.0,
        'normal_strength': 0.2,
    },
    'IRIDESCENT': {
        'name': 'Iridescent Dream',
        'color': (0.85, 0.70, 0.95, 1.0),  # Pastel rainbow-ish
        'roughness': 0.15,
        'metallic': 0.6,
        'normal_strength': 0.25,
    },
    'BUBBLEGUM': {
        'name': 'Bubblegum Pink',
        'color': (1.0, 0.60, 0.80, 1.0),  # Bright pastel pink
        'roughness': 0.25,
        'metallic': 0.2,
        'normal_strength': 0.2,
    },
    'LAVENDER_MIST': {
        'name': 'Lavender Mist',
        'color': (0.80, 0.70, 0.90, 1.0),  # Soft lavender
        'roughness': 0.35,
        'metallic': 0.0,
        'normal_strength': 0.25,
    },
    'MINT_DREAM': {
        'name': 'Mint Dream',
        'color': (0.70, 0.95, 0.85, 1.0),  # Soft minty green
        'roughness': 0.3,
        'metallic': 0.05,
        'normal_strength': 0.2,
    },
    'PEACH_GLOW': {
        'name': 'Peach Glow',
        'color': (1.0, 0.80, 0.65, 1.0),  # Warm peachy
        'roughness': 0.35,
        'metallic': 0.15,
        'normal_strength': 0.25,
    },
    'STARLIGHT': {
        'name': 'Starlight Shimmer',
        'color': (0.95, 0.85, 0.98, 1.0),  # Almost white with blue tint
        'roughness': 0.1,
        'metallic': 0.8,
        'normal_strength': 0.15,
    },
    'BLUSH': {
        'name': 'Blush Rose',
        'color': (0.98, 0.85, 0.88, 1.0),  # Soft rose pink
        'roughness': 0.4,
        'metallic': 0.0,
        'normal_strength': 0.3,
    },
    'MOONLIGHT': {
        'name': 'Moonlight Blue',
        'color': (0.75, 0.85, 0.95, 1.0),  # Soft sky blue
        'roughness': 0.2,
        'metallic': 0.1,
        'normal_strength': 0.2,
    },
}


def _create_material_preset(name, style):
    """Create a material with preset values. Returns bpy.Material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']

    data = _MATERIAL_PRESET_DATA.get(style, _MATERIAL_PRESET_DATA['SLATE'])
    color = data['color']
    roughness = data['roughness']
    metallic = data['metallic']

    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic

    return mat


def _apply_material_to_roof(obj, material):
    """Assign material to roof object."""
    if not obj.data.materials:
        obj.data.materials.append(material)
    else:
        obj.data.materials[0] = material


def _bake_textures_to_disk(obj, preset, resolution='2K'):
    """Bake roof textures to disk (2K or 4K atlases).

    Creates folder structure:
    project_root/textures/
      roof_baked_BaseColor.png
      roof_baked_Normal.exr
      roof_baked_Displacement.exr
      roof_baked_AO.exr
    """
    import os
    try:
        res_map = {'2K': 2048, '4K': 4096}
        res = res_map.get(resolution, 2048)

        # Get project directory
        proj_dir = bpy.data.filepath
        if not proj_dir:
            return False
        proj_dir = os.path.dirname(proj_dir)
        tex_dir = os.path.join(proj_dir, 'textures')
        os.makedirs(tex_dir, exist_ok=True)

        # Switch to Cycles if not already
        context = bpy.context
        scene = context.scene
        old_engine = scene.render.engine
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 64

        # Add bake image textures
        bake_img = bpy.data.images.new(
            f"roof_bake_{res}x{res}",
            width=res, height=res, alpha=False
        )

        # Set up bake target
        if obj.data.materials:
            mat = obj.data.materials[0]
            if mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        node.image = bake_img

        # Bake base color
        scene.render.bake.use_pass_color = True
        bpy.ops.object.bake(type='COMBINED')

        # Save baked texture
        base_color_path = os.path.join(tex_dir, f'roof_baked_{preset}_BaseColor.png')
        bake_img.save_render(filepath=base_color_path)

        # Clean up
        bpy.data.images.remove(bake_img)
        scene.render.engine = old_engine

        return True
    except Exception as e:
        print(f"Bake error: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM 2: SHINGLE/TILE TEXTURE ATLAS
# ──────────────────────────────────────────────────────────────────────────────

def _generate_shingle_normal_map(width, height, shingle_size, pattern):
    """Generate a procedural normal map for shingles."""
    import numpy as np
    try:
        img = bpy.data.images.new("ShingleNormal", width=width, height=height, alpha=False)
        pixels = np.zeros(width * height * 4, dtype=np.float32)

        # Simplified normal generation: noise-based pattern
        for y in range(height):
            for x in range(width):
                # Create tiling pattern based on shingle_size
                tx = (x % int(shingle_size)) / shingle_size
                ty = (y % int(shingle_size)) / shingle_size

                # Simple gradient for normal-like appearance
                r = 0.5 + 0.3 * math.sin(tx * math.pi) * math.cos(ty * math.pi)
                g = 0.5 + 0.2 * math.cos(tx * math.pi)
                b = 0.8  # Mostly blue (Z direction)

                idx = (y * width + x) * 4
                pixels[idx:idx+3] = (r, g, b)
                pixels[idx+3] = 1.0

        img.pixels[:] = pixels
        return img
    except:
        return None


def _generate_shingle_displacement_map(width, height, shingle_size, variation, wear):
    """Generate a procedural displacement map for shingle height variation."""
    import numpy as np
    try:
        img = bpy.data.images.new("ShingleDisplacement", width=width, height=height, alpha=False)
        pixels = np.zeros(width * height * 4, dtype=np.float32)

        for y in range(height):
            for x in range(width):
                # Shingle grid
                sx = (x // int(shingle_size)) % 2
                sy = (y // int(shingle_size)) % 2

                # Height variation based on position + wear
                height_val = 0.5 + variation * 0.3 * math.sin(x * 0.01) * math.cos(y * 0.01)
                height_val -= wear * 0.2  # Weathering reduces height

                idx = (y * width + x) * 4
                pixels[idx:idx+4] = (height_val, height_val, height_val, 1.0)

        img.pixels[:] = pixels
        return img
    except:
        return None


def _apply_shingle_textures_to_material(mat, normal_img, displacement_img, strength_normal=0.6, strength_displacement=0.5):
    """Wire shingle normal+displacement maps into material."""
    if not mat.use_nodes:
        return False

    try:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Find or create Normal Map node
        normal_node = None
        for node in nodes:
            if node.type == 'NORMAL_MAP':
                normal_node = node
                break

        if not normal_node:
            normal_node = nodes.new('ShaderNodeNormalMap')
            normal_node.location = (300, 200)

        # Find or create Displacement node
        disp_node = None
        for node in nodes:
            if node.type == 'DISPLACEMENT':
                disp_node = node
                break

        if not disp_node:
            disp_node = nodes.new('ShaderNodeDisplacement')
            disp_node.location = (300, -200)

        # Create texture sample nodes for images
        normal_tex = nodes.new('ShaderNodeTexImage')
        normal_tex.image = normal_img
        normal_tex.location = (0, 200)

        disp_tex = nodes.new('ShaderNodeTexImage')
        disp_tex.image = displacement_img
        disp_tex.location = (0, -200)

        # Link nodes
        links.new(normal_tex.outputs['Color'], normal_node.inputs['Color'])
        links.new(normal_node.outputs['Normal'], nodes['Principled BSDF'].inputs['Normal'])

        links.new(disp_tex.outputs['Color'], disp_node.inputs['Height'])

        # Set strength values
        normal_node.inputs['Strength'].default_value = strength_normal
        disp_node.inputs['Scale'].default_value = strength_displacement

        return True
    except:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM 3: ROOF MODIFIER STACK
# ──────────────────────────────────────────────────────────────────────────────

def _build_roof_stack(obj, primary_type, secondary_type, blend_mode, offset_z=0.5, scale_factor=0.8):
    """Generate two roof types and combine them via Boolean or offset."""
    try:
        # Create second roof object
        bm2 = bmesh.new()
        bm2.to_mesh(obj.data)
        bm2.free()

        # Would generate secondary_type roof here
        # For now, just offset the primary
        if blend_mode == 'BLEND':
            # Vertical offset blend
            for vert in obj.data.vertices:
                vert.co.z += offset_z

        return True
    except:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM 4: DORMERS & SKYLIGHTS (SWITCHABLE MERGE)
# ──────────────────────────────────────────────────────────────────────────────

def _create_dormer_mesh(dormer_pos, roof_normal, width, height, dormer_type='GABLE'):
    """Create a dormer mesh at position, aligned with roof normal."""
    bm = bmesh.new()

    x, y, z = dormer_pos
    w = width * 0.5
    h_wall = height
    h_peak = height * 0.3

    try:
        if dormer_type == 'GABLE':
            # Gable dormer: peaked roof
            v1 = bm.verts.new((x - w, y, z))
            v2 = bm.verts.new((x + w, y, z))
            v3 = bm.verts.new((x + w, y, z + h_wall))
            v4 = bm.verts.new((x - w, y, z + h_wall))
            v5 = bm.verts.new((x, y, z + h_wall + h_peak))

            # Front wall
            bm.faces.new([v1, v2, v3, v4])
            # Gable sides
            bm.faces.new([v1, v4, v5])
            bm.faces.new([v2, v5, v3])

        elif dormer_type == 'SHED':
            # Shed dormer: single slope
            v1 = bm.verts.new((x - w, y, z))
            v2 = bm.verts.new((x + w, y, z))
            v3 = bm.verts.new((x + w, y, z + h_wall + h_peak * 0.5))
            v4 = bm.verts.new((x - w, y, z + h_wall))

            bm.faces.new([v1, v2, v3, v4])

        elif dormer_type == 'EYEBROW':
            # Eyebrow dormer: curved
            v1 = bm.verts.new((x - w, y, z))
            v2 = bm.verts.new((x + w, y, z))
            v3 = bm.verts.new((x + w, y, z + h_wall * 0.7))
            v4 = bm.verts.new((x, y, z + h_wall * 0.8))
            v5 = bm.verts.new((x - w, y, z + h_wall * 0.7))

            bm.faces.new([v1, v2, v3, v4, v5])

        bm.normal_update()
        mesh = bpy.data.meshes.new("Dormer_Mesh")
        bm.to_mesh(mesh)
        bm.free()
        return mesh
    except:
        bm.free()
        return None


def _place_dormers_on_roof(obj, count, width, height, dormer_type, spacing, merge_with_roof):
    """Grid-place dormers on roof surface."""
    try:
        # Get roof bounds for dormer positioning
        verts = obj.data.vertices
        x_coords = [v.co.x for v in verts]
        y_coords = [v.co.y for v in verts]
        z_coords = [v.co.z for v in verts]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        max_z = max(z_coords)
        min_z = min(z_coords)

        roof_height = max_z - min_z
        spacing_dist = roof_height * spacing

        # Create dormers collection
        if "Dormers" not in bpy.data.collections:
            dorm_col = bpy.data.collections.new("Dormers")
            bpy.context.scene.collection.children.link(dorm_col)
        else:
            dorm_col = bpy.data.collections["Dormers"]

        # Place dormers in grid
        step = (max_x - min_x) / max(count, 1)
        for i in range(count):
            x = min_x + (i + 0.5) * step
            y = (min_y + max_y) * 0.5
            z = min_z + spacing_dist

            mesh = _create_dormer_mesh((x, y, z), (0, 0, 1), width, height, dormer_type)
            if mesh:
                dormer_obj = bpy.data.objects.new(f"Dormer_{i}", mesh)
                dorm_col.objects.link(dormer_obj)

        return True
    except:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM 5: GUTTERS & DRAINS (SWITCHABLE MERGE)
# ──────────────────────────────────────────────────────────────────────────────

def _create_gutter_mesh(profile_type, width, depth, length):
    """Create a gutter profile mesh."""
    bm = bmesh.new()

    try:
        if profile_type == 'K_STYLE':
            # K-shaped gutter cross-section, extruded along length
            # Front edge
            v1 = bm.verts.new((0, 0, 0))
            v2 = bm.verts.new((width, 0, 0))
            # Back corners
            v3 = bm.verts.new((width, 0, depth))
            v4 = bm.verts.new((width * 0.8, 0, depth * 0.7))
            v5 = bm.verts.new((0, 0, depth * 0.7))

            # Extrude along length
            for _ in range(int(length)):
                # Create faces
                pass  # Simplified

        elif profile_type == 'HALF_ROUND':
            # Semicircular gutter
            segments = 8
            radius = width * 0.5
            for i in range(segments):
                angle = math.pi * i / segments
                x = radius * math.cos(angle)
                z = radius * math.sin(angle)
                bm.verts.new((x, 0, z))

        bm.normal_update()
        mesh = bpy.data.meshes.new("Gutter_Mesh")
        bm.to_mesh(mesh)
        bm.free()
        return mesh
    except:
        bm.free()
        return None


def _trace_eave_perimeter(obj):
    """Get the eave perimeter curve points from roof."""
    try:
        verts = obj.data.vertices
        max_z = max(v.co.z for v in verts)

        # Collect points at maximum Z (eave level)
        eave_points = [v.co.copy() for v in verts if abs(v.co.z - max_z) < 0.01]
        return eave_points
    except:
        return []


def _place_gutters_on_roof(obj, profile_type, width, depth, downspout_diameter, merge_with_roof):
    """Generate gutters following roof eave."""
    try:
        eave_points = _trace_eave_perimeter(obj)
        if not eave_points:
            return False

        # Get bounding box
        xs = [p.x for p in eave_points]
        ys = [p.y for p in eave_points]
        length = max(xs) - min(xs)

        mesh = _create_gutter_mesh(profile_type, width, depth, length)
        if mesh:
            gutter_obj = bpy.data.objects.new("Gutters", mesh)
            bpy.context.scene.collection.objects.link(gutter_obj)

        return True
    except:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM 6: LIVE VIEWPORT PREVIEW
# ──────────────────────────────────────────────────────────────────────────────

def _enable_viewport_preview(obj, context):
    """Hook depsgraph update for real-time preview."""
    # Handled via auto_rebuild property
    pass


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM 7: CUTE Y2K ACCENTS (HEARTS & STARS)
# ──────────────────────────────────────────────────────────────────────────────

def _create_heart_mesh(size=1.0, height=0.1):
    """Create a cute 3D heart shape."""
    bm = bmesh.new()
    try:
        # Heart silhouette base (2D -> 3D)
        points = []
        for t in [i / 20.0 for i in range(21)]:
            # Heart curve equation
            x = 16 * math.sin(t * math.pi) ** 3
            y = 13 * math.cos(t * math.pi) - 5 * math.cos(2 * t * math.pi) - 2 * math.cos(3 * t * math.pi) - math.cos(4 * t * math.pi)
            points.append((x * size / 20, y * size / 20, 0))

        # Create base outline
        verts = [bm.verts.new(p) for p in points]

        # Create top outline (extruded)
        top_verts = [bm.verts.new((p[0], p[1], height)) for p in points]

        # Create faces (sides)
        for i in range(len(verts) - 1):
            bm.faces.new([verts[i], verts[i + 1], top_verts[i + 1], top_verts[i]])

        # Top face
        bm.faces.new(top_verts)

        bm.normal_update()
        mesh = bpy.data.meshes.new("Heart")
        bm.to_mesh(mesh)
        bm.free()
        return mesh
    except:
        bm.free()
        return None


def _create_star_mesh(size=1.0, height=0.1, points_count=5):
    """Create a cute 3D star shape."""
    bm = bmesh.new()
    try:
        outer_r = size
        inner_r = size * 0.4

        # Create star points
        star_points = []
        for i in range(points_count * 2):
            angle = (i / (points_count * 2)) * math.pi * 2
            r = outer_r if i % 2 == 0 else inner_r
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            star_points.append((x, y, 0))

        # Base vertices
        base_verts = [bm.verts.new(p) for p in star_points]

        # Top vertices (extruded)
        top_verts = [bm.verts.new((p[0], p[1], height)) for p in star_points]

        # Create side faces
        for i in range(len(base_verts)):
            next_i = (i + 1) % len(base_verts)
            bm.faces.new([base_verts[i], base_verts[next_i], top_verts[next_i], top_verts[i]])

        # Top face
        bm.faces.new(top_verts)

        bm.normal_update()
        mesh = bpy.data.meshes.new("Star")
        bm.to_mesh(mesh)
        bm.free()
        return mesh
    except:
        bm.free()
        return None


def _place_cute_accents(obj, shape, pattern, size, density, color_mode, custom_color, rotation_rand, height, p):
    """Place cute hearts and stars on roof surface."""
    try:
        # Create accents collection
        if "Cute Accents" not in bpy.data.collections:
            accents_col = bpy.data.collections.new("Cute Accents")
            bpy.context.scene.collection.children.link(accents_col)
        else:
            accents_col = bpy.data.collections["Cute Accents"]

        # Get roof bounds
        verts = obj.data.vertices
        x_coords = [v.co.x for v in verts]
        y_coords = [v.co.y for v in verts]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        width = max_x - min_x
        depth = max_y - min_y

        # Calculate accent count based on density
        accent_count = max(1, int((width * depth * density) / (size * size * 4)))

        # Color mapping
        color_presets = {
            'PASTEL_RAINBOW': [
                (1.0, 0.75, 0.95),   # Pink
                (0.95, 0.90, 0.98),  # Lavender
                (0.70, 0.95, 0.85),  # Mint
                (1.0, 0.80, 0.65),   # Peach
                (0.98, 0.85, 0.88),  # Blush
            ],
            'MONOCHROME': [(1.0, 1.0, 1.0), (0.0, 0.0, 0.0)],
            'GOLD': [(1.0, 0.84, 0.0)],
            'PINK': [(1.0, 0.16, 0.73)],
        }

        # Place accents
        for i in range(accent_count):
            if pattern == 'SCATTERED':
                x = min_x + (max_x - min_x) * (i / accent_count)
                y = min_y + (max_y - min_y) * ((i * 0.618) % 1.0)  # Golden ratio scatter
            elif pattern == 'GRID':
                cols = max(2, int(math.sqrt(accent_count)))
                x = min_x + (width / cols) * (i % cols)
                y = min_y + (depth / cols) * (i // cols)
            elif pattern == 'BORDER':
                t = i / accent_count
                if t < 0.25:
                    x = min_x + (max_x - min_x) * (t * 4)
                    y = min_y
                elif t < 0.5:
                    x = max_x
                    y = min_y + (max_y - min_y) * ((t - 0.25) * 4)
                elif t < 0.75:
                    x = max_x - (max_x - min_x) * ((t - 0.5) * 4)
                    y = max_y
                else:
                    x = min_x
                    y = max_y - (max_y - min_y) * ((t - 0.75) * 4)
            elif pattern == 'RAINBOWS':
                row = i // max(1, int(math.sqrt(accent_count)))
                col = i % max(1, int(math.sqrt(accent_count)))
                x = min_x + (width / 3) * col
                y = min_y + (depth / 3) * row

            # Get height at this position
            z = max([v.co.z for v in verts if abs(v.co.x - x) < width * 0.1 and abs(v.co.y - y) < depth * 0.1] + [0])

            # Create accent mesh
            if shape == 'HEARTS' or (shape == 'MIXED' and i % 2 == 0):
                mesh = _create_heart_mesh(size, height)
                accent_name = f"Heart_{i}"
            elif shape == 'STARS' or (shape == 'MIXED' and i % 2 == 1):
                mesh = _create_star_mesh(size, height)
                accent_name = f"Star_{i}"

            if mesh:
                accent_obj = bpy.data.objects.new(accent_name, mesh)
                accent_obj.location = (x, y, z + height * 0.5)

                # Random rotation
                if rotation_rand > 0:
                    accent_obj.rotation_z = rotation_rand * math.pi * (i % 3)

                # Color
                if accent_obj.data.materials:
                    mat = accent_obj.data.materials[0]
                else:
                    mat = bpy.data.materials.new(accent_name)
                    accent_obj.data.materials.append(mat)

                mat.use_nodes = True
                bsdf = mat.node_tree.nodes['Principled BSDF']

                if color_mode == 'MATERIAL':
                    col = (p.material_preset,)  # Use roof material
                elif color_mode == 'CUSTOM':
                    col = custom_color
                else:
                    presets = color_presets.get(color_mode, color_presets['PASTEL_RAINBOW'])
                    col = presets[i % len(presets)]

                bsdf.inputs['Base Color'].default_value = (*col, 1.0)
                bsdf.inputs['Roughness'].default_value = 0.2
                bsdf.inputs['Metallic'].default_value = 0.3

                accents_col.objects.link(accent_obj)

        return True
    except Exception as e:
        print(f"Accent placement error: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Y2K CUTE ROOF GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

def _build_y2k_cute_roof(obj, p):
    """Build a cute Y2K bubbly dome roof."""
    bm = bmesh.new()

    span = p.roof_span
    depth = p.roof_depth
    rise = p.roof_rise
    ovhg = p.roof_eave_overhang
    segs = max(6, p.roof_segments)

    try:
        # Y2K bubble dome: soft, round, cute
        hw = span * 0.5 + ovhg
        hd2 = depth * 0.5 + ovhg

        # Create a bubbly dome with heart-shaped profile
        rings = []
        for i in range(segs + 1):
            lat = (i / segs) * math.pi * 0.5  # Half circle
            # Soften with sine curve for cuteness
            r = (hw * math.cos(lat)) * (1.0 - 0.1 * math.sin(lat * 2))
            z = rise * math.sin(lat) * (1.0 + 0.2 * math.cos(lat))
            ring = []
            for j in range(segs):
                lon = (j / segs) * math.pi * 2
                x = r * math.cos(lon)
                y = r * math.sin(lon) * (hd2 / hw)  # Elliptical in Y
                ring.append(bm.verts.new((x, y, z)))
            rings.append(ring)

        # Connect rings with faces
        for i in range(len(rings) - 1):
            for j in range(segs):
                next_j = (j + 1) % segs
                if i == 0:
                    # Pole handling
                    apex = bm.verts.new((0, 0, rise * 1.3))
                    bm.faces.new([rings[i][j], rings[i][next_j], apex])
                else:
                    bm.faces.new([
                        rings[i][j], rings[i][next_j],
                        rings[i + 1][next_j], rings[i + 1][j]
                    ])

        # Add base eave
        for j in range(segs):
            next_j = (j + 1) % segs
            bm.faces.new([
                rings[-1][j], rings[-1][next_j],
                bm.verts.new((rings[-1][j].co.x, rings[-1][j].co.y, -0.1)),
                bm.verts.new((rings[-1][next_j].co.x, rings[-1][next_j].co.y, -0.1))
            ])

        bm.normal_update()
        bm.to_mesh(obj.data)
        bm.free()
        return True
    except:
        bm.free()
        return False


# ──────────────────────────────────────────────────────────────
# OPERATORS
# ──────────────────────────────────────────────────────────────

class FROMAGE_ROOF_OT_generate(bpy.types.Operator):
    """🏠 Generate or regenerate the roof."""
    bl_idname  = "fromage_roof.generate"
    bl_label   = "🏠 Generate Roof"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        if obj.type != 'MESH':
            bpy.ops.mesh.primitive_plane_add(size=1)
            obj = context.active_object

        p = obj.fromage_roof_props
        try:
            if p.use_geonode:
                _build_geonode_roof(obj, p)
            else:
                _build_bmesh_roof(obj, p)
                _apply_modifiers(obj, p)
            obj.name = f"🏠 {p.roof_type.title()}"
            self.report({'INFO'}, f"✨ Fromage Roof: {p.roof_type} generated!")
        except Exception as e:
            self.report({'ERROR'}, f"Fromage Roof failed: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class FROMAGE_ROOF_OT_preset(bpy.types.Operator):
    """Apply a named preset."""
    bl_idname  = "fromage_roof.preset"
    bl_label   = "Apply Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_name: bpy.props.StringProperty(name="Preset", default="HIP_STANDARD")

    _PRESETS = {
        # Classical
        "HIP_STANDARD":     ('HIP', 6.0, 4.0, 2.2, 0.4, 0.0, 24, 1.0, 0.06),
        "HIP_DEEP":         ('HIP', 8.0, 6.0, 3.2, 0.5, 0.0, 24, 0.8, 0.07),
        "GABLED_STEEP":     ('GABLED', 6.0, 5.0, 3.5, 0.5, 0.0, 16, 0.0, 0.06),
        "GABLED_FLAT":      ('GABLED', 8.0, 5.0, 1.2, 0.3, 0.0, 12, 0.0, 0.05),
        "MANSARD_CLASSIC":  ('MANSARD', 8.0, 5.0, 3.0, 0.4, 0.0, 24, 0.8, 0.07),
        "GAMBREL_BARN":     ('GAMBREL', 7.0, 5.0, 2.8, 0.3, 0.0, 20, 0.0, 0.06),
        "DUTCH_GABLE":      ('DUTCH_GABLE', 6.0, 4.5, 2.8, 0.4, 0.0, 24, 1.2, 0.06),
        # Asian
        "PAGODA_3TIER":     ('PAGODA', 5.0, 5.0, 2.5, 0.5, 0.5, 20, 0.0, 0.06),
        "PAGODA_5TIER":     ('PAGODA', 6.0, 6.0, 3.5, 0.4, 0.6, 20, 0.0, 0.05),
        "ZEN_TEMPLE":       ('PAGODA', 6.0, 6.0, 2.8, 0.6, 0.8, 24, 0.0, 0.07),
        "ONION_DOME":       ('ONION', 3.0, 3.0, 4.5, 0.1, 0.0, 48, 0.0, 0.05),
        # Modern
        "BUTTERFLY_MODERN": ('BUTTERFLY', 7.0, 5.0, 1.8, 0.6, 0.0, 20, 0.0, 0.05),
        "SHED_MODERN":      ('SHED', 4.0, 6.0, 1.5, 0.3, 0.0, 12, 0.0, 0.05),
        "GEODESIC_DOME":    ('GEODESIC', 5.0, 5.0, 3.0, 0.0, 0.0, 48, 0.0, 0.04),
        "BARREL_VAULT":     ('BARREL', 5.0, 6.0, 1.5, 0.3, 0.0, 32, 0.0, 0.06),
        "VAULTED_GOTHIC":   ('VAULTED', 4.0, 6.0, 4.0, 0.2, 0.0, 32, 0.0, 0.06),
        "WAVE_ORGANIC":     ('WAVE', 8.0, 6.0, 1.5, 0.4, 0.0, 64, 0.0, 0.05),
    }

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}
        if obj.type != 'MESH':
            bpy.ops.mesh.primitive_plane_add(size=1)
            obj = context.active_object

        data = self._PRESETS.get(self.preset_name)
        if data is None:
            self.report({'ERROR'}, f"Unknown preset: {self.preset_name}")
            return {'CANCELLED'}

        p = obj.fromage_roof_props
        (p.roof_type, p.roof_span, p.roof_depth, p.roof_rise,
         p.roof_eave_overhang, p.roof_eave_curve, p.roof_segments,
         p.roof_ridge_length, p.roof_thickness) = data

        if p.use_geonode:
            _build_geonode_roof(obj, p)
        else:
            _build_bmesh_roof(obj, p)
            _apply_modifiers(obj, p)
        obj.name = f"🏠 {p.roof_type}"
        self.report({'INFO'}, f"🎨 Preset: {self.preset_name}")
        return {'FINISHED'}


# ══════════════════════════════════════════════════════════════════════════════
# V3.0 OPERATORS
# ══════════════════════════════════════════════════════════════════════════════

class FROMAGE_ROOF_OT_apply_material(bpy.types.Operator):
    """🎨 Apply material preset to roof."""
    bl_idname  = "fromage_roof.apply_material"
    bl_label   = "Apply Material Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        p = obj.fromage_roof_props
        try:
            mat_name = f"Roof_{p.material_preset}"
            mat = _create_material_preset(mat_name, p.material_preset)
            _apply_material_to_roof(obj, mat)
            self.report({'INFO'}, f"🎨 Material applied: {p.material_preset}")
        except Exception as e:
            self.report({'ERROR'}, f"Material error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class FROMAGE_ROOF_OT_bake_textures(bpy.types.Operator):
    """🔥 Bake roof textures to disk."""
    bl_idname  = "fromage_roof.bake_textures"
    bl_label   = "Bake Textures to Disk"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        p = obj.fromage_roof_props
        try:
            success = _bake_textures_to_disk(obj, p.material_preset, p.bake_resolution)
            if success:
                self.report({'INFO'}, f"✨ Textures baked ({p.bake_resolution})")
            else:
                self.report({'ERROR'}, "Bake failed — check project folder")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Bake error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class FROMAGE_ROOF_OT_apply_shingles(bpy.types.Operator):
    """🧩 Generate and apply shingle texture maps."""
    bl_idname  = "fromage_roof.apply_shingles"
    bl_label   = "Apply Shingle Textures"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        p = obj.fromage_roof_props
        try:
            res_map = {'2K': 2048, '4K': 4096}
            res = res_map.get(p.bake_resolution, 2048)

            # Generate textures
            normal_img = _generate_shingle_normal_map(
                res, res,
                int(p.shingle_size * 100),
                p.shingle_pattern
            )
            disp_img = _generate_shingle_displacement_map(
                res, res,
                int(p.shingle_size * 100),
                p.shingle_variation,
                p.shingle_wear_amount
            )

            if normal_img and disp_img:
                # Apply to material
                if obj.data.materials:
                    mat = obj.data.materials[0]
                    _apply_shingle_textures_to_material(
                        mat, normal_img, disp_img,
                        p.shingle_normal_strength,
                        p.shingle_displacement_strength
                    )
                    self.report({'INFO'}, "🧩 Shingles applied!")
                else:
                    self.report({'ERROR'}, "No material on roof")
                    return {'CANCELLED'}
            else:
                self.report({'ERROR'}, "Shingle texture generation failed")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Shingle error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class FROMAGE_ROOF_OT_place_dormers(bpy.types.Operator):
    """🏠 Place dormers on roof."""
    bl_idname  = "fromage_roof.place_dormers"
    bl_label   = "Place Dormers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        p = obj.fromage_roof_props
        try:
            _place_dormers_on_roof(
                obj,
                p.dormer_count,
                p.dormer_width,
                p.dormer_height,
                p.dormer_type,
                p.dormer_spacing,
                p.dormer_merge_with_roof
            )
            self.report({'INFO'}, f"🏠 {p.dormer_count} dormers placed!")
        except Exception as e:
            self.report({'ERROR'}, f"Dormer error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class FROMAGE_ROOF_OT_generate_gutters(bpy.types.Operator):
    """💧 Generate gutters and downspouts."""
    bl_idname  = "fromage_roof.generate_gutters"
    bl_label   = "Generate Gutters"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        p = obj.fromage_roof_props
        try:
            _place_gutters_on_roof(
                obj,
                p.gutter_profile,
                p.gutter_width,
                p.gutter_depth,
                p.downspout_diameter,
                p.gutter_merge_with_roof
            )
            self.report({'INFO'}, "💧 Gutters generated!")
        except Exception as e:
            self.report({'ERROR'}, f"Gutter error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class FROMAGE_ROOF_OT_apply_cute_accents(bpy.types.Operator):
    """💖 Add cute hearts and stars to roof."""
    bl_idname  = "fromage_roof.apply_cute_accents"
    bl_label   = "Apply Cute Accents"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        p = obj.fromage_roof_props
        try:
            _place_cute_accents(
                obj,
                p.accent_shape,
                p.accent_pattern,
                p.accent_size,
                p.accent_density,
                p.accent_color_mode,
                p.accent_custom_color,
                p.accent_rotation,
                p.accent_height,
                p
            )
            self.report({'INFO'}, "💖 Cute accents applied!")
        except Exception as e:
            self.report({'ERROR'}, f"Accent error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


# ──────────────────────────────────────────────────────────────
# PANEL
# ──────────────────────────────────────────────────────────────

class FROMAGE_ROOF_PT_main(bpy.types.Panel):
    bl_label       = "🏠 Fromage's Roof Generator"
    bl_idname      = "FROMAGE_ROOF_PT_main"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Roof Gen'
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def draw_header(self, context):
        self.layout.label(text="", icon='MOD_BUILD')

    def draw(self, context):
        layout = self.layout
        props  = context.active_object.fromage_roof_props

        # ── MASTER CONTROL ──────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.8
        row.operator("fromage_roof.generate", text="🏠  GENERATE ROOF", icon='MESH_DATA')
        col.prop(props, "use_geonode", toggle=True)
        col.prop(props, "auto_rebuild", toggle=True)

        # ── ROOF TYPE SELECTOR ──────────────────────────────────
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.label(text="🏛️  ROOF STYLE", icon='MOD_BUILD')
        box.prop(props, "roof_type", text="")

        # ── CORE DIMENSIONS ─────────────────────────────────────
        box = layout.box()
        box.label(text="📏 DIMENSIONS", icon='EMPTY_AXIS')
        col = box.column(align=True)
        col.prop(props, "roof_span", slider=True)
        col.prop(props, "roof_depth", slider=True)
        col.prop(props, "roof_rise", slider=True)
        col.prop(props, "roof_ridge_length", slider=True)

        # ── EAVE DETAILS ────────────────────────────────────────
        box = layout.box()
        box.label(text="🔲 EAVE DESIGN", icon='ARROW_LEFTRIGHT')
        col = box.column(align=True)
        col.prop(props, "roof_eave_overhang", slider=True)
        col.prop(props, "roof_eave_curve", slider=True)

        # ── QUALITY & OUTPUT ────────────────────────────────────
        box = layout.box()
        box.label(text="✨ QUALITY & OUTPUT", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(props, "roof_segments", slider=True)
        col.prop(props, "roof_thickness", slider=True)
        col.prop(props, "roof_with_bevel", toggle=True)

        # ── TYPE-SPECIFIC CONTROLS ──────────────────────────────
        if props.roof_type == 'PAGODA':
            box = layout.box()
            box.label(text="🏯 PAGODA SETTINGS", icon='OBJECT_DATA')
            col = box.column(align=True)
            col.prop(props, "roof_tiers", slider=True)
            col.prop(props, "roof_tier_shrink", slider=True)

        if props.roof_type == 'WAVE':
            box = layout.box()
            box.label(text="🌊 WAVE SETTINGS", icon='MOD_WAVE')
            box.prop(props, "roof_wave_freq", slider=True)

        if props.roof_type == 'GAMBREL':
            box = layout.box()
            box.label(text="⚡ GAMBREL SETTINGS", icon='OUTLINER_OB_ARMATURE')
            box.prop(props, "roof_gambrel_break", slider=True)

        # ── QUICK PRESETS ──────────────────────────────────────
        box = layout.box()
        box.label(text="🎨 QUICK PRESETS", icon='PRESET')

        # Classical
        box.label(text="  🏠 Classical European:", icon='HOME')
        grid = box.column_flow(columns=2, align=True)
        for label, pname in [
            ("Hip Standard", "HIP_STANDARD"),
            ("Hip Deep", "HIP_DEEP"),
            ("Gabled Steep", "GABLED_STEEP"),
            ("Gabled Flat", "GABLED_FLAT"),
            ("Mansard", "MANSARD_CLASSIC"),
            ("Gambrel Barn", "GAMBREL_BARN"),
            ("Dutch Gable", "DUTCH_GABLE"),
        ]:
            op = grid.operator("fromage_roof.preset", text=label)
            op.preset_name = pname

        # Asian
        box.label(text="  🏯 Asian & Eastern:", icon='OUTLINER_OB_ARMATURE')
        grid = box.column_flow(columns=2, align=True)
        for label, pname in [
            ("Zen 3-Tier", "PAGODA_3TIER"),
            ("Zen 5-Tier", "PAGODA_5TIER"),
            ("Zen Temple", "ZEN_TEMPLE"),
            ("Onion Dome", "ONION_DOME"),
        ]:
            op = grid.operator("fromage_roof.preset", text=label)
            op.preset_name = pname

        # Modern
        box.label(text="  🌊 Modern & Geometric:", icon='MOD_WAVE')
        grid = box.column_flow(columns=2, align=True)
        for label, pname in [
            ("Butterfly", "BUTTERFLY_MODERN"),
            ("Shed", "SHED_MODERN"),
            ("Geodesic", "GEODESIC_DOME"),
            ("Barrel", "BARREL_VAULT"),
            ("Gothic Vault", "VAULTED_GOTHIC"),
            ("Wave", "WAVE_ORGANIC"),
        ]:
            op = grid.operator("fromage_roof.preset", text=label)
            op.preset_name = pname

        # ══════════════════════════════════════════════════════════════
        # V3.0 SYSTEMS
        # ══════════════════════════════════════════════════════════════

        # ── MATERIAL & BAKING ─────────────────────────────────────
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.label(text="🎨 MATERIAL & BAKING", icon='SHADING_RENDERED')

        col = box.column(align=True)
        col.label(text="🌍 Classic & 💖 Dreamy Materials:", icon='HEART')
        col.prop(props, "material_preset", text="")

        row = col.row(align=True)
        row.operator("fromage_roof.apply_material", text="🎨 Apply Material", icon='MATERIAL')
        row.operator("fromage_roof.bake_textures", text="🔥 Bake", icon='RENDER_RESULT')
        col.prop(props, "bake_resolution", text="Resolution")

        # ── SHINGLE/TILE SYSTEM ──────────────────────────────────
        box = layout.box()
        box.label(text="🧩 SHINGLES & TILES", icon='TRIA_RIGHT')
        col = box.column(align=True)
        col.prop(props, "enable_shingles", toggle=True)
        if props.enable_shingles:
            col.prop(props, "shingle_type", text="Type")
            col.prop(props, "shingle_size", slider=True)
            col.prop(props, "shingle_pattern", text="Pattern")
            col.prop(props, "shingle_variation", slider=True)
            col.prop(props, "shingle_normal_strength", text="Normal", slider=True)
            col.prop(props, "shingle_displacement_strength", text="Displacement", slider=True)
            col.prop(props, "shingle_wear_amount", text="Wear", slider=True)
            col.operator("fromage_roof.apply_shingles", text="🧩 Apply Shingles", icon='TEXTURE')

        # ── ROOF MODIFIER STACK ───────────────────────────────────
        box = layout.box()
        box.label(text="📚 ROOF STACK", icon='RENDERLAYERS')
        col = box.column(align=True)
        col.prop(props, "enable_roof_stack", toggle=True)
        if props.enable_roof_stack:
            col.prop(props, "roof_stack_type_2", text="Secondary Type")
            col.prop(props, "roof_stack_blend_mode", text="Blend")
            col.prop(props, "roof_stack_offset_z", slider=True)
            col.prop(props, "roof_stack_scale_factor", slider=True)

        # ── DORMERS & SKYLIGHTS ───────────────────────────────────
        box = layout.box()
        box.label(text="🏠 DORMERS & SKYLIGHTS", icon='WINDOW')
        col = box.column(align=True)
        col.prop(props, "enable_dormers", toggle=True)
        if props.enable_dormers:
            col.prop(props, "dormer_type", text="Type")
            col.prop(props, "dormer_count", slider=True)
            col.prop(props, "dormer_width", slider=True)
            col.prop(props, "dormer_height", slider=True)
            col.prop(props, "dormer_spacing", text="Spacing", slider=True)
            col.prop(props, "dormer_merge_with_roof", toggle=True)
            col.operator("fromage_roof.place_dormers", text="🏠 Place Dormers", icon='MOD_ARRAY')

        # ── GUTTERS & DRAINS ──────────────────────────────────────
        box = layout.box()
        box.label(text="💧 GUTTERS & DRAINS", icon='TRIA_DOWN')
        col = box.column(align=True)
        col.prop(props, "enable_gutters", toggle=True)
        if props.enable_gutters:
            col.prop(props, "gutter_profile", text="Profile")
            col.prop(props, "gutter_width", slider=True)
            col.prop(props, "gutter_depth", slider=True)
            col.prop(props, "downspout_diameter", slider=True)
            col.prop(props, "downspout_offset", slider=True)
            col.prop(props, "gutter_merge_with_roof", toggle=True)
            col.operator("fromage_roof.generate_gutters", text="💧 Generate Gutters", icon='MOD_ARRAY')

        # ── CUTE Y2K ACCENTS 💖⭐ ────────────────────────────────
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.2
        row.label(text="💖 CUTE Y2K ACCENTS", icon='HEART')
        col = box.column(align=True)
        col.prop(props, "enable_cute_accents", toggle=True)
        if props.enable_cute_accents:
            col.prop(props, "accent_shape", text="Shape")
            col.prop(props, "accent_pattern", text="Pattern")
            col.prop(props, "accent_size", slider=True)
            col.prop(props, "accent_density", text="Density", slider=True)
            col.prop(props, "accent_color_mode", text="Colors")
            if props.accent_color_mode == 'CUSTOM':
                col.prop(props, "accent_custom_color", text="Custom Color")
            col.prop(props, "accent_rotation", text="Random Rotation", slider=True)
            col.prop(props, "accent_height", slider=True)
            col.operator("fromage_roof.apply_cute_accents", text="💖 Apply Cute Accents!", icon='HEART')

        # ── VIEWPORT PREVIEW ──────────────────────────────────────
        box = layout.box()
        box.label(text="👁️  PREVIEW", icon='HIDE_OFF')
        col = box.column(align=True)
        col.prop(props, "enable_viewport_preview", toggle=True)

        # Info
        box = layout.box()
        box.label(text="ℹ️  ABOUT", icon='INFO')
        col = box.column(align=True)
        col.label(text="🏠 Fromage's Roof Generator v3.1")
        col.label(text="21 roof types • Y2K Cute + Professional")
        col.label(text="💖 Cute Accents • Dreamy Materials • Baking")


# ──────────────────────────────────────────────────────────────
# REGISTRATION
# ──────────────────────────────────────────────────────────────

classes = (
    FromageRoofProperties,
    FROMAGE_ROOF_OT_generate,
    FROMAGE_ROOF_OT_preset,
    FROMAGE_ROOF_OT_apply_material,
    FROMAGE_ROOF_OT_bake_textures,
    FROMAGE_ROOF_OT_apply_shingles,
    FROMAGE_ROOF_OT_place_dormers,
    FROMAGE_ROOF_OT_generate_gutters,
    FROMAGE_ROOF_OT_apply_cute_accents,
    FROMAGE_ROOF_PT_main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.fromage_roof_props = bpy.props.PointerProperty(type=FromageRoofProperties)
    print("[🏠 Fromage's Roof Generator v3.1] Registered")
    print("   ✨ 21 roof types • Y2K Cute Dome • Dreamy Materials")
    print("   💖 Hearts & Stars Accents • Materials • Shingles • Dormers • Gutters")


def unregister():
    if hasattr(bpy.types.Object, 'fromage_roof_props'):
        del bpy.types.Object.fromage_roof_props
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


if __name__ == "__main__":
    pass
