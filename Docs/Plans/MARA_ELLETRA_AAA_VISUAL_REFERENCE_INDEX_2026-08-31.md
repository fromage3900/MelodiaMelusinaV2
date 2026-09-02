# Mara / Elletra / Melusina — AAA Visual Reference Index

**Date:** 2026-08-31  
**Purpose:** pin the image hierarchy used by the Houdini hero-asset production plan so procedural iteration does not drift away from the actual character and current game.

## Primary attached board

`Docs/Plans/Images/mara_elletra_aaa_asset_reference_board_16x9_2026-08-31.svg`

This SVG embeds lightweight copies of the current chat-provided visual references so the production plan has a Git-tracked image companion rather than relying on chat history alone.

## Reference hierarchy

### R1 — Electra + Ebenezer concept language
Use for:
- surveyor/cartographer identity;
- relationship between instrument and companion;
- dark layered garment silhouette;
- brass/ornament density;
- field-tool rather than conventional weapon language.

Do not treat every generated label or prop on the sheet as canonical. Preserve the narrative/art-direction signal.

### R2 — user-authored art style
Use for:
- facial proportion;
- eye construction;
- line economy;
- hair massing;
- stylized expression;
- cel/anime read.

**Highest character-identity authority.** Procedural or generated character references do not override this.

### R3 — current runtime close shot
Use for:
- skin/hair/material relationship already working in UE;
- current costume scale;
- stylized material response under game lighting;
- actual game-camera read.

### R4 — current runtime silhouette/environment shot
Use for:
- body-to-world scale;
- costume readability at distance;
- current sea/sky palette;
- how oversized musical geometry must sit beside the character without swallowing her silhouette.

### R5 — current Blender proportions
Use for:
- implementation scale;
- hand size;
- shoulder/hip width;
- boot and skirt proportions;
- prop grip and holster tests.

### R6 — generated instrument exploration
Use for:
- silhouette breadth;
- ring/astrolabe/harp/drum/fan construction ideas;
- modular HDA family exploration;
- exploded-part and mechanism thinking.

**Not character identity authority.** The generated sheet is an ideation source for hero props only.

## Art-direction rule

When references disagree:

```text
user-authored art
> current production character/runtime asset
> established concept direction
> generated prop exploration
> external technical reference
```

This rule should be used at every review gate in `MARA_ELLETRA_HOUDINI_AAA_HERO_ASSET_PRODUCTION_BLUEPRINT_2026-08-31.md`.

## Shot package required for each hero prop review

1. orthographic prop-only silhouette;
2. prop in Mara/Elletra's hand using current production proportions;
3. gameplay camera at normal combat/exploration distance;
4. inventory/dialogue close shot;
5. Perfect resonance state;
6. Miss/disrupted resonance state;
7. side-by-side against this reference board.

## Why this is tracked

The Houdini system is supposed to increase iteration speed and family coherence. It is not allowed to gradually replace authored character design with whatever shape the procedural system produces most easily.
