# Cosmetics Data Drop-Zone

Drop authored cosmetic source records here (JSON or CSV) for the catalog-first
V2 wardrobe pipeline. Each record must carry an `id`, `slot`, and `rarity` field
at minimum; the draft linter (`Tools/wardrobe_draft_lint.py`) reads them.

The catalog contract test (`Tools/test_melodia_wardrobe_catalog_contract.py`)
asserts this directory exists. Do not delete it.