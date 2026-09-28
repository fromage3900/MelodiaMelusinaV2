"""Checks for staging_core.py - coordinate math, manifest IO, UE code generation.

    python verify_staging_core.py

Exit code 0 when every check passes, 1 otherwise. Filesystem checks use a
temporary directory so the real StageInbox is never touched, and ue_run_python
is exercised against a stub mcp_client.monolith (no editor required).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mcp_client  # noqa: E402  (stubbed below for the UE call check)
import staging_core as sc  # noqa: E402

RESULTS = []


def check(label, got, want):
    ok = got == want
    RESULTS.append((label, ok, got, want))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got  {got!r}\n        want {want!r}")


def check_true(label, cond, detail=""):
    RESULTS.append((label, bool(cond), detail, True))
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    if not cond and detail:
        print(f"        {detail}")


def check_coordinates():
    check("blender_to_ue_location(1,2,3) flips Y and scales x100",
          sc.blender_to_ue_location(1, 2, 3), (100.0, -200.0, 300.0))
    check("blender_to_ue_location rounds to 4 places",
          sc.blender_to_ue_location(0.1234567, -0.5, 0.0), (12.3457, 50.0, 0.0))
    check("blender_to_ue_location honours scale_factor",
          sc.blender_to_ue_location(1.5, -2.5, 0.0, scale_factor=10.0), (15.0, 25.0, 0.0))
    check("blender_to_ue_rotation negates only yaw",
          sc.blender_to_ue_rotation(10.0, 20.0, 30.0), (10.0, -20.0, 30.0))


def check_manifest_io(tmp):
    m = sc.create_manifest("unit_test", "blender", items=[{"name": "a"}])
    check("create_manifest sets the v2 format", m["format"], sc.SCHEMA_VERSION)
    check("create_manifest defaults the package root",
          m["target_package_root"], "/Game/MelodiaStaging")
    check("create_manifest keeps its items", m["items"], [{"name": "a"}])
    check("create_manifest defaults metadata/snap",
          (m["metadata"], m["snap_json_path"]), ({}, None))

    empty_a = sc.create_manifest("a", "blender")
    empty_b = sc.create_manifest("b", "blender")
    empty_a["items"].append({"name": "leak"})
    check_true("create_manifest does not share its default item list",
               empty_b["items"] == [], f"second manifest items: {empty_b['items']}")

    nested = os.path.join(tmp, "deep", "nested", "manifest.json")
    sc.write_manifest(m, nested)
    check_true("write_manifest creates missing parent folders", os.path.isfile(nested), nested)
    check("read_manifest round-trips", sc.read_manifest(nested), m)

    missing = os.path.join(tmp, "does_not_exist.json")
    try:
        sc.read_manifest(missing)
        check_true("read_manifest raises FileNotFoundError when absent", False, "no exception")
    except FileNotFoundError:
        check_true("read_manifest raises FileNotFoundError when absent", True)

    inbox = os.path.join(tmp, "inbox")
    written = sc.drop_manifest_to_inbox(m, inbox_dir=inbox)
    check("drop_manifest_to_inbox names the file after the manifest id",
          os.path.basename(written), "unit_test.stage_manifest.json")
    check_true("drop_manifest_to_inbox creates the inbox folder", os.path.isdir(inbox), inbox)
    check("staged manifest reads back unchanged", sc.read_manifest(written), m)


def check_codegen():
    manifest = sc.create_manifest(
        "codegen_test", "blender",
        target_package_root="/Game/UnitTestRoot",
        items=[{"kind": "static_mesh", "name": "SM_Unit",
                "file_path": __file__, "spawn_actor": True,
                "location": [1.0, 2.0, 3.0]}],
    )
    code = sc.generate_ue_staging_code(manifest)
    check_true("generate_ue_staging_code returns text",
               isinstance(code, str) and len(code) > 200)
    check_true("generated code interpolates the package root",
               'pkg_root = "/Game/UnitTestRoot"' in code, code[:200])
    check_true("generated code embeds the item list", '"SM_Unit"' in code)
    check_true("generated code has no unescaped template braces",
               "{{" not in code and "}}" not in code)

    try:
        compile(code, "<generated_ue_staging>", "exec")
        check_true("generated code is valid Python", True)
    except SyntaxError as e:
        check_true("generated code is valid Python", False,
                   f"SyntaxError line {e.lineno}: {e.msg}")

    # The UE-side script builds f"Live_{name}" labels; verify the nested
    # f-strings survived interpolation instead of being collapsed.
    check_true("generated code keeps nested f-strings intact",
               'f"Live_{name}"' in code,
               [ln for ln in code.splitlines() if "Live_" in ln])


def check_ue_run_python():
    calls = []
    original = mcp_client.monolith

    def stub(method, args=None, timeout=30):
        calls.append((method, args, timeout))
        return json.dumps({"ok": True, "ran": args.get("command", "")[:3]})

    mcp_client.monolith = stub
    try:
        out = sc.ue_run_python("print(1)", timeout=12.5)
        check("ue_run_python parses the JSON text payload", out, {"ok": True, "ran": "pri"})
        check("ue_run_python calls editor_query run_python",
              calls[0][0:2],
              ("editor_query", {"action": "run_python", "command": "print(1)"}))
        check("ue_run_python forwards the timeout", calls[0][2], 12.5)
    finally:
        mcp_client.monolith = original


def main():
    with tempfile.TemporaryDirectory() as tmp:
        print("staging_core coordinate conversion")
        check_coordinates()
        print("staging_core manifest IO")
        check_manifest_io(tmp)
        print("staging_core UE code generation")
        check_codegen()
        print("staging_core UE execution bridge")
        check_ue_run_python()

    failed = [r for r in RESULTS if not r[1]]
    print(f"\nchecks: {len(RESULTS)}   passed: {len(RESULTS) - len(failed)}   failed: {len(failed)}")
    for label, _, got, want in failed:
        print(f"  FAILED {label}: got {got!r} want {want!r}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
