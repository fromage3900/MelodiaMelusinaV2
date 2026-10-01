// Dumps the web game's musical design (design.js) as JSON on stdout.
import { BIOMES, HUB, RIFT_STYLE } from '../js/design.js';
const pick = (b) => ({ id: b.id, name: b.name, bpm: b.bpm, meter: b.meter, key: b.key, mode: b.mode, style: b.style, prog: b.prog, motif: b.motif, movement: b.movement ?? null, midi_preset: b.midi_preset ?? null });
console.log(JSON.stringify([HUB, ...BIOMES, RIFT_STYLE].map(pick)));
