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
  { name: 'desktop-npr-v2', query: '?npr=v2&avatar=chibi&shrine=glb', chibi: true, shrine: true, mobile: false, npr: true },
  { name: 'desktop-painterly', query: '?npr=v2&kuwahara=1&avatar=chibi&shrine=glb', chibi: true, shrine: true, mobile: false, npr: true, painterly: true },
  { name: 'mobile-npr-v2', query: '?npr=v2&kuwahara=0', chibi: false, shrine: false, mobile: true, npr: true },
  { name: 'desktop-live-tuner', query: '?npr=v2&kuwahara=1&avatar=chibi&shrine=glb&tune=1&look=soft', chibi: true, shrine: true, mobile: false, npr: true, painterly: true, tune: true },
  { name: 'desktop-worldexp', query: '?worldexp=1', chibi: false, shrine: false, mobile: false, worldexp: true },
  { name: 'desktop-worldexp-postfx', query: '?worldexp=1&postfx=1&dressing=dense&nikkilook=1&daycycle=1', chibi: false, shrine: false, mobile: false, worldexp: true, postfx: true },
  { name: 'desktop-npr-colour-review', query: '?npr=v2', chibi: false, shrine: false, mobile: false, npr: true },
  { name: 'desktop-grove-glb', query: '?grove=glb', chibi: false, shrine: false, mobile: false, grove: 'glb' },
  { name: 'mobile-grove-dense', query: '?grove=glb&worldexp=1&dressing=dense', chibi: false, shrine: false, mobile: true, worldexp: true, grove: 'glb' },
  { name: 'desktop-grove-fallback', query: '?grove=glb', chibi: false, shrine: false, mobile: false, grove: 'fallback' },
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
    if (test.grove === 'fallback') await page.route('**/harmonic-grove-37.glb', route => route.abort());
    const failures = [];
    page.on('pageerror', (e) => failures.push(e.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error' && /shader error|webglprogram|glTFloader|THREE\.WebGL|uncaught/i.test(msg.text())) failures.push(msg.text());
    });
    const response = await page.goto(base + test.query, { waitUntil: 'domcontentloaded', timeout: 60000 });
    assert.ok(response?.ok(), test.name + ': page returned HTTP error');
    assert.equal(await page.locator('.title-sigil img, .shrine-crest img').count(), 4,
      test.name + ': website SVG heritage ornaments absent');
    assert.ok(await page.evaluate(async () => {
      const images = [...document.querySelectorAll('.title-sigil img, .shrine-crest img')];
      await Promise.all(images.map(img => img.decode()));
      return images.every(img => img.naturalWidth > 0);
    }), test.name + ': website SVG failed to load');
    await page.waitForFunction(() => !!window.__melodia &&
      !document.querySelector('#play').disabled, null, { timeout: 90000 });
    const before = await page.evaluate(() => ({
      chibi: typeof window.__melodia.player.m.pose === 'function',
      shrineCount: window.__melodia.activities.pois.filter(p => p.type === 'shrine').length,
      uniforms: Object.keys(window.__melodia.world.uniforms),
      legacyTerrain: !!window.__melodia.world.terrainMat.isMeshLambertMaterial,
      chladni: window.__melodia.world.uniforms.uChladni.value,
      caustics: window.__melodia.world.uniforms.uCaustics.value,
      heritageTimeline: window.__melodia.activities.shrineTimeline.sample(2).values,
      painterly: !!window.__melodia.painterly,
      postfx: !!window.__melodia.postfx,
      worldexp: !!window.__melodia.world.worldExpansionEnabled,
      destinations: window.__melodia.activities.pois.filter(p => p.type === 'destination').length,
      paletteSize: window.__melodia.world.terrainMat.gradientMap?.image?.data?.length || 0,
      bellflowers: window.__melodia.world.hubGroup.children.filter(o => o.name.startsWith('RW_Bellflower_Plaza_')).length,
      flowerParts: window.__melodia.world.props.flower.parts.length,
      groveStatus: window.__melodia.world.groveStatus,
      groveCounts: window.__melodia.world.groveCounts,
      flowerbedEnabled: window.__melodia.world.flowerbedsEnabled,
      boxLanterns: window.__melodia.world.hubGroup.children.filter(o => o.isMesh && o.geometry.type === 'BoxGeometry' &&
        o.geometry.parameters.width === 0.5 && o.geometry.parameters.height === 0.6 &&
        o.geometry.parameters.depth === 0.5 && o.visible).length,
    }));
    assert.equal(before.chibi, test.chibi, test.name + ': incorrect avatar selection');
    assert.equal(before.flowerbedEnabled, test.flowerbed !== false, test.name + ': flowerbed flag not respected');
    assert.equal(before.flowerParts, test.grove === 'glb' ? 5 : test.flowerbed === false ? 1 : 3,
      test.name + ': incorrect shared flower geometry batches');
    assert.equal(before.groveStatus, test.grove || 'off', test.name + ': wrong Grove status');
    if (test.grove === 'glb') {
      assert.deepEqual(before.groveCounts, { flower: 5, bush: 3, grass: 2 },
        test.name + ': improper merged material groups');
    }
    const expectedFlowers = test.bellflower === false ? 0 : 4;
    assert.equal(before.bellflowers, expectedFlowers, test.name + ': incorrect bellflower count');
    assert.equal(before.boxLanterns, 12 - expectedFlowers, test.name + ': original lantern fallback mismatch');
    assert.equal(before.legacyTerrain, !!test.legacy, test.name + ': wrong environment shading');
    assert.equal(before.painterly, !!test.painterly, test.name + ': wrong painterly state');
    assert.equal(before.postfx, !!test.postfx, test.name + ': unexpected postprocessing state');
    assert.equal(before.worldexp, !!test.worldexp, test.name + ': world expansion flag mismatch');
    if (test.worldexp) assert.ok(before.destinations >= 16, test.name + ': destination POIs not generated');
    else assert.equal(before.destinations, 0, test.name + ': default map received opt-in destinations');
    if (test.npr) assert.equal(before.paletteSize, 12, test.name + ': missing RGB NPR gradient');
    else if (!test.legacy) assert.equal(before.paletteSize, 3, test.name + ': v1 gradient regression');
    if (test.legacy) {
      assert.equal(before.chladni, 0, 'legacy Chladni strength');
      assert.equal(before.caustics, 0, 'legacy caustics strength');
    }
    assert.ok(before.shrineCount > 0, test.name + ': no shrines to validate');
    assert.ok(Math.abs(before.heritageTimeline.yaw) < 0.001, test.name + ': timeline yaw wrong');
    assert.ok(Math.abs(before.heritageTimeline.rise) < 0.001, test.name + ': timeline lift wrong');
    assert.ok(before.uniforms.includes('uChladni') && before.uniforms.includes('uCaustics'),
      test.name + ': shader uniforms missing');
    if (test.shrine) {
      await page.waitForFunction(() => window.__melodia.activities.pois.some(
        p => p.type === 'shrine' && !!p.assetVisual
      ), null, { timeout: 45000 });
    }
    if (test.tune) {
      await page.waitForFunction(() => window.__melodiaShaderTuner?.enabled === true, null, { timeout: 10000 });
      const tuning = await page.evaluate(() => {
        const lab = window.__melodiaShaderTuner;
        lab.apply({
          strength: 0.41, radius: 3, anisotropy: 2.6,
          edgeProtect: 3.5, shadow: 0.62, ink: 0.73, scale: 0.45,
        }, 'custom');
        const u = window.__melodia.painterly.material.uniforms;
        return {
          strength: u.uStrength.value, radius: u.uRadius.value,
          anisotropy: u.uAnisotropy.value, edge: u.uEdgeProtect.value,
          scale: window.__melodia.painterly.scale,
          tint: lab.state().shadow, ink: lab.state().ink,
          url: location.search,
          sliders: lab.panel.shadowRoot.querySelectorAll('input[type=range]').length,
        };
      });
      assert.equal(tuning.strength, 0.41);
      assert.equal(tuning.radius, 3);
      assert.equal(tuning.anisotropy, 2.6);
      assert.equal(tuning.edge, 3.5);
      assert.equal(tuning.scale, 0.45);
      assert.equal(tuning.tint, 0.62);
      assert.equal(tuning.ink, 0.73);
      assert.equal(tuning.sliders, 7);
      assert.match(tuning.url, /paint=0.41/);
      assert.match(tuning.url, /ink=0.73/);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => !!window.__melodiaShaderTuner?.enabled && !document.querySelector('#play').disabled, null, { timeout: 90000 });
      const persisted = await page.evaluate(() => window.__melodiaShaderTuner.state());
      assert.equal(persisted.strength, 0.41, 'reload retained strength');
      assert.equal(persisted.ink, 0.73, 'reload retained ink');
    }
    await page.locator('#play').click();
    await page.waitForFunction(() => window.__melodia.started &&
      window.__melodia.renderer.info.render.calls > 0, null, { timeout: 30000 });
    // Capture one comparable Petal Cantata shot in both modes for art review.
    // This is a browser beauty reference, not a claim of human aesthetic approval.
    if (process.env.RW_SCREENSHOT_DIR &&
        (test.name === 'desktop-petal-cantata' || test.name === 'desktop-original-flowers' ||
         test.name === 'desktop-grove-glb' || test.name === 'desktop-npr-colour-review' ||
         test.name === 'desktop-default')) {
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
