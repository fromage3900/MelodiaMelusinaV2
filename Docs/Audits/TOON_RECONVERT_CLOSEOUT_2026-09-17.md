# TOON reconvert closeout — 2026-09-17

**Owner:** Fromage  
**Repo tip:** `C:\EnvironmentPortfolio\BS_GodFile` (MelodiaMelusinaV2)  
**Stamp:** 2026-09-17 (America/Toronto)  
**Mode:** Live UE reparent / wrap onto **Melodia Toon pipeline masters**. Docs receipt only — **no** `.uasset` in this PR.  
**Evidence:** owner-authoritative live project facts, 2026-09-17.

---

## Goal

Convert Quixel / Megascans / Enchanted Vehicles / Brushify Floating Islands onto **Melodia Toon pipeline masters**.

**Owner correction:** Quixel **Custom_MS** (`M_MS_CustomDefault` / `M_MS_CustomFoliage` and overwrite variants) is the **wrong** target. Abandoned after that correction. Same-day gap hunt [`MATERIALS_CONVERGENCE_GAP_HUNT_2026-09-17.md`](MATERIALS_CONVERGENCE_GAP_HUNT_2026-09-17.md) still names Custom_MS as a hypothesized retarget — that hypothesis is **superseded**.

## Correct masters

Cross-checked against [`Docs/Pipeline/MATERIAL_PIPELINE.md`](../Pipeline/MATERIAL_PIPELINE.md), [`Docs/Materials/LABEL_MAP_2026-09-09.md`](../Materials/LABEL_MAP_2026-09-09.md), and `Content/Python/paths.py` (`M_UNIVERSAL`, `M_TOON_FOLIAGE`).

| Role | Asset | Soft path |
|------|-------|-----------|
| **Primary** | `M_Master_Toon_Universal` | `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` |
| **Foliage** | `M_ToonFoliage` | `/Game/EnvSandbox/Materials/Masters/M_ToonFoliage` |

Do **not** retarget marketplace env MIs onto Custom_MS overwrite masters.

---

## Results (live UE, 2026-09-17)

| Pack | Result |
|------|--------|
| Megascans MI | **237/237** reparented onto Toon / ToonFoliage |
| Quixel / MSPresets leftovers | **2/2** on Toon Universal |
| Enchanted Vehicles (KitBash) | Stock assets are **masters** `M_KB3D_ECV_*` (**72**). Created Melodia MI wrappers at `/Game/Melodia/Imported/EnchantedVehicles/MI_KB3D_ECV_*` on Toon Universal with basecolor / normal / rough / metal / height + light Cymatic params. Disk confirmed **73** MI `.uasset` after owner save. |
| Brushify Floating Islands | **98** MI reparented onto Toon / ToonFoliage · **13** skipped (sky / cloud / water / FX) · **0** fail. Disk `Content/Brushify - Floating Islands/...` · UE mount `/Game/Brushify/...`. Prior disk census **111 MI / 19 M** (98 + 13 = 111 MI accounted). |

Megascans / Brushify / ECV Content trees are typically **local-only** (not on git `main`). Counts above are fromage disk / live editor, not this PR's tree.

---

## Owner actions

- **Ctrl+S** for remaining dirty packages (Megascans / Quixel parent edits **and** Brushify).
- Never use Monolith `save_packages` / `recompile_material`.

## Still pending

- **ECV mesh material slot retarget:** Monolith mesh APIs only expose `set_actor_material` / level swap — **no asset-slot setter**. Meshes still reference stock `M_KB3D_ECV_*`; Melodia wrappers are ready for manual or future-tool retarget.
- **Owner Ctrl+S** for Brushify dirty packages (and any leftover Megascans / Quixel).
- **SurrealFabric / flipbook Ctrl+S** if still dirty from earlier lane (`MI_SurrealFabric_CelestialSilk` / `CymaticPulse` / `BrassPatina`, `MF_FlipbookScrub` — see [`PACKAGE_A_MATERIALS_ORG_2026-09-17.md`](PACKAGE_A_MATERIALS_ORG_2026-09-17.md)).

## Hard rules honored

- No Monolith `save_packages` / `recompile_material` (owner Ctrl+S only)
- Melodia naming — no GrokBot prefixes
- Abandoned Custom_MS as pipeline target after owner correction

---

## Related

| Doc | Role |
|-----|------|
| [`LABEL_MAP_2026-09-09.md`](../Materials/LABEL_MAP_2026-09-09.md) | SHIP / LEGACY / QUARANTINE index |
| [`MATERIAL_PIPELINE.md`](../Pipeline/MATERIAL_PIPELINE.md) | Universal Toon spine |
| [`MATERIALS_CONVERGENCE_GAP_HUNT_2026-09-17.md`](MATERIALS_CONVERGENCE_GAP_HUNT_2026-09-17.md) | Inventory (Custom_MS target **superseded**) |
| [`PACKAGE_A_MATERIALS_ORG_2026-09-17.md`](PACKAGE_A_MATERIALS_ORG_2026-09-17.md) | Flipbook / SurrealFabric org + Ctrl+S list |
| [`SESSION_CLOSEOUT_2026-09-17.md`](SESSION_CLOSEOUT_2026-09-17.md) | Same-day session rollup |

**Saved/ mirror (fromage, local-only):** owner may copy this path → `Saved\Audit\TOON_RECONVERT_CLOSEOUT_2026-09-17.md`.

---

**End of TOON reconvert closeout.**
