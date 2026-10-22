# Maillezais DEM — IGN RGE ALTI 1 m

## Source
- Service: Géoplateforme WMS-Raster, layer `ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES` (RGE ALTI 1 m), FORMAT `image/x-bil;bits=32` (raw float32 elevations).
  Example request (NW quarter of 4 tiles of 1500x1500 px):
  https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES&STYLES=&CRS=EPSG:2154&BBOX=411190,6592590,412690,6594090&WIDTH=1500&HEIGHT=1500&FORMAT=image/x-bil;bits=32
- Cross-check: altimetry REST API https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json?lon=-0.739|-0.7300&lat=46.372|46.365&resource=ign_rge_alti_wld&zonly=true → [9.67, 13.15]; DEM value at the first point = 9.672 m (match).
- Licence: Etalab Licence Ouverte 2.0 — attribution "IGN – RGE ALTI®".
- Fetched 2026-10-20 (America/Toronto).

## Grid
- File `maillezais_rgealti1m_l93.tif`: float32, CRS EPSG:2154 (Lambert-93), 1 m pixels, 3000x3000, extent X 411190–414190, Y 6591090–6594090 (3x3 km centred on 46.372 N, -0.739 E = L93 412691, 6592589). Heights in m NGF-IGN69.
- min 1.40 m, max 17.40 m; percentiles p5 2.01 / p50 8.66 / p95 14.34.
- `maillezais_heightmap16.png`: uint16, linear 0 = 1.4015 m, 65535 = 17.4033 m (no georeference in PNG; use the GeoTIFF extent above).
- `hillshade.png` (az 315°, alt 45°, z×3, colour overlay 1.5–8 m), `profiles.png`, `numbers.json`, scripts `fetch.py`, `out.py`, `ana.py`.

## Measurements (all from the DEM; coordinates L93)
- Given abbey point (412691, 6592589): 9.67 m — this lies on the eastern edge of the limestone island, not necessarily the ruins.
- Oval walled/moated enclosure W of the given point (window 412150–412450 / 6592550–6592800): max 13.93 m, p90 9.36 m (the max likely includes ruins/walls; RGE ALTI is a bare-earth DTM but walls can survive).
- Island/plateau east (412600–413300 / 6591500–6592800): median 13.11 m, max 17.40 m.
- Drained marsh SW (411250–411700 / 6591200–6591900): median 2.10 m, std 0.19 m, p5–p95 range 0.53 m.
- **Relative rise: island ~11.0 m (plateau median) to ~11.8 m (enclosure max) above marsh; highest point 15.3 m above.**
- Field flatness, 100x100 m patches: std 0.09–0.10 m (p5–p95 0.29–0.32 m) in plain fields at (411300,6591300), (411600,6591200), (411300,6592000); patches containing ditches/banks: std 0.28 m and 0.54 m.
- Cross-sections (see profiles.png):
  - A (411360,6593500)→(411600,6593700), across the NW–SE diagonal canal: fields ~2.1 m, water surface 1.6 m, banks ~3.1 m → banks ~1.0 m above fields, ~1.5 m above water. (Profile then climbs to 13.9 m on the island tip.)
  - B (411800,6592320)→(411600,6592630), across the southern diagonal canal: water 1.52 m, banks 3.0–3.3 m, fields 2.0–2.8 m → banks ~0.8–1.2 m above fields, ~1.5–1.8 m above water.
  - C (411300,6593150)→(411300,6593450), across the E–W channel: single bank 3.38 m on 2.0 m field → 1.4 m; channel ~1.9 m.
  - D (412300,6592300)→(412300,6592600), channel S of the oval enclosure: bottom 2.2 m, flanks rising to 9.8 m (S) and 8.4 m (N).
  - E W–E transect y=6592650: marsh 2.0–2.5 m → enclosure 9–11.6 m → saddle ~5 m → plateau 16.9 m.
- Caveats: water surfaces in RGE ALTI are interpolated/flattened (no bathymetry), so "bottom" = water/fill surface. Canal names (Jeune Autise, Sèvre Niortaise, etc.) were NOT verified against a map; profiles are identified by coordinates only. Step-like artefacts in profiles come from mixed-source RGE ALTI interpolation.
