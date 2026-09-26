# UI visual direction — the Orrery is the hub (2026-09-26, owner: "too many competing elements; Orrery = main hub; animated magic starfield, editorial Magical Girls lookbook, through the whole project")

Supersedes the quiet-glass HUD styling. Builds on `2026-09-26_ui-orrery-overhaul-goal.md` (O1/O2 done).

## Why it reads rough (audit of what's on screen today)
- **Orrery screen stacks ~18 elements with no hierarchy:** CosmicBackdrop + NebulaVeil + IMG_VoidBG (3 backgrounds), constellation lines H+V, IMG_CoreOrnament (white square over the 3D core), 4 sphere buttons, kicker + title + instruction (3 text lines), persona accent, footer panel + divider + 3 buttons, and the new 3D OrreryView as a hard-edged square. Each fights the 3D chassis.
- **Overworld HUD duplicates the orrery's job:** system row 1/2/J/Esc, quest card, title block, hints all compete with the world.
- **Quill dialogue:** wiring is correct (DefaultGame.ini → WBP_MelodiaQuill* → UMelodiaQuill* C++), but the widgets are unstyled, so they read as stock QuillScript.
- **8 font families** in the Figma redesign; UE ships one UI font.

## Direction
**One hero object:** the Orrery. Every menu is a *station on the orrery* (a sphere on a ring), not a separate screen. Settings, Journal, Codex, Wardrobe become orbiting medallions that the chassis rotates to the front.
**Editorial lookbook grammar:** large display serif set tight, tiny tracked caps kickers, generous negative space, one image per spread, captions not panels. Cream/pearl type on deep indigo; rose-gold filigree hairlines; one accent per screen.
**Animated magic starfield:** a single shared backdrop (twinkle + slow parallax + beat-dithered glow) used by the orrery, Quill, results and loading — the connective tissue "through the project".
**Motion:** beat-locked (0/117/234/469/703 ms). Nothing animates off-beat.
**Type ramp:** 2 families — display serif (Kaisei Decol) + body (Klee One or M PLUS Rounded 1c). Drop Inter/Nunito/Cinzel/Times/Arimo.

## Cut / keep per surface
| Surface | Keep | Cut or fold in |
|---|---|---|
| Orrery hub | 3D chassis (circular, starfield behind), 4 world medallions ON the rings, one editorial title, one caption line | 2 of 3 backgrounds, constellation lines, CoreOrnament, persona accent, footer panel/divider; Quests/Codex/Settings → orbiting medallions |
| Overworld HUD | minimap ring, vitals (name + 2 bars), 4 skills, interaction prompt | system row → one orrery sigil (M); quest card → 3 s toast on update only; title block → area caption on entry only; hints → first-minute only |
| Quill dialogue | lookbook caption card (name kicker + body), choice list as tracked-caps menu | stock box chrome |
| Battle | QWOP highway (unchanged layout) + starfield backdrop + lookbook grade pop | — |

## Assets (SVG kit → Figma → UE)
`Content/UI/AssetKit_20260926/`: starfield tile, orrery medallion (locked/unlocked/focused), filigree hairline frame, editorial divider, orrery sigil. Owner assembles motion in Figma (Smart Animate on the medallion states + KF timing); I read the file back via API and build it in UMG/material.

## Order
V1 asset kit (SVG) · V2 orrery hub cut-down (delete competing elements, circular mask, medallions on rings) · V3 shared starfield backdrop (first UI-domain master — **owner approval pending**) · V4 HUD cut-down · V5 Quill restyle · V6 font ramp.
