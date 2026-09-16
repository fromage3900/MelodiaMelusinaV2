# WebGL Submission / Git State Audit — 2026-09-10

**Refreshed:** final repo-side consolidation  
**Purpose:** distinguish canonical source, preserved evidence, and the small set of machine/human checks that remain before submission.

## Executive state

Nothing important in today's three application lanes is stranded in an agent workspace as an undocumented repo dependency.

`fromage3900/my-site` is the authority for the website, WebGL kit, application drafts, submission manifest and tracker. `fromage3900/MelodiaMelusinaV2` remains the game/capstone authority; its PR #176 is retained only as an audit/capture archive for the Cursor industrial run and must not be applied blindly over current website source.

The WebGL kit remains inside the explicit recruiter-site freeze exception under `tools/fromage-webgl-kit/`; this does not authorize unrelated public-site redesign.

## Lane 1 — $10k procedural industrial homepage loop

**State:** FINAL SOURCE CANONICAL / ONE NORMAL-BROWSER SANITY CHECK BEFORE SEND.

Canonical on `my-site/main`:

- final industrial `app.js` source;
- polished/capture-ready `index.html`;
- shared deterministic timeline helper;
- final proposal at `prototypes/procedural-industrial-loop/APPLICATION_DRAFT_AFTER_QA.md`;
- refreshed evidence at `prototypes/procedural-industrial-loop/EVIDENCE.md`;
- canonicalization receipt at `submissions/2026-09-10/INDUSTRIAL_CANONICALIZATION_RECEIPT.md`;
- current submission manifest and application-tracker CSV.

Current canonical source implements the documented buyer-facing behavior: fixed camera, RoomEnvironment reflection response, ACES tone mapping, restrained studio shadows, shared BODY/SHELL/ACCENT/MACHINE/ACTUATOR materials, rounded fabricated housings, sparse manufacturing detail, greyscale BASE, information-only Structural/Flow/Thermal modes, deterministic capture URLs, Seed 01 canonical, diagnostics disclosure, and the unchanged 16-second absolute-time motion law.

Cursor's preserved capture receipt in Melodia PR #176 records zero console errors, `LOOP Δ = 0`, 81 draws, 16,948 triangles, a full 16-second BASE capture, hero/visualization stills, seed captures and mobile evidence. Those measurements belong to Cursor's captured build. Current `my-site/main` was canonicalized from the documented final behavior rather than treated as a bit-for-bit application of the large transfer patch, so a normal-browser sanity check remains the truthful last technical gate.

**Remaining outside Git:** open current main in a normal browser, verify the deterministic capture URL and loop boundary, inspect the five attachments, recheck the listing, then submit after human review.

## Lane 2 — Three.js fabric technical-art consultant

**State:** CANONICAL DOCS / RUNTIME + PROVENANCE + OWNER PROOF NEEDED.

Canonical on `my-site/main`:

- `fabric/FABRIC_CONSULTANT_EVIDENCE.md`;
- `fabric/CLO_TO_WEB_PIPELINE.md`;
- `fabric/APPLICATION_DRAFT_AFTER_QA.md`;
- existing `wix/` fabric/material viewer architecture used as source evidence.

Still required outside Git before submission:

- runtime-check the existing viewer;
- classify material/texture provenance;
- select one genuine Brennan-owned CLO or Blender artifact;
- choose concise explainable evidence links;
- recheck the listing before send.

A full knitwear configurator is not required for the consulting listing.

## Lane 3 — $3k web-ready product / GLB animation

**State:** AURIGA SOURCE CANONICAL / BLENDER GENERATION + RUNTIME/CAPTURE NEEDED.

Canonical on `my-site/main`:

- `scripts/build_auriga_meter.py`;
- `scripts/check_auriga_meter.py`;
- `prototypes/product-motion-lab/src/auriga-meter.js`;
- `prototypes/product-motion-lab/package.json`;
- existing Product Motion Lab `index.html`, `app.js` and `EVIDENCE.md`.

This supersedes the earlier audit note that the source existed only in Kimi's workspace. The source is now remote and canonical. What does **not** yet exist is the generated `assets/auriga_meter.glb` plus observed Blender/checker/browser evidence.

Still required outside Git before submission:

- run the canonical Blender builder;
- perform Brennan visual/silhouette review;
- run the GLB checker;
- browser-load the GLB through the canonical loader;
- verify deterministic scrub and all three anchors;
- capture desktop/mobile proof and measured diagnostics;
- recheck the listing before send.

## Repository closure rules

- `my-site/main` is the sole website/WebGL-kit source of truth.
- Melodia PR #175 is superseded and remains closed.
- Melodia PR #176 is archive-only; once this final state is recorded it should remain closed, not merged into game main and not re-applied over website main.
- No new commercial prototype is needed today.
- No public recruiter-site redesign is part of these application lanes.
- Do not promote agent-reported or headless-only measurements to buyer-facing claims without the stated sanity/owner checks.

## Canonical decision summary

```text
INDUSTRIAL: SOURCE CANONICAL / EXTERNAL SANITY + HUMAN SEND ONLY
FABRIC:     DOCS CANONICAL / VIEWER + PROVENANCE + OWNER PROOF + HUMAN SEND
PRODUCT:    AURIGA SOURCE CANONICAL / BLENDER + GLB + BROWSER PROOF + HUMAN SEND
CAPSTONE:   CHORAL SHEEP REMAINS P0 AFTER THE APPLICATIONS
```

There are no additional repo-architecture, transfer, branch, or documentation tasks required for these three applications. Remaining gates are deliberately execution/evidence/human-send gates and must not be disguised as completed Git work.
