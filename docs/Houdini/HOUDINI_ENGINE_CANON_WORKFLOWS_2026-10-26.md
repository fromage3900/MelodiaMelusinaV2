# Houdini Engine canonical must-have workflows (2026-10-26)

Governing rules (AGENTS.md): Houdini is **offline authoring**; runtime world-building is Unreal PCG only. Every workflow below
ends in a baked asset or a point/curve set that UE consumes: static mesh, VAT, flipbook, VDB-baked volume texture, JSON/CSV
point set, or a cooked HDA instance in the editor. No Houdini at runtime. Status words: **PROVEN** (ran, gate passed),
**SPIKE** (ran once, narrow), **PLANNED** (designed only). Existing materials only; no new masters.

| ID | Workflow | Status | Script / asset | Output -> UE intake |
|---|---|---|---|---|
| W1 | Live HDA cook + place (HoudiniPublicAPI `instantiate_asset`, proxy mesh, do not save HE temp) | PROVEN (8 Faraway HDAs imported/cooked 2026-10-26) | `hda/*.hda`, `Content/HDA/Faraway/` | HDA actor in level |
| W2 | Measured-bounds gate for every HDA (bounds, outputs, controls, attribs) | PROVEN | `Tools/Houdini/faraway/measure_faraway_hdas.py` | `hda_measure.json` |
| W3 | Global-field biome classifier + placement sets | PROVEN | `build_faraway_biomes.py` | mask PNG + `placements.json` |
| W4 | Seam extraction, exact junctions, stitch dressing | PROVEN | `build_faraway_seam_dressing.py` | polylines + CSV points |
| W5 | Wonder-layer data (fauna settle points, landmark/guide rules, bloom/lantern/hop sets) | PROVEN | `build_faraway_wonder_data.py` | JSON for PCG/BP |
| W6 | Vellum cloth drape over cooked terrain (contact/relief gate) | SPIKE | `build_faraway_hero_drape.py`, `FARAWAY_VELLUM_USAGE_2026-10-26.md` | static mesh / VAT |
| W7 | Contact sheets for every layer (top-down + per-HDA) | PROVEN (maps) | `make_faraway_contact_sheets.py` | PNG sheets |
| W8 | Pyro/volume fog banks + god-rays baked to flipbook / volume texture | PLANNED -> in loop | `build_faraway_fog_volumes.py` | flipbook + manifest |
| W9 | FLIP waterfall + Ocean spectrum for basin, baked to flipbook/VAT | PLANNED -> in loop | `build_faraway_basin_water.py` | flipbook/VAT |
| W10 | Heightfield erosion + strata masks on peaks | PLANNED -> in loop | `build_faraway_peak_erosion.py` | height/mask PNG |
| W11 | Crowd/flock simulation baked to beat-locked flight paths | PLANNED -> in loop | `build_faraway_lacewing_flocks.py` | path JSON / VAT |
| W12 | CHOPs/audio curves from a motif (lullaby -> glow/breath/bloom timing) | PLANNED -> in loop | `build_faraway_lullaby.py` | MIDI + curve JSON |
| W13 | Vellum hair / wire for fringe, tassels, hair | PLANNED | after models exist | static/VAT |
| W14 | PDG/TOPs tile batch with caching + per-tile manifests | PLANNED -> in loop | `faraway_tiles_pdg.py` | per-tile outputs |
| W15 | Labs imposters + LOD chain for peaks and orchard trees | PLANNED | after W1 placements are final | LOD FBX / imposter atlas |
| W16 | Copernicus biome-driven procedural fabric textures | SPIKE elsewhere (4 fabric sets exist) | `Tools/Houdini/copernicus/` | texture sets for existing MIs |
| W17 | Solaris/Karma lookdev contact renders | PLANNED | n/a | PNG review only (MRQ for final) |

## Rules that apply to every workflow

1. One deterministic script per workflow, seed 3900, two runs must hash identically.
2. Every script has a numeric gate that can fail; a first gate that passes a broken result is a bug in the gate (W6 lesson).
3. Outputs go under `Saved/Staging/HoudiniForge/<Name>_<date>/` with a sha256 manifest; never `Content/`, never
   `Saved/Audit/houdini_faraway_mother/`.
4. Bounds come from measurement (W2), not from parameters or docs.
5. Each workflow produces a contact sheet or a number the reviewer can open.
6. Houdini cooks at 505, skirt/horizon off; rename HDA type per version.
