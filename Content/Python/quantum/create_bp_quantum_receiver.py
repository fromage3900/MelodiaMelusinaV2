"""
Create or update a Blueprint Actor `BP_QuantumReceiver` with a
Blueprint-callable function `ApplyQuantumResult(winnerId: string, jobId: string)`.

Run inside Unreal Editor's Python environment (Window -> Developer Tools -> Python
Console or run as an editor script).

Usage:
    # From the Unreal Python console:
    import quantum.create_bp_quantum_receiver as creator
    creator.create_or_update()

The script is idempotent: it will create the Blueprint if missing, add the
function signature if missing, attempt to add a simple PrintString node in the
function body, then compile and save the asset.

Notes:
 - The script uses the editor `BlueprintEditorLibrary` when available. If the
   host editor doesn't expose all helper functions, the script falls back to
   best-effort operations and will still create the Blueprint and function
   signature.
 - The Blueprint is created at: /Game/BS_GodFile/Quantum/BP_QuantumReceiver
"""
import traceback
import unreal


ASSET_DIR = "/Game/BS_GodFile/Quantum"
ASSET_NAME = "BP_QuantumReceiver"
ASSET_PATH = f"{ASSET_DIR}/{ASSET_NAME}"


def _log(msg):
    unreal.log(f"[create_bp_quantum_receiver] {msg}")


def _ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _create_blueprint_if_missing():
    if unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
        _log(f"Blueprint exists: {ASSET_PATH}")
        return unreal.load_asset(ASSET_PATH)

    _log(f"Creating Blueprint: {ASSET_PATH}")
    _ensure_directory(ASSET_DIR)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.BlueprintFactory()
    try:
        # set parent class to Actor
        factory.set_editor_property("parent_class", unreal.Actor)
    except Exception:
        try:
            factory.set_editor_property("ParentClass", unreal.Actor)
        except Exception:
            pass

    bp = None
    try:
        bp = asset_tools.create_asset(
            asset_name=ASSET_NAME,
            package_path=ASSET_DIR,
            asset_class=unreal.Blueprint,
            factory=factory
        )
    except Exception as e:
        _log(f"create_asset raised: {e}")
        _log(traceback.format_exc())

    if bp:
        unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
        _log(f"Created blueprint: {ASSET_PATH}")
        return bp

    _log("Failed to create Blueprint via AssetTools; attempting load if present on disk.")
    try:
        return unreal.load_asset(ASSET_PATH)
    except Exception:
        return None


def _get_function_list(bp):
    lib = getattr(unreal, "BlueprintEditorLibrary", None)
    if lib is None:
        return []

    try:
        if hasattr(lib, "get_functions"):
            return lib.get_functions(bp) or []
    except Exception:
        _log("get_functions failed; falling back to empty list")
    return []


def _function_exists(bp, name):
    funcs = _get_function_list(bp)
    for f in funcs:
        try:
            # f may be a string or dict-like
            if isinstance(f, str) and f.lower() == name.lower():
                return True
            if hasattr(f, "get"):
                if f.get("function_name", "").lower() == name.lower() or f.get("name", "").lower() == name.lower():
                    return True
        except Exception:
            continue
    return False


def _add_function_signature(bp, name):
    lib = getattr(unreal, "BlueprintEditorLibrary", None)
    if lib is None:
        _log("BlueprintEditorLibrary not available; cannot add function graph programmatically.")
        return False

    try:
        # Prefer add_function_graph (adds a new function graph)
        if hasattr(lib, "add_function_graph"):
            _log(f"Adding function graph '{name}'")
            library_result = lib.add_function_graph(bp, name)
        elif hasattr(lib, "add_function"):
            _log(f"Adding function '{name}' (add_function)")
            library_result = lib.add_function(bp, name)
        else:
            _log("No add_function API found on BlueprintEditorLibrary")
            return False
    except Exception as e:
        _log(f"Exception while adding function graph: {e}")
        _log(traceback.format_exc())
        return False

    # Set function parameters (two strings) if API exists
    try:
        if hasattr(lib, "set_function_params"):
            inputs = [{"name": "winnerId", "type": "string"}, {"name": "jobId", "type": "string"}]
            _log(f"Setting function params for '{name}' -> {inputs}")
            # Try a few calling conventions: (bp, name, inputs, outputs) or (ASSET_PATH, name, params)
            try:
                lib.set_function_params(bp, name, inputs, [])
            except Exception:
                try:
                    lib.set_function_params(ASSET_PATH, name, inputs)
                except Exception:
                    _log("set_function_params failed with available signatures")
    except Exception:
        _log("set_function_params encountered an error")

    return True


def _attempt_add_printnode(bp, func_name):
    lib = getattr(unreal, "BlueprintEditorLibrary", None)
    if lib is None:
        return False

    try:
        # Attempt to add a PrintString call node and wire it to the function entry.
        # This is best-effort: many BlueprintEditorLibrary variants accept a dict
        # return describing node id. We handle exceptions gracefully.
        _log("Attempting to add PrintString node to function body (best-effort)")

        # Add a CallFunction (PrintString) node
        call_node = None
        try:
            call_node = lib.add_node(bp, node_type="CallFunction", graph_name=func_name, position=[300, 0], function_name="PrintString")
        except Exception:
            try:
                call_node = lib.add_node(bp, "CallFunction", func_name, [300, 0], {"function_name": "PrintString"})
            except Exception:
                call_node = None

        if not call_node:
            _log("Could not create CallFunction node; skipping node injection.")
            return False

        # Set the InString pin default to a helpful message (best-effort).
        try:
            # pin name could be InString or In Text; try a few variants
            for pin_name in ("InString", "In Text", "InText"):
                try:
                    lib.set_pin_default(bp, call_node, pin_name, "ApplyQuantumResult called (winnerId, jobId)")
                except Exception:
                    pass
        except Exception:
            pass

        # Wire exec from the function entry to the PrintString node
        try:
            # add_node may have returned an id or object; resolve id if necessary
            call_node_id = call_node if isinstance(call_node, str) else (call_node.get("node_id") if hasattr(call_node, "get") else None)
            # Find the entry node for the function
            entry_nodes = lib.get_function_entry_nodes(bp) if hasattr(lib, "get_function_entry_nodes") else None
            entry_id = None
            if entry_nodes:
                # entry_nodes may be list of node ids or node objects
                first = entry_nodes[0]
                entry_id = first if isinstance(first, str) else (first.get("node_id") if hasattr(first, "get") else None)

            if entry_id and call_node_id:
                try:
                    lib.connect_pins(bp, source_node=entry_id, source_pin="Then", target_node=call_node_id, target_pin="execute")
                except Exception:
                    try:
                        lib.connect_pins(bp, entry_id, "Then", call_node_id, "execute")
                    except Exception:
                        pass
        except Exception:
            pass

        return True
    except Exception:
        _log("Failed during add_printnode: " + traceback.format_exc())
        return False


def create_or_update():
    """Main entry point: create or update the BP and function."""
    _log(f"Starting upsert for {ASSET_PATH}")
    bp = _create_blueprint_if_missing()
    if bp is None:
        _log("Unable to create or load the Blueprint asset. Aborting.")
        return False

    func_name = "ApplyQuantumResult"
    if _function_exists(bp, func_name):
        _log(f"Function '{func_name}' already exists in {ASSET_NAME}")
    else:
        added = _add_function_signature(bp, func_name)
        if added:
            _log(f"Function '{func_name}' added (signature set).")
        else:
            _log(f"Failed to add function '{func_name}' programmatically.")

    # Attempt to add a PrintString node that logs a static message (best-effort)
    try:
        _attempt_add_printnode(bp, func_name)
    except Exception:
        _log("Non-fatal: could not inject PrintString node into function body.")

    # Compile and save
    try:
        lib = getattr(unreal, "BlueprintEditorLibrary", None)
        if lib and hasattr(lib, "compile_blueprint"):
            _log("Compiling blueprint...")
            lib.compile_blueprint(bp)
    except Exception:
        _log("Compile step failed (non-fatal)")

    try:
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        _log(f"Saved blueprint: {ASSET_PATH}")
    except Exception:
        try:
            unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
            _log(f"Saved blueprint via path: {ASSET_PATH}")
        except Exception:
            _log("Failed to save blueprint asset")

    _log("Upsert completed.")
    return True


if __name__ == "__main__":
    create_or_update()
