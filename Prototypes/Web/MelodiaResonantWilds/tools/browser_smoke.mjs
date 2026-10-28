// Cloud-only Chromium/WebGL smoke for the zero-build Resonant Wilds game.
// Installed transiently in Actions; not a production/runtime npm dependency.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.GAME_URL;
if (!base) throw new Error('GAME_URL is required');
const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--enable-webgl', '--use-gl=angle',
    '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const variants = [
  { name: 'desktop-default', query: '', chibi: false, shrine: false, mobile: false },
  { name: 'desktop-chibi-shrine', query: '?avatar=chibi&shrine=glb', chibi: true, shrine: true, mobile: false },
  { name: 'mobile-baseline', query: '?chladni=0&caustics=0', chibi: false, shrine: false, mobile: true },
  { name: 'desktop-legacy-render', query: '?render=legacy', chibi: false, shrine: false, mobile: false, legacy: true },
  { name: 'desktop-npr-v2', query: '?npr=v2&avatar=chibi&shrine=glb', chibi: true, shrine: true, mobile: false, npr: true },
  { name: 'desktop-painterly', query: '?npr=v2&kuwahara=1&avatar=chibi&shrine=glb', chibi: true, shrine: true, mobile: false, npr: true, painterly: true },
  { name: 'mobile-npr-v2', query: '?npr=v2&kuwahara=0', chibi: false, shrine: false, mobile: true, npr: true },
];
try {
  for (const test of variants) {
    const context = await browser.newContext({
      viewport: test.mobile ? { width: 844, height: 390 } : { width: 1280, height: 720 },
      deviceScaleFactor: test.mobile ? 2 : 1,
      hasTouch: test.mobile,
      isMobile: test.mobile,
      serviceWorkers: 'block',
    });
    const page = await context.newPage();
    const failures = [];
    page.on('pageerror', (e) => failures.push(e.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error' && /shader error|webglprogram|glTFloader|THREE\.WebGL|uncaught/i.test(msg.text())) failures.push(msg.text());
    });
    const response = await page.goto(base + test.query, { waitUntil: 'domcontentloaded', timeout: 60000 });
    assert.ok(response?.ok(), test.name + ': page returned HTTP error');
    await page.waitForFunction(() => !!window.__melodia &&
      !document.querySelector('#play').disabled, null, { timeout: 90000 });
    const before = await page.evaluate(() => ({
      chibi: typeof window.__melodia.player.m.pose === 'function',
      shrineCount: window.__melodia.activities.pois.filter(p => p.type === 'shrine').length,
      uniforms: Object.keys(window.__melodia.world.uniforms),
      legacyTerrain: !!window.__melodia.world.terrainMat.isMeshLambertMaterial,
      chladni: window.__melodia.world.uniforms.uChladni.value,
      caustics: window.__melodia.world.uniforms.uCaustics.value,
      painterly: !!window.__melodia.painterly,
      paletteSize: window.__melodia.world.terrainMat.gradientMap?.image?.data?.length || 0,
    }));
    assert.equal(before.chibi, test.chibi, test.name + ': incorrect avatar selection');
    assert.equal(before.legacyTerrain, !!test.legacy, test.name + ': wrong environment shading');
    assert.equal(before.painterly, !!test.painterly, test.name + ': wrong painterly state');
    if (test.npr) assert.equal(before.paletteSize, 12, test.name + ': missing RGB NPR gradient');
    else if (!test.legacy) assert.equal(before.paletteSize, 3, test.name + ': v1 gradient regression');
    if (test.legacy) {
      assert.equal(before.chladni, 0, 'legacy Chladni strength');
      assert.equal(before.caustics, 0, 'legacy caustics strength');
    }
    assert.ok(before.shrineCount > 0, test.name + ': no shrines to validate');
    assert.ok(before.uniforms.includes('uChladni') && before.uniforms.includes('uCaustics'),
      test.name + ': shader uniforms missing');
    if (test.shrine) {
      await page.waitForFunction(() => window.__melodia.activities.pois.some(
        p => p.type === 'shrine' && !!p.assetVisual
      ), null, { timeout: 45000 });
    }
    await page.locator('#play').click();
    await page.waitForFunction(() => window.__melodia.started &&
      window.__melodia.renderer.info.render.calls > 0, null, { timeout: 30000 });
    assert.deepEqual(failures, [], test.name + ': WebGL/JavaScript console errors');
    if (process.env.GAME_SCREENSHOTS === '1') {
      await page.screenshot({ path: '/tmp/resonant-wilds-' + test.name + '.png' });
    }
    console.log('PASS', test.name, JSON.stringify({
      shrubs: before.shrineCount, avatar: test.chibi ? 'chibi' : 'procedural',
      shrine: test.shrine ? 'GLB loaded' : 'procedural',
    }));
    await context.close();
  }
} finally {
  await browser.close();
}
