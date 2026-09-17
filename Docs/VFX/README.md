# Melodia VFX / Niagara docs

Canonical home for Melodia Niagara and VFX material documentation. Dated
audit files keep the evidence date in the filename; status still lives in
`CURRENT_STATE.md`.

## 2026-09-17 — project-wide inventory + Fix A

| File | What it is |
|---|---|
| [`VFX_NIAGARA_FULL_INVENTORY_2026-09-17.md`](VFX_NIAGARA_FULL_INVENTORY_2026-09-17.md) | Materials → instances → Niagara systems, with counts and presence flags |
| [`VFX_NIAGARA_GRAPH_2026-09-17.md`](VFX_NIAGARA_GRAPH_2026-09-17.md) | Mermaid graph of the same tree, including orphans |
| [`VFX_NIAGARA_INVENTORY_2026-09-17.csv`](VFX_NIAGARA_INVENTORY_2026-09-17.csv) | Machine table: `kind,path,parent,ns_refs,fix_a_status,notes` |
| [`VFX_FIXA_RISKS_2026-09-17.md`](VFX_FIXA_RISKS_2026-09-17.md) | Flipbook double-scrub (Fix A) risks first |

Companion receipts this inventory reads, it does not replace:

- [`MELODIA_NIAGARA_ECOSYSTEM_SPEC_2026-09-14.md`](MELODIA_NIAGARA_ECOSYSTEM_SPEC_2026-09-14.md)
- [`CHORAL_SHEEP_VFX_STARRYNIGHT_WORK_ORDER_2026-09-14.md`](CHORAL_SHEEP_VFX_STARRYNIGHT_WORK_ORDER_2026-09-14.md)
- [`../VFX_ASSET_MANIFEST.md`](../VFX_ASSET_MANIFEST.md) (2026-08-15 unification snapshot)
- [`../NIAGARA_ECOSYSTEM_2026-08-09.md`](../NIAGARA_ECOSYSTEM_2026-08-09.md)

A follow-up live Monolith pass should merge pin-level SubUV / FlipFPS results into
the CSV `fix_a_status` column. This checkout cannot: Niagara `.uasset` bodies are
either gitignored or LFS pointers.
