# NikkiChain Variant Convergence — Decision Memo (2026-09-06)

Census (offline binary-ref scan of ALL 1,808 material assets + 50 .umap +
36 WBP/NS/DA; string-scan confirms presence, never absence — rule 20):

| Variant | Consumers | Verdict |
|---|---|---|
| M_Master_Toon_Universal_NikkiChain | 9 (MI_NikkiIntegrated_Bloom/Dream/Moonlit + 6) | **OWNER — keep** |
| M_Master_Toon_Universal_NikkiChainRepair | 0 | delete candidate |
| M_Master_Toon_Universal_NikkiChainRepairV2 | 0 | delete candidate |
| M_Master_Toon_Universal_NikkiChainIntegratedV1 | 0 | delete candidate |

Zero maps, widgets, Niagara systems, or DAs reference the three orphan variants.

⚠ Before delete (editor session, Batch L): reflection-confirm via Monolith
`get_cdo_properties` + reference-graph (soft refs invisible to byte-scan; AGENTS rule
11/20 family). Then delete_asset the three, rescan, and verify_baseline re-freeze.
If any orphan's graph contains node work the base chain lacks (the 09-05 "Repair"
commits suggest iteration that may not have been folded back), MERGE those nodes up
into the base first — delete only after the knowledge is preserved. This is the
exact defect class AGENTS calls four parallel implementations converging to one.

Note: verify_baseline's frozen catalog excludes all four (not in
material_catalog.json) — no baseline churn from deleting them, but re-run anyway.
