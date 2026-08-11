# V13: Primitive UI Definitions
# Defines display names and default values for each shape type

PRIMITIVE_UI_DEFS = {
    'sphere': {
        'label': "Sphere",
        'params': [
            ('radius', "Radius", 1.0),
        ]
    },
    'box': {
        'label': "Box",
        'params': [
            # Box uses standard scale(x,y,z), so p-params are unused
        ]
    },
    'rounded_box': {
        'label': "Rounded Box",
        'params': [
            ('p1', "Roundness", 0.1),
        ]
    },
    'torus': {
        'label': "Torus",
        'params': [
            ('p1', "Main Radius", 1.0),
            ('p2', "Pipe Radius", 0.3),
        ]
    },
    'cylinder': {
        'label': "Cylinder",
        'params': [
            ('p1', "Radius", 0.5),
            ('p2', "Height (Half)", 1.0),
        ]
    },
    'capsule': {
        'label': "Capsule",
        'params': [
            ('p1', "Radius", 0.3),
            ('p2', "Height (Half)", 0.7),
        ]
    },
    'hex_prism': {
        'label': "Hex Prism",
        'params': [
            ('p1', "Radius", 0.5),
            ('p2', "Height (Half)", 1.0),
        ]
    },
    'pyramid': {
        'label': "Pyramid",
        'params': [
            ('p1', "Base Size", 1.0),
            ('p2', "Height", 1.5),
        ]
    },
    'capped_cone': {
        'label': "Tapered Cylinder",
        'params': [
            ('p1', "Bottom Radius", 0.5),
            ('p2', "Top Radius", 0.3),
            ('p3', "Height", 1.5),
        ]
    },
    'ngon_prism': {
        'label': "N-gon Prism",
        'params': [
            ('p1', "Radius", 0.5),
            ('ngon_sides', "Sides", 6),
            ('p3', "Height", 1.0),
        ]
    },
    'ellipsoid': {
        'label': "Ellipsoid",
        'params': [
            ('p1', "Radius X", 1.0),
            ('p2', "Radius Y", 0.7),
            ('p3', "Radius Z", 0.5),
        ]
    },
    'rounded_cylinder': {
        'label': "Rounded Cylinder",
        'params': [
            ('p1', "Radius", 0.5),
            ('p2', "Edge Radius", 0.1),
            ('p3', "Height (Half)", 1.0),
        ]
    },
    'capped_torus': {
        'label': "Capped Torus",
        'params': [
            ('p1', "Main Radius", 1.0),
            ('p2', "Pipe Radius", 0.3),
            ('p3', "Angle (rad)", 2.0),
        ]
    },
    'octahedron': {
        'label': "Octahedron",
        'params': [
            ('p1', "Size", 1.0),
        ]
    },
    'cut_sphere': {
        'label': "Cut Sphere",
        'params': [
            ('p1', "Cut Height", 0.0),
        ]
    },
}

# --- Inherited constants from V12.1 ---
_PRIM_COLORS = [
    (0.2, 0.5, 1.0, 1.0), (1.0, 0.3, 0.3, 1.0), (0.3, 0.9, 0.4, 1.0), (1.0, 0.7, 0.1, 1.0),
    (0.8, 0.3, 1.0, 1.0), (0.1, 0.9, 0.9, 1.0), (1.0, 0.5, 0.7, 1.0), (0.6, 0.8, 0.2, 1.0),
]

_fsq_coords = [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)]
_fsq_indices = [(0, 1, 2), (0, 2, 3)]

_SHAPE_MAP = {
    'sphere': 0.0,
    'box': 1.0,
    'torus': 2.0,
    'cylinder': 3.0,
    'rounded_box': 4.0,
    'capsule': 5.0,
    'hex_prism': 6.0,
    'pyramid': 7.0,
    'capped_cone': 8.0,
    'ngon_prism': 9.0,
    'ellipsoid': 10.0,
    'rounded_cylinder': 11.0,
    'capped_torus': 12.0,
    'octahedron': 13.0,
    'cut_sphere': 14.0,
}

