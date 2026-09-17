# Melodia VFX / Niagara docs

Canonical home for Melodia Niagara and VFX material documentation. Dated
audit files keep the evidence date in the filename; status still lives in
`CURRENT_STATE.md`.

## 2026-09-17 — project-wide inventory + Fix A (LIVE_MONOLITH)

Live editor pin read, then owner-saved LeafPile Fix A. Authority for SubUV /
SubImageSize is the DETAIL CSV (updated after Ctrl+S). LeafPile **SubImageSize
stays 2×2** (atlas variants); only `SubUVAnimation` was disabled.

| File | What it is |
|---|---|
| [`VFX_NIAGARA_FULL_INVENTORY_2026-09-17.md`](VFX_NIAGARA_FULL_INVENTORY_2026-09-17.md) | Materials → instances → Niagara systems, with live counts |
| [`VFX_NIAGARA_GRAPH_2026-09-17.md`](VFX_NIAGARA_GRAPH_2026-09-17.md) | Mermaid graph of live NS→material edges |
| [`VFX_NIAGARA_INVENTORY_2026-09-17.csv`](VFX_NIAGARA_INVENTORY_2026-09-17.csv) | Canonical machine table (65 ship NS + bound MI/masters) |
| [`VFX_FIXA_DETAIL_2026-09-17.csv`](VFX_FIXA_DETAIL_2026-09-17.csv) | **Authoritative** Fix A pin read (emitter / SubUV live / SubImage) |
| [`VFX_NIAGARA_SHIP_NS_LIVE_2026-09-17.csv`](VFX_NIAGARA_SHIP_NS_LIVE_2026-09-17.csv) | Coarse 65-NS inventory |
| [`VFX_NS_MATERIAL_EDGES_2026-09-17.csv`](VFX_NS_MATERIAL_EDGES_2026-09-17.csv) | Live NS→material renderer edges (106) |
| [`VFX_FIXA_RISKS_2026-09-17.md`](VFX_FIXA_RISKS_2026-09-17.md) | Flipbook double-scrub: **0 RISK_DOUBLE** |
| [`VFX_FIXA_RISKS_LIVE_2026-09-17.csv`](VFX_FIXA_RISKS_LIVE_2026-09-17.csv) | Live risks table — **empty** (header only) |
| [`VFX_FIXA_LEAFPILE_2026-09-17.md`](VFX_FIXA_LEAFPILE_2026-09-17.md) | LeafPile Fix A receipt (SubUV off; 2×2 atlas kept) |
| [`VFX_BEATPULSE_BP_WIRE_2026-09-17.md`](VFX_BEATPULSE_BP_WIRE_2026-09-17.md) | BP_ChoralSheep `User.BeatPulse` graph contract (binary not in this PR) |

Companion receipts this inventory reads, it does not replace:

- [`MELODIA_NIAGARA_ECOSYSTEM_SPEC_2026-09-14.md`](MELODIA_NIAGARA_ECOSYSTEM_SPEC_2026-09-14.md)
- [`CHORAL_SHEEP_VFX_STARRYNIGHT_WORK_ORDER_2026-09-14.md`](CHORAL_SHEEP_VFX_STARRYNIGHT_WORK_ORDER_2026-09-14.md)
- [`../VFX_ASSET_MANIFEST.md`](../VFX_ASSET_MANIFEST.md) (2026-08-15 unification snapshot)
- [`../NIAGARA_ECOSYSTEM_2026-08-09.md`](../NIAGARA_ECOSYSTEM_2026-08-09.md)

**Live ship headline:** 65 NS under `/Game/Melodia` + `/Game/EnvSandbox`
(Candidates / `_Archive` excluded). **0 RISK_DOUBLE.** **5 CLEAN_FIXA**
(four Choral Sheep SubUV-off / 1×1, plus LeafPile SubUV-off / **2×2 atlas kept**).
LeafPile Fix A applied live (owner Ctrl+S). BeatPulse BP wire compiled on
`BP_ChoralSheep` (docs-only here).
