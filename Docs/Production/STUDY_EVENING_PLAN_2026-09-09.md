# Melusina's Study — Evening Polish + Render + UE Export Plan

Date: 2026-09-09 (evening)
File: Saved/MelusinasHouse/Melusinas_Study_FullNikkiDecorated.blend (Sep 6 21:24, 1.0 MB)
Reviewed live via Blender MCP + 2 EEVEE preview renders (Saved/Audit/melusinashouse/study_preview_20260909.png, study_34_20260909.png)
Authority: GIT PIPELINE LAW (branch + PR per operation, owner approval per push). Capstone S2 pipeline (workshop → graduate → verify → promote → consume).

## 1. What the scene actually is (review findings)

76 objects. The name overpromises — this is an exterior massing with decorated roofs, not a study interior:

- ~46 SurrealArch GN wall/floor cubes (SurrealArch_Cube groups .001–.016 + bevels). Unnamed: Cube … Cube.045.
- Roof_Main (7.6×10.1×4.4 m) carries 13 GN modifiers: roof + beads catenary + star pendants + heart filigree + wall-bead strings. Roof_Main.001 smaller, single modifier. This is the real authored work.
- Templates + curve guides parked at y=-20 (bead, heart, star, filigree, note-head). Correct practice, keep.
- 5 materials, all flat Principled, no textures except shingle bump on MH_MAT_Roof. Openings are unglazed voids. No furniture, no interior, no ground plane.
- Render: EEVEE 1920×1080, Sky Day world, compositor ON, output /tmp\. 1 camera (50mm), 3 lights (1000W white point, blue point, pink sun 10).
- Foreground framing note: the saved camera looks at wall backs; both previews needed re-aiming. Camera work is part of tonight.

Against P0/capstone: the study is not on the UE P0 gate path, so it routes through S2 — workshop file stays in Saved/ (gitignored) until promotion; UE consumes FBX/glTF exports, never the blend. Portfolio renders curate from Saved/RenderFarm per S3.

## 2. Key decision (owner, before polish starts)

The file says "Study" but contains no interior. Two directions:

- A: Exterior hero (recommended) — finish what is actually here: glazed openings, ground, trim, roof jewelry tuned, 3 exterior hero shots. Honest scope, shippable tonight.
- B: True study interior — build the interior (desk, shelves, violin, lamp, chair, rug) inside the shell. Bigger job; exterior still needs pass A first for portfolio.

Default to A tonight; B becomes a follow-up session.

## 3. Polish passes (in order, Blender MCP live)

1. Naming + organization — rename Cube.* to WALL_/FLOOR_/TRIM_ roles; collections: STUDY_SHELL, STUDY_ROOFS, STUDY_GUIDES (parked templates, excluded from render), STUDY_LIGHTING, STUDY_CAMS. (Fixes portfolio hygiene + UE export filtering.)
2. Openings — glaze all voids: glass Principled (transmission 1, roughness 0.05) + white frame trim via MEL_moulding_run pattern; door leaf + handle on the empty door frame.
3. Ground + contact — ground plane (stone/marble blend), skirt trim where walls meet grade. Kills the floating-mass look.
4. Material pass — stone/marble get roughness variation + subtle bump (reuse DPM2/Cairo/Bricks groups already in-file); keep pastel palette, it is the deliberate mood.
5. Roof jewelry tune — beads/filigree/pendants already wired; check density at render distance, kill interpenetration, exclude guide curves from render.
6. Lighting — keep 3-light scheme; add warm interior point behind glass (sells "study" at dusk shots), tune sun angle for long shadows, verify no blown highlights on marble.
7. Cameras — lock 3 shots: HERO three-quarter (13,-3,7.5 → study center), FRONT elevation, DETAIL roof-jewelry closeup. 50mm hero, 35mm front, 85mm detail. Never move the saved camera again without versioning.

## 4. Tonight's renders (laptop = EEVEE iteration lane)

- Previews at 50% until lock, finals 100% 1920×1080 EEVEE.
- Output to Saved/RenderFarm/study_20260909/ (NOT /tmp\).
- Contact sheet + defect sweep after each final (z-fight, floaters, blowout, voids).
- Cycles finals, if wanted, go to the home-PC worker per semester topology — laptop stays EEVEE.

## 5. UE import (S2 consume step)

- Export STUDY_SHELL + STUDY_ROOFS (guides/lighting excluded) as FBX, decimeter scale check, to RawArt/MelusinasHouse/Exports/study_20260909/.
- Import + stage on the desktop side (UE editor work is desktop-owned; laptop never touches the live Content tree).
- Blend stays in Saved/ until the promotion decision; exports are outputs, never inputs.

## 6. Git route (tonight)

- Plan doc + export manifest: branch collab/laptop/study-20260909 → PR → owner approval → merge. No direct main pushes (pipeline law).
- Renders stay local (Saved/RenderFarm is gitignored); only curated portfolio promotion touches the site repo, and the showcase freeze still applies.

## 7. Done criteria

- Zero unglazed voids, zero floating masses, all objects named, guides excluded from render.
- 3 locked finals + contact sheet in Saved/RenderFarm/study_20260909/.
- FBX export + manifest staged for desktop UE import.
- Branch pushed as PR, owner approval pending. Blender file UNSAVED-in-place edits? No — save versioned: Melusinas_Study_20260909_A.blend, keep Sep-6 file untouched.
