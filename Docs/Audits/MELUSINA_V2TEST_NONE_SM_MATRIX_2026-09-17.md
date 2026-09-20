# Melusina V2Test ΓÇö None SM decision matrix ΓÇö 2026-09-17

**Package:** A ΓÇö Materials org  
**Stamp:** 2026-09-17 ~18:25 EDT (America/Toronto)  
**Count:** ~**33** Melusina V2Test static-mesh material slots still **None** (clean-env 2026-09-09; parked ΓÇö not stubbed)  
**Source inventory (local):** `Saved/Audit/ENGINE_DEFAULT_SM_SLOTS_2026-09-09.csv` (New Bot: 2515 SM scanned; 187 None; V2Test subset parked)  
**Hard rule:** Study bot does **not** decide alone. This is an **OWNER CALL** matrix with a lean recommendation.

## Why these were skipped

Clean-env stub pass assigned `MI_Melodia_Stub_Toon` / `Stub_Fabric` to WorldGrid / None **non-hero** slots. Melusina **V2Test** character meshes were **explicitly skipped** so they would not permanently wear lookdev stubs ΓÇö they need real wardrobe / character MIs (or intentional quarantine).

## Options

| Option | What | Pros | Cons |
|--------|------|------|------|
| **A ΓÇö Prep stub (temporary)** | Assign `MI_Melodia_Stub_Toon` or `Stub_Fabric` now; track list for later wardrobe replace | Clean viewport / no pink-black None; reversible | Easy to forget; stubs can ship by accident if not labeled |
| **B ΓÇö Quarantine / park** | Leave None **or** move meshes under a `_Quarantine` / V2Test-only folder; document do-not-ship | Forces real MI work later; no false ΓÇ£doneΓÇ¥ | Viewport noise; PIE may show engine default / None |
| **C ΓÇö Real character MIs now** | Build Melusina wardrobe MIs (Universal / SurrealFabric / body MIs) and assign | Correct end state | Out of Package A; needs art + owner authoring time |
| **D ΓÇö Hybrid** | Quarantine non-hero V2Test props; stub only blocking hero slots; real MIs for body/cloth | Balanced | Needs owner triage pass on the 33-row CSV |

## Recommendation (lean ΓÇö not a decision)

**Lean D / B-primary:** Keep Melusina V2Test **None slots parked (quarantine mindset)** until wardrobe MIs exist. Use **prep stub (A)** only on slots that **block a named hero shot this week**, and tag those rows `TEMP_STUB` in the CSV with an owner follow-up.

Do **not** mass-stub all 33 as if complete. Do **not** treat stubs as character SHIP.

## OWNER CALL (fill in)

| Field | Owner |
|-------|-------|
| Chosen option | **A / B / C / D:** ________ |
| If A or D: which slots may stub | ________ |
| Target wardrobe MI family | Universal / SurrealFabric / other: ________ |
| Deadline / next session | ________ |
| Sign-off | Fromage ________ date ________ |

## Prep checklist (after owner picks)

1. Re-open `ENGINE_DEFAULT_SM_SLOTS_2026-09-09.csv` (or fresh Monolith mesh_query) filtered to Melusina V2Test / None.
2. Apply chosen option **in editor**; agents must not `save_packages` ΓÇö owner **Ctrl+S**.
3. Update LABEL_MAP OPEN row + this matrix with final counts.
4. If stubbing: list every soft path stubbed in a new receipt; schedule replace.

## Soft-path stubs already available (if Option A)

- `/Game/Melodia/Materials/Lookdev/MI_Melodia_Stub_Toon`
- `/Game/Melodia/Materials/Lookdev/MI_Melodia_Stub_Fabric`

## Related

- `Docs/Materials/RECEIPT_MATERIALS_CLEAN_ENV_2026-09-09.md` (Still open: Melusina V2Test)
- `Docs/Materials/LABEL_MAP_2026-09-09.md` OPEN row
- Closeout handoff: decision later ΓåÆ this matrix
