# BUILD_RECEIPT_PAINTER — SMS_Melusina_Handpaint

**When:** 2026-09-24 02:10 ET (America/Toronto)
**Machine:** fromage
**Naming:** Melodia / Melusina only — **`SMS_Melusina_Handpaint`**. No fake `.spsm`. No Monolith.

## Installed

| Path | Role |
|---|---|
| `C:\Users\froma\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\melodia_build_sms_handpaint.py` | Primary Painter plugin |
| `C:\Users\froma\OneDrive\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\melodia_build_sms_handpaint.py` | OneDrive mirror |
| `...\MelusinaSmartMaterial\painter_plugins\melodia_build_sms_handpaint.py` | Source / backup in SMS tree |
| `...\MelusinaSmartMaterial\build_recipe\PAINTER_CLICKPATH.md` | Paths fixed + **Scripted build** section |
| `...\MelusinaSmartMaterial\BUILD_NEXT.md` | ≤3-line human next steps |

Existing reference plugin (patterns reused): Documents `python\plugins\melodia_stage_bakes.py`.

## Cymatic resources

`resources\cymatic\` complete vs `Bakes_Cymatic\FrozenFracture\` (Height, Emissive, Metallic, Opacity, Normal, BaseColor + ORM/Roughness/Iridescence). No gaps.

## How to run

```python
import melodia_build_sms_handpaint as m; m.build_sms()
```

Menu: **Melodia: Build SMS_Melusina_Handpaint**. Env `MELUSINA_AUTO_BUILD_SMS=1` auto-fires ~20s after plugin start.

## Project / launch

- No ZenLantern `.spp` found under HandpaintPrep.
- Showcase FBX verified: `...\02_ZenLantern\substance\meshes\ZenLantern_V2_Showcase.fbx`
- Painter launched with that FBX if process start succeeded (see agent summary).

## API limits

- Mask generators (AO × vcol.R, Curvature × vcol.G, vcol.A) left as TODO + black mask slots.
- `create_smart_material` best-effort; else human Create smart material.
- Cannot drive Painter Python console from outside → `BUILD_NEXT.md`.

## Blockers / next

See `BUILD_NEXT.md` (3 steps). Real `exports\SMS_Melusina_Handpaint.spsm` only after GUI Create smart material — not authored as fake bytes.

