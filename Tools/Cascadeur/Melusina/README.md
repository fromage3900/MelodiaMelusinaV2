# Melusina Cascadeur Authoring Lane

Cascadeur is a manual authoring/cleanup gate for foreign sources and a
canonical source-rig authoring tool for new clips. The reusable reference is:

`Imports/Animations/Cascadeur/Target/SK_Melusina_Cascadeur_Target.fbx`

The UE handoff contract is the existing source rig, not a direct live-skeleton
import:

- source rig: `SK_Source_Melusina` (464 bones)
- 30 FPS, centimetres, underscore-normalized names
- animation-only FBX, one clip per file
- loop/root-motion/consumer/provenance in a v2 sidecar
- UE import onto `SK_Source_Melusina`, then `RTG_Source_to_Melusina`

For Quaternius/UAL1, use the manual AutoPosing/retarget/contact/polish gate;
the Cascadeur bridge cannot perform that retarget automatically. Create a
handoff report without importing with:

```powershell
python Tools/animation_import_pipeline/pipeline.py cascadeur-handoff `
  Imports/Animations/Cascadeur/Inbox/A_CAS_Melusina_Idle_Loop.fbx
```

Do not bypass the gate by sending UAL1 or dotted ARP FBX directly to the live
Melusina skeleton. Existing direct-target clips remain rollback assets.
