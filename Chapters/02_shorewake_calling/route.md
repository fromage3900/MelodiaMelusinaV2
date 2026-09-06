# Route — Chapter 02 Shorewake Calling

| Leg | Map | Entry trigger | Exit verb |
|---|---|---|---|
| 0 | L_KaleidoNave (P0 proven) | terrace tide-line actor (new placement, name: `ShorewakeCallingTrigger_01`, isolated-space pattern per f407220f precedent) | `melodia:flag:flag.shorewake.calling:true` |
| 1 | KaleidoNave interior→quay | Melusina wardrobe swap beat (DawnChorus→Shorewake via subsystem API only) | `melodia:travel:...LV_SeaAbove_Prototype` |
| 2 | LV_SeaAbove_Prototype | spawn at quay PCG grid (height-aware raycast mandatory) | reef encounter zone |
| 3 | SeaAbove reef | `encounter.shorewake.reef_choir` (allowlisted) | typed result → Quill resumes once |
| 4 | Starskiff mooring | lyre phrase host (`APCGHeroMusicGraphHost`, one pattern → route-open) | `melodia:quest:quest.shorewake.calling` complete + `melodia:stat:shorewake_first_tide:melodia_resonance:5` + `melodia:reward:reward.shorewake.skiff_charm` |
| 5 | departure cinematic | existing cutscene lane (SeaAbove cutscene qsc family) | travel back / chapter end checkpoint |

Travel authority: DA allowlist + `Decision 023` single travel path only. Trigger
actors are placed by name-manageable actors; after each `manage_sublevel move_actors`
batch, verify per-level counts (names repeat across levels, rule 23).
