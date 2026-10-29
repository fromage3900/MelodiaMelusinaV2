// Zero-dependency release contract for edge-locked anisotropic Kuwahara.
// Real shader compilation and rendering are covered by browser_smoke.mjs.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const read = p => readFileSync(join(root,p),'utf8');
const paint = read('js/painterly.js'), composer=read('js/postfx.js');
const game=read('js/game.js'), tuner=read('js/npr-tuner.js');
const sw=read('sw.js'), smoke=read('tools/browser_smoke.mjs');
assert.match(paint,/query\.get\('kuwahara'\) === '1'/);
assert.match(paint,/!legacyRender && nprV2/, 'only on canonical hard-cel');
assert.match(paint,/uEdgeLock/, 'edge-aware compositing');
assert.match(paint,/smoothstep\(0\.035,0\.16,edge\)/, 'edge protection mask');
assert.match(paint,/uEdgeProtect/, 'historic variance-preserving weighting');
assert.match(paint,/Math\.min\(range\[1\],Math\.max/, 'bounded inputs');
assert.match(paint,/this\.pass\.enabled = this\.settings\.strength > 0\.001/, 'paint=0 bypass');
assert.doesNotMatch(paint,/WebGLRenderTarget|setRenderTarget|this\.target\s*=/,
  'no independent scene render target or half-resolution upscaling');
assert.match(paint,/this\.pass\.uniforms\.uTexel\.value\.set\(1\/Math\.max\(1,widthPixels\)/,
  'full-resolution composer pixel step');
assert.match(composer,/this\.composer\.addPass\(this\.output\)/);
assert.match(composer,/if \(this\.painterly\) this\.composer\.addPass\(this\.painterly\.pass\)/);
assert.ok(composer.indexOf('this.composer.addPass(this.output)') <
          composer.indexOf('this.composer.addPass(this.painterly.pass)'),
  'run paint after canonical cel/outlines/bloom/output');
assert.match(composer,/this\.fxaa\.enabled = this\.enabled && !paintOn/,
  'no extra FXAA blur on painterly presentation');
assert.match(game,/painterlyEnabled \? new PainterlyFilter\(\) : null/);
assert.match(game,/new PostFX\(this, \{ worldEffects: flagPostfx \}\)/,
  'allow paint-only mode with postfx=0');
for (const flag of ["'paint'","'rad'","'anis'","'edge'","'sharp'"]) {
  assert.ok(tuner.includes(flag),flag+' missing from live tuner');
}
assert.match(tuner,/floraison:/);
assert.match(tuner,/shadow: 0\.12, ink: 0\.67/);
assert.match(tuner,/anisotropy: 1\.5, edgeProtect: 3\.7/);
assert.match(tuner,/url\.searchParams\.delete\('scale'\)/,
  'historical half-resolution scale must not be copied');
assert.match(sw,/resonant-wilds-v16-20261029-crisp-kuwahara/);
assert.match(sw,/\.\/js\/painterly\.js/);
assert.match(smoke,/desktop-floraison-crisp/);
assert.match(smoke,/mobile-floraison-crisp/);
assert.match(smoke,/desktop-kuwahara-ab/);
console.log('Crisp Kuwahara contract PASS: full-res compositing, hard cel, edge lock, A/B, mobile cap, v16 PWA');
