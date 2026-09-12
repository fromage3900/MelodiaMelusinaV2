# Audio-Reactive Bridge — Owner Checklist

> **Generated:** 2026-09-05T03:40:00Z  
> **Lane:** docs (consolidation)  
> **Sources:** `audio_reactive_bridge_execution_2026-09-03.json`, `audio_reactive_bridge_gate_prep_2026-09-03.json`, `audio_reactivity_bridge_option_b_spec_2026-09-03.json`  
> **Status:** SPEC_READY_FOR_OWNER_REVIEW — no .uasset written  

---

## Pre-Flight Requirements

| Check | Critical |
|:---|:---:|
| Backup `MPC_Melodia_Palette` asset | ✅ |
| Backup `M_Master_Toon_Universal` asset | ✅ |
| Close all other material editors (free GPU memory) | |
| Save all open assets | ✅ |
| Verify `M_Master_Toon_Universal` PS instruction count = 1182 | |
| Verify no broken references in `M_Master_Toon_Universal` | ✅ |

---

## Phase 1: Create MF_AudioReactive MaterialFunction

### Step 1 — Create the MaterialFunction asset
- Content Browser → Right-click → Materials & Textures → Material Function
- Name: `MF_AudioReactive`
- Path: `/Game/Melodia/_PROJECT/04_Materials/`

**Done criteria:** Asset exists, opens in Material Function Editor.

### Step 2 — Add 4 ScalarParameter inputs
- Right-click → ScalarParameter (×4)
- Names + defaults:
  - `BeatPulse` = 0
  - `BassIntensity` = 0
  - `TrebleIntensity` = 0
  - `GlobalReactivity` = 1
- Set Group = `MPC_Melodia_Palette` for each

**Done criteria:** 4 ScalarParameter nodes, all grouped.

### Step 3 — Build AudioSheen output (4 nodes)
1. Multiply(BeatPulse × 0.3 → BeatSheen)
2. Multiply(TrebleIntensity × 0.85 → TrebleSheen)
3. Add(BeatSheen + TrebleSheen → SheenBase)
4. Multiply(SheenBase × GlobalReactivity → AudioSheen output)

### Step 4 — Build AudioEmissive output (4 nodes)
1. Multiply(BassIntensity × 0.5 → BassEmissive)
2. Multiply(BeatPulse × 0.5 → BeatEmissive)
3. Add(BassEmissive + BeatEmissive → EmissiveBase)
4. Multiply(EmissiveBase × GlobalReactivity → AudioEmissive output)

### Step 5 — Build AudioRoughness output (4 nodes)
1. Multiply(BeatPulse × 0.1 → BeatDip)
2. OneMinus(BeatDip → RoughnessBase)
3. Clamp(RoughnessBase, 0, 1 → RoughnessClamped)
4. Multiply(RoughnessClamped × GlobalReactivity → AudioRoughness output)

### Step 6 — Expose 3 Output Result nodes
- Add 3 Output Result nodes: `AudioSheen`, `AudioEmissive`, `AudioRoughness`
- Connect respective final Multiply outputs

**Done criteria:** 3 output pins visible; MaterialFunction compiles standalone.

---

## Phase 2: Wire into M_Master_Toon_Universal

### Step 7 — Open the master material
- Navigate to `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`
- Double-click to open Material Editor

### Step 8 — Add MaterialFunctionCall node
- Right-click → MaterialFunctions → `MF_AudioReactive`
- Place after `MF_NikkiDreamGrade`, before final color output

### Step 9 — Wire AudioSheen → Sheen input
- Find existing Sheen input pin
- Add Multiply: `(Existing Sheen) × (MF_AudioReactive.AudioSheen) → Sheen`

### Step 10 — Wire AudioEmissive → EmissiveColor input
- Find existing EmissiveColor input pin
- Add Multiply: `(Existing EmissiveColor) × (MF_AudioReactive.AudioEmissive) → EmissiveColor`

### Step 11 — Wire AudioRoughness → Roughness input
- Find existing Roughness input pin
- Add Multiply: `(Existing Roughness) × (MF_AudioReactive.AudioRoughness) → Roughness`

### Step 12 — Apply and Compile
- Click Apply
- Wait for shader compile
- Check Output Log for errors

**Done criteria:**
- Compiles successfully
- PS instruction count delta: +80–120 (projected ~1282, max safe 1400)
- No broken references

---

## Gate Acceptance

```bash
python Tools/echo_run.py record audio_reactivity_bridge pass
```

**Prerequisites for gate:**
- All 12 milestones verified done
- MF_AudioReactive MaterialFunction exists and compiles standalone
- M_Master_Toon_Universal compiles with MF_AudioReactive wired
- PS instruction count delta is +80–120
- Material instance children inherit changes correctly

---

## Rollback Procedure

1. If compile fails → Delete MF_AudioReactive MaterialFunctionCall node from M_Master_Toon_Universal
2. If PS budget exceeded → Remove output wirings individually
3. If catastrophic → Restore M_Master_Toon_Universal from backup
4. Verify PS instruction count returns to 1182
5. Document which output caused budget issue

---

## Cross-References

- `Saved/Audit/audio_reactive_bridge_execution_2026-09-03.json` (12 milestones + done criteria)
- `Saved/Audit/audio_reactive_bridge_gate_prep_2026-09-03.json` (materialization steps)
- `Saved/Audit/audio_reactivity_bridge_option_b_spec_2026-09-03.json` (alternative routing)
- `Saved/Audit/audio_reactivity_exec_spec_grounded_2026-09-03.json` (grounded execution spec)
- `Saved/Audit/audio_reactivity_gap_spec_2026-09-02.json` (gap analysis)
- `Saved/Audit/p1_task_ledger_cymatics_update_2026-09-03.json` (ledger context)
- `Saved/Audit/audio_reactive_bridge_gate_prep_2026-09-03.json` (gate prep)

---

*End of checklist. Spec only — no .uasset created.*