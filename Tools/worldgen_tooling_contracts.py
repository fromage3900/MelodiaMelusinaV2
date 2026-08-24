"""Pure, offline verdict contracts for Blender/world-generation tooling.

Keep these checks free of ``bpy`` so ordinary Python unit tests can prove that
the Blender-side runners fail closed when evidence is missing or malformed.
"""

import hashlib
import os


def builder_entry_passes(entry):
    """Return True only when a Geometry Nodes probe has usable geometry."""
    if entry.get("errors"):
        return False
    if entry.get("nodes", 0) <= 0 or entry.get("links", 0) <= 0:
        return False
    if entry.get("outputs", 0) <= 0:
        return False
    if entry.get("duplicate_inputs", False):
        return False
    if entry.get("nan_values", True) or entry.get("nan_vertices", True):
        return False
    if entry.get("verts", 0) <= 0:
        return False
    if entry.get("edges", 0) <= 0 and entry.get("polygons", 0) <= 0:
        return False
    if entry.get("zero_area_faces", 0) > 0:
        return False
    return True


def scene_entry_passes(entry):
    """Return True only when a scene opened, measured, and rendered."""
    if entry.get("errors"):
        return False
    if not entry.get("opened") or not entry.get("preview_ok"):
        return False
    stats = entry.get("stats") or {}
    return (
        stats.get("objects", 0) > 0
        and stats.get("meshes", 0) > 0
        and stats.get("triangles", 0) > 0
    )


def report_exit_code(report):
    """Map an evidence report to a process code; anything but PASS fails."""
    return 0 if report.get("verdict") == "PASS" else 1


def daemon_run_passes(run, preset_count):
    """Validate that every discovered MIDI/preset job was accounted for."""
    midi_found = run.get("midi_found", 0)
    expected = midi_found * preset_count
    accounted = run.get("processed", 0) + run.get("skipped", 0)
    return midi_found > 0 and run.get("errors", 0) == 0 and accounted == expected


def sha256_file(path):
    """Return a stable content digest for an evidence artifact."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_is_within(path, root):
    """Return True when an absolute path stays under an allowlisted root."""
    path = os.path.abspath(os.fspath(path))
    root = os.path.abspath(os.fspath(root))
    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False
