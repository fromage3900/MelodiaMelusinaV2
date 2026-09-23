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
| `MI_SALON_IMPOSSIBLE` | 5 resolved | Hero interior: Belvedere loggia + Penrose stair + **Belvedere ladder** + Circle-Limit window + chapel walls |
| `MI_COUR_D_HONNEUR` | 5 resolved | Courtyard: Haussmann bay + slab + Mobius rail + relief panels + **Fountain Loop** |
| `MI_MAISON_NUIT` | 5 resolved | Night pass: duality tiling + gold tribar + max-density window + lit channel + **Day-Night Facade** |

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

## Track A, builder 1: `GN_PARIS_EscherLadder` (shipped 2026-09-20)

The Belvedere ladder, extracted from `MEL_escher_belvedere` (where it existed
only as an inseparable part of the loggia) into a reusable Parisian device:
stone flight + mansard landing + wrought-iron handrail.

**Why not a "Parisian Penrose stair".** That was the original plan for builder
1, and it was dropped on evidence: `MEL_escher_penrose_stairs` already ships
Runs / Run Length / Steps per Run / Step Rise / Railings / Second Loop / Loop
Offset / Wobble / Seed. A Parisian twin would have been a *parallel
implementation of identical geometry* — the defect class this repo forbids.
The ladder is a different device with a different defect: one **open** flight
whose **top join** is wrong, versus N runs closed into a loop.

**The impossibility is a parameter.** `Join Error` is the vertical distance by
which the ladder fails to meet the landing (the landing stays where the
building says it should):

| Join Error | Read |
|---|---|
| `0.0` | an honest working ladder — the top rung meets the landing |
| `+` | it overshoots the landing surface |
| `-` | it falls short (the Piranesi read) |

`Floating Steps` gives the stringer its *own* length while the rungs keep
going, so the top N treads are unsupported and hang — done with maths on the
existing sockets, not a second geometry chain.

**Verification** (`deploy/_melodia_health_paris_ladder.py`, headless Blender):
builds clean, `link_failures()` empty, all 13 params present, evaluates to
152 verts / 110 polys, and Join Error changes *no* vertex count (it slides the
ladder rather than rebuilding it).

Two defects this caught that a green build would have shipped:

1. **Degenerate handrails.** The rail profile was a *Mesh* Circle. It links
   without complaint, and Curve to Mesh then emits a 2-vertex "rail" with no
   tube. The link recorder could not see this — the link really is made; only
   the geometry is empty. It surfaced as a **vertex-count delta** (railing cost
   4 verts instead of 32) and is fixed by taking a *Curve* circle profile, the
   `aesthetic_fx.py` house pattern. The health script now asserts the delta.
2. **A lying check.** The first version read param names from the group-input
   node's outputs and reported all 13 missing while `set_param()` was setting
   them fine. Params live on the tree interface — read it there.

**Not yet wired:** the one-line `from . import paris_escher_ladder` in
`melodia_gn/__init__.py`. That file is being edited by a concurrent lane, so the
module self-registers on import and the wiring is left to that lane rather than
risking a lost line in someone else's buffer.

## Track A, builders 2-3: FountainLoop + DayNightFacade (shipped 2026-09-22)

Both reserved slots are now real builders, each with 3-4 presets and its own
headless health script. Build record + evidence:
`Saved/Audit/PARIS_TRACKA_BUILDERS_2_3_2026-09-22.md`.

**`GN_PARIS_FountainLoop`** — the courtyard fountain, carrying the Escher device
as a dial: `Loop Error` is the vertical distance by which the self-feeding
channel's mouth misses its own spout (0.0 = meets; + = overshoots; - = never
arrives), and `Feed Rise` is the channel's own arch height. 23 params (flutes,
scallop bosses, bead rim, tiers, crown spikes, ripples, streams, droplets).
Health: `deploy/_melodia_health_paris_fountain_loop.py` — problems=0 PASS;
tier slots delete cleanly, Self Feed removes the channel, Loop Error slides it
(no rebuild).

**`GN_PARIS_DayNightFacade`** — the day/night duality as a slider: `Night Mix`
0→1 lights the windows from the TOP FLOOR DOWN, dark panes recessed vs lit
panes popped proud with brass trim; the roofline carries two interlocking bird
flocks (`Bird Lock`). 31 params (shutters swing a full 180°, balcony bands,
dentils, seeded geranium boxes, portal + oculus). Health:
`deploy/_melodia_health_paris_daynight_facade.py` — problems=0 PASS; Night Mix
extremes safe, every toggle removes geometry, Shutter Open swings without
rebuilding.

Two defects the harnesses caught that a green build would have shipped: a
`NEGATE` math op that silently defaulted to ADD (flower boxes above the
windows), and the water disc buried inside the solid drum. Details in the
build record.

The ladder's `__init__.py` wiring (left pending on 2026-09-20) is now closed;
registry 593 → 596, gate 6/6, census clean.

## Next

1. Remaining `GN_PARIS_*` Track A builders — MobiusBalcony, HyperbolicRose
   (Mansard, PenroseArch and MetamorphosisFrieze shipped 2026-09-23, along
   with the BRUTALIST pair OfficeBlock + CubicleFarm; see
   `CLOSEOUT_PLAN_2026-09-23.md` and
   `Saved/Audit/BRUTALIST_AND_STAGE_2026-09-23.md`).
   Each lands with 2-3 presets and its own health script assertions.
2. Brand-pack apply operator + hub brand row (needs a Blender session to
   validate end to end; not shipped blind).
3. Preset-gap pass for the remaining hero/sku builders so the pack surface —
   not the raw registry — is the browsable product.
