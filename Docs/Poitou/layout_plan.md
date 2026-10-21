# Melusina's Morning: Layout Plan v0 (Marais Poitevin / Poitou)

## Core identity
A single dawn in the "Venise Verte" of the Marais Poitevin, western France. Melusina, the water fairy of Lusignan legend, moves from a misty marsh edge along tree-lined conches, through a lime-washed limestone village and its Romanesque church, and up to a ruined Lusignan-style keep on the limestone rise at the edge of the marsh. Everything is flat, wet, and green, organised by water. The only vertical drama comes from the church steeple, the rows of poplar and ash, and the limestone rise (the "coteau" where marsh meets plain). That rise replaces the floating islands with something the region actually has.

## Level size
- **About 1 x 1 km playable focus**, plus a 300–500 m backdrop ring of meadows, poplar walls and mist with low or no detail.
- Reasoning: a real village like Arçais or Coulon is roughly 300–400 m across. Meadow islands are about 1–13 ha (the La Garette island is 13 ha, its large parcels 5.5 ha). Inside 1 km you get one village, about 6–10 parcel islands and a full marsh-to-rise transect. At walking pace (~1.4 m/s), the ~1.6 km route takes about 15–20 minutes, which suits a portfolio walkthrough. Mist and poplar curtains cut sightlines naturally, so the backdrop stays cheap.
- Schematic coordinates: 0–1000 m, north up. Heatmaps: 1024 px, 1 px ≈ 0.98 m.

## Player route (see layout_map.png)
| # | Beat | Notes / sightline |
|---|------|------|
| 1 | Landing jetty in the mist (SW) | Start by barque. A faint steeple silhouette (A) shows through the mist. |
| 2 | Meadow footbridge | Wooden passerelle over a fossé. First clear look at the ruin (B) on the rise. Lone pollarded ash (E) frames the view. |
| 3 | Grand Port & barques | Crossing the main bief. Wooden crane (C) and moored plates (barques). |
| 4 | Romanesque church square | Village core, lime-washed stone, the steeple overhead. |
| 5 | Quéreux lane / balais to water | Stepped barns run down to a conche. View east toward the lock (D). |
| 6 | Poplar allée & lock | A long framed allée with the ruin as the vanishing point. |
| 7 | Ruin on the limestone rise | End beat. Look back over the whole marsh, the steeple and the mist (reverse sightline). |

Landmarks: A church steeple, B ruin keep (Lusignan-style), C Grand Port crane, D lock (écluse), E pollarded ash ("têtard").

## Zones and PCG heatmap channels
In every map, white means maximum density and black means none. **Global exclusions: water, the route path, and a 4 m path buffer** are forced to 0.

| Zone / channel file | Grayscale meaning | Mesh families | Density (at white) | Extra exclusions |
|---|---|---|---|---|
| Village core: `village_buildings.png` | Building-plot likelihood; brightest near the church | Limestone houses (R+1), balais barns, quéreux walls, dry-stone enclos, gardens | 1 building per 150–300 m² in the core; 0.6 grey at the edges | Within 4 m of water (quays placed by hand); church square kept clear by hand |
| Canal network: `canal_banks.png` | Distance falloff from the water edge (~6 m) | Reeds, irises, duckweed decals, mooring posts, barques, footbridges | Reeds 4–10 per m² at the bank; props every 20–40 m | Open water centre; bridge footprints |
| Wet meadow parcels: `wet_meadow_grass.png` | Grass/flower coverage modulated by noise | Hay meadow grass, buttercup, meadowsweet, cattle, hay bales, gates | Grass 20–40 per m²; cattle 0.5–2 per ha | Parcel ditches (~70 m grid) |
| Poplar & ash rows: `tree_rows_poplar_ash.png` | A band 4–9 m from the canal edge, plus parcel-edge rows | Lombardy/hybrid poplar, pollarded ash (têtards), alder | One tree every 6–7 m along a row (7x8 m in plantations) | Within 5 m of water (per the poplar charter); village; rise |
| Limestone rise & ruin: `ruin_rise.png` | Radial; rubble and scrub thicken toward the keep | Ruined curtain walls, keep, scattered limestone blocks, oak/box scrub, dry grass | Rubble 0.05–0.2 per m² near the keep | Keep footprint and walkway placed by hand |
| Mist marsh edge: `mist_marsh_reeds.png` | Reedbed and sedge density in the low, wild marsh | Phragmites, sedge, willow scrub, dead snags, heron spawn points | Reeds 10–30 per m² | Jetty and path |
| (atmos) `mist_volume.png` | Local fog-volume density / height mask | Local fog volumes, Niagara mist cards | Not applicable (drives material and volume parameters) | None |

## Scale and metric rules
- **Waterways:** fossé/ditch under 4 m; conche 4–8 m (use 5–7 m); bief / route d'eau 5–20 m (main bief 18 m); canal over 15 m. Water level sits 0.3–0.8 m below the bank; banks are soft and slumped.
- **Paths:** towpath (chemin de halage) 2–3 m; village street 4–6 m; quéreux lane 2–3 m; footbridge 1.2–1.5 m wide.
- **Buildings:** 1–2 storeys plus attic. Eaves 4–6.5 m, ridge 7–10 m. Barns 5–8 m. Church nave about 12 m, steeple 25–35 m. Ruin keep 18–25 m on a rise of 15–25 m. The whole marsh is flat to ±0.5 m.
- **Trees:** poplars 25–30 m, ash pollards 8–12 m, row spacing 6–7 m.
- **Barque (plate):** about 6 x 1.2 m.
- **Parcels:** 1–5 ha islands, edged by ditches and tree rows. The schematic uses a ~70 m ditch grid in the south as a simplification.

## Open questions
1. A real Lusignan castle sits on a rise 30+ km from the marsh. Should the game compress geography ("Lusignan-style ruin on the marsh coteau"), or use an abbey ruin such as Maillezais? Maillezais is actually on a limestone island in the marsh and may be the stronger fit.
2. Is the route on foot, by barque, or both? This affects canal widths and bridge heights.
3. Fixed dawn time-of-day versus a dawn-to-morning progression along the route?
4. Should the backdrop ring be a World Partition HLOD or a skybox card?
5. What season? Pollarding and hay cutting change how the meadows and trees read.
6. Should the heatmaps be painted in-editor (landscape layers) or imported as textures into PCG "Texture Sampler" nodes?
7. Does Melusina get water-only traversal moments, such as swimming the bief?

## Sources
- Wikipedia FR, "Marais poitevin" (waterway typology and widths): https://fr.wikipedia.org/wiki/Marais_Poitevin
- PNR Marais Poitevin, La Garette atelier (parcel sizes, ash rows, footbridges): https://pnr.parc-marais-poitevin.fr/wp-content/uploads/2015/12/Synthese-atelier-16092015-LaGarette-Coulon.pdf
- PNR, Arçais / St-Hilaire atelier (coteau village, balais, quéreux, Grand Port): https://pnr.parc-marais-poitevin.fr/wp-content/uploads/2015/12/Synthese-atelier-GS-141015-st-halaire-palud-arcais.pdf
- Peupliers de France, Marais Poitevin poplar charter (6–7 m rows, 7x8 m plantations, 5 m from water): https://www.peupliersdefrance.org/uploads/uploads-FR/DocumentsTechniques/MaraisPoitevin-Charte%20populicole-Oct2020.pdf
- Parc du Marais Poitevin, Arçais visit page: https://www.parc-marais-poitevin.fr/en/hiking/visite-darcais-petit-village-maraichin-de-la-venise-verte
- Building and tree heights and the steeple/keep figures are typical-value estimates, not sourced.
