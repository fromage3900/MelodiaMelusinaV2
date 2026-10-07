"""Headless Gate 0A verifier for the Melodia Houdini Studio package.

Run through hython (the installer does this with -Verify):

    hython deploy/houdini/verify_melodia_studio.py

Proves, without a GUI:
  * the local package pointer resolves to this repository,
  * the committed package's environment and HOUDINI_PATH entry are live,
  * both desktops and the Melodia shelf are discoverable,
  * the shelf parses and exposes the eight expected tools,
  * melodia_studio imports and every tool runs without a missing path,
  * both .desk files are structurally valid,
  * no local desktop override silently shadows a repo desktop (warn only),
  * no committed package file contains a machine-local path.

Writes ``Saved/Audit/houdini_studio/setup_<stamp>.json`` and exits non-zero
when any required check fails.

GUI acceptance (desktop actually appears, switches, survives reload, and looks
right) is intentionally NOT covered here - that remains owner-held.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time

CHECKS = []


def check(name, ok, detail, required=True):
    CHECKS.append(
        {"name": name, "ok": bool(ok), "required": bool(required), "detail": str(detail)}
    )
    flag = "PASS" if ok else ("FAIL" if required else "warn")
    print("[%s] %-22s %s" % (flag, name, detail))
    return bool(ok)


_ALLOWED_DESK_MODES = frozenset(
    """sceneview imageview details chaneditor python pythonpanel neteditor
    parmeditor materialpalette perfmon bundlelist datatree textport renderview
    rendergallery channelview contextview treecontrol parmsheet""".split()
)

_EXPECTED_TOOLS = (
    ("melodia_project", "Project"),
    ("melodia_animation_doctor", "AnimationDoctor"),
    ("melodia_shorewake", "Shorewake"),
    ("melodia_vellum_cache", "Vellum Cache"),
    ("melodia_copernicus", "Copernicus"),
    ("melodia_foundry_validate", "Foundry Validate"),
    ("melodia_evidence", "Evidence"),
    ("melodia_ue_handoff", "UE Handoff"),
)


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def houdini_find(relative):
    """hou.findFile raises instead of returning '' when nothing matches."""
    try:
        import hou

        return hou.findFile(relative) or ""
    except Exception:
        return ""


def check_desk(path, hou):
    """Structural validation of a .desk file. Returns (ok, detail)."""
    if not os.path.isfile(path):
        return False, "missing file: %s" % path
    text = read_text(path)

    problems = []
    if text.count("{") != text.count("}"):
        problems.append("brace mismatch %d/%d" % (text.count("{"), text.count("}")))
    if not re.search(r"^\s*root\s*\{", text, re.MULTILINE):
        problems.append("no root block")

    # Only pane definition lines carry a pane mode; trailing config lines use
    # their own -m flags (viewerstow ... -m hide, geospreadsheet ... -m none).
    modes = re.findall(r"^\s*pane\s+\S+\s+-a\b[^\n]*?-m\s+(\w+)", text, re.MULTILINE)
    unknown = sorted(set(m for m in modes if m not in _ALLOWED_DESK_MODES))
    if unknown:
        problems.append("unknown -m tokens: %s" % ",".join(unknown))
    if "-m sceneview" not in text:
        problems.append("no scene view pane")

    # Pane definitions: "<tabs ...> { pane <name> -a ..." lines.
    defined = set(re.findall(r"^\s*pane\s+(\S+)\s+-a\s+", text, re.MULTILINE))
    counts = re.findall(r"^\s*pane\s+(\S+)\s+-a\s+", text, re.MULTILINE)
    dupes = sorted(set(n for n in counts if counts.count(n) > 1))
    if dupes:
        problems.append("duplicate pane names: %s" % ",".join(dupes))

    # Trailing config lines must only point at panes that were defined above.
    referenced = set(re.findall(r"\bpanetab\w*\b", text)) - defined
    if referenced:
        problems.append("references undefined panes: %s" % ",".join(sorted(referenced)))

    # Shelf set named in shelfdock must be defined by our shelf file.
    for match in re.findall(r"^\s*shelfdock\b.*\badd\s+(.+)$", text, re.MULTILINE):
        for shelf_set in match.split():
            if shelf_set.startswith("melodia") and shelf_set != "melodia_shelf_set":
                problems.append("unexpected melodia shelf set: %s" % shelf_set)

    if problems:
        return False, "; ".join(problems)
    return True, "%d panes, %d mode tokens, %d shelf sets" % (
        len(defined),
        len(modes),
        len(re.findall(r"\badd\s+\S+", text)),
    )


def check_no_machine_paths(root):
    """Committed package files must not carry a drive letter or a user name.

    Scans source *and* docs (``.md``) so a README added next to the package
    cannot quietly document a machine-local path.
    """
    # Single letter + colon + separator. The lookbehind keeps English prose
    # such as "written:\n" from being read as a drive letter.
    banned = re.compile(
        r"(?<![A-Za-z])[A-Za-z]:[\\/]|AppData[\\/]|\bUsers[\\/]|\bhoudini2\d",
        re.IGNORECASE,
    )
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if not name.endswith((".py", ".json", ".desk", ".shelf", ".ps1", ".md")):
                continue
            path = os.path.join(dirpath, name)
            for number, line in enumerate(read_text(path).splitlines(), 1):
                if banned.search(line):
                    hits.append("%s:%d: %s" % (os.path.relpath(path, root), number, line.strip()[:80]))
    if hits:
        return False, "; ".join(hits[:5])
    return True, "scanned %s" % os.path.basename(root)


def main():
    import hou

    print("=" * 72)
    print("Melodia Houdini Studio - Gate 0A headless verification")
    print("=" * 72)

    houdini_root = os.path.abspath(hou.homeHoudiniDirectory().replace("/", os.sep))
    repo_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    # __file__ = <repo>/deploy/houdini/verify_melodia_studio.py -> up 3 = <repo>

    # 1. Local pointer -------------------------------------------------------
    pointer_path = os.path.join(houdini_root, "packages", "melodia_studio_local.json")
    pointer_ok, pointer_detail = False, "missing: %s" % pointer_path
    if os.path.isfile(pointer_path):
        try:
            payload = json.loads(read_text(pointer_path))
            target = payload.get("package_path", "")
            expected = os.path.join(repo_root, "deploy", "houdini", "packages")
            pointer_ok = os.path.normcase(os.path.normpath(target)) == os.path.normcase(
                os.path.normpath(expected)
            )
            pointer_detail = "package_path=%s" % target
        except Exception as exc:
            pointer_detail = "unreadable: %s" % exc
    check("pointer_installed", pointer_ok, pointer_detail)

    # 2. Committed package is live ------------------------------------------
    env_root = hou.getenv("MELODIA_ROOT") or ""
    repo_ok = bool(env_root) and os.path.isdir(os.path.join(env_root, "deploy")) and os.path.isdir(
        os.path.join(env_root, "Content")
    )
    check("package_env", repo_ok, "MELODIA_ROOT=%s" % env_root)

    package_root = hou.getenv("MELODIA_PACKAGE_ROOT") or ""
    path_entries = [e.strip() for e in (hou.getenv("HOUDINI_PATH") or "").split(os.pathsep)]
    norm = lambda p: os.path.normcase(os.path.normpath(p))
    hpath_ok = bool(package_root) and norm(package_root) in [norm(e) for e in path_entries if e]
    check("houdini_path", hpath_ok, "package root on HOUDINI_PATH: %s" % package_root)

    # 3. Desktops discoverable ------------------------------------------------
    desk_names = []
    for name in ("Melodia_Studio", "Melodia_KineFX"):
        resolved = houdini_find("desktop/%s.desk" % name)
        ok = bool(resolved) and os.path.isfile(resolved)
        if ok:
            desk_names.append(name)
        check("desk_discovered", ok, "%s -> %s" % (name, resolved or "(not found)"))

    # 3b. Local desktop overrides -------------------------------------------
    # Houdini writes "Save Current Desktop" output to <user pref>/desktop/.
    # If a local copy of one of our desktops lands there it shadows the repo
    # copy on the next launch, so later repo improvements stop being visible
    # until that local file is promoted or deleted. A local override is legal,
    # so this warns rather than fails - it exists so the shadowing is never
    # silent.
    for name in desk_names or ("Melodia_Studio", "Melodia_KineFX"):
        shadow = os.path.join(houdini_root, "desktop", "%s.desk" % name)
        if not os.path.isfile(shadow):
            check("desk_local_override", True,
                  "%s: no local override, repo copy is authoritative" % name,
                  required=False)
            continue
        repo_desk = os.path.join(
            repo_root, "deploy", "houdini", "melodia_studio", "desktop", "%s.desk" % name
        )
        identical = os.path.isfile(repo_desk) and read_text(shadow) == read_text(repo_desk)
        if identical:
            detail = "%s: local copy is byte-identical to the repo copy (%s)" % (name, shadow)
        else:
            detail = ("%s: local copy DIFFERS from the repo copy (%s) - repo changes are "
                      "being shadowed; delete the local file or promote it into "
                      "deploy/houdini/melodia_studio/desktop/" % (name, shadow))
        check("desk_local_override", False, detail, required=False)

    # 4. Shelf discoverable ---------------------------------------------------
    shelf_file = houdini_find("toolbar/Melodia.shelf")
    check("shelf_file", bool(shelf_file) and os.path.isfile(shelf_file),
          shelf_file or "(not found)")

    # hou.shelves.shelves() returns a dict of name -> hou.Shelf in H22 (it has
    # also existed as a tuple), so resolve through a small adapter.
    shelf, shelf_names, shelf_error = None, set(), None
    try:
        table = hou.shelves.shelves()
        if isinstance(table, dict):
            shelf_names = set(str(k) for k in table)
            shelf = table.get("melodia")
            if isinstance(shelf, str):
                shelf = None
        else:
            for item in table:
                key = item if isinstance(item, str) else item.name()
                shelf_names.add(str(key))
                if str(key) == "melodia":
                    shelf = None if isinstance(item, str) else item
    except Exception as exc:
        shelf_error = "%s: %s" % (exc.__class__.__name__, exc)

    if shelf_error:
        check("shelf_loaded", False, "hou.shelves.shelves() raised: %s" % shelf_error)
    else:
        check("shelf_loaded", shelf is not None,
              "'melodia' %s (%d shelves registered)"
              % ("present" if shelf else "MISSING", len(shelf_names)))

    # 5. Shelf tools ----------------------------------------------------------
    if shelf is not None:
        actual, tools_error = {}, None
        try:
            for tool in shelf.tools():
                actual[tool.name()] = tool.label()
        except Exception as exc:
            tools_error = "%s: %s" % (exc.__class__.__name__, exc)
        if tools_error:
            check("shelf_tools", False, "shelf.tools() raised: %s" % tools_error)
        else:
            missing = [n for n, _ in _EXPECTED_TOOLS if n not in actual]
            wrong = ["%s=%s" % (n, actual.get(n)) for n, lbl in _EXPECTED_TOOLS
                     if n in actual and actual[n] != lbl]
            ok = not missing and not wrong
            detail = "%d/%d tools" % (len(actual), len(_EXPECTED_TOOLS))
            if missing:
                detail += " missing: %s" % ",".join(missing)
            if wrong:
                detail += " mislabelled: %s" % ",".join(wrong)
            check("shelf_tools", ok, detail)
    else:
        check("shelf_tools", False, "shelf not loaded")

    # 6. Python module --------------------------------------------------------
    module = None
    try:
        import melodia_studio

        module = melodia_studio
        info = melodia_studio.project.info()
        ok = info.get("repo_root") == repo_root and bool(info.get("package_root"))
        check("module_import", ok, "%s" % getattr(melodia_studio, "__file__", "?"))
    except Exception as exc:
        check("module_import", False, "%s: %s" % (exc.__class__.__name__, exc))

    # 7. .desk structural syntax ---------------------------------------------
    desk_dir = os.path.join(repo_root, "deploy", "houdini", "melodia_studio", "desktop")
    for name in desk_names or ("Melodia_Studio", "Melodia_KineFX"):
        ok, detail = check_desk(os.path.join(desk_dir, "%s.desk" % name), hou)
        check("desk_syntax", ok, "%s: %s" % (name, detail))

    # 8. Shelf/desk shelf-set cross reference --------------------------------
    shelf_xml = os.path.join(
        repo_root, "deploy", "houdini", "melodia_studio", "toolbar", "Melodia.shelf"
    )
    if os.path.isfile(shelf_xml):
        text = read_text(shelf_xml)
        ok = '<shelfSet name="melodia_shelf_set"' in text
        check("shelf_set_defined", ok, "melodia_shelf_set in Melodia.shelf: %s" % ok)
    else:
        check("shelf_set_defined", False, "shelf file missing")

    # 9. Every tool launches ---------------------------------------------------
    # Shelf tool ids are "<module key>" prefixed with "melodia_" - prove both
    # directions of the wiring: every shelf tool has a module handler and the
    # module registers exactly those handlers.
    if module is not None:
        handlers = getattr(module, "_TOOLS", None)
        if not isinstance(handlers, dict):
            check("tool_registry", False, "_TOOLS is not a dict: %r" % type(handlers))
            handlers = {}
        else:
            check("tool_registry", True, "%d handlers: %s"
                  % (len(handlers), ",".join(sorted(handlers))))

        module_keys = set()
        for shelf_id, _label in _EXPECTED_TOOLS:
            key = shelf_id[len("melodia_"):] if shelf_id.startswith("melodia_") else shelf_id
            module_keys.add(key)
            func = handlers.get(key)
            if func is None:
                check("tool_launch", False, "%s -> melodia_studio._TOOLS[%r] missing" % (shelf_id, key))
                continue
            try:
                text = func()
                ok = isinstance(text, str) and len(text.strip()) > 0
                first = (text.strip().splitlines() or [""])[0][:70]
                check("tool_launch", ok, "%s -> %s" % (shelf_id, first))
            except Exception as exc:
                check("tool_launch", False, "%s raised %s: %s" % (shelf_id, exc.__class__.__name__, exc))

        orphan = sorted(set(handlers) - module_keys)
        check("tool_wiring", not orphan,
              "unreachable handlers: %s" % (",".join(orphan) if orphan else "none"))
    else:
        check("tool_launch", False, "module unavailable")

    # 10. No machine-local paths in any committed package file ---------------
    # One walk over the whole deploy/houdini tree: plugin content, package
    # definition, installer, verifier and docs. Source scans alone would miss
    # the installer and any README sitting beside it.
    ok, detail = check_no_machine_paths(os.path.join(repo_root, "deploy", "houdini"))
    check("no_machine_paths", ok, detail)

    # Manifest ---------------------------------------------------------------
    failed = [c for c in CHECKS if c["required"] and not c["ok"]]
    manifest = {
        "gate": "0A",
        "houdini_version": hou.applicationVersionString(),
        "repo_root": repo_root,
        "package_root": package_root,
        "pointer_path": pointer_path,
        "desktops": desk_names,
        "shelf": "melodia" if shelf else None,
        "shelf_tools": [n for n, _ in _EXPECTED_TOOLS],
        "headless_ok": not failed,
        "gui_acceptance": "owner-held: desktop visible, switch, reload survival, screenshots",
        "checks": CHECKS,
    }

    target = None
    if module is not None:
        try:
            target = module.evidence.write("setup", manifest)
        except Exception as exc:
            print("[warn] evidence write failed: %s" % exc)
    if target is None:
        out_dir = os.path.join(repo_root, "Saved", "Audit", "houdini_studio")
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        target = os.path.join(out_dir, "setup_%s.json" % time.strftime("%Y%m%d_%H%M%S"))
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)

    print("-" * 72)
    print("required checks : %d" % len([c for c in CHECKS if c["required"]]))
    print("failures        : %d" % len(failed))
    print("manifest        : %s" % target)
    print("evidence level  : headless package/shelf/module discovery proven;"
          " GUI desktop acceptance still owed by the owner")
    print("=" * 72)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
