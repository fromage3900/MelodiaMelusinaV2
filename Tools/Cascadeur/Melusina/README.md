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

## Golden scene status (2026-09-20)

- The MCP bridge (`Tools/cascadeur_rpc.py` + `deploy/cascadeur_mcp_server.py`)
  round-trips cleanly against Cascadeur **2026.1.3** — no app restart needed.
- `SK_Melusina_Cascadeur_Target.fbx` is IMPORTED and verified live in the
  owner's running instance: 467 objects, zero dotted names, `root_x`,
  `spine_01_x`, `head_x`, `c_kilt_master_x` present. No `hair*` bones —
  CORRECT per contract (hair skeleton lives in the separate
  `ABP_Melusina_WaterHair` runtime; never animate/rename it).
- Cascadeur 2026 scripting exposes NO headless `.casc` save (Scene/Sf3Loader/
  SceneAutosaver tools are all dialog-driven). The owner saves in-UI:
  Ctrl+Shift+S → `Tools/Cascadeur/Melusina/SC_Melusina_Golden.casc`
  (confirm 30 fps in the save dialog).
- After save: pose in the UI; export round-trips headless via
  `cascadeur_rpc.py export <path.fbx>` (binary, baked, Y-up per contract);
  then `python Tools/animation_import_pipeline/pipeline.py cascadeur-handoff`
  gates the clip into the UE lane.
- 2026-09-20 evening: owner saved `SC_Melusina_Golden.casc` (found at G:\ root,
  copied to the contract path, MD5-verified). Smoke round-trip GREEN:
  live scene → `Saved/Audit/cascadeur_smoke/A_CAS_SmokeTest_20260920.fbx`
  (+ v2 sidecar) → `cascadeur-handoff` ok:true, status manual_required
  (report: `Saved/Audit/cascadeur_smoke/smoke_report_20260920.json`). For real
  clips: bridge export ships the scene as-is (no Y-up/bake options exposed);
  confirm export axis settings on the first authored clip before promotion.
