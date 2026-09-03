# Dreamprint — LookdevDirector BP Graph Execution Steps (2026-08-15)

Target: `/Game/EnvSandbox/Lookdev/Candidates/BP_MelodiaLookdevDirector_Candidate`

## Overview
The director BP becomes the runtime conductor that: (a) plays the MetaSound music pulse source, (b) samples its Envelope output into `MPC_MelodiaInk InkReact`, and (c) switches profile MIs per ProfileIndex.

---

## 1. Components (Actor Defaults)

| Name | Class | Notes |
|---|---|---|
| **MusicPulseSource** | `UAudioComponent` | Sound = `/Game/Melodia/_PROJECT/04_Audio/Music/MSS_MelodiaMusicPulse`; Auto Activate = false; Loop via the MetaSound graph (WavePlayer loop), not the component |

**To set**: Open BP_MelodiaLookdevDirector_Candidate → Components → Add Component → `Audio Component` → rename to `MusicPulseSource` → set Sound to `/Game/Melodia/_PROJECT/04_Audio/Music/MSS_MelodiaMusicPulse` → uncheck `Auto Activate`.

---

## 2. Exposed Variables (Instance Editable)

In the **My Blueprint** panel, add:

| Variable Name | Type | Category |
|---|---|---|
| `ProfileIndex` | `int` | `Director` |
| `MPC_MelodiaInk` | `Material Instance Constant` | `Materials` |
| `InkMasterWeight` | `float` | `Director` (optional, overridden per profile) |

**Defaults**: `ProfileIndex` = 1 (Narrative). `InkMasterWeight` default = 0.65.

---

## 3. BeginPlay Wiring

### 3.1 Setup Sequence (Construction Script or BeginPlay)

1. **Set ProfileIndex** — set to default value 1 (Narrative). This can be done via **Construction Script** so the default persists, or set in **BeginPlay**.

2. **Play Music Pulse**:  
   `MusicPulseSource` → **Play**  
   *(This starts the MetaSound WavePlayer loop inside the audio component.)*

3. **Subscribe to MetaSound Envelope**:  
   - Get world **GameInstance** → **Get Subsystem** → `UMetaSoundOutputSubsystem` (cast/verify)  
   - Call: **WatchOutput**  
     - **AudioComponent**: `MusicPulseSource`  
     - **OutputName**: `"Envelope"`  
     - **OnOutputValueChanged**: **Promote to custom event** → name `OnEnvelopeChanged` (see Step 4)

4. **Apply Initial Profile**:  
   Call the **ApplyProfile** custom event (see Step 5) with the current `ProfileIndex`.

---

## 4. OnEnvelopeChanged(float Value) — Amplitude Bridge

**Purpose**: Route MetaSound envelope amplitude → `MPC_MelodiaInk` scalar parameter `InkReact`.

```
OnEnvelopeChanged(float Value)
   |
   v
Clamp Value:    Float A = Value
                Float B = 0.0
                Float C = 1.0
                Result = Clamp(A, B, C)    // clamp(Value, 0.0, 1.0)

   |
   v
Set Scalar Parameter:
   Target:     MPC_MelodiaInk        (Material Instance Constant pin)
   Parameter:  "InkReact"
   Value:      Result from Clamp
```

**Final node chain** (in BP graph):

1. **Custom Event `OnEnvelopeChanged`** receives `Value` pin (float).
2. **Float > Float** node (Clamp):  
   - **A**: `Value`  
   - **B**: `0.0` (type float)  
   - **C**: `1.0` (type float)  
   → Output is clamped value in [0,1].
3. **Set Scalar Parameter Value** (or **Set Vector Parameter Value** if using the MPC's full vector):  
   - **Object**: `MPC_MelodiaInk` (drag reference from My Blueprint → Materials)  
   - **Parameter Name**: `"InkReact"`  
   - **Parameter Value**: `Clamp` output pin.

**Result**: Envelope amplitude (0–1) drives InkReact liveliness in the material.

---

## 5. ApplyProfile (ProfileIndex 0/1/2)

**Purpose**: Swap the candidate PPV's `M_PP_MelodiaInk_*` blendable to the matching profile MI and set `InkMasterWeight`.

### 5.1 Profile → MI Mapping Table

| ProfileIndex | Profile | Target Material Instance | InkMasterWeight |
|---|---|---|---|
| 0 | GameplayStandard | `MI_MelodiaInk_GameplayStandard` | 0.45 |
| 1 | Narrative | `MI_MelodiaInk_Narrative` | 0.65 |
| 2 | PortfolioHero | `MI_MelodiaInk_PortfolioHero` | 1.0 |

### 5.2 Graph Logic

Create custom event **`ApplyProfile(int32 ProfileIndex)`** (call from BeginPlay after WatchOutput subscription, or via a UI button).

**Branch on ProfileIndex**:

```
Branch:          ProfileIndex == 0
   | True:      Set scalar parameter "InkMasterWeight" on MPC_MelodiaInk = 0.45
   | False:     Branch: ProfileIndex == 1
              | True:  Set scalar parameter "InkMasterWeight" on MPC_MelodiaInk = 0.65
              | False: Set scalar parameter "InkMasterWeight" on MPC_MelodiaInk = 1.0
```

**Alternative (cleaner)** — use **Select** node:

1. **Select (int32) ProfileIndex**:
   - **Case 0**: `0.45`
   - **Case 1**: `0.65`
   - **Case 2**: `1.0`
   → Output pin → **Set Scalar Parameter Value** on `MPC_MelodiaInk` → `"InkMasterWeight"`.

2. **Also apply the profile MI** — after setting the weight, set the material index/override on the PPV.  
   This is typically done by dragging the **PPV (Post Process Volume)** reference and setting its **Materials** slot to the corresponding `MI_MelodiaInk_*` instance.  
   If the director BP has a **PPV component** or references the world's PPV, promote a reference and do:

   ```
   WorldSettings / GameInstance PPV → Set Material Parameter
   ```

   More precisely, if the candidate has a **named material slot** on the PPV material `M_PP_MelodiaInk`, use **Set Material Parameter** node on the PPV to swap the MI instance.

**Full ApplyProfile sequence** (called from BeginPlay step 4):

```
BeginPlay
   |
   v
Set ProfileIndex = 1 (default) [Construction Script or Set Node]
   |
   v
MusicPulseSource.Play()
   |
   v
Get Subsystem UMetaSoundOutputSubsystem → WatchOutput(MusicPulseSource, "Envelope", OnEnvelopeChanged)
   |
   v
ApplyProfile(ProfileIndex)   // sets InkMasterWeight + swaps MI
```

---

## 6. A/B Verification Before Promotion

**Tool**: `setup_dreamprint_ab.py` (in-editor Python script).

### 6.1 Commands

| Mode | Usage |
|---|---|
| `mode("source")` | Activates source camera view on: `L_KaleidoNave`, `L_FallenMoon`, `ZenForestTest`, `L_MelusinaMorning` |
| `mode("candidate", profile=...)` | Activates candidate view with profile index substituted |

**To execute** (in Unreal Editor Python console or via the script):

```python
import subprocess
subprocess.run(["python", "Content/Python/setup_dreamprint_ab.py", "mode", "candidate", "profile=1"])
# or
python setup_dreamprint_ab.py mode source
```

**Verification checklist** before promoting:
- Both `mode("source")` and `mode("candidate", profile=1)` display correctly on their respective cameras.
- No live PPV edits until owner sign-off.
- Profile MI swaps match the table in Step 5.

---

## 7. Assets Reference (for drag-and-drop pins)

| Asset | Path | Usage |
|---|---|---|
| `MPC_MelodiaInk` | `/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk` | Target material instance constant for `InkReact` and `InkMasterWeight` |
| `M_PP_MelodiaInk` (master, After Tonemap) | `/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk` | Master material (read-only, for reference) |
| `MI_MelodiaInk_GameplayStandard` | `/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_GameplayStandard` | Profile MI — Index 0 |
| `MI_MelodiaInk_Narrative` | `/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_Narrative` | Profile MI — Index 1 |
| `MI_MelodiaInk_PortfolioHero` | `/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_PortfolioHero` | Profile MI — Index 2 |
| `M_PP_MeluColorGrade + SyncVision block` | `/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade` | Additional color grading (not directly wired in v1) |
| `MSS_MelodiaMusicPulse` | `/Game/Melodia/_PROJECT/04_Audio/Music/MSS_MelodiaMusicPulse` | MetaSound wave + envelope source |

---

## 8. Complete BeginPlay Construction Script Summary

```
Construction Script (or BeginPlay):
1. Set ProfileIndex = 1 (default Narrative)
2. MusicPulseSource->Play()
3. Subsystem = UMetaSoundOutputSubsystem.GetWorldSubsystem()
4. WatchOutput(AudioComponent=MusicPulseSource, OutputName="Envelope", OnOutputValueChanged=OnEnvelopeChanged)
5. Call ApplyProfile(ProfileIndex)
```

**OnEnvelopeChanged graph**:
```
OnEnvelopeChanged(Value)
  → Clamp(Value, 0.0, 1.0)
  → SetScalarParameterValue(MPC_MelodiaInk, "InkReact", Clamped)
```

**ApplyProfile graph**:
```
Branch/Select on ProfileIndex:
  0 → SetScalarParameterValue(MPC_MelodiaInk, "InkMasterWeight", 0.45)
  1 → SetScalarParameterValue(MPC_MelodiaInk, "InkMasterWeight", 0.65)
  2 → SetScalarParameterValue(MPC_MelodiaInk, "InkMasterWeight", 1.0)
[Also: swap PPV material slot to corresponding MI_MelodiaInk_*]
```

---

## 9. Notes & Future Extensions

- **Band detail**: InkBass/InkMid/InkTreble currently remain on the TouchDesigner OSC bridge (`MPC_Portfolio_Audio`). A future MetaSound graph pass can expose per-band outputs (3x band-pass + envelope) and the director can write the same three channels in-engine.
- **A/B toggle**: The `ab.mode("source")` / `ab.mode("candidate","<profile>")` is controlled externally via `setup_dreamprint_ab.py` — not wired inside the BP graph itself, but verified before promotion.
- **Profile switching at runtime**: The `ApplyProfile` custom event can be bound to a UI widget or input key to swap profiles at runtime without restarting play.