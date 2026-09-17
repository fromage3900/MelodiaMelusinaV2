# Melodia VFX / Niagara docs

Canonical home for Melodia Niagara and VFX material documentation. Dated
audit files keep the evidence date in the filename; status still lives in
`CURRENT_STATE.md`.

## 2026-09-17 — project-wide inventory + Fix A (LIVE_MONOLITH)

Live editor pin read merged on the same date as the documentary first pass.
Authority for SubUV / SubImageSize is the DETAIL CSV, not the coarse 65-row
inventory (that pass scored LeafPile CLEAN and missed `SubImageSize` 2×2).

| File | What it is |
|---|---|
| [`VFX_NIAGARA_FULL_INVENTORY_2026-09-17.md`](VFX_NIAGARA_FULL_INVENTORY_2026-09-17.md) | Materials → instances → Niagara systems, with live counts |
| [`VFX_NIAGARA_GRAPH_2026-09-17.md`](VFX_NIAGARA_GRAPH_2026-09-17.md) | Mermaid graph of live NS→material edges |
| [`VFX_NIAGARA_INVENTORY_2026-09-17.csv`](VFX_NIAGARA_INVENTORY_2026-09-17.csv) | Canonical machine table (65 ship NS + bound MI/masters) |
| [`VFX_FIXA_DETAIL_2026-09-17.csv`](VFX_FIXA_DETAIL_2026-09-17.csv) | **Authoritative** Fix A pin read (emitter / SubUV live / SubImage) |
| [`VFX_NIAGARA_SHIP_NS_LIVE_2026-09-17.csv`](VFX_NIAGARA_SHIP_NS_LIVE_2026-09-17.csv) | Coarse 65-NS inventory (0 RISK; LeafPile scored CLEAN) |
| [`VFX_NS_MATERIAL_EDGES_2026-09-17.csv`](VFX_NS_MATERIAL_EDGES_2026-09-17.csv) | Live NS→material renderer edges (106). LeafPile `subuv_live` disagrees with DETAIL — DETAIL wins |
| [`VFX_FIXA_RISKS_2026-09-17.md`](VFX_FIXA_RISKS_2026-09-17.md) | Flipbook double-scrub: **1 RISK_DOUBLE** (`NS_Melodia_LeafPileLoop`) |

Companion receipts this inventory reads, it does not replace:

- [`MELODIA_NIAGARA_ECOSYSTEM_SPEC_2026-09-14.md`](MELODIA_NIAGARA_ECOSYSTEM_SPEC_2026-09-14.md)
- [`CHORAL_SHEEP_VFX_STARRYNIGHT_WORK_ORDER_2026-09-14.md`](CHORAL_SHEEP_VFX_STARRYNIGHT_WORK_ORDER_2026-09-14.md)
- [`../VFX_ASSET_MANIFEST.md`](../VFX_ASSET_MANIFEST.md) (2026-08-15 unification snapshot)
- [`../NIAGARA_ECOSYSTEM_2026-08-09.md`](../NIAGARA_ECOSYSTEM_2026-08-09.md)

**Live ship headline:** 65 NS under `/Game/Melodia` + `/Game/EnvSandbox`
(Candidates / `_Archive` excluded). **1 RISK_DOUBLE** (`NS_Melodia_LeafPileLoop`).
**4 CLEAN_FIXA_SUBUV_OFF** (BeatBurst, HybridSparkles, PetalCascade, MotionTrails).
LeafPile was **not** fixed in-engine — document RISK only.
