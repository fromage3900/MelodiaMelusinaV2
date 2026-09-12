"""Insert the Resonance Ecology processor into the Sea Above PCG biome graphs.

Expands the existing Sea Above derivatives (decision 057) rather than replacing
them: every graph keeps its own generators, splines, raycast grounding and mesh
choices. This only splices one PCGPythonDataProcessor in front of each
StaticMeshSpawner so the points arriving at the spawner carry

    Resonance  EcologyClass  MaterialVariant  ScaleBias

and configures that spawner to pack Resonance as per-instance custom data so a
material can read it. The processor composes with upstream scale/density, so the
authored look of each biome survives.

The shared hero graphs under PCG/Musical/Hero are deliberately NOT touched --
same rule ground_sea_above_pcg.py follows.

Run inside the editor:
    exec(open(r"...\apply_resonance_to_sea_above.py").read())
"""

import unreal

SCRIPT_PATH = (
    "C:/EnvironmentPortfolio/BS_GodFile/Content/Python/pcg/"
    "resonance_ecology_processor.py"
)
STYLE_ROOT = "/Game/EnvSandbox/PCG/Styles/SeaAbove"
RESONANCE_ATTR = "Resonance"

DRY_RUN = False

# Pins we must never mistake for the data input.
_CONTROL_PINS = {"Execution Dependency", "Overrides"}


def _log(msg):
    print("[ResonanceSeaAbove] %s" % msg)


def _settings_class_name(node):
    s = node.get_settings()
    return s.get_class().get_name() if s else ""


def _data_input_pin(node):
    for pin in node.input_pins:
        label = str(pin.get_editor_property("properties").get_editor_property("label"))
        if label not in _CONTROL_PINS:
            return label
    return None


def _data_output_pin(node):
    """Pick the data output by name. output_pins[0] on the Python processor is
    "Execution Dependency", so indexing silently produces a control-pin edge that
    carries no points and leaves the spawner with nothing to instance."""
    labels = [
        str(p.get_editor_property("properties").get_editor_property("label"))
        for p in node.output_pins
    ]
    for label in labels:
        if label not in _CONTROL_PINS:
            return label
    return labels[0] if labels else None


def _is_resonance_processor(node):
    if _settings_class_name(node) != "PCGPythonDataProcessorSettings":
        return False
    s = node.get_settings()
    try:
        fp = s.get_editor_property("script_path").get_editor_property("file_path")
    except Exception:
        return False
    return "resonance_ecology_processor" in str(fp).replace("\\", "/")


def _make_processor(graph, position):
    node, settings = graph.add_node_of_type(unreal.PCGPythonDataProcessorSettings)
    settings.set_editor_property(
        "script_input_method", unreal.PCGPythonScriptInputMethod.FILE
    )
    fp = unreal.FilePath()
    fp.set_editor_property("file_path", SCRIPT_PATH)
    settings.set_editor_property("script_path", fp)
    node.set_node_position(int(position[0]), int(position[1]))
    return node


def _configure_packer(spawner_node):
    """Pack Resonance as per-instance custom data on this spawner."""
    s = spawner_node.get_settings()
    packer = s.get_editor_property("instance_data_packer_parameters")
    if packer is None or packer.get_class().get_name() != "PCGInstanceDataPackerByAttribute":
        # InstanceDataPackerParameters is read-only from Python; assigning the
        # *type* makes the engine construct the instance, same as the details panel.
        s.set_editor_property("instance_data_packer_type", unreal.PCGInstanceDataPackerByAttribute)
        packer = s.get_editor_property("instance_data_packer_parameters")
    if packer is None:
        return "packer unavailable"

    existing = list(packer.get_editor_property("attribute_selectors") or [])
    for sel in existing:
        if RESONANCE_ATTR in str(sel.export_text()):
            return "already packed"

    sel = unreal.PCGAttributePropertyInputSelector()
    # set_attribute_name has value semantics through Python; import_text is the
    # only reliable way to set a selector from script.
    sel.import_text("PCGBegin(%s)PCGEnd" % RESONANCE_ATTR)
    packer.set_editor_property("attribute_selectors", existing + [sel])
    return "packed %s" % RESONANCE_ATTR


def repair_processor_edges(graph):
    """Re-seat any resonance-processor edge that leaves a control pin."""
    fixed = 0
    for edge in list(graph.get_all_edges()):
        src = edge.get_input_node()
        if not _is_resonance_processor(src):
            continue
        src_pin = str(edge.get_input_pin_label())
        if src_pin not in _CONTROL_PINS:
            continue
        dst = edge.get_output_node()
        dst_pin = str(edge.get_output_pin_label())
        good = _data_output_pin(src)
        graph.remove_edge(src, src_pin, dst, dst_pin)
        graph.add_edge(src, good, dst, dst_pin)
        fixed += 1
    return fixed


def apply_to_graph(graph_path):
    graph = unreal.load_asset(graph_path)
    if graph is None:
        return "MISSING %s" % graph_path

    name = graph_path.split("/")[-1]
    spawners = [
        n for n in graph.get_editor_property("nodes")
        if _settings_class_name(n) == "PCGStaticMeshSpawnerSettings"
    ]
    if not spawners:
        return "%-42s no StaticMeshSpawner -- skipped" % name

    inserted = 0
    skipped = 0
    packed = []
    repaired = repair_processor_edges(graph)

    for spawner in spawners:
        in_label = _data_input_pin(spawner)
        feeders = [
            e for e in graph.get_all_edges()
            if e.get_output_node() == spawner
            and str(e.get_output_pin_label()) == in_label
        ]
        if not feeders:
            skipped += 1
            continue

        for edge in feeders:
            src = edge.get_input_node()
            src_pin = str(edge.get_input_pin_label())
            if _is_resonance_processor(src):
                skipped += 1
                continue

            sx, sy = src.get_node_position()
            dx, dy = spawner.get_node_position()
            pos = ((sx + dx) / 2.0, (sy + dy) / 2.0 - 150)

            if DRY_RUN:
                _log("  would splice %s.%s -> [Resonance] -> %s.%s"
                     % (_settings_class_name(src), src_pin,
                        _settings_class_name(spawner), in_label))
                inserted += 1
                continue

            proc = _make_processor(graph, pos)
            p_in = _data_input_pin(proc)
            p_out = _data_output_pin(proc)

            graph.remove_edge(src, src_pin, spawner, in_label)
            graph.add_edge(src, src_pin, proc, p_in)
            graph.add_edge(proc, p_out, spawner, in_label)
            inserted += 1

        if not DRY_RUN:
            packed.append(_configure_packer(spawner))

    return "%-42s spawners=%d inserted=%d skipped=%d repaired=%d  %s" % (
        name, len(spawners), inserted, skipped, repaired,
        "; ".join(sorted(set(packed)))
    )


def remove_from_graph(graph_path):
    """Take the resonance processors back out and re-seat the original edges.

    Note: disabling the node is NOT equivalent -- a disabled PCGPythonDataProcessor
    emits nothing on its Output pin, so every downstream spawner starves. Removal
    has to reconnect the upstream node to the spawner directly.
    """
    graph = unreal.load_asset(graph_path)
    if graph is None:
        return "MISSING %s" % graph_path

    removed = 0
    for node in list(graph.get_editor_property("nodes")):
        if not _is_resonance_processor(node):
            continue
        ups, downs = [], []
        for edge in list(graph.get_all_edges()):
            if edge.get_output_node() == node:
                ups.append((edge.get_input_node(), str(edge.get_input_pin_label()),
                            str(edge.get_output_pin_label())))
            elif edge.get_input_node() == node:
                downs.append((str(edge.get_input_pin_label()),
                              edge.get_output_node(), str(edge.get_output_pin_label())))
        for src, src_pin, _ in ups:
            for _, dst, dst_pin in downs:
                graph.add_edge(src, src_pin, dst, dst_pin)
        graph.remove_node(node)
        removed += 1
    return "%-42s removed=%d" % (graph_path.split("/")[-1], removed)


def discover_sea_above_graphs():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    out = []
    for a in ar.get_assets_by_path(STYLE_ROOT, recursive=True):
        path = str(a.package_name)
        if path.split("/")[-1].startswith("PCG_SeaAbove"):
            out.append(path)
    return sorted(out)


def main(targets=None):
    targets = targets or discover_sea_above_graphs()
    _log("targets: %d  (DRY_RUN=%s)" % (len(targets), DRY_RUN))
    results = [apply_to_graph(t) for t in targets]
    for r in results:
        _log(r)
    if not DRY_RUN:
        saved = unreal.EditorAssetLibrary.save_directory(STYLE_ROOT, False, True)
        _log("save_directory(%s) -> %s" % (STYLE_ROOT, saved))
    return results


if __name__ == "__main__":
    main()
