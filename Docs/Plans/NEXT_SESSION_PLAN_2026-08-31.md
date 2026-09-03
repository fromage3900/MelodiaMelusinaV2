# Next Session Plan — 2026-08-31 (Post-Commit)

## Immediate Priorities (Morning)

### 1. Editor Recovery
- [ ] Restart Unreal Editor (modal loop cleared)
- [ ] Verify port 9316 listening
- [ ] Run `hermes gateway start` if needed

### 2. Jellyfish Wiring (P0 Sea Above)
- [ ] Wire `MI_Jelly_Bell` → `JELLY_Bell` skeletal mesh
- [ ] Tag jellyfish in `P0_TASK_LEDGER.json`
- [ ] Set parallax on jelly MIs: `ParallaxStrength=0.35, ParallaxScale=0.08, ParallaxHeight=0.12`
- [ ] Author `ABP_JellyBell` for 2-bone pulse animation
- [ ] Assemble `BP_Jelly_SeaAbove` and place in `LV_SeaAbove_Prototype`

### 3. Material Instance Review
- [ ] Nikki masters: parallax, inline vs MF split, bNikkiHero switch, BaseTint
- [ ] Fabric MIs: Faraway COPs import, parallax, sheen params
- [ ] Jelly MIs: verify parent is `M_Master_Toon_Universal_Alpha`

---

## Tomorrow's Material Work (Per Emerging Toolchain §9)

### P0 Sea Above (Direct)
| Task | Tool | Status |
|------|------|--------|
| Jellyfish bell material | Monolith | Blocked |
| Jellyfish arms material | Monolith | Done |
| Water surface (oceanology) | Monolith | Read-only |
| Coral skin instances | Monolith | 18 meshes need wiring |
| Kelp sway WPO | Monolith | Scaffolded |
| Terrain height blend | Monolith | Needs parallax |

### P2 Faraway Mother (Integration)
| Task | Tool | Status |
|------|------|--------|
| Faraway COPs textures | Houdini COPs | Imported |
| Pearl lace 3x3 variants | Houdini COPs | 72 textures |
| Pearl painterly 4K | Houdini COPs | 7 maps/variant |
| Faraway dress MI | Monolith | Needs wiring |
| Corset gilded acanthus | Monolith | Needs wiring |
| Carved alabaster wood | Monolith | Needs wiring |

### Advanced Fabric + PBR Integration
| Task | Tool | Status |
|------|------|--------|
| M_Master_Nikki fabric params | Monolith | Inline vs MF issue |
| M_Universal_Enhanced_Fabric | Monolith | Exists, needs instances |
| Sheen params on all fabric MIs | Monifold | Needs audit |
| Parallax on all PBR sets | Monolith | Needs audit |
| Subsurface for translucency | Pipeline | Missing map |

---

## New Skills to Create

1. **melodia-p0-sea-above-material** — P0 Sea Above material wiring workflow
2. **melodia-faraway-cops-import** — Faraway COPs texture → MI workflow
3. **melodia-fabric-sheen-audit** — Fabric sheen param audit + fix
4. **melodia-parallax-propagation** — Set parallax on all MIs project-wide

---

## Emerging Tech Integration (Per Master Index)

### PRESENT (extend, don't rebuild)
- Copernicus: now 11 variants, pure numpy — extend for new maps
- SpeedTree: M_SpeedTreeMaster exists — bridge for Sea Above kelp
- Houdini Engine: 22.0.368 — use for terrain stamps, path corridors
- PCG: enabled — use for reef scatter, coral distribution
- Monolith: 1330+ actions — primary editor interface

### SCAFFOLDED (finish before parallel)
- UMelodiaCymaticsSubsystem: audio→geometry Chladni (read-only)
- UMelodiaDressingSubsystem: dash-capable dressing
- UMelodiaCaptureRenderSubsystem: offscreen HDR render

### WATCH (don't promote without task)
- Magpie: seam scaffolded, no renderer
- Neural shaders: needs material onnx
- Procedura: research only

---

## Anti-Duplication Checklist (Per §9)
1. PRESENT systems: extend audio writer (single), music clock
2. SCAFFOLDED: finish CymaticsSubsystem before parallel
3. WATCH: Magpie needs explicit owner task
4. External: IlluGen, LiquiGen, EmberGen — can't build natively
5. World Field Bus: reuse FilterFlow/Tension/Moisture/Contact/Residue
6. Editor: one instance, one :9316, batch saves unattended
7. Evidence: offline probe + live PIE + ledger row

---

*Generated 2026-08-31 ~03:15 AM. Commit in progress.*
