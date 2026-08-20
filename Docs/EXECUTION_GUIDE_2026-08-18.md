# Execution Guide — Triple-A Melusina Animation Pipeline

**Date:** 2026-08-18
**Status:** All tools built. Ready to execute when editor is available.

---

## Task Ledger

| # | Task | Status | Tool |
|---|------|--------|------|
| 1 | Research AAA animation pipelines | DONE | `Saved/Research/aaa_animation_pipeline_report.md` |
| 2 | Research UE5 retargeting | DONE | `Saved/Research/ue5_retargeting_report.md` |
| 3 | Research glide techniques | DONE | `Saved/Research/magical_girl_glide_report.md` |
| 4 | Research agentic AI tools | DONE | `Saved/Research/agentic_animation_report.md` |
| 5 | Write pipeline design doc | DONE | `Docs/TRIPLE_A_MELUSINA_ANIMATION_PIPELINE_2026-08-18.md` |
| 6 | Build retarget pipeline tool | DONE | `Tools/run_cascadeur_retarget_pipeline.py` |
| 7 | Build idle fix tool | DONE | `Tools/wire_melusina_idle.py` |
| 8 | Build glide state tool | DONE | `Tools/wire_melusina_glide.py` |
| 9 | Build facial rig tool | DONE | `Tools/build_melusina_face_rig.py` |
| 10 | Execute retarget pipeline | PENDING | needs editor |
| 11 | Author Cascadeur clips | PENDING | needs Cascadeur |

---

## Execution Order (when editor is ready)

### Phase 1 — Fix the Broken Things (no new authoring)

```bash
# 1. Fix idle (repoint to mocap idle)
python Tools/wire_melusina_idle.py --plan
python Tools/wire_melusina_idle.py --apply
python Tools/wire_melusina_idle.py --verify

# 2. Add Locomotion state (walk/run/sprint blendspace)
python Tools/build_melusina_locomotion_stack.py --preflight
python Tools/build_melusina_locomotion_stack.py --plan
python Tools/build_melusina_locomotion_stack.py --apply
python Tools/build_melusina_locomotion_stack.py --verify

# 3. Add Glide state
python Tools/wire_melusina_glide.py --plan
python Tools/wire_melusina_glide.py --apply
python Tools/wire_melusina_glide.py --verify
```

### Phase 2 — Fix the Retarget Pipeline

```bash
# 1. Batch retarget all Cascadeur inbox clips
python Tools/run_cascadeur_retarget_pipeline.py --dry-run
python Tools/run_cascadeur_retarget_pipeline.py --apply

# 2. Check the report
cat Saved/Audit/cascadeur_retarget_pipeline_*.json
```

### Phase 3 — Wire Facial Animation

```bash
python Tools/build_melusina_face_rig.py --plan
python Tools/build_melusina_face_rig.py --apply
python Tools/build_melusina_face_rig.py --verify
```

### Phase 4 — Polish

1. PIE test: idle is not a T-pose
2. PIE test: walk/run/sprint blend by speed
3. PIE test: SpaceBar hold → wind-up → launch
4. PIE test: glide state enters/exits cleanly
5. PIE test: facial curves drive morph targets
6. Add VFX (sparkles on glide, petal burst on victory)
7. Camera adjustments (pull back slightly during glide)

---

## Pre-conditions

- [ ] Unreal Editor running with Monolith on 127.0.0.1:9316
- [ ] Blender 5.2 accessible as `blender` on PATH
- [ ] RTG_Source_to_Melusina IK retargeter exists in UE
- [ ] SK_Source_Melusina source skeleton exists in UE
- [ ] ABP_Melusina_Current is the active Animation Blueprint

---

## File Map

```
BS_GodFile/
├── Docs/
│   └── TRIPLE_A_MELUSINA_ANIMATION_PIPELINE_2026-08-18.md
├── Saved/
│   ├── Research/
│   │   ├── aaa_animation_pipeline_report.md
│   │   ├── ue5_retargeting_report.md
│   │   ├── magical_girl_glide_report.md
│   │   └── agentic_animation_report.md
│   └── Audit/
│       └── (generated reports from each tool run)
├── Tools/
│   ├── run_cascadeur_retarget_pipeline.py  (batch retarget)
│   ├── wire_melusina_idle.py               (idle fix)
│   ├── wire_melusina_glide.py              (glide state)
│   ├── build_melusina_face_rig.py          (facial FACS)
│   ├── build_melusina_locomotion_stack.py  (existing, locomotion)
│   ├── build_melusina_idle_life.py         (existing, blink/breath)
│   ├── scan_cascadeur_fbx.py               (existing, offline scan)
│   └── remap_arp_fbx_to_ue.py              (existing, name+unit fix)
└── Content/
    └── Melodia/Characters/Melusina/
        ├── ABP_Melusina_Current.uasset
        ├── Animations/
        │   ├── Locomotion/     (mocap idle/walk/run/sprint/jump/land)
        │   ├── Mocap/          (raw mocap clips)
        │   ├── QuaterniusRetargeted/  (42 clips, registry issue)
        │   └── SourceRetargeted/      (retargeted output)
        └── SK_Melusina_V2_Body (68 FACS morph targets)
```

---

## Risks

1. **Editor PID 2320 is hung** — must be killed + restarted before any `--apply`
2. **Quaternius packages unloadable** — registry finds 0; may need re-import
3. **Monolith schema drift** — first `--apply` may abort on schema mismatch (designed for)
4. **Save not persisting** — `save_asset` returns saved=true even when disk write fails; always check uasset mtime

---

## Evidence Standard

Every `--apply` run writes a report to `Saved/Audit/`. Done = named evidence file +
uasset mtime updated within 10 minutes. No evidence = not done.
