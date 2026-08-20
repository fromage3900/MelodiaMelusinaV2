# Wardrobe content-contract gaps — authored drafts vs the C++ model (2026-08-14)

> **CORRECTED 2026-08-14, later same day. Read this before the rest.**
>
> This report called the 40 cosmetic drafts *authored content* and argued that because they are
> "40 assets deep and internally consistent", **the content is more likely right** than the C++
> enum. That reasoning is wrong.
>
> **The drafts are LLM output.** `deploy/ollama_wardrobe_catalog_daemon.py` generates them with
> `qwen2.5-coder:7b` at `temperature 1.0`, `CAP = 40`, sampling from hardcoded `SLOTS` / `RARITY` /
> `PACKS` / `ELEMENTS` lists. Their internal consistency is a script picking from lists — not forty
> considered design decisions — so it confers **no authority** over the C++ model.
>
> Two consequences:
>
> 1. **The rarity recommendation in §2 does not hold.** `Refined` and `Couture` appear because they
>    are in the daemon's `RARITY` list, which is a plausible-sounding guess. Whether the shipping
>    ladder should be couture-flavoured is still a real question — but it is an **open design
>    question**, not something the content has already settled.
> 2. **`element_mood` was never a new vocabulary.** The daemon's own docstring names its anchor:
>    *"Schema anchors: EMelodiaSpellElement palette moods."* `EMelodiaSpellElement` already exists
>    in `MelodiaCore/MelodiaSpellTypes.h` — seven harmonic elements used by skills, enemies and
>    equippable keys. I mistook a copy for a source. Corrected in `488b74f6`:
>    `FMelodiaStyleScore` now carries `EMelodiaSpellElement` directly, and the `StyleAxisIds` array
>    and its validator were deleted as a redundant second copy.
>
> **Also resolved since:** the "currency gap" was not one. Owner confirms **one Melody Token
> wallet**; `heart`/`swirl` are token art variants resolving to Forte/Arcane element shards, which
> the wallet already implements. See §4 — that section is a retraction.
>
> What still stands: the **slot** mapping gap (`dress` → `Body`) and `content_pack_id` being
> unmodelled. Those are real regardless of who wrote the drafts — but treat every count below as "what a generator produced",
> not "what a designer decided".

**40 cosmetic drafts exist** (generator-produced — see the banner above) at `Imports/Data/Cosmetics/Cos_*.json`, schema
`MelodiaCosmetic-draft-v1`. They are richer than the C++ model that is supposed to import
them, and three fields **cannot round-trip today**. Importing as-is loses authored data
silently.

Found while building a worked authoring example for the new wardrobe layers. The example
is unnecessary — real content already exists and is the better test.

---

## 1. The generated vocabulary (what a daemon emitted — NOT ground truth)

| Field | Values found across 40 drafts |
|---|---|
| `element_mood` | **Tide** (9), **Radiant** (7), **Arcane** (6), **Umbral** (6), **Gale** (5), **Stone** (4), **Forte** (3) |
| `slot` | dress (12), trail (7), gloves (6), shawl (6), hat (5), hair_charm (4) |
| `rarity` | Refined (14), Common (11), **Couture** (9), Grandmaster (6) |
| `content_pack_id` | Core (20), Pack_MoonlitSonata (13), Pack_GildedOverture (7) |
| `token_cost` | `heart` (40) + `swirl` (40) — **element shards, not currencies**: Forte + Arcane. See §4 |

Also present: `palette` (hex triples), `flavor`, `material_notes`, `display_name`.

**`element_mood` is a COPY of `EMelodiaSpellElement`**, not a new vocabulary. Those seven names
are the daemon's hardcoded `ELEMENTS` list, and its docstring says so outright: *"Schema anchors:
EMelodiaSpellElement palette moods."* The real vocabulary lives in
`MelodiaCore/MelodiaSpellTypes.h` and is used by skills, enemies and equippable keys.

`FMelodiaStyleScore` now carries `EMelodiaSpellElement` directly (`488b74f6`), so there is no
`StyleAxisIds` array to seed — the enum is the declaration.

---

## 2. Gap A — 23 of 40 drafts have a rarity C++ cannot represent

```
EMelodiaCosmeticRarity { Common, Uncommon, Rare, Epic, Legendary, Grandmaster }
drafts use               Common, Refined, Couture, Grandmaster
```

**`Refined` (14) and `Couture` (9) do not exist in the enum.** Only `Common` and
`Grandmaster` overlap. `Uncommon`, `Rare`, `Epic`, `Legendary` are used by **no draft at all**.

So the enum models a generic MMO rarity ladder while the drafts use a couture-flavoured one.
On import, 23 of 40 drafts silently take the default (`Common`) — a wrong value that looks
valid, which is the silent-no-op class again. **That import hazard is real regardless of
provenance** and is the part of this section that still stands.

**Open design question, NOT settled by the drafts:** should the shipping ladder be
`Common → Refined → Couture → Grandmaster`? `Refined` and `Couture` appear only because they
sit in the daemon's hardcoded `RARITY` list — a plausible-sounding guess, not a decision. The
enum's four unused values (`Uncommon`/`Rare`/`Epic`/`Legendary`) are equally unexamined. Neither
side has authority here; the owner picks.

Note the enum is **not** save-serialized by value the way `EMelodiaWardrobeSlot` is
(`EquippedCosmeticIds` keys on slot, not rarity), so renumbering rarity is comparatively safe
— but confirm before changing it.

## 3. Gap B — slot names do not map

Drafts say `dress`; the enum's body slot is `Body`. The other five (`hat`, `gloves`,
`shawl`, `trail`, `hair_charm`) map cleanly to `Hat`/`Gloves`/`Shawl`/`Trail`/`HairCharm`
modulo case and underscore.

No draft uses the V2 split-garment slots (`Shirt`, `Skirt`, `Boots`, `Accessories`), so
those are unexercised by current content.

**This one is cheap:** a documented mapping table in the importer. It just must exist and be
explicit — `dress → Body` is not inferable from the string.

**Do not renumber `EMelodiaWardrobeSlot` to fix this.** Its comment is unambiguous: *"Append
only: the preceding values are serialized into existing save records and must never be
renumbered."*

## 4. ~~Gap C — two authored currencies~~ — RESOLVED, and the premise was wrong

**Owner, 2026-08-14: there is one wallet, the Melody Token wallet.** `heart` and `swirl` were
never currencies. They are **token art variants that resolve to element shards** inside that one
wallet, per the canonical model at `Content/Python/gmm/game/tokens.py`:

| Draft key | Display | Element | Value | Rarity |
|---|---|---|---|---|
| `heart` | Forte Shard | **Forte** | 10 | common |
| `star` | Radiant Shard | **Radiant** | 12 | uncommon |
| `swirl` | Arcane Shard | **Arcane** | 15 | rare |
| `water` | Tide Shard | **Tide** | 12 | common |

So `{"heart": 5, "swirl": 2}` means **5 Forte shards + 2 Arcane shards** — one wallet,
element-keyed, exactly as designed.

`UMelodiaTokenWalletSubsystem` already implements this: `TMap<FName,int32> Shards` keyed by
element, with `GetShards` / `TryGrantShards(Element, Amount, GrantId)` / `TrySpendShards`, plus
mana and `GoldenTokens`. Its header calls itself *"the single Unreal-side authority for the token
stat economy"* and mirrors the GMM model.

**I called this "the most consequential gap — economy design, not a mapping fix". That was wrong
on both counts.** It is a naming mismatch between draft art-variant keys and element names, and it
is now validated automatically: `Tools/wardrobe_draft_lint.py` reads the mapping out of
`gmm/game/tokens.py` (not a hardcoded copy) and reports **0 token_cost findings across all 40
drafts**. Unmodelled notes fell 80 → 40.

**One real consequence remains:** `PurchaseCosmetic(FName, int32 GoldenPrice)` takes a flat Golden
price and cannot express a shard cost at all. The wallet supports shards; the wardrobe's purchase
path does not use them. That is a small C++ change, not an economy decision.

**Drift risk worth carrying:** the wallet header states there is **no runtime GMM↔Unreal channel**
— it is a parallel implementation of the same contract, kept honest only by matching test
expectations (`Content/Python/gmm/tests/test_tokens.py`). Two implementations of one economy with
no automated cross-check.

## 5. Gap D — `content_pack_id` is not modelled

`Core` / `Pack_MoonlitSonata` / `Pack_GildedOverture` — a content-pack grouping with no C++
representation. Directly relevant to the deferred outfit-set/collection layer: **the packs
are the natural set boundary**, already authored, and a collection album could be built on
them rather than on a new invented grouping.

## 6. What this changes about the new layers

`FMelodiaStyleScore` was restructured because of what this investigation turned up: its axis
is now `EMelodiaSpellElement` rather than an FName, and `StyleAxisIds` +
`FindUndeclaredStyleAxes()` were deleted as a redundant second copy of a fixed enum
(`488b74f6`). `FMelodiaResonantForm` is unaffected.

`SlotStyleWeights` still wants `Body` weighted highest — dresses are the silhouette — but note
the 12-of-40 figure is a generator's sampling ratio, not evidence about the shipping catalog.

No draft names a Resonant Form, so all 40 are decorative. That remains the correct default;
ability outfits should be a deliberate small subset.

## 7. Recommended order

1. **Settle rarity** (Gap A) — blocks a faithful import of 23 assets.
2. **Write the slot mapping table** (Gap B) — mechanical, cheap.
3. **Seed `StyleAxisIds` from `element_mood`** — no decision needed, the vocabulary exists.
4. **Defer currency** (Gap C) until the economy is decided; preserve `token_cost` as inert
   data meanwhile rather than flattening it lossily.
5. Revisit `content_pack_id` when the collection layer is built.

Importer entry point to update: `Content/Python/import_melusina_wardrobe_contract.py`.
