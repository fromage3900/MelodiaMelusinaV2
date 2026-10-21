# P2 Faraway Mother: Concept / Architecture Sheet Conventions (2026-10-17)

**Status:** working conventions for the shared sheet tool. This is planning and reference only. It does not lock the art direction or claim that any asset has been implemented.
**Tool:** `Tools/concept_sheets/make_concept_sheet.py` (Pillow + numpy). Layouts: `creature`, `architecture`, `silhouettes`. Styles: `faraway_highkey` (default), `gothic_watercolour`, `clean`. Run `python make_concept_sheet.py --help` for the full spec format, or `--example` to print an example spec.
**Example specs:** `Tools/concept_sheets/specs/`
**Output folder:** `Saved/Audit/faraway_mother_p2_enemies_20261017/concept_sheets/`. Painted art from the Concept Breakdown Artist goes to `.../concept/`. The tool only *reads* that folder.

> Direction note (2026-10-17, 07:32): the first P2 blockouts (Thimblet, Lullaby Mobile, Cradle Spire, Seam Nursery diorama) were dropped. The new direction is Melusina-style elegant dolls gone wrong. No sheets were made for the dropped designs. The tool is design-agnostic.

## 1. What published JRPG / FromSoftware art books show (sourced)

Most of these books are image-led and only lightly annotated, so treat what follows as layout conventions, not quotes. Where a source is only a store page or a review, the claim is limited to what that page says.

- **Rough to final, with creator comments.** The Xenoblade Chronicles 2 *Alrest Record* book is described as having two to four pages per important character, prototype designs, and illustrator comments. Its world-design pages are dense and compacted ([RPGamer import review](https://rpgamer.com/2019/02/rpg-import-elements-xenoblade-chronicles-2-artworks-utawarerumono-duology-visual-collection/); [Rascal blog review](https://rascal.pl/en/artbooks/xenoblade-2-official-artworks-alrest-record-famitsu-kadokawa-2019-2/)). The Xenoblade 3 *Aionios Moments* book is described as about 80% development artwork, with creator comments for every character and fewer comments on the world pages ([hyperTs review, JP](https://hyperts.net/xenoblade3/artworks-review/)).
  *Use for us:* each subject gets a hero image, its variants, and short creator-style callouts. Environment sheets can be denser.
- **FromSoftware horror side.** *Bloodborne Official Artworks* is a 256-page book of character concepts, creature designs, location illustrations, weapons and items. Its contents list pairs locations with their creatures ([Simon & Schuster](https://www.simonandschuster.com/books/Bloodborne-Official-Artworks/Sony/9781772940367); [Bloodborne Wiki contents list](https://www.bloodborne-wiki.com/2017/01/bloodborne-official-artworks.html)). A review notes that *Dark Souls: Design Works* includes rough sketches but has notably few annotations ([OtakuStudy review](https://www.otakustudy.com/books/2014/01/dark-souls-design-works-artbook-review/); [UDON](https://store.udonentertainment.com/products/dark-souls-design-works-hardcover)).
  *Use for us:* the horror reads through image and mood, not text. Keep callouts short and let the dormant/awake and state panels carry the dread.
- **Turnaround / model sheet.** The views are front, 3/4, side and back, drawn at the same scale and pose and aligned on shared guide lines. They are often accompanied by colour, material and expression notes, and the design should be checked by its silhouette from each view ([NHance glossary](https://nhance-school.com/tools/glossary/model-sheet-turnaround); [Clip Studio / Art Rocket model sheets](https://www.clipstudio.net/how-to-draw/archives/164740); [AWN Toon Institute](https://www.awn.com/tooninstitute/lessonplan/model.htm)).
- **Silhouette and value tests.** Fill the shape with one flat value, check that it reads small, and check that it stays distinct from the rest of the cast. Then check in greyscale that the focal point carries the strongest contrast ([CoArtist readability article](https://coartist.net/blog/character-design-readability-silhouette-shape-language-contrast); [Theseus thesis on 3D game character readability](https://www.theseus.fi/bitstream/handle/10024/904059/Olgskaia-Mustonen_Kristina.pdf?isAllowed=y&sequence=2)).
- **Architecture sheets: plan / elevation / section.** A plan is a horizontal cut seen from above. An elevation is a flat view of one face. A section is a vertical cut, with the cut material drawn bold. All three are orthographic, with no perspective ([Wikipedia: Architectural drawing](https://en.wikipedia.org/wiki/Architectural_drawing); [CUNY City Tech handout, PDF](https://openlab.citytech.cuny.edu/christo-arch1101-fall-2020/files/2020/09/Architectural-Drawings_Plan-Section-Elevation.pdf); [Columbia CDP module](https://cdp.arch.columbia.edu/smorgasbord/modules/13-arch-drawing/13-1_orthographic-drawing/); [Designing Buildings: Elevations](https://www.designingbuildings.co.uk/wiki/Elevations), which also lists the title block, scale and level datums).
- **House layout lock (in-repo).** The owner-approved 2026-09-08 Choral Sheep and Melusina boards (`Docs/References/VisualBoards/2026-09-08/`) use ivory paper, lavender drafting rules and a serif title top-left. Below that sit a tall hero figure on the left and, on the right, panel rows with small header tabs: a turnaround, a silhouette strip, an expression/state strip, close-ups, a palette box and notes, with a footer bar. **The tool copies this structure and only ages it**, so it does not introduce a new layout.

## 2. Gothic watercolour references (sourced)

- **Yoshitaka Amano (Final Fantasy).** He works in pencil, then ink/brush line, then watercolour washes, and is the JRPG precedent for ink-and-wash concept art ([Cook & Becker spotlight](https://www.cookandbecker.com/en/article/174/spotlight-yoshitaka-amano.html); [Game Informer interview, 2016](https://gameinformer.com/b/features/archive/2016/04/27/the-art-that-shaped-final-fantasy-thoughts-from-famed-artist-yoshitaka-amano)).
- **Arthur Rackham.** His method was a tinted drawing: pen-and-ink line with thin, translucent, muted watercolour washes. This is the closest Victorian/Edwardian reference for our "sepia ink + wash" look ([Wikipedia](https://en.wikipedia.org/wiki/Arthur_Rackham); [Tulane exhibit](https://exhibits.tulane.edu/exhibit/canvases/arthur-rackham-1867-1939/); [LMU Munich, "The Fairy World in Watercolour and Ink"](https://www.en.shakespeare-bibliothek.anglistik.uni-muenchen.de/miscellany/archive/miscellany13/index.html)).
- **Victorian natural-history plates.** Ernst Haeckel's *Kunstformen der Natur* (1899-1904) is 100 plates, each paired with descriptive text. Plates combine several specimens with magnified details ([Internet Archive scans](https://archive.org/details/KunstformenDerNaturErnstHaeckel/Kunstformen%20der%20Natur%20-%20Ernst%20Haeckel); [Heidelberg digitised 1899 edition](https://digi.ub.uni-heidelberg.de/diglit/haeckel1899bd1/0101)). This is the model for "Plate" numbering, specimen-style figures and close-up insets.
- **FromSoftware.** The Bloodborne and Dark Souls books above are the horror mood reference. No claim is made here about the artists' specific media.

## 3. Sheet anatomy used by the tool

| Panel | Creature layout | Architecture / diorama layout | Silhouette page |
|---|---|---|---|
| Title block | serif (highkey) or blackletter (gothic) name, caps subtitle, italic meta line (region, biome, slot, date, plate), intro | same | same |
| Hero | painted image from `concept/` if one exists (as-is), else blockout render (watercolour-treated), else placeholder | same | - |
| Turnaround | front / 3/4 / side / back / top | - | - |
| Plan / Elevation / Section | - | three orthographic panels; `generator: "chladni"` draws the PCG doc formula as a diagram | - |
| Motif breakdown | - | row of named motifs + text | - |
| Silhouette strip | silhouettes derived from renders by background key | - | 12-16 numbered cells, each beside a **165 cm, 6.5-head doll figure** |
| State strip | Omen > Wake > Strike > Hush | same (beats) | - |
| Dormant vs awake | two panels | - | - |
| Scale | 170 cm drafting mannequin, ruler, crown-height line, creature silhouette at `height_cm` | 170 cm figure | 165 cm doll figure per cell |
| Close-ups & callouts | numbered markers on the hero; `crop` close-ups taken from the hero render | same | - |
| Palette box | swatches read live from `materials/p2_palette.json` (linear to sRGB), named by `p2_mat`, with rough/metal/alpha/emit and use | same | - |
| Notes | **SKT_Root pivot note on every creature sheet**, then bullet notes | notes | - |
| Footer | name, sheet type, status | same | same |

## 4. Honesty rules (enforced by the tool)

1. **No invented art.** A missing image becomes a hatched box marked "NOT YET RENDERED" (or "EMPTY SLOT"). Diagrams are drawn only from documented formulas and are captioned as diagrams.
2. **Treated renders are labelled.** Every blockout image that goes through the watercolour filter is captioned "blockout render, watercolour-treated". The filter smooths edges while keeping them, mutes the colour, lets colour bleed past the edges, adds iron-gall ink edges, multiplies in the paper texture and adds a soft wash ground. Painted images from `concept/` are captioned "painted concept" and are never filtered.
3. **English only.** No decorative pseudo-script and no foreign-language captions.
4. **Fits are logged.** Text shrinks to a minimum size and is then truncated with "...". Every fit and every truncation is written to `<sheet>.layout.json`, together with the images used, the placeholders and the fonts.

## 5. Style

- **`faraway_highkey` (default for P2, 2026-10-17 07:38):** this follows the user's Faraway Mother key art, which is a high-key pastel world, not a dark one. The paper is pale blush (`#ecd9d6` family) with the same procedural grain, stains and soft vignette, kept in a high value range. Drafting lines are mauve `#cdabac` and lavender-grey `#aba6b6`. The darkest ink is dusty plum `#483e49`; nothing on the sheet goes near-black. The title is serif (Playfair Display Bold, installed), with Cinzel caps and Libre Caslon body text. The watercolour filter lifts render darks strongly so that grey/navy blockouts sit in that value range, with mauve wash pools and plum edge ink.
- `gothic_watercolour` (the older option, kept): aged ivory/parchment paper (multi-scale procedural noise, watercolour stains with tide-line rims, a soft umber vignette, grain). Hand-ruled iron-gall/sepia ink frames with slight wobble and pooled ends. The house drafting lines are kept in dusty lavender. The title is in blackletter: **Old English Text MT (`OLDENGL.TTF`, installed)**; UnifrakturMaguntia is used first if it is ever installed. Caps are Cinzel and body text is Libre Caslon Text. Palette swatches sit on watercolour blots. The muted accent colours are moon-silver, milk, umber and ink-blue.
- `clean`: flat ivory paper, crisp lavender rules and a serif title, matching the Sep-8 boards.

## 6. Spec quick-start (for other bots)

```json
{"layout": "creature", "style": "faraway_highkey",
 "base_dir": "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/faraway_mother_p2_enemies_20261017",
 "output": "concept_sheets/P2_<Name>_sheet.png",
 "palette_file": "materials/p2_palette.json", "palette": "all",
 "title": {"name": "...", "subtitle": "...", "region": "P2 The Faraway Mother", "biome": "...", "slot": "...", "date": "2026-10-17", "plate": "Plate I", "status": "..."},
 "intro": "...",
 "hero": {"painted": "concept/<Name>*.png", "src": ["gn/<bot>/renders/<Name>_v3*.png", "gn/<bot>/renders/<Name>_v2*.png"]},
 "turnaround": [{"view": "front", "src": "..."}, {"view": "side"}, {"view": "back"}],
 "silhouettes": [{"src": "...", "caption": "rest"}],
 "states": [{"beat": "Omen", "src": "...", "caption": "..."}, {"beat": "Wake"}, {"beat": "Strike"}, {"beat": "Hush"}],
 "dormant_awake": {"dormant": {"src": "..."}, "awake": {"src": "..."}},
 "scale": {"figure_cm": 170, "height_cm": 60, "crown_cm": 95, "src": "...", "note": "where the numbers come from"},
 "callouts": [{"n": 1, "text": "...", "at": [0.5, 0.3], "crop": [0.3, 0.1, 0.7, 0.5]}],
 "pivot_note": "SKT_Root pivot: ...", "notes": ["..."]}
```

- An image ref can be a string, a list of candidates or a glob. The first candidate that matches wins, and within one glob the last match in sorted order wins (so `_v3` beats `_v2`).
- Object form: `{"src": ..., "caption": ..., "treat": false, "crop": "auto" | [u0,v0,u1,v1] | "none", "key": false}`. Use `key: false` for full-frame scenes such as dioramas, where background keying would grab the floor.
- `at` and `crop` are normalised coordinates of the **framed hero tile** (after auto-crop). Check the output and adjust them.
- Run: `python Tools/concept_sheets/make_concept_sheet.py <spec.json> [...]`

## 7. Known limits

- The background key assumes the team's smooth navy Blender background. Dark velvet parts can partly drop out of silhouettes, soft floor shadows are rejected, and shadows on a lit floor may not be. For full scenes use `key: false`.
- The watercolour filter is a cosmetic treatment of a blockout. It is not painting and must not be presented as concept art.
- The mannequin and doll figures are simple drafting diagrams for scale, not character art.
- One sheet takes about 20-40 s and runs single-threaded.
- The palette box is sized for 10 swatches or fewer. With `"palette": "all"` (the file now holds 15 MAT_* entries) the names shrink to fit, but the "use" text is cut to one line; the cut is logged in `.layout.json`. List the 6-10 materials that matter for the sheet instead.
