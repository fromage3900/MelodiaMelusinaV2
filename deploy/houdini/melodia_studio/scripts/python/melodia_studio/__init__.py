"""Melodia Houdini Studio package.

Installed by ``deploy/houdini/install_melodia_studio.ps1``. Every path is
resolved from the repository root at runtime (``melodia_studio.project``),
so nothing in this package is machine specific.
"""

from __future__ import annotations

import os

from . import evidence, project

__version__ = "1.0.0"

# Lazily filled: name -> zero argument callable returning a str report.
_TOOLS = {}


def _rel(path):
    """Repo-relative path when possible, absolute otherwise. Always / separators."""
    root = project.repo_root()
    try:
        if os.path.normcase(path).startswith(os.path.normcase(root)):
            return os.path.relpath(path, root).replace("\\", "/")
    except Exception:
        pass
    return path.replace("\\", "/")


def _lines(paths, limit=20):
    if not paths:
        return ["  (nothing found)"]
    out = ["  - %s" % _rel(p) for p in paths[:limit]]
    if len(paths) > limit:
        out.append("  ... and %d more" % (len(paths) - limit))
    return out


def project_message():
    info = project.info()
    env = project.env_report()
    lines = [
        "Melodia Houdini Studio %s" % __version__,
        "",
        "repo root   : %s" % info["repo_root"],
        "package root: %s" % info["package_root"],
        "on HOUDINI_PATH: %s" % ("yes" if info["on_houdini_path"] else "NO"),
        "Houdini     : %s" % info["houdini_version"],
        "git HEAD    : %s" % (info["git_head"] or "unknown"),
        "",
        "package environment:",
    ]
    for key in sorted(env):
        lines.append("  %-22s = %s" % (key, env[key] or "(unset)"))
    return "\n".join(lines)


def animation_doctor_message():
    root = project.repo_root()
    hits = []
    hits += project.scan(os.path.join(root, "Saved", "Audit"), "*doctor*", limit=30)
    hits += project.scan(os.path.join(root, "Content", "Python"), "*doctor*", limit=20)
    hits += project.scan(os.path.join(root, "Tools", "Houdini"), "*doctor*", limit=20)
    seen, unique = set(), []
    for path in hits:
        key = os.path.normcase(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    lines = ["AnimationDoctor artifacts under this repo", "  %d found" % len(unique)]
    lines += _lines(unique)
    if not unique:
        lines.append("  Nothing recovered yet - this is a lookup tool, not a failure.")
    return "\n".join(lines)


def shorewake_message():
    root = project.repo_root()
    hits = []
    hits += project.scan(os.path.join(root, "Imports"), "*shorewake*", limit=30)
    hits += project.scan(os.path.join(root, "Tools", "Houdini"), "*shorewake*", limit=20)
    hits += project.scan(os.path.join(root, "Saved"), "*shorewakedress*", limit=20)
    seen, unique = set(), []
    for path in hits:
        key = os.path.normcase(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    lines = ["Shorewake wardrobe sources inside this repo", "  %d found" % len(unique)]
    lines += _lines(unique)
    lines.append("  Staged copies outside the repo are intentionally not searched.")
    return "\n".join(lines)


def vellum_cache_message():
    cache = project.cache_root()
    entries = project.list_dir(cache, limit=40)
    total = 0
    if os.path.isdir(cache):
        for name in entries:
            path = os.path.join(cache, name)
            try:
                if os.path.isfile(path):
                    total += os.path.getsize(path)
            except OSError:
                pass
    lines = [
        "Vellum / cache root: %s" % _rel(cache),
        "exists: %s" % ("yes" if os.path.isdir(cache) else "no"),
        "entries: %d   (%.1f MB of loose files)" % (len(entries), total / 1048576.0),
    ]
    lines += _lines([os.path.join(cache, n) for n in entries], limit=20)
    return "\n".join(lines)


def copernicus_message():
    root = project.repo_root()
    tools = os.path.join(root, "Tools", "Houdini")
    copernicus = os.path.join(tools, "copernicus")
    lines = [
        "Copernicus lane",
        "scripts dir: %s" % _rel(copernicus),
        "  %s" % ("present" if os.path.isdir(copernicus) else "absent"),
    ]
    lines.append("listing:")
    lines += _lines([os.path.join(copernicus, n) for n in project.list_dir(copernicus)], limit=20)
    tidepool = project.scan(tools, "*tidepool*", limit=20)
    lines.append("tidepool matches under Tools/Houdini: %d" % len(tidepool))
    lines += _lines(tidepool)
    return "\n".join(lines)


def foundry_validate_message():
    root = project.repo_root()
    validator = os.path.join(root, "Tools", "Houdini", "foundry", "houdini_foundry.py")
    ok = os.path.isfile(validator)
    lines = [
        "Foundry validator",
        "  %s" % _rel(validator),
        "  present: %s" % ("yes" if ok else "NO"),
        "",
        "Run from a shell with the repo as cwd:",
        "  hython Tools/Houdini/foundry/houdini_foundry.py validate <paths...>",
        "  hython Tools/Houdini/foundry/houdini_foundry.py verify  <manifest>",
        "  hython Tools/Houdini/foundry/houdini_foundry.py probe   <paths...>",
        "",
        "This shelf tool only reports readiness; it never mutates the scene.",
    ]
    return "\n".join(lines)


def evidence_message():
    path = evidence.write("shelf_evidence", {"tool": "melodia_studio", "source": "shelf"})
    return "Evidence manifest written:\n  %s" % _rel(path)


def ue_handoff_message():
    return "\n".join(
        [
            "UE handoff contract (read-only from this lane)",
            "",
            "  beauty render target : /Game/Melodia/Lookdev/RT_UE_Beauty",
            "  beauty sender actor  : /Game/Melodia/Lookdev/BP_UE_BeautySender",
            "  integration map      : /Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",
            "  canonical heroine    : /Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
            "",
            "  One Unreal Editor, one Monolith writer: inspect -> mutate -> assert -> save.",
            "  Never Python-load skill Blueprints.",
            "  This Houdini lane never mutates UE assets.",
        ]
    )


_TOOLS = {
    "project": project_message,
    "evidence": evidence_message,
    "animation_doctor": animation_doctor_message,
    "shorewake": shorewake_message,
    "vellum_cache": vellum_cache_message,
    "copernicus": copernicus_message,
    "foundry_validate": foundry_validate_message,
    "ue_handoff": ue_handoff_message,
}

TOOL_IDS = tuple(sorted(_TOOLS))


def show(text, title="Melodia Studio"):
    """Display in the GUI when available, print when headless."""
    try:
        import hou

        ui = getattr(hou, "ui", None)
        if ui is not None and hasattr(ui, "displayMessage"):
            ui.displayMessage(str(text), title=title, buttons=("OK",))
            return
    except Exception:
        pass
    print("%s\n%s" % (title, text))


def launch(name):
    """Run one shelf tool. Never raises - failures are reported, not thrown."""
    func = _TOOLS.get(name)
    title = "Melodia Studio - %s" % name
    if func is None:
        show("Unknown Melodia tool: %s\nKnown: %s" % (name, ", ".join(TOOL_IDS)), title)
        return
    try:
        show(func(), title)
    except Exception as exc:  # pragma: no cover - defensive shelf path
        show("Tool '%s' failed:\n%s: %s" % (name, exc.__class__.__name__, exc), title)
