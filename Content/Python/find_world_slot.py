"""Locate every component in ZenForestTest whose material slot holds a
non-material object (World etc.) and show the slot's override list."""
from __future__ import annotations

import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les.load_level("/Game/ZenForestTest")

for actor in eas.get_all_level_actors() or []:
    for comp in actor.get_components_by_class(unreal.PrimitiveComponent) or []:
        mats = []
        try:
            mats = list(comp.get_editor_property("override_materials") or [])
        except Exception:
            try:
                mats = list(comp.get_editor_property("materials") or [])
            except Exception:
                continue
        for i, m in enumerate(mats):
            if m is not None and type(m).__name__ not in ("Material", "MaterialInstanceConstant"):
                print(f"ACTOR={actor.get_actor_label()} COMP={comp.get_name()} SLOT={i} "
                      f"CLASS={type(m).__name__} PATH={m.get_path_name()}")