"""Publish contract: git push stays OFF unless the artist opts in.

Runs on naked Python (no bpy). Parses stage_publish.py so the live GUI
addon import is never required.

  python deploy/test_stage_publish_contract.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent
SRC = DEPLOY / "surreal_arch" / "stage_publish.py"


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(SRC))

    git_push_default = None
    boolprop_default = None
    push_live_gated = False

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "GIT_PUSH_DEFAULT":
                    git_push_default = ast.literal_eval(node.value)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name == "BoolProperty":
                kw = {k.arg: k.value for k in node.keywords if k.arg}
                # This file has one BoolProperty (push_live).
                default = kw.get("default")
                if default is not None:
                    if isinstance(default, ast.Constant):
                        boolprop_default = default.value
                    elif isinstance(default, ast.Name):
                        boolprop_default = default.id

        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "push_live":
                push_live_gated = True

    if git_push_default is not False:
        _fail(f"GIT_PUSH_DEFAULT must be False, got {git_push_default!r}")
    if boolprop_default not in (False, "GIT_PUSH_DEFAULT"):
        _fail(f"push_live BoolProperty default must be False or GIT_PUSH_DEFAULT, got {boolprop_default!r}")
    if "if push_live:" not in text:
        _fail("operators must gate git push on push_live")
    if not push_live_gated:
        _fail("AST did not find `if push_live:` gate")
    if "subprocess.run" in text and "git" in text and "push" in text:
        # git push exists, but only inside _git_push_live which is gated.
        if "def _git_push_live" not in text:
            _fail("git push helper missing")

    print("stage_publish contract: git push default is False")
    print(f"  GIT_PUSH_DEFAULT={git_push_default}")
    print(f"  BoolProperty default={boolprop_default}")
    print("  operators call _git_push_live only when push_live is True")
    print("OK")


if __name__ == "__main__":
    main()
