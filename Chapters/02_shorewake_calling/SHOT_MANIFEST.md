# Chapter 02 — Shorewake Calling Shot Manifest

**Status:** ACTIVE FALL 2026 ART TARGET
**Primary hero shot:** SHW_HERO_01_STARSKIFF_MOORING
**Map:** /Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype

## Visual thesis

Shorewake should read as a serene, impossible departure point above the sea: pearl cloth, living reef architecture, pale water-light, musical ornament, and one unmistakable destination — the Starskiff.

Image hierarchy:
1. Melusina / Shorewake silhouette.
2. Starskiff as destination.
3. Luminous reef frame.
4. Sea Above depth / horizon.
5. Small musical and material detail.

Do not let particles, bloom, decals, PCG density, or shader novelty compete with that hierarchy.

## HERO 01 — Starskiff Mooring

Story beat: Melusina reaches the mooring after crossing the reef. The Starskiff is waiting. The frame should feel like the instant before she commits to departure.

### Composition

Target a 16:9 recruiter / reel master composition.

Foreground:
- one strong reef or cloth-banner framing element;
- avoid cluttering Melusina's silhouette;
- optional shallow-depth detail for material richness.

Midground:
- Melusina in Shorewake;
- Starskiff mooring / lyre host;
- readable path between character and vessel.

Background:
- Sea Above horizon / void;
- restrained bell-tree / reef silhouettes;
- enough atmospheric depth to make the scene feel enormous.

### Camera intent

Keep three candidates until one clearly wins:
- A — Processional 3/4: behind/side of Melusina looking toward Starskiff.
- B — Intimate profile: Melusina profile + Starskiff occupying opposite third.
- C — Wide destination: small Melusina, dominant Starskiff, enormous Sea Above scale.

Focal-length tests:
- 28–35 mm for the wide;
- 40–55 mm for hero 3/4;
- 65–85 mm only for intimate character/detail coverage.

### Lighting thesis

- soft pearl / dawn key;
- cool sea-cyan / lavender fill;
- Starskiff brass and wake emission as warm accent;
- character rim separates Shorewake silhouette without flattening fabric;
- preserve readable darks — do not solve everything with bloom.

Use PPV_NikkiDream as the base. No new master post-process material.

### Material priorities

1. Shorewake fabric — PearlWoven/shimmer motion, controlled sparkle, StickerEdge.
2. Starskiff brass — warm separation against the cool environment.
3. Reef surfaces — T1 Nikki-chain treatment; avoid equal-frequency sparkle everywhere.
4. Cloth banner — T2 rim + twinkle only where it supports composition.
5. Wake emission — water-light read, no sticker treatment.

### Environment dressing rule

Dress for the camera first. Every placed/PCG element must serve at least one of:
- frame Melusina;
- point toward Starskiff;
- create depth;
- create material contrast;
- explain the mooring as a place.

Anything else can be hidden or deferred.

## HERO 02 — Reef Choir Crossing

Purpose: environment-art proof, PCG/procedural breakdown, traversal shot, visual bridge between quay and Starskiff.

Art target:
- strong coral/kelp silhouette rhythm;
- one obvious navigable path;
- musical repetition without procedural uniformity;
- height-aware placement remains mandatory.

## HERO 03 — Shorewake Quay

Purpose: chapter opening, outfit reveal, quieter emotional frame before reef spectacle.

Art target:
- architectural/environment composition;
- wardrobe silhouette;
- restrained density;
- establish palette and horizon language.

## Required breakdown coverage

For each hero composition eventually capture:
- beauty;
- ungraded / lighting-only comparison;
- wireframe or mesh-density view;
- material close-up;
- procedural/PCG view where relevant;
- one annotated composition image;
- 5–10 second camera motion test.

## Naming

Use SHW_<TYPE>_<NN>_<SUBJECT>_<VERSION>.

Examples:
- SHW_HERO_01_STARSKIFF_MOORING_v001
- SHW_DETAIL_01_SHOREWAKE_FABRIC_v003
- SHW_BREAKDOWN_01_REEF_PCG_v002

Evidence destination: Saved/SemesterEvidence/2026-W37/Shorewake/
Render-farm outputs: Saved/RenderFarm/<job>/

## HERO 01 blockout gate

HERO 01 is ready for polish when:
- Melusina, Starskiff, and horizon read instantly at thumbnail size;
- no major silhouette tangencies;
- three camera candidates have been captured;
- one lighting direction clearly wins;
- dress/boat/environment palette feels intentional;
- foreground/midground/background separation is obvious;
- obvious placeholder geometry is hidden or deliberately framed out;
- a 5-second camera move works without revealing broken composition;
- a screenshot exists before detail polish begins.

Do not polish individual coral/material details before this gate passes.