# Toon Profile Creation Guide — Phase 1

## Why Toon Profiles

The Toon BSDF node already handles diffuse/specular toon lighting, but **all materials share one** `TP_Default`. Creating dedicated profiles lets **fabric behave differently from foliage** — without any shader permutation cost (profiles are data, not shader variants).

## Profiles to Create

| Profile | For | Diffuse Ramp | Specular Ramp | GI Intensity |
|---|---|---|---|---|
| `TP_Character` | Nikki, Melusina, NPCs | 3-stop (anime shadow) | Narrow highlight | 0.3 |
| `TP_Foliage` | Grass, leaves, vines | Wide (soft transition) | None (matte) | 0.8 |
| `TP_Water` | Water surfaces | 2-stop + high contrast | Strong specular | 1.0 |
| `TP_Hero` | Nikki/Melusina close-ups | Same as Character + shadow hatching enabled | Narrow | 0.3 |

## Step-by-Step (In-Editor)

### 1. Create Each Profile

1. Open **any material** that uses Substrate Toon BSDF (e.g., `M_Master_Toon_Universal`)
2. Select the Substrate Toon BSDF node
3. In Details panel → **Toon Profile** dropdown → **Create New Asset** → **Toon Profile**
4. Save it to: `/Game/EnvSandbox/Materials/ToonProfiles/TP_Character`
5. Repeat for `TP_Foliage`, `TP_Water`, `TP_Hero`

### 2. Tune Each Profile

#### TP_Character (3-stop anime shadow)
- **Diffuse Ramp**: 3 keys at NdotL 0.0, 0.3, 1.0
  - Key 0 (shadow): deep indigo `#0A0815` (this is the Hoyo-style shadow replacement)
  - Key 1 (mid): base color
  - Key 2 (lit): base color + warm bias
- **Specular Ramp**: 1 narrow key at NdotL 0.9
- **Indirect Diffuse Intensity**: 0.3 (keep GI subtle on characters)
- **Indirect Specular Intensity**: 0.3

#### TP_Foliage (soft painterly shadows)
- **Diffuse Ramp**: 2 keys with smooth interpolation
  - Key 0: dark green `#0D1A0D` 
  - Key 1: base color
- **Specular Ramp**: flat (no specular)
- **Indirect Diffuse Intensity**: 0.8 (foliage catches bounce light)
- **Indirect Specular Intensity**: 0.5

#### TP_Water (high-contrast reflective)
- **Diffuse Ramp**: 2 keys
  - Key 0: deep teal `#0A1A20`
  - Key 1: base water color
- **Specular Ramp**: strong highlight
- **Indirect Diffuse Intensity**: 1.0
- **Indirect Specular Intensity**: 1.0

#### TP_Hero (character close-up with hatching)
- Same as TP_Character but:
  - **Shadow Hatching Pattern**: assign a line texture (`T_HatchPattern` — create if not present)
  - **Shadowing Extinction**: 0.3 (subtle hatch in shadows)

### 3. Check for Known Bug

UE 5.8 has a bug where Toon Profile overrides in Material Instances don't persist after editor restart ([forum link](https://forums.unrealengine.com/t/ue-5-8-substrate-toon-profile-override-in-material-instance-fails-to-apply-after-restarting-the-editor/2738757)). Workaround: assign profiles at the **master material level** (not the instance), and trigger a dummy recompile after restart.

### 4. Run Assignment Script

After profiles exist, run:
```python
# Via editor Output Log:
py "Content/Python/assign_toon_profiles.py" --apply

# Or headless:
python Content/Python/run_headless.py --script "Content/Python/assign_toon_profiles.py" -- --apply
```

---

## Verifying Profiles Are Active

Open a material, select the BSDF node, check Details → Toon Profile. The profile name should appear.

For validation across all materials:
```python
py "Content/Python/assign_toon_profiles.py" --list
```

Expected output:
```
M_Master_Toon_Universal      -> TP_Default
M_Master_Nikki               -> TP_Character
M_Master_Toon_Landscape_HeightBlend -> TP_Foliage
```

(The universal master stays `TP_Default` as safe baseline; character, landscape, and water masters get custom profiles.)
