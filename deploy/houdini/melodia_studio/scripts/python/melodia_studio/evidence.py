"""Melodia Houdini Studio - setup evidence manifests.

Writes small JSON receipts under ``<repo>/Saved/Audit/houdini_studio``.
``Saved/Audit/*.json`` is allowlisted in the pre-commit hook, so these need
no extra sign-off.
"""

from __future__ import annotations

import json
import os
import time

from . import project


def stamp():
    return time.strftime("%Y%m%d_%H%M%S")


def manifest_dir(create=True):
    path = os.path.join(project.audit_root(), "houdini_studio")
    if create and not os.path.isdir(path):
        os.makedirs(path)
    return path


def write(name, payload):
    """Write ``<name>_<stamp>.json`` and return the absolute path."""
    target = os.path.join(manifest_dir(), "%s_%s.json" % (name, stamp()))
    body = {"schema": "melodia.houdini_studio.manifest/1", "name": name}
    body.update(project.info())
    body.update(payload or {})
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(body, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return target


def recent(limit=5):
    """Newest manifest paths, newest first."""
    folder = manifest_dir(create=False)
    if not os.path.isdir(folder):
        return []
    names = [n for n in os.listdir(folder) if n.endswith(".json")]
    names.sort(reverse=True)
    return [os.path.join(folder, n) for n in names[:limit]]
