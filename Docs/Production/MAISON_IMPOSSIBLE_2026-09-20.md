# Maison Impossible — brand record (2026-09-20)

`Maison Impossible` is the curated front door for the Parisian × Escher work:
**Haussmann geometry, impossible logic**. It is a *reference layer*, not a new
preset system — `melodia_gn/presets.py` remains the single source of truth for
every param value.

## Why a brand layer at all

The registry holds ~600 GN builders. That is the library's strength and its
usability problem. A brand pack lets a person build a room from three curated
choices instead of six hundred, while every underlying builder stays exactly
where it is. This is the trim mechanism: **hide behind taste, never delete
behind it.**

## Data rule (do not break this)

A pack stores **no param values** — only `(builder_id, preset_name)` references.

```python
"MI_SALON_IMPOSSIBLE": {
    "label": "Salon Impossible",
    "refs": [{"builder": "MEL_escher_belvedere", "preset": "CANONICAL_LOGGIA"}, ...],
}
```

Consequences, all intentional:

- A pack **cannot drift** from the presets it names; change a preset and every
  pack that references it follows.
- Refs that point at builders not yet built are authored `"pending": True` and
  are reported, never silently dropped.
- A ref that stops resolving lands in `unresolved` on resolve (and fails
  `_melodia_preset_audit.py`), instead of raising at click time.

## The reference set (locked)

| Architect / source | What is pulled | Where it lands |
|---|---|---|
| **Haussmann system** (Second Empire immeuble) | Lutetian limestone, continuous cornice line, bay rhythm, slate mansard, iron rail | `GN_PARIS_WallDetail`, `GN_PARIS_SlabTrim` — the base palette every impossibility happens inside |
| **Charles Garnier** (Opéra Garnier) | Grand stair as theatre, gold + mirror + red, overloaded ornament | `MI_SALON_IMPOSSIBLE`, `MEL_escher_penrose_stairs` |
| **Hector Guimard** (Métro entrances) | Whiplash wrought iron, organic railings | `MEL_mobius_strip` (`RAILING_RIBBON`) |
| **Viollet-le-Duc / Sainte-Chapelle** | Rayonnant tracery, pointed-arch logic | `MI_GOTHIC_CHAPEL`, `MEL_hyperbolic_window` |
| **Ricardo Bofill** (Les Espaces d'Abraxas) | Surreal classical at housing scale — proof the brand is buildable | `MI_COUR_D_HONNEUR`, `MI_STRIPPED_MODERN` |
| **M.C. Escher** (devices, not buildings) | Belvedere, Ascending and Descending, Waterfall, Relativity, Day and Night, Circle Limit, Metamorphosis | one device per builder, hero trio + math quartet |
| **Piranesi** (*Carceri*) | Mood only for stair work: infinite stone, no exit | `MEL_escher_penrose_stairs` mood |

**Deliberately excluded:** Le Corbusier / high modernism (wrong Paris — a future
counter-brand, not this one) and Gehry-style formal arbitrariness (our
impossibilities must read as *logical paradoxes*, not blobs). Gaudí / Candela
and Nouvel are engineering footnotes for shells and the light-mix slider, not
visual drivers.

## Palette contract

Lutetian limestone cream · zinc/slate mansard blue-grey · wrought-iron
near-black green · gold leaf accent · Garnier red + mirror (interiors) · night
mode: deep blue + warm window light. All three packs must be expressible in
these six swatches — that is what makes them feel like one brand.

## Packs

| Pack | Steps | Intent |
|---|---|---|
| `MI_SALON_IMPOSSIBLE` | 4 resolved | Hero interior: Belvedere loggia + Penrose stair + Circle-Limit window + chapel walls |
| `MI_COUR_D_HONNEUR` | 4 resolved, 1 pending | Courtyard: Haussmann bay + slab + Mobius rail + relief panels; pending `GN_PARIS_FountainLoop` |
| `MI_MAISON_NUIT` | 4 resolved, 1 pending | Night pass: duality tiling + gold tribar + max-density window + lit channel; pending `GN_PARIS_DayNightFacade` |

## API

```python
from surreal_arch.melodia_gn.presets import (
    brands, brand_info, brand_packs, brand_pack_names,
    resolve_brand_pack, export_brand_pack,
)
```

`resolve_brand_pack(brand, pack)` returns `steps` (each with `builder`, `preset`,
`label`, `params`), plus `pending` and `unresolved`. The apply path is
`mel_gn.apply_preset` (`melodia_gn/stack.py`), one call per step — it matches
params onto the tree's INPUT sockets **by name**, which is why `params` from a
step is directly usable.

## Verification

```
python deploy/_melodia_preset_audit.py          # shadowed keys + brand refs
python deploy/surreal_arch/melodia_gn/presets.py  # library + brand inventory
```

`_melodia_preset_audit.py` parses `presets.py` as an AST on purpose: it detects
keys Python has **already silently discarded**, which no runtime dump can ever
find. On 2026-09-20 it found 2 (`MEL_allee_ribbon`, `MEL_column`) — one a
byte-identical copy, one a *different* curated set shadowed for months with no
reader. Both removed; the curation is preserved as notes on the authority.

## Next

1. `GN_PARIS_*` Track A builders (PenroseStair, BelvedereMansard, FountainLoop,
   MobiusBalcony, DayNightFacade, HyperbolicRose, PenroseArch,
   MetamorphosisFrieze) — fill the 2 pending slots, then mark them resolved.
2. Brand-pack apply operator + hub brand row (needs a Blender session to
   validate; not shipped blind).
3. Preset-gap pass for the remaining hero/sku builders so the pack surface — not
   the raw registry — is the browsable product.
