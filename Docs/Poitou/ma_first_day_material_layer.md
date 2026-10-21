## Material layer: Melusina's first day (Material Artist)

Beats, stop names and times come from CONVERGENCE_PLAN.md §3. All MIs parent to `M_Master_Toon_Universal`. **Every value below is a design target, not a measurement.** `Wetness` is assumed to be a scalar in the Wetness group. **[name check needed]**

| # | Beat / time | DawnLowColor | DawnHighColor | MistColor | MistStrength | Wetness* | Material note |
|---|---|---|---|---|---|---|---|
| 1 | Jetty, 06:00 | #8A93C8 (Shadow lilac) | #FFE8C8 (Sun warm) | #DCE3E4 (Mist) | 0.85 | 0.80 | Dew on the morning reeds and jetty oak; duckweed reads as a flat sheen |
| 2 | Footbridge, 07:00 | #8A93C8 | #FFE8C8 | #DCE3E4 | 0.60 | 0.65 | Oak and tarred piano keys still damp; the mist lifts off the canal teal |
| 3 | Grand Port, 09:00 | #9DB8A5 (Shutter green) | #FFE8C8 | #CFDDEA (Fog) | 0.35 | 0.40 | Quay stone drying from the top down; moored barques keep wet hull lines |
| 4 | Church square, 12:00 | #CFDDEA (Fog) | #E6DFCC (LimeWash) | #CFDDEA | 0.10 | 0.05 | Dry noon lime wash and quoins; tile roofs at full warmth; step-grid stays matte |
| 5 | Quéreux lane, 14:30 | #9DB8A5 | #E6DFCC | #CFDDEA | 0.15 | 0.10 | Dry lane; moss only in the shade of the balais steps |
| 6 | Poplar allée + lock, 17:00 | #8A93C8 | #FFE8C8 | #DCE3E4 | 0.30 | 0.35 | Lock gate oak splash-wet below the waterline; long lilac shadows on Stone_Weathered |
| 7 | Ruin on rise, 19:30 | #8A93C8 | #C07A57 (Tile) | #DCE3E4 | 0.70 | 0.70 | Wet quay and ruin stone at dusk; mist bands return over the marsh |

\*`Wetness` 0–1. `MossColor` stays at #5F6B3B all day. `AtmosphericFadeColor` follows MistColor. `DistanceFadeStrength` tracks MistStrength ×0.8 (target).

**Driver.** Drive all of this from one Material Parameter Collection, proposed as `MPC_Poitou_TimeOfDay`. The time-of-day system (or the music/PhraseBus beat cue) sets it, blending between rows. Don't swap MIs per beat. The MIs keep only static surface values. The master reads the time-of-day parameters from the MPC. **[I]** That gives one draw path and no hitches when a beat changes.

**Checkable rules**
1. Linear albedo is ≥ 0.08 on every surface. Only accents under 5% of the screen may go lower. Tar #26221E (≈0.02 linear) is accent-only: key edges and hull trim.
2. No more than 4 terrain layers in any beat's reference frame. Target set: wet meadow, canal bank, moss/duckweed, path stone.
3. Only `MPC_Poitou_TimeOfDay` changes over the day. A grep of the level's MIs finds no ToD parameter overrides.
4. MistStrength is lowest at beat 4 (≤ 0.15) and highest at beat 1 (≥ 0.8). Check this in each beat's benchmark frame.
5. Every hex in the table comes from the project palette (style_contract_palette_filled.md).
