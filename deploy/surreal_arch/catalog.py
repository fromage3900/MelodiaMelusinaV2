"""ARCH_CATALOG — unified metadata for search, picker, and dispatch hooks."""

from __future__ import annotations


def invalidate_catalog_cache():
    build_catalog._cache = None


def _style_from_arch_type(at_id):
    low = at_id.lower()
    if "romanesque" in low:
        return "romanesque"
    if "brutalist" in low:
        return "brutalist"
    if "venetian" in low or at_id == "BIFORA":
        return "venetian"
    if "scifi" in low or "pressure" in low:
        return "scifi"
    if at_id.startswith("GB_GOTHIC_"):
        return "gothic"
    if at_id.startswith(("GREYBOX_", "GB_")):
        return "greybox"
    return "experimental"


def _tags_for_type(at_id, style):
    tags = [style]
    low = at_id.lower()
    for word in (
        "corridor", "room", "gothic", "door", "window", "tower", "greybox", "arc",
        "romanesque", "brutalist", "venetian", "offset", "scifi", "pressure", "airlock",
        "loggia", "panel", "arcade", "gasket",
    ):
        if word in low:
            tags.append(word)
    return tags


def _attach_research_presets(catalog):
    try:
        from .research_presets import RESEARCH_PRESETS
    except ImportError:
        return
    catalog["_research_presets"] = {}
    for pid, pspec in RESEARCH_PRESETS.items():
        at = pspec["props"].get("arch_type", "")
        style = _style_from_arch_type(at)
        entry = {
            "id": pid,
            "label": pspec["label"],
            "description": pspec.get("description", ""),
            "research_ref": pspec.get("research_ref", ""),
            "arch_type": at,
            "style": style,
            "tags": _tags_for_type(at, style) + ["research", "preset", "quick_launch"],
            "operator": f"surreal_arch.preset_research_{pid}",
        }
        catalog["_research_presets"][pid] = entry
        if at in catalog:
            catalog[at].setdefault("research_presets", []).append(pid)
            catalog[at].setdefault("glossary", []).append(pspec.get("research_ref", ""))


def build_catalog(monolith):
    """Build catalog entries from monolith registries (lazy, once)."""
    if getattr(build_catalog, "_cache", None):
        return build_catalog._cache
    cat_style = {}
    for style_id, _label, cat_ids in monolith._ARCH_PICKER_STYLE_GROUPS:
        for cid in cat_ids:
            cat_style[cid] = style_id.lower()
    catalog = {}
    for cat_id, cat_label, _icon, items in monolith._ARCH_CATEGORIES:
        style = cat_style.get(cat_id, "experimental")
        for at_id, at_label in items:
            catalog[at_id] = {
                "id": at_id,
                "label": at_label,
                "category": cat_label,
                "cat_id": cat_id,
                "style": _style_from_arch_type(at_id) if at_id.startswith("GB_") else style,
                "tags": _tags_for_type(at_id, style),
                "param_spec": monolith._ARCH_PARAM_SPEC.get(at_id),
                "builder_attr": getattr(monolith, "_CATALOG_DISPATCH", {}).get(at_id)
                or getattr(monolith, "_KIT_DISPATCH", {}).get(at_id),
                "snap_emitter": monolith._match_greybox_arch(at_id)
                or at_id.startswith(("GB_GOTHIC_", "GB_ROMANESQUE_", "GB_SCIFI_")),
                "trim_capable": at_id.startswith(("GREYBOX_", "GB_")),
                "glossary": [],
                "research_presets": [],
            }
    for key, spec in monolith._ARCH_PRESETS.items():
        catalog.setdefault("_presets", {})[key] = spec
    _attach_research_presets(catalog)
    build_catalog._cache = catalog
    return catalog


def search_index(monolith):
    catalog = build_catalog(monolith)
    entries = []
    for at_id, meta in catalog.items():
        if at_id.startswith("_"):
            continue
        glossary_bits = list(meta.get("glossary", []))
        for sid, spec in monolith.STYLE_REGISTRY.items():
            hints = spec.get("hints_by_type", {})
            if at_id in hints:
                glossary_bits.extend(hints[at_id])
        preset_labels = []
        for pid in meta.get("research_presets", []):
            rp = catalog.get("_research_presets", {}).get(pid, {})
            preset_labels.append(rp.get("label", pid))
            glossary_bits.append(rp.get("research_ref", ""))
        search_text = " ".join(
            [at_id, meta["label"], meta["category"], meta["style"],
             " ".join(meta.get("tags", [])), " ".join(glossary_bits),
             " ".join(preset_labels)]
        ).lower()
        entries.append({**meta, "search_text": search_text, "glossary": glossary_bits, "builder_attr": meta.get("builder_attr")})
    for pid, rp in catalog.get("_research_presets", {}).items():
        entries.append({
            **rp,
            "category": "Research Preset",
            "search_text": " ".join([
                pid, rp["label"], rp.get("description", ""), rp.get("research_ref", ""),
                rp["arch_type"], " ".join(rp.get("tags", [])),
            ]).lower(),
            "glossary": [rp.get("research_ref", "")],
        })
    return entries
