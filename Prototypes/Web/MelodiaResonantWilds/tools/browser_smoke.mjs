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
  // Old shared URLs must remain playable; the retired filter flag is ignored.
  { name: 'retired-kuwahara-flag', query: '?npr=v2&kuwahara=1&avatar=chibi&shrine=glb', chibi: true, shrine: true, mobile: false, npr: true, retired: true },
  { name: 'mobile-npr-v2', query: '?npr=v2', chibi: false, shrine: false, mobile: true, npr: true },
  { name: 'desktop-live-tuner', query: '?npr=v2&avatar=chibi&shrine=glb&tune=1&look=soft', chibi: true, shrine: true, mobile: false, npr: true, tune: true },
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
    const heritage = await page.locator('.title-sigil img, .shrine-crest img').count();
    assert.equal(heritage, 4, test.name + ': four reused site SVG ornaments absent');
    const loadedHeritage = await page.evaluate(async () => {
      const images = [...document.querySelectorAll('.title-sigil img, .shrine-crest img')];
      await Promise.all(images.map((img) => img.decode()));
      return images.every((img) => img.naturalWidth > 0);
    });
    assert.ok(loadedHeritage, test.name + ': a reused site SVG failed to load');
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
      retiredPostFX: 'painterly' in window.__melodia,
      paletteSize: window.__melodia.world.terrainMat.gradientMap?.image?.data?.length || 0,
    }));
    assert.equal(before.chibi, test.chibi, test.name + ': incorrect avatar selection');
    assert.equal(before.legacyTerrain, !!test.legacy, test.name + ': wrong environment shading');
    assert.equal(before.retiredPostFX, false, test.name + ': retired GPU postprocess still present');
    if (test.npr) {
      const uniforms = await page.evaluate(() => {
        const sh = window.__melodia.world.terrainMat.userData.melodiaNPRShader;
        return sh ? {
          hardness: sh.uniforms.uBandHardness?.value,
          depth: sh.uniforms.uBandShadowDepth?.value,
          shaderContainsRGB: sh.fragmentShader.includes('shadowRGB'),
          preservedWorldRipple: sh.fragmentShader.includes('rwChladni'),
        } : null;
      });
      assert.ok(uniforms, test.name + ': RGB toon shader did not compile');
      assert.ok(uniforms.shaderContainsRGB && uniforms.preservedWorldRipple,
        test.name + ': toon bands and world ripple shader hooks must compose');
      if (!test.tune) {
        assert.equal(uniforms.hardness, 0.98, test.name + ': hard bands not default');
        assert.equal(uniforms.depth, 0.39, test.name + ': dark band not default');
      }
    }
    if (test.npr) assert.equal(before.paletteSize, 12, test.name + ': missing RGB NPR gradient');
    else if (!test.legacy) assert.equal(before.paletteSize, 3, test.name + ': v1 gradient regression');
    if (test.legacy) {
      assert.equal(before.chladni, 0, 'legacy Chladni strength');
      assert.equal(before.caustics, 0, 'legacy caustics strength');
    }
    assert.ok(before.shrineCount > 0, test.name + ': no shrines to validate');
    assert.ok(Math.abs(before.heritageTimeline.yaw) < 0.001, test.name + ': site timeline yaw wrong');
    assert.ok(Math.abs(before.heritageTimeline.rise) < 0.001, test.name + ': site timeline rise wrong');
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
        lab.apply({ shadow: 0.62, ink: 0.73, hardness: 0.99, threshold: 0.53, depth: 0.31 }, 'custom');
        const sh = window.__melodia.world.terrainMat.userData.melodiaNPRShader;
        return {
          tint: lab.state().shadow, ink: lab.state().ink,
          url: location.search,
          sliders: lab.panel.shadowRoot.querySelectorAll('input[type=range]').length,
          band: {
            hardness: sh.uniforms.uBandHardness.value,
            threshold: sh.uniforms.uBandThreshold.value,
            depth: sh.uniforms.uBandShadowDepth.value,
          },
        };
      });
      assert.equal(tuning.tint, 0.62);
      assert.equal(tuning.ink, 0.73);
      assert.equal(tuning.sliders, 5);
      assert.equal(tuning.band.hardness, 0.99);
      assert.equal(tuning.band.threshold, 0.53);
      assert.equal(tuning.band.depth, 0.31);
      assert.match(tuning.url, /ink=0.73/);
      assert.match(tuning.url, /hard=0.99/);
      assert.match(tuning.url, /dark=0.31/);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => !!window.__melodiaShaderTuner?.enabled && !document.querySelector('#play').disabled, null, { timeout: 90000 });
      const persisted = await page.evaluate(() => window.__melodiaShaderTuner.state());
      assert.equal(persisted.ink, 0.73, 'reload retained ink');
      assert.equal(persisted.hardness, 0.99, 'reload retained hard band');
      assert.equal(persisted.depth, 0.31, 'reload retained deep shadow');
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
