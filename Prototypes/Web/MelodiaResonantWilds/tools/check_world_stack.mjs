// World-expansion source contract; headless browser performs actual runtime tests.
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const read = p => readFileSync(join(root, p), 'utf8');
const g = read('js/game.js'), world = read('js/world.js'), a = read('js/activities.js');
const design = read('js/design.js'), flags = read('js/flags.js'), sw = read('sw.js'), smoke = read('tools/browser_smoke.mjs');
const progress = read('js/progress.js'), ui = read('js/ui.js');
assert.match(g, /new PostFX\(this, \{ worldEffects: flagPostfx \}\)/);
assert.match(g, /painterlyEnabled \? new PainterlyFilter/);
assert.match(g, /this\.postfx\.render\(\)/);
assert.match(flags, /liteMode/);
assert.match(flags, /flagWorldexp/);
assert.match(flags, /flagDressingDense/);
assert.match(flags, /flagNikkiLook/);
assert.match(flags, /flagDaycycle/);
assert.match(flags, /flagPostfx/);
assert.match(world, /flagWorldexp/);
assert.match(a, /flagWorldexp/);
assert.match(design, /flagDressingDense/);
assert.match(g, /flagPostfx/);
assert.match(g, /flagDaycycle/);
assert.match(a, /planExploration\(b, bi, rng, this\.pois\.slice\(\)\)/);
assert.match(progress, /regionStatus\(/);
assert.match(progress, /regionPing\(/);
assert.match(progress, /checkRegionComplete\(/);
assert.match(ui, /Ping nearest Dew/);
assert.match(smoke, /desktop-worldexp-postfx/);
assert.match(smoke, /desktop-lite/);
assert.match(smoke, /destinations >= 16/);
assert.match(sw, /resonant-wilds-v16-20261029-crisp-kuwahara/);
assert.match(sw, /js\/flags\.js/);
assert.match(sw, /js\/playground\.js/);
assert.match(sw, /js\/grove-catalog\.js/);
assert.match(sw, /js\/floraison-pov\.js/);
assert.match(sw, /js\/painterly\.js/);
assert.match(smoke, /desktop-grove-full/);
assert.match(smoke, /desktop-chladni-mode/);
assert.match(smoke, /desktop-v1-cel/);
assert.match(smoke, /desktop-floraison-pov/);
const ow = read('js/openworld.js');
for (const id of ['choir_marsh', 'glass_orchard', 'starlit_moor']) {
  assert.match(ow, new RegExp(id + '\\s*:'));
}
assert.match(ow, /Mist Choir Reedwalk/);
assert.match(ow, /Prism Picnic Glade/);
assert.match(ow, /Starlit Moongate/);
assert.match(ow, /fashionPhoto/);
assert.match(ow, /ABILITY_OUTFITS/);
assert.match(ow, /mist_float/);
assert.match(ow, /prism_veil/);
assert.match(ow, /nightbell_glide/);
assert.match(a, /_unlockAbilityOutfit/);
assert.match(a, /onAbilityOutfitEquipped/);
assert.match(g, /Ability Outfit/);
for (const p of ['js/openworld.js','js/postfx.js','js/flags.js','js/playground.js','js/grove-catalog.js','js/floraison-pov.js','js/flower-landscape.js','js/resonant-botany.js','vendor/postprocessing/OutlinePass.js',
 'vendor/postprocessing/UnrealBloomPass.js','vendor/shaders/FXAAShader.js']) {
 assert.ok(existsSync(join(root,p)), p+' missing');
}
console.log('World expansion integration contracts: PASS');
