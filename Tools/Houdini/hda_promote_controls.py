"""hda_promote_controls.py — expose a controls null's authored parameters on the HDA type.

Context: the 2026-10-06 HDA audit found both shipped HDAs kept every drive parameter
on an INNER `controls` null, so the asset TYPE exposed none of them: from UE's Houdini
Engine panel (or any newly created instance) the network could only ever cook at its
authored defaults. The registry pins the promoted names (`expect.parms`) and a real
drive probe (`expect.parm_drive`), so a rebuilt-but-unpromoted HDA fails Gate 2.

Promotion runs in two stages INSIDE THE BUILDER, because of two Houdini behaviours
this module exists to work around:

stage1 — plain geo node, BEFORE createDigitalAsset
    An HDA instance's content is LOCKED: adding the inner `controls` expressions
    after conversion raises hou PermissionError ("locked assets"). On the
    pre-conversion geo node they can be added freely. stage1 copies each authored
    template onto the owner node — renaming to `<name>_ctrl` when the name collides
    with a built-in (`scale` exists on every Object node) — and points each inner
    parm at it: ch("../<promoted>").

stage2 — AFTER createDigitalAsset
    createDigitalAsset leaves those templates as instance SPARE parms, and a freshly
    created instance would have no such parm at all: the inner expression would then
    silently evaluate to 0 (a worse state than the original one). stage2 appends
    them to the DEFINITION's parm template group and saves, which absorbs the spares.

Usage (from either builder)::

    pairs = hda_promote_controls.stage1_promote(controls, owner, authored_names)
    hda_promote_controls.stage1_wire(controls, pairs)
    asset = owner.createDigitalAsset(...)
    hda_promote_controls.stage2_promote_definition(asset, pairs, out_path)

stage1_promote assumes a FRESHLY created owner node (both builders rebuild their
network from scratch every run); it is not idempotent across calls on one node.
`hou` is imported lazily, so non-hython tooling may import this module safely.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Both builders reach this module via their own repo-root constant; this fallback
# only serves direct `hython Tools/Houdini/hda_promote_controls.py` inspection.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))


def _hou(hou=None):
    if hou is not None:
        return hou
    import hou as _hou_mod
    return _hou_mod


def clone_pt(t, new_name: str, hou=None):
    """Clone a parm template under a new name.

    hou has no copyWithNewName, and the collision path (`scale` -> `scale_ctrl`)
    needs a template with the same semantics as the original: same defaults,
    ranges and menu items, so promoting never changes a value.
    """
    hou = _hou(hou)
    if isinstance(t, hou.MenuParmTemplate):
        return hou.MenuParmTemplate(new_name, t.label(), t.menuItems(), t.menuLabels(),
                                    default_value=t.defaultValue())
    if isinstance(t, hou.IntParmTemplate):
        return hou.IntParmTemplate(new_name, t.label(), t.numComponents(),
                                   default_value=t.defaultValue(),
                                   min=t.min(), max=t.max())
    if isinstance(t, hou.FloatParmTemplate):
        return hou.FloatParmTemplate(new_name, t.label(), t.numComponents(),
                                     default_value=t.defaultValue(),
                                     min=t.min(), max=t.max())
    if isinstance(t, hou.ToggleParmTemplate):
        return hou.ToggleParmTemplate(new_name, t.label(),
                                      default_value=t.defaultValue())
    if isinstance(t, hou.StringParmTemplate):
        return hou.StringParmTemplate(new_name, t.label(), t.numComponents(),
                                      default_value=t.defaultValue(),
                                      default_language=t.defaultLanguage())
    raise TypeError(f"cannot clone {type(t).__name__} ({t.name()}) as {new_name!r}")


def stage1_promote(controls, owner, authored, hou=None) -> list[tuple[str, str]]:
    """Copy each authored controls template onto `owner` (a plain node).

    Returns [(inner_name, promoted_name)] so stage1_wire/stage2 know the mapping.
    Raises if an authored name is missing — a silent skip would ship an unpromoted
    HDA whose Gate 2 failure looks like unrelated damage later.
    """
    hou = _hou(hou)
    group = owner.parmTemplateGroup()
    pairs: list[tuple[str, str]] = []
    for name in authored:
        t = controls.parmTemplateGroup().find(name)
        if t is None:
            raise RuntimeError(f"{controls.path()}: authored parm {name!r} not on the controls null")
        if owner.parm(name) is None:
            promoted = name
        else:
            # collides with an owner built-in (Object nodes own `scale`)
            promoted = f"{name}_ctrl"
            t = clone_pt(t, promoted, hou)
        if group.find(promoted) is None:
            group.append(t)
        pairs.append((name, promoted))
    owner.setParmTemplateGroup(group)
    return pairs


def stage1_wire(controls, pairs, hou=None) -> None:
    """Point each inner controls parm at its owner parm: ch("../<promoted>")."""
    hou = _hou(hou)
    for inner, promoted in pairs:
        parm = controls.parm(inner)
        if parm is None:
            raise RuntimeError(f"{controls.path()}: no parm {inner!r} to wire")
        parm.setExpression(f'ch("../{promoted}")', hou.exprLanguage.Hscript)


def stage2_promote_definition(asset, pairs, hda_file, hou=None):
    """Move the promoted templates from the instance's spares onto the HDA type.

    Saves the definition to `hda_file` (hou.HDADefinition.save requires the path)
    and verifies the spares were absorbed — leftovers would mean a fresh instance
    sees a different parameter set than this one.
    """
    hou = _hou(hou)
    definition = asset.type().definition()
    if definition is None:
        raise RuntimeError(f"{asset.path()}: node has no HDA definition")

    group = definition.parmTemplateGroup()
    existing = {t.name() for t in group.parmTemplates()}
    wanted = {promoted for _, promoted in pairs}
    appended = []
    for _inner, promoted in pairs:
        t = asset.parmTemplateGroup().find(promoted)
        if t is None:
            raise RuntimeError(f"{asset.path()}: promoted template {promoted!r} missing")
        if promoted not in existing:
            group.append(t)
            existing.add(promoted)
            appended.append(promoted)

    definition.setParmTemplateGroup(group)
    definition.save(str(hda_file))

    leftover = [t.name() for t in asset.spareParms() if t.name() in wanted]
    if leftover:
        raise RuntimeError(
            f"{asset.path()}: spares not absorbed into the definition: {leftover}")
    return definition
