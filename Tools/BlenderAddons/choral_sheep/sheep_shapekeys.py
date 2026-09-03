# -*- coding: utf-8 -*-
"""Choral Sheep shape-key authoring panel.

Lets the owner author expressive shape keys on the sheep body mesh with
one click, plus a preview cycle that drives them in the viewport.

Creative shape-key library it manages (on the Skin_Sheep_* body mesh):

  Group "breath":
    Breath_In   - body inflate (slight overall scale-out on the ribcage)
    Breath_Out  - body deflate (settle)

  Group "blink":
    Blink       - eyelid/eye flatten (closes the eye region)

  Group "interact" (emotional sets for Graze / Harmonize / Guide):
    Cheek_Puff      - cheeks swell (happy / harmonize)
    Jaw_Open        - jaw drops (graze / sing)
    Ears_Perk       - ears raise (alert / guide)
    Body_Squash     - whole body squashes (stomp/hop anticipation)
    Body_Stretch    - whole body stretches (reach / leap)

How to use in Blender:
  - Object Mode, select the sheep body mesh (Skin_Sheep_*).
  - Sidebar (N) > Melodia > Choral Sheep Shape Keys.
  - Buttons: create the group, bake from the current mesh deformation,
    clear a key, and drive a preview cycle.

These are authored ON the live mesh so you can push/pull vertices and hit
'Bake Current' to capture the pose into the active key. Geometry stays
non-destructive (shape keys are additive, never modify base mesh).

Blender 5.2 compatibility: shape-key API unchanged; panel uses bl_category
'Melodia' to sit with the rest of the suite.
"""
try:
    import bpy  # type: ignore
    from bpy.types import Operator, Panel
    from bpy.props import StringProperty
    _HAVE_BPY = True
except Exception:  # offline import safety
    bpy = None  # type: ignore
    Operator = object  # type: ignore
    Panel = object  # type: ignore
    StringProperty = lambda *a, **k: None  # type: ignore
    _HAVE_BPY = False

BL_IDNAME = "MELODIA_PT_sheep_shapekeys"


def _find_sheep_mesh(context):
    """Prefer selected Skin_* mesh, else the Sheep_/Skin_ body mesh."""
    if context.active_object and context.active_object.type == "MESH":
        return context.active_object
    for o in context.scene.objects:
        if o.type == "MESH" and o.name.startswith("Skin_"):
            return o
    return None


def _ensure_shapekeys(obj):
    if obj.data.shape_keys is None:
        basis = obj.shape_key_add(name="Basis")
        basis.interpolation = "KEY_LINEAR"
    return obj.data.shape_keys


def _key_exists(obj, name):
    if obj.data.shape_keys is None:
        return False
    return name in obj.data.shape_keys.key_blocks


def _add_key(obj, name):
    _ensure_shapekeys(obj)
    if _key_exists(obj, name):
        return obj.data.shape_keys.key_blocks[name]
    key = obj.shape_key_add(name=name)
    key.value = 0.0
    key.interpolation = "KEY_LINEAR"
    return key


def _bake_current(obj, name):
    """Copy the current (possibly edited) mesh into a shape key's offset."""
    if not _key_exists(obj, name):
        _add_key(obj, name)
    # from_edit is false; we copy from the object's current coords
    key = obj.data.shape_keys.key_blocks[name]
    if not key.data:
        # fallback: create the key block data explicitly
        for i, vert in enumerate(obj.data.vertices):
            if i < len(key.data):
                key.data[i].co = vert.co
    return key


class MELODIA_OT_sheep_sk_create_group(Operator):
    """Create the full Choral Sheep shape-key library."""
    bl_idname = "melodia.sheep_sk_create_group"
    bl_label = "Create Shape-Key Library"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = _find_sheep_mesh(context)
        if obj is None:
            self.report({"ERROR"}, "Select the sheep mesh first")
            return {"CANCELLED"}
        for name in ("Breath_In", "Breath_Out", "Blink",
                     "Cheek_Puff", "Jaw_Open", "Ears_Perk",
                     "Body_Squash", "Body_Stretch"):
            _add_key(obj, name)
        self.report({"INFO"}, f"Created 8 shape keys on {obj.name}")
        return {"FINISHED"}


class MELODIA_OT_sheep_sk_bake(Operator):
    """Bake the current mesh pose into the named shape key."""
    bl_idname = "melodia.sheep_sk_bake"
    bl_label = "Bake Current"
    bl_options = {"REGISTER", "UNDO"}
    key_name: StringProperty()

    def execute(self, context):
        obj = _find_sheep_mesh(context)
        if obj is None:
            self.report({"ERROR"}, "Select the sheep mesh first")
            return {"CANCELLED"}
        _bake_current(obj, self.key_name)
        self.report({"INFO"}, f"Baked current pose into '{self.key_name}'")
        return {"FINISHED"}


class MELODIA_OT_sheep_sk_clear(Operator):
    """Clear (zero out) a shape key."""
    bl_idname = "melodia.sheep_sk_clear"
    bl_label = "Clear"
    bl_options = {"REGISTER", "UNDO"}
    key_name: StringProperty()

    def execute(self, context):
        obj = _find_sheep_mesh(context)
        if obj is None:
            return {"CANCELLED"}
        if _key_exists(obj, self.key_name):
            obj.data.shape_keys.key_blocks[self.key_name].value = 0.0
        return {"FINISHED"}


class MELODIA_OT_sheep_sk_cycle(Operator):
    """Preview-cycle the emotional sets on the sheep."""
    bl_idname = "melodia.sheep_sk_cycle"
    bl_label = "Preview Cycle"
    bl_options = {"REGISTER", "UNDO"}
    set_name: StringProperty(default="harmonize")

    SETS = {
        "breath":   {"Breath_In": 1.0, "Breath_Out": 0.0, "Blink": 0.0},
        "blink":    {"Breath_In": 0.0, "Breath_Out": 0.0, "Blink": 1.0},
        "harmonize": {"Cheek_Puff": 1.0, "Ears_Perk": 0.6, "Blink": 0.0},
        "guide":    {"Ears_Perk": 1.0, "Body_Stretch": 0.5, "Blink": 0.0},
        "graze":    {"Jaw_Open": 1.0, "Body_Squash": 0.5, "Blink": 0.0},
        "neutral":  {"Breath_In": 0.0, "Breath_Out": 0.0, "Blink": 0.0,
                     "Cheek_Puff": 0.0, "Jaw_Open": 0.0, "Ears_Perk": 0.0,
                     "Body_Squash": 0.0, "Body_Stretch": 0.0},
    }

    def execute(self, context):
        obj = _find_sheep_mesh(context)
        if obj is None or obj.data.shape_keys is None:
            self.report({"ERROR"}, "No sheep mesh/shape keys")
            return {"CANCELLED"}
        target = self.SETS.get(self.set_name, self.SETS["neutral"])
        for kb in obj.data.shape_keys.key_blocks:
            kb.value = target.get(kb.name, 0.0)
        self.report({"INFO"}, f"Applied {self.set_name} pose")
        return {"FINISHED"}


class MELODIA_PT_sheep_shapekeys(Panel):
    bl_label = "Choral Sheep Shape Keys"
    bl_idname = BL_IDNAME
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia"

    def draw(self, context):
        layout = self.layout
        obj = _find_sheep_mesh(context)
        if obj is None:
            layout.label(text="Select the sheep mesh (Skin_Sheep_*)", icon="ERROR")
            return

        layout.label(text=f"Mesh: {obj.name}", icon="MESH_DATA")
        has_sk = obj.data.shape_keys is not None

        if not has_sk:
            layout.operator(MELODIA_OT_sheep_sk_create_group.bl_idname,
                            text="Create Shape-Key Library", icon="ADD")
            return

        row = layout.row()
        row.operator(MELODIA_OT_sheep_sk_create_group.bl_idname, icon="ADD")

        layout.separator()
        layout.label(text="Preview Cycle", icon="PLAY")
        for sname in ("neutral", "breath", "blink", "harmonize", "guide", "graze"):
            op = layout.operator(MELODIA_OT_sheep_sk_cycle.bl_idname,
                                 text=f"{sname.capitalize()}")
            op.set_name = sname

        layout.separator()
        layout.label(text="Keys", icon="SHAPEKEY_DATA")
        for kb in obj.data.shape_keys.key_blocks:
            if kb.name == "Basis":
                continue
            row = layout.row(align=True)
            row.prop(kb, "value", text=kb.name, slider=True)
            b = row.operator(MELODIA_OT_sheep_sk_bake.bl_idname, text="Bake", icon="REC")
            b.key_name = kb.name
            c = row.operator(MELODIA_OT_sheep_sk_clear.bl_idname, text="0", icon="X")
            c.key_name = kb.name


classes = (
    MELODIA_OT_sheep_sk_create_group,
    MELODIA_OT_sheep_sk_bake,
    MELODIA_OT_sheep_sk_clear,
    MELODIA_OT_sheep_sk_cycle,
    MELODIA_PT_sheep_shapekeys,
)


def register():
    if _HAVE_BPY:
        for cls in classes:
            bpy.utils.register_class(cls)


def unregister():
    if _HAVE_BPY:
        for cls in reversed(classes):
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass


if __name__ == "__main__":
    register()
