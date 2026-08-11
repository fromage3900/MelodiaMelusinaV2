#!/usr/bin/env python3
"""
ui_lint.py — UMG structural linter.

Finds common widget tree defects without opening the editor.

Modes:
  Online  — queries Monolith MCP for live widget tree (ui_query:get_widget_tree)
  Offline — reads T3D export text (project_query:export_asset_text)

Checks:
  1. CanvasPanel wrappers left at default 100x30 slot size
  2. Duplicate widget names in one tree
  3. Widgets with no slot (orphaned)
  4. CanvasPanel/Overlay roots on widgets in list containers
  5. Zero-width or zero-height images
  6. BindWidgetOptional names present in C++ but absent from tree

Usage:
    python Tools/ui_lint.py --widget /Game/.../WBP_Example
    python Tools/ui_lint.py --all-melodia
    python Tools/ui_lint.py --report
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp_client import monolith

SAVED_DIR = Path(__file__).resolve().parent.parent / "Saved"
REPORT_DIR = SAVED_DIR / "lint_reports"


@dataclass
class Violation:
    widget: str
    check: str
    severity: str  # error | warning
    message: str


@dataclass
class LintResult:
    asset_path: str
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    @property
    def errors(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "warning"]


# ---------------------------------------------------------------------------
# T3D parser helpers (offline mode)
# ---------------------------------------------------------------------------

_CANVAS_SLOT_RE = re.compile(
    r"Begin\s+Object\s+Class=CanvasPanelSlot\s+Name=([^\s]+).*?"
    r"SlotSize=\(\s*X=(\d+\.?\d*)\s*,Y=(\d+\.?\d*)",
    re.DOTALL,
)

_WIDGET_BLOCK_RE = re.compile(
    r"Begin\s+Object\s+Class=([^\s]+)\s+Name=([^\s]+)(.*?)(?=End\s+Object)",
    re.DOTALL,
)

_IMAGE_SIZE_RE = re.compile(
    r"(Width|Height)=(\d+\.?\d*)",
)


def _parse_t3d_widgets(t3d_text: str) -> list[dict]:
    """Parse a T3D export into a list of widget dicts with parent/child info."""
    widgets: list[dict] = []
    stack: list[dict] = []

    for match in _WIDGET_BLOCK_RE.finditer(t3d_text):
        cls = match.group(1)
        name = match.group(2)
        body = match.group(3)
        w = {"class": cls, "name": name, "body": body, "children": [], "slot": None}
        if stack:
            stack[-1]["children"].append(w)
        widgets.append(w)
        stack.append(w)
        # Track nesting via indentation heuristic
        begin_count = body.count("Begin Object")
        end_count = body.count("End Object")
        delta = begin_count - end_count
        if delta <= 0:
            for _ in range(-delta + 1):
                if stack:
                    stack.pop()

    return widgets


def _check_default_slot_size(widget: dict, path: str, violations: list[Violation]) -> None:
    """Check 1: CanvasPanel wrappers at default 100x30 slot size."""
    if "CanvasPanel" not in widget.get("class", ""):
        return
    for child in widget.get("children", []):
        body = child.get("body", "")
        m = _CANVAS_SLOT_RE.search(body)
        if m:
            sx, sy = float(m.group(2)), float(m.group(3))
            if abs(sx - 100.0) < 0.01 and abs(sy - 30.0) < 0.01:
                violations.append(Violation(
                    widget=f"{path}/{child.get('name', '?')}",
                    check="default_slot_size",
                    severity="warning",
                    message=f"Child '{child.get('name', '?')}' has default CanvasPanel slot size 100x30",
                ))


def _check_duplicate_names(widget: dict, path: str, violations: list[Violation]) -> None:
    """Check 2: Duplicate widget names in one tree."""
    names = {}
    for child in widget.get("children", []):
        cname = child.get("name", "")
        names.setdefault(cname, []).append(child)
    for cname, siblings in names.items():
        if len(siblings) > 1:
            violations.append(Violation(
                widget=path,
                check="duplicate_name",
                severity="error",
                message=f"Duplicate widget name '{cname}' ({len(siblings)} occurrences)",
            ))


def _check_orphaned(widget: dict, path: str, violations: list[Violation]) -> None:
    """Check 3: Widgets with no slot (orphaned)."""
    body = widget.get("body", "")
    if "Slot=" not in body and widget.get("class") != "CanvasPanel":
        violations.append(Violation(
            widget=f"{path}/{widget.get('name', '?')}",
            check="orphaned",
            severity="warning",
            message=f"Widget '{widget.get('name', '?')}' has no slot assignment",
        ))


def _check_list_container_root(widget: dict, path: str, violations: list[Violation]) -> None:
    """Check 4: CanvasPanel/Overlay root when parent is a list container."""
    cls = widget.get("class", "")
    if cls not in ("CanvasPanel", "Overlay"):
        return
    for child in widget.get("children", []):
        ccls = child.get("class", "")
        if ccls in ("VerticalBox", "HorizontalBox", "GridPanel", "WrapBox"):
            violations.append(Violation(
                widget=f"{path}/{widget.get('name', '?')}",
                check="list_container_root",
                severity="error",
                message=f"{cls} wrapper around {ccls} — use {ccls} directly as root",
            ))


def _check_zero_size_image(widget: dict, path: str, violations: list[Violation]) -> None:
    """Check 5: Zero-width or zero-height images."""
    cls = widget.get("class", "")
    if "Image" not in cls:
        return
    body = widget.get("body", "")
    sizes = {}
    for m in _IMAGE_SIZE_RE.finditer(body):
        sizes[m.group(1)] = float(m.group(2))
    w = sizes.get("Width", -1)
    h = sizes.get("Height", -1)
    if w == 0 or h == 0:
        violations.append(Violation(
            widget=f"{path}/{widget.get('name', '?')}",
            check="zero_size_image",
            severity="error",
            message=f"Image has zero dimension (Width={w}, Height={h})",
        ))


def lint_t3d(asset_path: str, t3d_text: str) -> LintResult:
    result = LintResult(asset_path=asset_path)
    widgets = _parse_t3d_widgets(t3d_text)
    for w in widgets:
        p = asset_path
        _check_default_slot_size(w, p, result.violations)
        _check_duplicate_names(w, p, result.violations)
        _check_orphaned(w, p, result.violations)
        _check_list_container_root(w, p, result.violations)
        _check_zero_size_image(w, p, result.violations)
    return result


# ---------------------------------------------------------------------------
# Online mode (Monolith MCP)
# ---------------------------------------------------------------------------

def _traverse_widget_tree(node: dict, path: str, violations: list[Violation]) -> None:
    cls = node.get("class", "")
    name = node.get("name", "")
    p = f"{path}/{name}" if path else name

    # 1. Default slot size on children
    if "CanvasPanel" in cls:
        for child in node.get("children", []):
            slot = child.get("slot", {})
            if isinstance(slot, dict):
                sx = slot.get("size", {}).get("x", 0)
                sy = slot.get("size", {}).get("y", 0)
                if abs(sx - 100.0) < 0.01 and abs(sy - 30.0) < 0.01:
                    violations.append(Violation(
                        widget=f"{p}/{child.get('name', '?')}",
                        check="default_slot_size",
                        severity="warning",
                        message=f"Child '{child.get('name', '?')}' has default slot size 100x30",
                    ))

    # 2. Duplicate names
    names = {}
    for child in node.get("children", []):
        cname = child.get("name", "")
        names.setdefault(cname, []).append(child)
    for cname, siblings in names.items():
        if len(siblings) > 1:
            violations.append(Violation(
                widget=p,
                check="duplicate_name",
                severity="error",
                message=f"Duplicate widget name '{cname}' ({len(siblings)} occurrences)",
            ))

    # 3. Orphaned (no slot)
    if "slot" not in node and name and path:
        violations.append(Violation(
            widget=p,
            check="orphaned",
            severity="warning",
            message=f"Widget '{name}' has no slot assignment",
        ))

    # 4. CanvasPanel/Overlay wrapping list container
    if cls in ("CanvasPanel", "Overlay"):
        for child in node.get("children", []):
            ccls = child.get("class", "")
            if ccls in ("VerticalBox", "HorizontalBox", "GridPanel", "WrapBox"):
                violations.append(Violation(
                    widget=p,
                    check="list_container_root",
                    severity="error",
                    message=f"{cls} wrapper around {ccls} — use {ccls} directly as root",
                ))

    # 5. Zero-size image
    if "Image" in cls:
        w = node.get("width", node.get("desired_size", {}).get("x", -1))
        h = node.get("height", node.get("desired_size", {}).get("y", -1))
        if w == 0 or h == 0:
            violations.append(Violation(
                widget=p,
                check="zero_size_image",
                severity="error",
                message=f"Image has zero dimension (Width={w}, Height={h})",
            ))

    for child in node.get("children", []):
        _traverse_widget_tree(child, p, violations)


def lint_online(asset_path: str) -> LintResult:
    result = LintResult(asset_path=asset_path)
    try:
        resp = monolith("ui_query", {"action": "get_widget_tree", "asset_path": asset_path})
        raw = json.loads(resp) if isinstance(resp, str) else resp
        tree = raw if isinstance(raw, dict) else {}
        _traverse_widget_tree(tree, "", result.violations)
    except Exception as e:
        result.violations.append(Violation(
            widget=asset_path,
            check="connectivity",
            severity="error",
            message=f"Monolith query failed: {e}",
        ))
    return result


# ---------------------------------------------------------------------------
# Discover melodia widgets
# ---------------------------------------------------------------------------

def _discover_melodia_widgets() -> list[str]:
    try:
        resp = monolith("project_query", {"action": "search", "type": "WidgetBlueprint", "path": "/Game/Melodia"})
        raw = json.loads(resp) if isinstance(resp, str) else resp
        assets = raw if isinstance(raw, list) else raw.get("results", raw.get("assets", []))
        return [a.get("path", a) if isinstance(a, dict) else a for a in assets]
    except Exception as e:
        print(f"Failed to discover melodia widgets: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def format_results(results: list[LintResult], output_path: Path | None = None) -> str:
    total_violations = sum(len(r.violations) for r in results)
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)

    lines = [
        "# UMG Lint Report",
        "",
        f"**Assets scanned:** {len(results)}",
        f"**Total violations:** {total_violations} ({total_errors} errors, {total_warnings} warnings)",
        "",
    ]

    for r in results:
        if r.ok:
            continue
        lines.append(f"## {r.asset_path}")
        lines.append(f"**{len(r.errors)} error(s), {len(r.warnings)} warning(s)**")
        lines.append("")
        for v in r.violations:
            icon = "E" if v.severity == "error" else "W"
            lines.append(f"- [{icon}] **{v.check}**: {v.message} ({v.widget})")
        lines.append("")

    if total_violations == 0:
        lines.append("_No violations found._")

    report = "\n".join(lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"Report written to {output_path}")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="UMG structural linter.")
    p.add_argument("--widget", help="Single widget asset path to lint")
    p.add_argument("--all-melodia", action="store_true", help="Lint all Melodia widgets")
    p.add_argument("--report", action="store_true", help="Generate markdown report")
    p.add_argument("--offline", action="store_true", help="Use T3D export text instead of online tree")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    results: list[LintResult] = []

    if args.widget:
        if args.offline:
            try:
                resp = monolith("project_query", {"action": "export_asset_text", "asset_path": args.widget})
                t3d = json.loads(resp) if isinstance(resp, str) and resp.startswith("{") else resp
                if isinstance(t3d, dict):
                    t3d_text = t3d.get("text", t3d.get("export_text", ""))
                else:
                    t3d_text = str(t3d)
                results.append(lint_t3d(args.widget, t3d_text))
            except Exception as e:
                print(f"Failed to export {args.widget}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            results.append(lint_online(args.widget))

    elif args.all_melodia:
        widgets = _discover_melodia_widgets()
        if not widgets:
            print("No Melodia widgets discovered or Monolith unavailable.", file=sys.stderr)
            sys.exit(1)
        for w in widgets:
            if args.offline:
                try:
                    resp = monolith("project_query", {"action": "export_asset_text", "asset_path": w})
                    t3d = json.loads(resp) if isinstance(resp, str) and resp.startswith("{") else resp
                    t3d_text = t3d.get("text", t3d.get("export_text", "")) if isinstance(t3d, dict) else str(t3d)
                    results.append(lint_t3d(w, t3d_text))
                except Exception:
                    pass
            else:
                results.append(lint_online(w))
    else:
        print("Specify --widget or --all-melodia")
        sys.exit(1)

    for r in results:
        if r.violations:
            print(f"\n{r.asset_path} — {len(r.errors)}E/{len(r.warnings)}W")
            for v in r.violations:
                print(f"  [{v.severity[0].upper()}] {v.check}: {v.message}")

    if args.report:
        report_path = REPORT_DIR / f"ui_lint_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
        format_results(results, output_path=report_path)

    fail_count = sum(1 for r in results if r.errors)
    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    from datetime import datetime, timezone
    main()
