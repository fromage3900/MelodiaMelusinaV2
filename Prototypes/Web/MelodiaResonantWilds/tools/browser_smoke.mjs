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
  { name: 'desktop-bellflower-off', query: '?bellflower=0', chibi: false, shrine: false, mobile: false, bellflower: false },
  { name: 'desktop-petal-cantata', query: '?flowerbeds=1', chibi: false, shrine: false, mobile: false, flowerbed: true },
  { name: 'desktop-original-flowers', query: '?flowerbeds=0', chibi: false, shrine: false, mobile: false, flowerbed: false },
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
      bellflowers: window.__melodia.world.hubGroup.children.filter(o => o.name.startsWith('RW_Bellflower_Plaza_')).length,
      flowerParts: window.__melodia.world.props.flower.parts.length,
      flowerbedEnabled: window.__melodia.world.flowerbedsEnabled,
      boxLanterns: window.__melodia.world.hubGroup.children.filter(o => o.isMesh && o.geometry.type === 'BoxGeometry' &&
        o.geometry.parameters.width === 0.5 && o.geometry.parameters.height === 0.6 &&
        o.geometry.parameters.depth === 0.5 && o.visible).length,
    }));
    assert.equal(before.chibi, test.chibi, test.name + ': incorrect avatar selection');
    assert.equal(before.flowerbedEnabled, test.flowerbed !== false, test.name + ': flowerbed flag not respected');
    assert.equal(before.flowerParts, test.flowerbed === false ? 1 : 3, test.name + ': incorrect shared instancing mesh count');
    const expectedFlowers = test.bellflower === false ? 0 : 4;
    assert.equal(before.bellflowers, expectedFlowers, test.name + ': incorrect bellflower count');
    assert.equal(before.boxLanterns, 12 - expectedFlowers, test.name + ': original lantern fallback mismatch');
    assert.equal(before.legacyTerrain, !!test.legacy, test.name + ': wrong environment shading');
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
    // Capture one comparable Petal Cantata shot in both modes for art review.
    // This is a browser beauty reference, not a claim of human aesthetic approval.
    if (process.env.RW_SCREENSHOT_DIR &&
        (test.name === 'desktop-petal-cantata' || test.name === 'desktop-original-flowers')) {
      await page.evaluate(() => {
        const g = window.__melodia, x = 0, z = -210;
        g.player.pos.set(x, g.world.height(x, z), z);
        g.camTarget.copy(g.player.pos);
        g.world.warm(x, z);
      });
      // The in-game title banner fades after 2.8 seconds; keep the A/B view unobscured.
      await page.waitForTimeout(3200);
      await page.screenshot({ path: process.env.RW_SCREENSHOT_DIR + '/' + test.name + '.png' });
    }
    assert.deepEqual(failures, [], test.name + ': WebGL/JavaScript console errors');
    console.log('PASS', test.name, JSON.stringify({
      shrubs: before.shrineCount, avatar: test.chibi ? 'chibi' : 'procedural',
      shrine: test.shrine ? 'GLB loaded' : 'procedural',
    }));
    await context.close();
  }
} finally {
  await browser.close();
}
