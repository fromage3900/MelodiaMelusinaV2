# Editor-Up Execution Checklist — 2026-08-28

**Author:** Melusina (Hermes agent, z-ai/glm-5.2)
**Date:** 2026-08-28
**Status:** Ready to execute when editor is up

---

## Prerequisites

- [ ] UnrealEditor is running (check `tasklist | grep UnrealEditor`)
- [ ] Port 9316 has exactly one listener (check `netstat -ano | grep 9316 | grep LISTEN`)
- [ ] No modal dialogs open (grep `Saved/Logs/BS_GodFile.log` for `MODAL_OPEN`)
- [ ] Git is clean of uncommitted source changes (already committed this session)

---

## Step 1: Full Closed-Editor Build

**Why:** MelodiaShader is a new module (Source/MelodiaShader/). Live Coding cannot register new reflected types. A full UBT build is required.

**Close the editor first**, then run:

```bash
"%LOCALAPPDATA%/../Local/Programs/Epic Games/UE_5.8/EngineBuild/BatchFiles/Build.bat" \
  BS_GodFileEditor Win64 Development \
  -project="C:/EnvironmentPortfolio/BS_GodFile/BS_GodFile.uproject" \
  -NoUba -MaxParallelActions=6 -WaitMutex
```

**Verify:**
- Build completes with 0 errors
- `Binaries/Win64/UnrealEditor-BS_GodFile.dll` is updated
- No unity-build symbol collisions (AGENTS.md #21)

**If build fails:**
- Check for missing includes (MelodiaShader.Build.cs has RenderCore, RHI, Engine, CoreUObject, Core)
- Check for UE 5.7 vs 5.8 API differences (UserDefinedStruct.h moved to CoreUObject/StructUtils/)
- Check for unity-build collisions — qualify anonymous-namespace constants

**After build succeeds:** Reopen the editor.

---

## Step 2: Static Gates Run

**Why:** The static gate chain was last recorded FAIL (2026-08-14). It needs to re-run against current content.

```bash
python Tools/echo_run.py run static_gates
```

**Expected gates (5):**
1. `graph_reachability` — dead exec islands inside graphs
2. `bp_live_path` — assets reachable from configured entry points
3. `bp_sweep` — 5 shipped defect classes (shadowed events, empty bodies, dead islands, unreachable assets, duplicate short names)
4. `ui_style_audit` — fonts/colours/paddings consistency
5. `verify_baseline` — fingerprint match against `Docs/T3D_Baseline/bp_fingerprints.json`

**If any fail:** Read the gate output, diagnose the defect class, fix before proceeding to PIE.

**After all 5 pass:** Record to ledger:
```bash
python Tools/record_gate.py static_gates pass --note "2026-08-28 full static chain 5/5 pass after MelodiaShader build"
```

---

## Step 3: PIE — rhythm_owner + rhythm_grade_to_result

**Same PIE session — rhythm gates share a battle.**

1. Start PIE on `MelodiaIntegrationMap`
2. Trigger the P0 Playthrough (Quill dialogue -> encounter)
3. Start battle with Melusina
4. Use Melusina's unique skill — rhythm highway should appear
5. **rhythm_owner:** Confirm exactly one rhythm path reaches JRPG damage (no competing subsystem)
6. **rhythm_grade_to_result:** Play with real keyboard (Q/W/O/P), achieve a grade, confirm it changes the battle result
7. Confirm Quill resumes exactly once after battle
8. Record both gates:
```bash
python Tools/record_gate.py rhythm_owner pass --note "2026-08-28 PIE: one rhythm path to damage, Melusina unique skill"
python Tools/record_gate.py rhythm_grade_to_result pass --note "2026-08-28 PIE: real-key grade changed battle result, Quill resumed once"
```

---

## Step 4: PIE — wardrobe_equip_roundtrip + wardrobe_gameplay_hook

**Same PIE session — wardrobe gates share equip/unequip.**

1. PIE on MelodiaIntegrationMap
2. **wardrobe_equip_roundtrip:** Equip an outfit via UMelodiaWardrobeSubsystem, save game, restart PIE, load save, verify outfit + materials correct
3. **wardrobe_gameplay_hook:** Equip an outfit with a traversal capability (Glide), verify capability active, unequip, verify inactive
4. Record both gates:
```bash
python Tools/record_gate.py wardrobe_equip_roundtrip pass --note "2026-08-28 PIE: equip/save/restart/load correct"
python Tools/record_gate.py wardrobe_gameplay_hook pass --note "2026-08-28 PIE: outfit produces traversal difference"
```

**Alternative:** If RiderLink is installed, run the C++ automation tests:
- `RunTests Melodia.Wardrobe.EquipRoundtrip`
- `RunTests Melodia.Wardrobe.GameplayHook`

---

## Step 5: PIE — music_world_key

**Separate PIE — may need BP creation first.**

1. Check if `BP_MelodiaPCGChallengeHost` exists in the content tree
2. If not, create it (T3D injection or manual placement in the level)
3. PIE: play a musical phrase on the world instrument
4. Verify OnPatternCompleted reaches UMelodiaNarrativeSubsystem as a 7-verb notification
5. Verify a world object responds (door opens, etc.)
6. Record:
```bash
python Tools/record_gate.py music_world_key pass --note "2026-08-28 PIE: one phrase -> one world response -> 7-verb notification"
```

---

## Step 6: Final Ledger Check

```bash
python Tools/echo_run.py status
```

**Expected: all 11 gates PASS (6 existing + 5 new).**

If all pass, P0 is CLOSED.

---

## MelodiaShader Module Build Readiness Assessment

| File | Size | Content |
|------|------|---------|
| MelodiaShader.Build.cs | ~1.5KB | Module rules: Core, CoreUObject, Engine, RenderCore, RHI; PCHUsage explicit; Shaders/ include path |
| MelodiaShader.h | ~0.3KB | FMelodiaShaderModule : IModuleInterface (empty Startup/Shutdown) |
| MelodiaShader.cpp | ~0.2KB | IMPLEMENT_MODULE(FMelodiaShaderModule, MelodiaShader) |
| MelodiaBiolumCommon.ush | 4.7KB | Bioluminescence decay + contact impulse helpers |
| MelodiaInkBioluminescent.ush | 5.8KB | Bioluminescent ink shader |
| MelodiaInkCommon.ush | 6.9KB | Shared ink types/constants/helpers |
| MelodiaInkPatternRouter.ush | 7.6KB | Pattern router |
| MelodiaInkSdfNotation.ush | 8.6KB | SDF music-notation patterns |
| MelodiaNikkiCommon.ush | 5.5KB | Nikki aesthetic helpers (SDF ribbon, pearl sheen, glitter) |

**Assessment:** The .Build.cs has correct dependencies for a shader-only module. The .h/.cpp are minimal (no exported types, just IMPLEMENT_MODULE). The .ush files are shader source, not compiled by UBT — they're consumed by UE's shader compiler at material compile time. This should build clean.

**Risk:** Low. The module is a pure shader source container. The only risk is if another module's Build.cs references MelodiaShader but doesn't have the shader compiler path set up — but BS_GodFile.Build.cs already adds it as a dependency.

---

## Post-Build: Stale .uasset Recompile

Two non-P0 .qsc have .uasset older than their source:
- `MelodiaQuillDawnVeil.uasset` — source is 1786122004, .uasset is 1786122004 (same — may be OK)
- `MelodiaQuillSolsticeDrum.uasset` — source is 1786122004, .uasset is 1786122004 (same — may be OK)

Actually checking: both .qsc and .uasset have the same mtime, so they may have been compiled together. Non-blocking either way — these are not P0 scripts.

---

## Safety Reminders

- One editor instance, always. Check port 9316 has exactly one listener.
- MODAL_OPEN in the log is not a hang — grep before concluding the editor is dead.
- Never `git clean -fd` or `git checkout -- .`
- Never touch Content/TurnBasedJRPGTemplate/Blueprints/Skills/ from Python
- Never FBX import into a path that already holds an asset
