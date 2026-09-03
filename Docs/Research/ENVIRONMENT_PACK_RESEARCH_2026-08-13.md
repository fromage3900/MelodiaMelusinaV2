# Environment Pack Research — Findings & Handoff (2026-08-13)

**Goal:** Infinity-Nikki-themed environment asset packs for UE 5.8, to close loose
ends in the musical turn-based JRPG (Melodia). This doc records what is verified,
what is delegated to a research model, and the integration plan.

## Verified now (links live, 2026-08-13 — HEAD 200)

| Pack | Source | License | Use |
|---|---|---|---|
| Kenney Mini Forest | kenney.nl/assets/mini-forest | CC0 | Dreamstate/Morning traversal foliage |
| Kenney Modular Cave Kit | kenney.nl/assets/modular-cave-kit | CC0 | KaleidoNave grotto/baroque-cave blocking |
| Kenney Skyboxes | kenney.nl/assets/skyboxes | CC0 | Dreamy skies (UDS already present — optional) |
| Quaternius (all packs) | quaternius.com | CC0 | Pastel-able base geometry; Toon Profiles do the Nikki lift (same publisher as staged animation library — provenance pattern exists) |
| Poly Haven HDRIs | polyhaven.com | CC0 | Look-dev lighting (textures only) |

## Delegated to research model (SuperGrok / phone — search pages are bot-blocked here)

Paste-ready prompt:

> Research environment asset packs for a UE 5.8 stylized JRPG with an Infinity
> Nikki / Genshin-style soft-pastel fantasy look (musical turn-based game; levels:
> kaleidoscope nave arena, dream-traversal forest, morning sanctuary, sakura path,
> baroque grotto, cosmic cathedral). For EACH pack found, report: name, link,
> price (USD), license, format (UE project / FBX / glTF / Blender), polygon style
> (stylized/pastel vs photoreal), and best-fit level.
>
> Search targets:
> 1. Fab.com — "stylized fantasy environment", "pastel world", "stylized village",
>    "Japanese garden", "music box props", "whimsical fantasy props", "toon environment".
> 2. itch.io (free tag, stylized + environment) — free packs with permissive licenses.
> 3. Gumroad — Stylized Station (storybook UE packs), indie stylized-nature kits.
> 4. Infinity Nikki / Genshin-style fan kits specifically (search both names).
> 5. Music-theme props: harps, music boxes, grand pianos, floating notes — the
>    musical-JRPG loose end.
>
> Deliverable: a ranked table (best-fit first) of 10–15 packs, each with link +
> price + license + format + fit. Flag which are free.

## Integration plan (once packs land)

1. **Manifest**: `Imports/Environment/pack_manifest.json` — same shape as
   `Imports/NPCs/source_manifest.json` (link_verified, license, format, staging_path).
2. **Stage**: `Imports/Environment/<Pack>/`; Fab-native UE projects install directly;
   FBX/glTF go through the Blender 5.2 bridge or UE import.
3. **The Nikki pass (free-AI)**: swap pack materials onto the Toon Profile /
   `M_Master_Toon_Universal` spine (`MF_NikkiDreamGrade` already exists); free vision
   lane reviews pack renders against the design system; deep lane maps each pack to
   a level with a fit verdict.
4. **Deliver**: per-pack verdict doc + downloads checklist (pattern:
   `Imports/NPCs/downloads_todo.md`).

## Open questions for owner

- Budget: free/CC0 only, or paid Fab packs (Stylized Station tier ~$30–60) allowed?
- Priority levels: arena dressing vs traversal foliage vs sakura path vs music props?
