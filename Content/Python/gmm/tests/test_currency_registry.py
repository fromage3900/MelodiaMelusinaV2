"""Contract tests for the exported currency registry mirror.

The Unreal DataAsset is canonical (Decision 055), but it is binary and cannot be read here.
specs/economy/melodia_currency_registry.v1.json is its published text form, and these tests
are what stop a bad row reaching Python, the wardrobe lint, CI and the MCP server without a
running editor. They enforce the same invariants UMelodiaCurrencyRegistry::PostLoad warns
about in the editor, so a mistake is caught on whichever side it is made.

Also pins the freshness gate's premise: the mirror must exist at all.

Stdlib unittest only — this lane must run under plain
``python -m unittest discover`` with no third-party deps installed.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

# Content/Python/gmm/tests/<this file> -> project root is four levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_JSON = PROJECT_ROOT / "specs" / "economy" / "melodia_currency_registry.v1.json"
CATALOG_JSON = PROJECT_ROOT / "specs" / "economy" / "melodia_token_catalog.v1.json"

VALID_KINDS = {"Shard", "Premium", "Resource"}
LEGACY_ELEMENTS = {"Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"}


def _load_registry() -> dict:
    assert REGISTRY_JSON.exists(), (
        f"{REGISTRY_JSON} is missing. Re-export it with "
        "Content/Python/export_melodia_currency_registry.py, or restore the asset with "
        "author_melodia_currency_registry.py."
    )
    return json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))


def _load_currencies() -> list[dict]:
    rows = _load_registry().get("currencies")
    assert isinstance(rows, list) and rows, "registry declares no currencies"
    return rows


class TestCurrencyRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = _load_registry()
        self.currencies = self._currencies()

    def _currencies(self) -> list[dict]:
        rows = self.registry.get("currencies")
        self.assertIsInstance(rows, list)
        self.assertTrue(rows, "registry declares no currencies")
        return rows

    def test_schema_and_version(self) -> None:
        self.assertEqual(self.registry["schema"], "melodia_currency_registry.v1")
        self.assertGreaterEqual(self.registry["registry_schema_version"], 1)

    def test_currency_ids_are_unique(self) -> None:
        # A duplicate makes UMelodiaCurrencyRegistry::Find ambiguous: it returns whichever row
        # comes first, so half the game prices against one row and half against the other.
        ids = [row["currency_id"] for row in self.currencies]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        self.assertFalse(duplicates, f"duplicate currency_id(s): {duplicates}")
        self.assertTrue(all(ids), "a row has an empty currency_id and could never be granted or spent")

    def test_seed_currencies_present(self) -> None:
        """The nine currencies the wallet's compatibility shims name directly."""
        ids = {row["currency_id"] for row in self.currencies}
        missing = (LEGACY_ELEMENTS | {"Golden", "Mana"}) - ids
        self.assertFalse(missing, (
            f"missing seed currencies: {sorted(missing)}. The legacy shims (TryGrantShards, "
            "TryGrantGolden, TryAddMana) resolve these by name and would start rejecting."
        ))

    def test_kinds_are_valid(self) -> None:
        for row in self.currencies:
            self.assertIn(row["kind"], VALID_KINDS, f"{row['currency_id']}: bad kind {row['kind']!r}")

    def test_resource_currencies_have_a_positive_cap(self) -> None:
        # A Resource with max_value 0 clamps to zero, so every grant is a silent no-op.
        for row in self.currencies:
            if row["kind"] == "Resource":
                self.assertGreater(row.get("max_value", 0), 0, (
                    f"{row['currency_id']}: Resource with max_value {row.get('max_value')} clamps "
                    "to zero and can never hold a balance"
                ))

    def test_non_resource_currencies_do_not_set_a_cap(self) -> None:
        # max_value is ignored for Shard and Premium at runtime; setting it misleads the reader.
        for row in self.currencies:
            if row["kind"] != "Resource":
                self.assertEqual(row.get("max_value", 0), 0, (
                    f"{row['currency_id']}: {row['kind']} sets max_value "
                    f"{row['max_value']}, which the wallet ignores"
                ))

    def test_defaults_are_within_their_cap(self) -> None:
        for row in self.currencies:
            if row["kind"] == "Resource":
                self.assertLessEqual(row.get("default_value", 0), row["max_value"], (
                    f"{row['currency_id']}: starts above its cap and is clamped down on first load"
                ))

    def test_legacy_element_mapping_is_one_to_one(self) -> None:
        """Each legacy element is claimed by exactly one currency.

        CurrencyIdForElement returns the first match, so two rows claiming Forte would make the
        compatibility shims non-deterministic — and those shims are what the wardrobe calls.
        """
        claimed: dict[str, str] = {}
        for row in self.currencies:
            if not row.get("has_legacy_element"):
                continue
            element = row["legacy_element"]
            self.assertIn(element, LEGACY_ELEMENTS, f"{row['currency_id']}: bad element {element!r}")
            self.assertNotIn(element, claimed,
                f"{element} is claimed by both {claimed.get(element)} and {row['currency_id']}")
            claimed[element] = row["currency_id"]

        self.assertEqual(set(claimed), LEGACY_ELEMENTS, (
            f"unclaimed legacy elements: {sorted(LEGACY_ELEMENTS - set(claimed))}"
        ))

    def test_mana_and_golden_do_not_inflate_total_collected(self) -> None:
        # TotalCollected is a "shards picked up" stat. Premium and regenerating currencies
        # counting toward it would make the HUD number meaningless.
        by_id = {row["currency_id"]: row for row in self.currencies}
        for currency_id in ("Golden", "Mana"):
            self.assertIs(by_id[currency_id]["counts_toward_total_collected"], False)

    def test_golden_is_the_refundable_currency(self) -> None:
        refundable = {row["currency_id"] for row in self.currencies if row.get("refundable")}
        self.assertIn("Golden", refundable, (
            "Golden must stay refundable: the wardrobe's purchase path calls TryRefundGolden "
            "to unwind a failed cosmetic grant."
        ))

    def test_token_catalog_variants_resolve_to_registry_currencies(self) -> None:
        """Every token variant's element must exist as a currency.

        This is the join the whole economy rests on: cosmetics price in VARIANTS (heart, swirl),
        ResolveCost turns those into ELEMENTS, and the wallet spends CURRENCIES. A variant
        pointing at an element with no currency row is a price that can never be paid.
        """
        self.assertTrue(CATALOG_JSON.exists(), f"{CATALOG_JSON} is missing; re-export it")
        catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        registry = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))

        currency_ids = {row["currency_id"] for row in registry["currencies"]}
        for group in ("tokens", "extra_elemental_types"):
            for row in catalog.get(group) or []:
                self.assertIn(row["element"], currency_ids, (
                    f"variant {row['variant_id']!r} resolves to element {row['element']!r}, "
                    "which has no currency row"
                ))

    def test_python_mirror_agrees_with_the_export(self) -> None:
        """gmm.game.tokens must be reading the mirror, not its fallback literals.

        If this fails while the mirror exists, the loader silently fell back — which is exactly
        the drift the inversion was meant to remove.
        """
        from gmm.game.tokens import TOKEN_TYPES, TOKEN_SOURCE

        self.assertEqual(str(CATALOG_JSON), TOKEN_SOURCE, (
            f"tokens.py loaded from {TOKEN_SOURCE!r} instead of the exported mirror"
        ))

        catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
        exported = {row["variant_id"]: row["element"] for row in catalog["tokens"]}
        self.assertEqual({k: v["element"] for k, v in TOKEN_TYPES.items()}, exported)


if __name__ == "__main__":
    unittest.main()
