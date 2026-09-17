# TouchDesigner Render Pipeline Audit — 2026-09-17

**Stamp:** 2026-09-17 15:18 ET (America/Toronto)  
**Owner lane:** MelodiaTouchDesigner  
**No destructive edits.**  
**FROZEN copy — do not edit:** `C:\EnvironmentPortfolio\_TouchDesigner`

---

## Canon vs frozen
| Role | Path |
|---|---|
| **CANON git checkout** | `C:\MelodiaTouchDesigner` |
| **Active toe tip (2026-09-16)** | `grandmaster_melodia7.3.toe` / `grandmaster_melodia7.toe` |
| **FROZEN mirror (do not edit)** | `C:\EnvironmentPortfolio\_TouchDesigner` |
| Game authority | `C:\EnvironmentPortfolio\BS_GodFile` |
| Website | `C:\Users\froma\my-site` |

Contract: TD/AE are **downstream presentation** — consume UE/music semantics; never save/gameplay authority. Cross-repo stamp 2026-09-08 moved TD docs out of BS_GodFile into private MelodiaTouchDesigner.

Confirm full toe paths with:
`Get-ChildItem C:\MelodiaTouchDesigner -Recurse -Filter grandmaster_melodia7*.toe`

---

## Project layout (canon tips)
| Path | Role |
|---|---|
| `C:\MelodiaTouchDesigner\td\grandmaster_melodia\` | Grandmaster network / comps |
| `…\td\grandmaster_melodia\renders\` | TD beauty / sequence renders → **curate into my-site heroes** |
| `…\td\grandmaster_melodia\assets\houdini_flip\` | Houdini flip / cymatics-adjacent flipbooks |
| `…\td\grandmaster_melodia\assets\vfx_alphas\` | VFX alpha plates |
| `…\td\grandmaster_melodia\assets\nikki_atlus_lookdev.cube` | Nikki-soft lookdev LUT (pattern/grade only) |
| `C:\MelodiaTouchDesigner\scratch\portfolio_hero_renders\` | Portfolio hero stills → **priority curate into my-site heroes** |
| `C:\MelodiaTouchDesigner\exports\` | Export / deliverable stills & movies |

Legacy frozen tree historically supplied `.venv` for EnvironmentPortfolio `.mcp.json` embody envoy — document retarget to canon; **do not edit frozen tree**.

---

## UE bridge / Spout / ports
| Link | Detail |
|---|---|
| **Spout** | TD↔UE (or peers) GPU share for live lookdev/concert; my-site publish should prefer offline `renders/` / `exports/` / `portfolio_hero_renders` stills |
| LiveLink / OSC | Port **9876** (`BS_GodFile\Docs\Architecture\MELUSINA_T3D_LIVELINK_OSC_PIPELINE_2026-08-14.md`) |
| Embody envoy MCP | Port **9870** (`EnvironmentPortfolio\.embody\envoy-bridge.py`) — historically frozen `_TouchDesigner\…\.venv` |
| Blender MCP | Port **9877** |
| Validator | `BS_GodFile\deploy\touchdesigner_validator.py` |

Sheep/cymatics: **UE owns** `MPC_Cymatics_Driver` + `T_Chladni_*` + ChladniFleece evidence; Houdini under `Saved\Audit\choral_sheep\houdini_variants_v3\`; TD `houdini_flip` / `vfx_alphas` consume for concert/editorial. Board 06 lock: `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`.

---

## How TD feeds Melodia / my-site
1. UE game → beat/harmony + sheep Chladni materials.  
2. TD grandmaster7 (+ optional Spout live) → `renders\`, `exports\`, `scratch\portfolio_hero_renders\`.  
3. Grade via `nikki_atlus_lookdev.cube` for soft magical consistency.  
4. Approved stills → `C:\Users\froma\my-site\public\melodia\melusina-morning-vfx\2026-09-17\heroes\`.  
5. AE same MelodiaTouchDesigner lane for tracking/editorial.

---

## Gaps vs Infinity-Nikki-soft lookdev
| Gap | Sev | Notes |
|---|---|---|
| TD portfolio/renders not yet QC-copied into 2026-09-17 my-site heroes | **P0** | Parent CopyToBox + promote; executor blocked |
| Dual checkout drift (canon vs FROZEN EnvPortfolio `_TouchDesigner`) | **P0** | mcp.json may still reference frozen venv |
| Spout live vs offline export path not one-pager | **P1** | Prefer offline folders for site |
| `.cube` grade applied inconsistently across UE vs TD stills | **P1** | Align Morning heroes to soft teal/mote language |
| Full path of `grandmaster_melodia7.3.toe` not re-listed live here | **P1** | Parent confirm |
| Sheep Board-06 lock vs TD experimental fleece comps | **P0** | Only feed approved frames |

---

## Recommended next actions
1. Enumerate toe tips + newest stills under `scratch\portfolio_hero_renders`, `td\grandmaster_melodia\renders`, `exports` → census beside this receipt.  
2. CopyToBox best 4–8 stills; QC Nikki-soft; land in my-site heroes + Working `Curated\` as `11_TD_*`….  
3. Confirm Spout sender/receiver in grandmaster7; document offline export COMP for site.  
4. Point embody/mcp venv notes at **canon** MelodiaTouchDesigner (leave frozen untouched).  
5. Document `nikki_atlus_lookdev.cube` as shared soft grade for Morning VFX heroes.  
6. **Do not edit** `C:\EnvironmentPortfolio\_TouchDesigner`.

---

## Cross-link
Nikki audit §4–5. Staging: `/workspace/fromage-push/`.
