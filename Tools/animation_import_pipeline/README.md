# Additive Animation Import Pipeline

Import public-source animation clips into Melusina without touching the working rig.

## Architecture

```
                     ┌─ Lane A ─────────────────────────────┐
Source FBX ──► Pre-flight ──► Import onto ──► Batch retarget ──► Verify
(clip +          validate       SK_Source_      via RTG_Source_     post-
 manifest)       (FPS, bones,   Melusina        to_Melusina         contract
                  naming,       skeleton        (464 source → target) check
                  metadata)     (staging)                           (staging)
                     └──────────────────────────────────────────────┘
                                    │
                                    ▼
                              Wire into ABP /
                              blendspace /
                              montage via
                              t3d_anim_injector.py
```

## Infrastructure (already built)

### Retargeter Pair (staging only — never touches the working rig)

| Asset | Path | Status |
|-------|------|--------|
| Source skeleton contract | `/Game/Melodia/Mocap/Source/SK_Source_Melusina` | ✅ Existing authoritative 464-bone source-rig mesh contract verified |
| Source IK Rig | `/Game/Melodia/Mocap/Source/IK_Source_Melusina` | ✅ Created (464 bones) |
| Target IK Rig | `/Game/Melodia/Mocap/Retarget/IK_Melusina_Body_Current` | ✅ Pre-existing |
| Retargeter | `/Game/Melodia/Characters/Melusina/RTG_Source_to_Melusina` | ✅ Owner-confirmed reusable source-rig retargeter |
| Staging output | `/Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/` | Ready |

### Pipeline scripts

| Script | Purpose | Location |
|--------|---------|----------|
| `validate_source.py` | Pre-flight: FPS, bones, naming, manifest schema | `Tools/animation_import_pipeline/` |
| `import_chain.py` | Full chain: validate → import → retarget → verify | `Tools/animation_import_pipeline/` |
| `manifest_v2.py` / `sidecar_schema_v2.json` | Canonical manifest contract, BOM-tolerant parsing, deterministic clip IDs | `Tools/animation_import_pipeline/` |
| `registry.py` | Catalog and classify canonical, manual, blocked, legacy, and promoted clips | `Tools/animation_import_pipeline/` |
| `pipeline.py` | `catalog`, `preflight`, `cascadeur-handoff`, UE gate, and promotion-plan CLI | `Tools/animation_import_pipeline/` |
| `live_promotion.py` | Guarded live BlendSpace/montage mutation through the existing Monolith/editor bridge; montage creation uses UE's solved AnimMontageFactory path | `Tools/animation_import_pipeline/` |
| `Content/Python/mual_headless_blendspace_promotion.py` | Explicit fallback when the interactive editor owns the package but Monolith is temporarily unavailable; snapshots, replaces one verified speed-zero sample, saves, and verifies in UE | `Content/Python/` |
| `pie_smoke.py` | Existing MelodiaIntegrationMap PIE evidence producer | `Tools/animation_import_pipeline/` |
| `foot_contact_audit.py` | Read-only Monolith foot-plant/contact evidence audit; optional sidecar update | `Tools/animation_import_pipeline/` |
| `Tools/export_melusina_animation_source.py` | ARP operator bake, approved bone-map normalization, helper filtering, 30 FPS/cm animation-only FBX export without saving the stage | `Tools/` |
| `Tools/probe_melusina_stage_actions.py` | Read-only action/NLA inventory used to distinguish authored locomotion from the solved ARP idle | `Tools/` |

## Source Type → Pipeline Path

### Lane A — Canonical source-rig clips
Animation authored/exported on `SK_Source_Melusina` (464 bones).
→ Import onto the source skeleton, then use `RTG_Source_to_Melusina` for the
final target animation. Even a source-rig clip does not bypass the staging
retarget/verification lane.

**Before you start:** Move the authored FBX + `.manifest.json` to `Imports/Animations/Cascadeur/Inbox/`.

### Lane B — Foreign source normalization
Animation on a different skeleton must first pass the manual/foreign source
gate and be normalized to `SK_Source_Melusina`. Only the normalized result
enters the universal lane; direct Quaternius-to-Melusina retargeters remain
legacy rollback paths.

**Quaternius clips (42 staged at `Imports/Animations/Cascadeur/Inbox/`):**

1. Re-import the Quaternius skeleton to a staging path:
   - `mesh_query:import_mesh` → `/Game/Melodia/Mocap/Source/Quaternius/SK_Quaternius`
2. Create IK_Quaternius rig for that skeleton
3. Create RTG_Quaternius_to_Source retargeter (Quaternius → SK_Source_Melusina)
4. Export the normalized source-rig clip with a v2 manifest
5. Then use the main RTG_Source_to_Melusina for the final retarget

Any existing direct Quaternius-to-Melusina retargeter is retained only for
comparison/rollback; it cannot produce a canonical library or promotion
record.

**Important:** The Quaternius FBX files have embedded mesh (~23MB each) and use the UAL1 rig (65 bones, 24 FPS, dot-separated bone names). Each must be:
- Pre-flight validated (will fail until bone naming is normalized)
- Optionally cleaned up in Blender (bone rename, FPS resample, mesh strip)

### Lane C — Rokoko Mocap
See `Tools/import_rokoko_mocap.py` and `Docs/ROKOKO_MELUSINA_MOCAP.md`.
Requires neck hierarchy fix first — do not use until that gate is cleared.

## v2 Per-Clip Workflow

```bash
# 1. Catalog the library and inspect the classification
python Tools/animation_import_pipeline/pipeline.py catalog

# 2. Create a v2 .manifest.json sidecar beside the canonical FBX
#    See sidecar_schema_v2.json; clip_id is deterministic.

# 3. Run pre-flight validation
python Tools/animation_import_pipeline/validate_source.py \
  Imports/Animations/Cascadeur/Inbox/MyClip.fbx

# 4. Run the staging import and RTG_Source_to_Melusina chain in UE
powershell -ExecutionPolicy Bypass -File Tools/run_mual_ue_source_pilot.ps1

# 5. Audit contact evidence through the existing Monolith animation action.
#    For a static idle montage, pass --consumer montage; BlendSpace remains
#    bilateral-contact gated.
python Tools/animation_import_pipeline/pipeline.py contact-audit \
  path/to/MyClip.manifest.json \
  --animation /Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/MyClip__MUAL_TARGET

# Static-pose montage example:
python Tools/animation_import_pipeline/pipeline.py contact-audit \
  path/to/MyClip.manifest.json --animation /Game/Staging/MyClip__MUAL_TARGET \
  --consumer montage --apply

# Static-pose idle BlendSpace evidence is allowed only with an explicit
# declared speed-zero manifest and a scoped contact audit:
python Tools/animation_import_pipeline/pipeline.py contact-audit \
  path/to/MyClip.manifest.json --animation /Game/Staging/MyClip__MUAL_TARGET \
  --consumer blendspace --reuse-static-report Saved/Audit/static_idle_contact.json --apply

# 6. Produce a fail-closed promotion plan; live wiring is a separate gate
python Tools/animation_import_pipeline/pipeline.py pie-smoke MyClip

# 7. Produce a fail-closed promotion plan; live wiring is a separate gate
python Tools/animation_import_pipeline/pipeline.py promotion-plan \
  path/to/MyClip.manifest.json Saved/Audit/melusina_ue_source_pilot.json \
  --animation /Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/MyClip__MUAL_TARGET \
  --consumer blendspace --speed 420

# A speed-zero idle may replace the existing speed-zero sample only when the
# manifest has verified static-pose evidence and the contact audit is scoped
# to BlendSpace. The live writer stores the replaced row in a rollback backup.
python Tools/animation_import_pipeline/pipeline.py promotion-plan \
  path/to/MyClip.manifest.json Saved/Audit/melusina_ue_source_pilot.json \
  --animation /Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/MyClip__MUAL_TARGET \
  --consumer blendspace --speed 0 --replace-existing-speed

# 8. Apply only an allowed plan; this snapshots live consumer state first
python Tools/animation_import_pipeline/pipeline.py live-promotion \
  path/to/MyClip.manifest.json Saved/Audit/melusina_ue_source_pilot.json \
  Saved/Audit/mual_promotion_plan.json \
  --animation /Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/MyClip__MUAL_TARGET \
  --consumer blendspace --apply

# 9. Verify the working system; do not bypass the guarded promoter with a
#    direct live-skeleton or generic injector write.
python Tools/anim_diagnostic.py
python Content/Python/audit_melusina_integration.py
```

## Legacy v1 Sidecar Compatibility

The original v1 sidecar remains readable for rollback imports, but it cannot
enter the canonical v2 lane until normalized. New source-rig clips use
`sidecar_schema_v2.json` and the fields shown in the generated pilot manifest.
For reference, the legacy shape is:

```json
{
  "schema_version": "1.0",
  "clip_id": "Idle_Serene",
  "source_name": "Cascadeur authoring – Idle_Serene",
  "context": "locomotion",
  "expected_skeleton": "SK_Source_Melusina_Skeleton",
  "fps": 30,
  "root_motion": "in_place",
  "loop": true,
  "start_frame": 0,
  "end_frame": 60,
  "consumer": "blendspace",
  "notify_contract": []
}
```

## Quality Gates

| Gate | What it checks | Tool |
|------|---------------|------|
| Pre-import | FPS=30, bone naming, manifest fields | `validate_source.py` |
| Post-import | Skeleton reference, asset exists | `import_chain.py verify` |
| Post-wire | Blendspace sample count, speed axis | `audit_melusina_integration.py` |
| Compile | ABP compiles (0 errors, T3D path) | `t3d_anim_injector.py` |
| Smoke | PIE: character loads, animates, no crash | `pie_smoke_runner.py` |

## Do Not

- Import any FBX directly onto the working SK_Melusina package path
- Batch-import more than one clip at a time
- Wire a clip into the ABP until it passes post-import verification
- Delete existing mocap samples — add new samples alongside them
- Use Cascadeur Python API for retargeting (it doesn't support AutoPose/Retarget programmatically)
