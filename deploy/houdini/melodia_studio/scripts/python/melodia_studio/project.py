"""Melodia Houdini Studio - project path and environment helpers.

Every path in this module is derived from the repository root at runtime.
No drive letter, user name or machine-local path is ever hardcoded here.
"""

from __future__ import annotations

import os

_PACKAGE_REL = os.path.join("deploy", "houdini", "melodia_studio")
_ENV_KEYS = (
    "MELODIA_ROOT",
    "MELODIA_HOUDINI_ROOT",
    "MELODIA_HDA_ROOT",
    "MELODIA_AUDIT_ROOT",
    "MELODIA_CACHE_ROOT",
    "MELODIA_PACKAGE_ROOT",
)


def _looks_like_repo(path):
    """A repo root carries both ``deploy`` and ``Content``."""
    if not path:
        return False
    return os.path.isdir(os.path.join(path, "deploy")) and os.path.isdir(
        os.path.join(path, "Content")
    )


def _env(name):
    """Read a package-provided environment variable from hou, then os.environ."""
    try:
        import hou

        value = hou.getenv(name)
        if value:
            return value
    except Exception:
        pass
    return os.environ.get(name)


def _resolve_git_dir(repo):
    dot_git = os.path.join(repo, ".git")
    if os.path.isdir(dot_git):
        return dot_git
    if os.path.isfile(dot_git):
        try:
            with open(dot_git, "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    line = line.strip()
                    if line.startswith("gitdir:"):
                        target = line.split(":", 1)[1].strip()
                        if not os.path.isabs(target):
                            target = os.path.join(repo, target)
                        return target
        except OSError:
            return None
    return None


def repo_root():
    """Absolute repository root, resolved from the package env or this file."""
    env_root = _env("MELODIA_ROOT")
    if env_root:
        candidate = os.path.abspath(env_root)
        if _looks_like_repo(candidate):
            return candidate

    path = os.path.abspath(os.path.dirname(__file__))
    for _ in range(10):
        if _looks_like_repo(path):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent

    # Last resort: walk the documented layout <repo>/deploy/houdini/<pkg>/scripts/python/<pkg>
    path = os.path.abspath(os.path.dirname(__file__))
    for _ in range(6):
        path = os.path.dirname(path)
    return path


def package_root():
    """The HOUDINI_PATH root of the Melodia Studio package."""
    env_root = _env("MELODIA_PACKAGE_ROOT")
    if env_root and os.path.isdir(env_root):
        return os.path.abspath(env_root)
    return os.path.join(repo_root(), _PACKAGE_REL)


def hda_root():
    env_root = _env("MELODIA_HDA_ROOT")
    if env_root:
        return os.path.abspath(env_root)
    return os.path.join(repo_root(), "hda")


def audit_root():
    env_root = _env("MELODIA_AUDIT_ROOT")
    if env_root:
        return os.path.abspath(env_root)
    return os.path.join(repo_root(), "Saved", "Audit")


def cache_root():
    env_root = _env("MELODIA_CACHE_ROOT")
    if env_root:
        return os.path.abspath(env_root)
    return os.path.join(repo_root(), "Saved", "HoudiniFoundry")


def houdini_version():
    try:
        import hou

        return hou.applicationVersionString()
    except Exception:
        return "unknown"


def git_head():
    """Short commit id read straight from the object store - no subprocess."""
    git_dir = _resolve_git_dir(repo_root())
    if not git_dir:
        return None
    try:
        with open(os.path.join(git_dir, "HEAD"), "r", encoding="utf-8", errors="replace") as handle:
            head = handle.read().strip()
    except OSError:
        return None
    if not head.startswith("ref:"):
        return head[:12]
    ref_name = head.split(":", 1)[1].strip()
    ref_path = os.path.join(git_dir, *ref_name.split("/"))
    try:
        with open(ref_path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().strip()[:12]
    except OSError:
        return ref_name


def env_report():
    """Resolved MELODIA_* values, empty string when not provided."""
    return dict((key, _env(key) or "") for key in _ENV_KEYS)


def on_houdini_path():
    """True when the package root is present in HOUDINI_PATH."""
    root = os.path.normcase(os.path.normpath(package_root()))
    try:
        import hou

        raw = hou.getenv("HOUDINI_PATH") or ""
    except Exception:
        raw = os.environ.get("HOUDINI_PATH") or ""
    for entry in raw.split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        if os.path.normcase(os.path.normpath(entry)) == root:
            return True
    return False


def scan(root, match, limit=40, max_depth=6):
    """Depth-capped, result-capped case-insensitive filename search."""
    import fnmatch

    hits = []
    if not root or not os.path.isdir(root):
        return hits
    root = os.path.abspath(root)
    needle = match.lower()
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath[len(root):].count(os.sep)
        if depth >= max_depth:
            dirnames[:] = []
        dirnames[:] = [
            name
            for name in dirnames
            if not name.startswith(".") and name not in ("Intermediate", "Binaries")
        ]
        for name in filenames:
            if fnmatch.fnmatch(name.lower(), needle):
                hits.append(os.path.join(dirpath, name))
                if len(hits) >= limit:
                    return hits
    return hits


def list_dir(root, limit=25):
    """Shallow listing of an existing directory."""
    if not root or not os.path.isdir(root):
        return []
    entries = sorted(os.listdir(root))
    return entries[:limit]


def info():
    """Machine readable project facts - shared by the shelf and the verifier."""
    data = {
        "repo_root": repo_root(),
        "package_root": package_root(),
        "houdini_version": houdini_version(),
        "git_head": git_head(),
        "on_houdini_path": on_houdini_path(),
    }
    data.update(env_report())
    return data
