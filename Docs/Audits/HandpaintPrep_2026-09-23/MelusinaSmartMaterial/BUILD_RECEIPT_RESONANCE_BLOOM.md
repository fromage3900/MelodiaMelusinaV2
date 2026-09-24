# BUILD_RECEIPT_RESONANCE_BLOOM — SMS_Melusina_Handpaint

**When:** 2026-09-24 ~02:55 ET (America/Toronto)  
**Owner:** Melodia / Melusina  
**Milestone:** M2 — VNP-style folder 11 + Resonance Bloom folder 15  
**Pilot:** ZenLantern V2 Showcase  

---

## What changed

### Plugin (`painter_plugins\melodia_build_sms_handpaint.py`)
- Stack log/docstring: **01–10 + 11 VNP + 15 ResonanceBloom**
- New folder **`11_VeryNormal_Workflow`** after cymatic folder 10:
  - `11a_WSN_Inject` — Normal fill; TODO assign baked WSN
  - `11b_Paint` / `11b_PaintNormals` — paint slot for stroke normals
  - `11c_WSN_Anchor` — named anchor placeholder (opacity 0)
  - `11d_TangentCombine` — Normal fill; optional Cymatic Normal SoftLight @0.15; TODO tangent / shelf converter (Melusina does not ship VNP SBSAR)
- New folder **`15_ResonanceBloom`** after 11:
  - `15a_ResonanceCore` — Emissive Accent Add @ ResonanceCore 0.55; mask TODO vcol.A (×B)
  - `15b_MoonglowHalo` — cooler Accent Add @ 0.40; try Opacity → mask; **TODO INVERT** + Height × vcol.B
  - `15c_CharmFlash` — hotter Accent Add @ 0.35; try Metallic → mask (sparkle remap); TODO × vcol.G
  - `15d_InnerEmber` — warm cedar `(0.55, 0.28, 0.12)` Add @ 0.25; mask TODO inverted AO
- Layer **06** left for compatibility; console note points to 15a as refined core
- Fail-soft try/except around folders 11 and 15
- **No fake `.spsm` bytes**; `create_smart_material` only if API present

### Docs
- `MELUSINA_SMART_MATERIAL_SPEC.md` — 11a–d, 15a–d, remapping rationale, new exposed params
- `build_recipe\PAINTER_CLICKPATH.md` — bake WSN before 11*; mask wires for 15b/c/d
- `designer\...\PAINTER_WIRE.md` — preferred M2 order (SBSAR → 11 optional → 15)
- `GOAL_V2_GO.md` (root + designer copy) — M2 SMS milestone; Designer re-cook not required
- `designer\...\GRAPH_SPEC.md` — §10 SMS-side Resonance Bloom note

### Plugin sync
| Location | Status |
|---|---|
| `MelusinaSmartMaterial\painter_plugins\` (source of truth) | Updated |
| `C:\Users\froma\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\` | Synced |
| `C:\Users\froma\OneDrive\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\` | Synced |

---

## Key layer names (lock)

`11_VeryNormal_Workflow` · `11a_WSN_Inject` · `11b_Paint` · `11b_PaintNormals` · `11c_WSN_Anchor` · `11d_TangentCombine`  
`15_ResonanceBloom` · `15a_ResonanceCore` · `15b_MoonglowHalo` · `15c_CharmFlash` · `15d_InnerEmber`

---

## Brennan next steps

1. **Reload Painter plugins** (Python → Reload plugins list, or restart Painter).
2. Open ZenLantern Showcase; bake AO + **WSN** + Curvature (+ vcol) if not already.
3. Console one-liner:

```python
import melodia_build_sms_handpaint as m; m.build_sms()
```

4. Wire TODO masks (especially 15b INVERT Opacity, 15c × vcol.G, 15d inverted AO, 11a WSN).
5. Right-click folder **`SMS_Melusina_Handpaint`** → **Create smart material**.
6. Copy the real `.spsm` Painter wrote →  
   `MelusinaSmartMaterial\exports\SMS_Melusina_Handpaint.spsm`  
   (never invent bytes offline).

---

## Explicitly not done / blockers

- No Monolith `save_packages` / recompile called
- No Designer re-cook for this milestone
- No fake SPSM authored
- Runtime mask generator wiring still manual (Painter API limits) — TODOs logged by plugin
- WSN / Tangent mesh maps must exist in the project before 11* looks correct

---

## Naming check

Melodia / Melusina only. No GrokBot / GrokStaged prefixes in code or docs (aside from explicit “never Grok*” guard comments).
