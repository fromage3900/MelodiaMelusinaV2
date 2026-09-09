#!/usr/bin/env node
"use strict";

const { coherenceOf } = require("./membrane.js");

const rest = coherenceOf({ C: 0, E: 0, G: 0 });
const c = coherenceOf({ C: 1, E: 0, G: 0 });
const ce = coherenceOf({ C: 1, E: 1, G: 0 });
const ceg = coherenceOf({ C: 1, E: 1, G: 1 });
const world = coherenceOf({ C: 1, E: 1, G: 1, world: 1 });

const rows = { REST: rest, C: c, "C+E": ce, "C+E+G": ceg, WORLD: world };
console.log("Chladni fleece coherence (Board 02)");
for (const [name, v] of Object.entries(rows)) {
  console.log(`  ${name.padEnd(8)} ${v.toFixed(3)}`);
}

const failures = [];
if (rest !== 0) failures.push(`REST should be 0, got ${rest}`);
if (!(c > ce)) failures.push(`C (${c.toFixed(3)}) should be more settled than C+E (${ce.toFixed(3)})`);
if (!(ceg > ce)) failures.push(`C+E+G (${ceg.toFixed(3)}) should be more ordered than C+E (${ce.toFixed(3)})`);
if (!(world >= ceg)) failures.push(`WORLD should not be less coherent than the resolved chord`);

if (failures.length) {
  console.error("FAIL");
  for (const f of failures) console.error(" -", f);
  process.exit(1);
}

console.log("PASS  interval is less settled; triad is more ordered");
