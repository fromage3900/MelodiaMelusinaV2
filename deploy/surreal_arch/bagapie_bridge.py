"""Melodia wrapper for Bagapie ivy scattering on Blender 5.1."""

from __future__ import annotations

import json
from typing import Iterable

import bpy
from bpy.props import BoolProperty, IntProperty


IVY_MODIFIER_NAME = "BagaPie_Ivy_Generator"
IVY_OBJECT_PREFIX = "BagaPie_Ivy"
RQ_WALL_WORTHY_TOKENS = (
    "gazebo",
    "door_archway",
    "door archway",
    "archway",
    "bricks",
    "brick",
    "gothic_tracery",
    "gothic tracery",
    "tracery",
    "vault_ribs",
    "vault ribs",
    "oculus_frame",
    "oculus frame",
    "quatrefoil",
    "rose_window",
    "rose window",
    "crown_molding",
    "crown molding",
    "corbel",
    "spiral_stair",
    "spiral stair",
    "column_capital",
    "column capital",
)
RQ_SKIP_TOKENS = (
    "jewelry",
    "jewel",
    "token",
    "violin",
    "musical",
    "clef",
    "note",
    "ornament",
    "melusina",
    "sk_melusina",
    "hair",
)


def bagapie_available() -> bool:
    """Return True when Bagapie's ivy operator is registered and callable."""
    try:
        op = bpy.ops.bagapie.ivy
        op.get_rna_type()
        return True
    except Exception:
        return False


def _selected_meshes(context) -> list[bpy.types.Object]:
    return [obj for obj in (context.selected_objects or []) if obj and obj.type == "MESH"]


def _new_ivy_mesh(before_names: set[str]) -> bpy.types.Object | None:
    candidates = []
    for obj in bpy.context.scene.objects:
        if obj.name in before_names or obj.type != "MESH":
            continue
        if obj.name.startswith(IVY_OBJECT_PREFIX) or _ivy_modifier(obj) is not None:
            candidates.append(obj)
    if candidates:
        return candidates[-1]
    return _latest_ivy_mesh()


def _latest_ivy_mesh() -> bpy.types.Object | None:
    candidates = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if obj.name.startswith(IVY_OBJECT_PREFIX) or _ivy_modifier(obj) is not None:
            candidates.append(obj)
    return candidates[-1] if candidates else None


def _ivy_modifier(obj: bpy.types.Object):
    for mod in obj.modifiers:
        if mod.name == IVY_MODIFIER_NAME:
            return mod
        node_group = getattr(mod, "node_group", None)
        if node_group and node_group.name.startswith(IVY_MODIFIER_NAME):
            return mod
    return None


def _safe_modifier_get(modifier, key: str):
    try:
        return modifier[key]
    except Exception:
        return None


def _collection_from_modifier(modifier, key: str):
    value = _safe_modifier_get(modifier, key)
    if isinstance(value, bpy.types.Collection):
        return value
    if isinstance(value, str):
        return bpy.data.collections.get(value)
    return None


def _collection_payload(ivy: bpy.types.Object, modifier) -> dict[str, bpy.types.Collection | None]:
    payload = {
        "target": _collection_from_modifier(modifier, "Input_9"),
        "assets": _collection_from_modifier(modifier, "Input_16"),
        "emitter": _collection_from_modifier(modifier, "Input_17"),
    }

    list_prop = getattr(ivy, "bagapieList", None)
    if list_prop:
        try:
            index = max(0, min(getattr(ivy, "bagapieIndex", len(list_prop) - 1), len(list_prop) - 1))
            val = json.loads(list_prop[index]["val"])
            mod_names = val.get("modifiers", [])
            if len(mod_names) >= 4:
                payload["target"] = payload["target"] or bpy.data.collections.get(mod_names[1])
                payload["emitter"] = payload["emitter"] or bpy.data.collections.get(mod_names[3])
        except Exception:
            pass

    payload["assets"] = payload["assets"] or bpy.data.collections.get("BagaPie_Ivy_Assets")
    return payload


def _iter_group_input_sockets(node_group) -> list[dict[str, str]]:
    sockets: list[dict[str, str]] = []
    interface = getattr(node_group, "interface", None)
    items_tree = getattr(interface, "items_tree", None)
    if items_tree is not None:
        for item in items_tree:
            if getattr(item, "item_type", None) != "SOCKET":
                continue
            if getattr(item, "in_out", None) != "INPUT":
                continue
            sockets.append(
                {
                    "identifier": getattr(item, "identifier", "") or "",
                    "name": getattr(item, "name", "") or "",
                    "socket_type": getattr(item, "socket_type", "") or "",
                }
            )
    else:
        for item in getattr(node_group, "inputs", []) or []:
            sockets.append(
                {
                    "identifier": getattr(item, "identifier", "") or getattr(item, "name", "") or "",
                    "name": getattr(item, "name", "") or "",
                    "socket_type": getattr(item, "type", "") or "",
                }
            )
    return [s for s in sockets if s["identifier"]]


def _is_collection_socket(socket_info: dict[str, str]) -> bool:
    haystack = f"{socket_info.get('socket_type', '')} {socket_info.get('name', '')} {socket_info.get('identifier', '')}".lower()
    return "collection" in haystack


def _resolve_socket_key(
    modifier,
    legacy_key: str,
    role: str,
    name_hints: Iterable[str],
    collection_index: int,
) -> str | None:
    node_group = getattr(modifier, "node_group", None)
    if node_group is None:
        return legacy_key

    sockets = _iter_group_input_sockets(node_group)
    identifiers = {s["identifier"] for s in sockets}
    if legacy_key in identifiers:
        return legacy_key

    hint_tokens = tuple(h.lower() for h in name_hints)
    for socket_info in sockets:
        label = f"{socket_info['name']} {socket_info['identifier']}".lower()
        if any(token in label for token in hint_tokens):
            return socket_info["identifier"]

    collection_sockets = [s for s in sockets if _is_collection_socket(s)]
    if collection_index < len(collection_sockets):
        return collection_sockets[collection_index]["identifier"]

    # Last resort: keep Bagapie's legacy key so its own panel still shows a value.
    return legacy_key


def _assign_collection_socket(modifier, legacy_key: str, resolved_key: str | None, collection) -> bool:
    if collection is None or resolved_key is None:
        return False

    changed = False
    for key in dict.fromkeys((legacy_key, resolved_key)):
        try:
            if _safe_modifier_get(modifier, key) != collection:
                modifier[key] = collection
                changed = True
        except Exception:
            continue
    return changed


def repair_ivy_collection_sockets(ivy: bpy.types.Object) -> dict[str, object]:
    """Bind Bagapie ivy collection sockets by identifier/name, not only Input_* keys."""
    modifier = _ivy_modifier(ivy)
    if modifier is None:
        return {"ok": False, "error": f"{IVY_MODIFIER_NAME} modifier not found"}

    payload = _collection_payload(ivy, modifier)
    specs = (
        ("target", "Input_9", ("target", "surface", "object"), 0),
        ("assets", "Input_16", ("asset", "assets", "leaf", "leaves", "instance"), 1),
        ("emitter", "Input_17", ("emitter", "emiter", "source"), 2),
    )

    resolved: dict[str, str | None] = {}
    changed_roles: list[str] = []
    missing_roles: list[str] = []
    for role, legacy_key, hints, index in specs:
        coll = payload.get(role)
        if coll is None:
            missing_roles.append(role)
            continue
        key = _resolve_socket_key(modifier, legacy_key, role, hints, index)
        resolved[role] = key
        if _assign_collection_socket(modifier, legacy_key, key, coll):
            changed_roles.append(role)

    try:
        ivy.update_tag()
        bpy.context.view_layer.update()
    except Exception:
        pass

    return {
        "ok": not missing_roles,
        "changed_roles": changed_roles,
        "missing_roles": missing_roles,
        "resolved": resolved,
    }


def select_ivy_mesh(context, ivy: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    ivy.select_set(True)
    context.view_layer.objects.active = ivy


def _review_queue_haystack(obj: bpy.types.Object) -> str:
    collections = " ".join(coll.name for coll in getattr(obj, "users_collection", []) or [])
    props = getattr(obj, "surreal_arch_props", None)
    arch_type = getattr(props, "arch_type", "") if props else ""
    return f"{obj.name} {getattr(obj.data, 'name', '')} {collections} {arch_type}".lower().replace("-", "_")


def _is_wall_worthy_review_queue_mesh(obj: bpy.types.Object) -> bool:
    if obj is None or obj.type != "MESH":
        return False
    haystack = _review_queue_haystack(obj)
    if any(token in haystack for token in RQ_SKIP_TOKENS):
        return False
    in_review_queue = any(token in haystack for token in ("review_queue", "review queue", "rq_"))
    return in_review_queue and any(token in haystack for token in RQ_WALL_WORTHY_TOKENS)


def review_queue_ivy_targets(context) -> tuple[list[bpy.types.Object], list[str]]:
    targets: list[bpy.types.Object] = []
    skipped: list[str] = []
    for obj in context.scene.objects:
        if obj.type != "MESH":
            continue
        haystack = _review_queue_haystack(obj)
        if any(token in haystack for token in ("review_queue", "review queue", "rq_")):
            if _is_wall_worthy_review_queue_mesh(obj):
                targets.append(obj)
            else:
                skipped.append(obj.name)
    targets.sort(key=lambda o: o.name.lower())
    return targets, skipped


class SURREAL_ARCH_OT_ivy_scatter(bpy.types.Operator):
    bl_idname = "surreal_arch.ivy_scatter"
    bl_label = "Ivy (Bagapie)"
    bl_description = (
        "Create Bagapie ivy on the selected mesh, then repair Blender 5.1 collection "
        "socket bindings and select the ivy mesh."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context):
        if not bagapie_available():
            self.report({"ERROR"}, "Enable the Bagapie extension to use Ivy (Bagapie)")
            return {"CANCELLED"}

        meshes = _selected_meshes(context)
        if not meshes:
            self.report({"WARNING"}, "Select a mesh before running Ivy (Bagapie)")
            return {"CANCELLED"}

        active = context.active_object
        before_names = {obj.name for obj in bpy.context.scene.objects}
        try:
            result = bpy.ops.bagapie.ivy()
        except Exception as exc:
            self.report({"ERROR"}, f"Bagapie ivy failed: {exc}")
            return {"CANCELLED"}
        if "CANCELLED" in result:
            self.report({"WARNING"}, "Bagapie ivy cancelled")
            return {"CANCELLED"}

        ivy = _new_ivy_mesh(before_names)
        if ivy is None:
            self.report({"WARNING"}, "Bagapie ran, but no BagaPie_Ivy mesh was found")
            if active:
                context.view_layer.objects.active = active
            return {"CANCELLED"}

        repair = repair_ivy_collection_sockets(ivy)
        select_ivy_mesh(context, ivy)

        if repair.get("missing_roles"):
            missing = ", ".join(repair["missing_roles"])
            self.report({"WARNING"}, f"Ivy created; missing collection socket data: {missing}")
        elif repair.get("changed_roles"):
            changed = ", ".join(repair["changed_roles"])
            self.report({"INFO"}, f"Ivy created; repaired sockets: {changed}")
        else:
            self.report({"INFO"}, "Ivy created; ivy mesh selected")
        return {"FINISHED"}


class SURREAL_ARCH_OT_ivy_scatter_review_queue(bpy.types.Operator):
    bl_idname = "surreal_arch.ivy_scatter_review_queue"
    bl_label = "RQ Ivy Batch"
    bl_description = "Apply Bagapie ivy once to wall-worthy Review Queue architecture props"
    bl_options = {"REGISTER", "UNDO"}

    max_targets: IntProperty(
        name="Max targets",
        default=12,
        min=1,
        max=64,
        description="Safety cap for one batch run",
    )
    dry_run: BoolProperty(
        name="Dry run",
        default=False,
        description="Only report eligible Review Queue targets; do not create ivy",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=360)

    def execute(self, context):
        targets, skipped = review_queue_ivy_targets(context)
        targets = targets[: self.max_targets]
        report = {
            "dry_run": self.dry_run,
            "targets": [obj.name for obj in targets],
            "applied": [],
            "failed": [],
            "skipped_count": len(skipped),
            "stage_saved": False,
        }
        if not targets:
            context.scene["surreal_arch_ivy_scatter_review_queue_last"] = json.dumps(report, sort_keys=True)
            self.report({"WARNING"}, "No wall-worthy Review Queue architecture meshes found")
            return {"CANCELLED"}
        if self.dry_run:
            context.scene["surreal_arch_ivy_scatter_review_queue_last"] = json.dumps(report, sort_keys=True)
            self.report({"INFO"}, f"RQ ivy dry run: {len(targets)} eligible target(s)")
            return {"FINISHED"}
        if not bagapie_available():
            self.report({"ERROR"}, "Enable the Bagapie extension to run RQ Ivy Batch")
            return {"CANCELLED"}

        original_active = context.active_object
        original_selection = list(context.selected_objects or [])
        try:
            for obj in targets:
                before = {o.name for o in context.scene.objects}
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                context.view_layer.objects.active = obj
                try:
                    result = bpy.ops.surreal_arch.ivy_scatter()
                except Exception as exc:
                    report["failed"].append({"target": obj.name, "error": str(exc)})
                    continue
                ivy = _new_ivy_mesh(before)
                if "FINISHED" in result and ivy is not None:
                    report["applied"].append({"target": obj.name, "ivy": ivy.name})
                else:
                    report["failed"].append({"target": obj.name, "error": "Bagapie did not finish or ivy mesh not found"})
        finally:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in original_selection:
                if context.scene.objects.get(obj.name) is not None:
                    obj.select_set(True)
            if original_active and context.scene.objects.get(original_active.name) is not None:
                context.view_layer.objects.active = original_active

        context.scene["surreal_arch_ivy_scatter_review_queue_last"] = json.dumps(report, sort_keys=True)
        if report["failed"]:
            self.report(
                {"WARNING"},
                f"RQ ivy applied {len(report['applied'])}/{len(targets)}; {len(report['failed'])} failed",
            )
        else:
            self.report({"INFO"}, f"RQ ivy applied to {len(report['applied'])} Review Queue prop(s); no stage save")
        return {"FINISHED"}


BAGAPIE_BRIDGE_CLASSES = (SURREAL_ARCH_OT_ivy_scatter, SURREAL_ARCH_OT_ivy_scatter_review_queue)
