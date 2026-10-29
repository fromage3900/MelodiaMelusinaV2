// Nikki-lens live itinerary smoke (desktop Chromium stand-in for phone Safari).
// Does NOT claim Safari/offline owner QA. Proves Ability Outfit + worldexp loops
// on the published flag pack before the owner device pass.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.GAME_URL;
if (!base) throw new Error('GAME_URL is required');
const root = base.replace(/\?.*$/, '').replace(/\/?$/, '/');
const url = `${root}?worldexp=1&postfx=1&dressing=dense&nikkilook=1&daycycle=1`;

const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--enable-webgl', '--use-gl=angle',
    '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});

const steps = [];
const pass = (name, detail = '') => {
  steps.push({ name, ok: true, detail });
  console.log('PASS', name, detail || '');
};
const fail = (name, err) => {
  steps.push({ name, ok: false, detail: String(err) });
  throw err;
};

try {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    serviceWorkers: 'block',
  });
  const page = await context.newPage();
  const failures = [];
  page.on('pageerror', (e) => failures.push(e.message));

  // 1. Hub boot with Nikki flag pack
  const res = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  assert.ok(res?.ok(), 'page HTTP error');
  await page.waitForFunction(() => !!window.__melodia && !document.querySelector('#play').disabled, null, { timeout: 90000 });
  const boot = await page.evaluate(() => ({
    worldexp: !!window.__melodia.world.worldExpansionEnabled,
    destinations: window.__melodia.activities.pois.filter((p) => p.type === 'destination').length,
    abilities: window.__melodia.activities.pois
      .filter((p) => p.abilityOutfit)
      .map((p) => ({ type: p.type, name: p.name, abilityOutfit: p.abilityOutfit })),
  }));
  assert.equal(boot.worldexp, true, 'worldexp flag');
  assert.ok(boot.destinations >= 16, `destinations ${boot.destinations}`);
  const ids = new Set(boot.abilities.map((a) => a.abilityOutfit));
  for (const id of ['mist_float', 'prism_veil', 'nightbell_glide']) {
    assert.ok(ids.has(id), `missing ability outfit POI ${id}`);
  }
  pass('1-hub-boot', `${boot.destinations} destinations · ${ids.size} ability outfits`);

  await page.locator('#play').click();
  await page.waitForFunction(() => window.__melodia.started, null, { timeout: 30000 });
  pass('2-play-start');

  // 3. Ability Outfit locked deny → equip shoes → ready
  const outfitBeat = await page.evaluate(() => {
    const g = window.__melodia;
    const mist = g.activities.pois.find((p) => p.abilityOutfit === 'mist_float' && p.type === 'destination');
    if (!mist) return { error: 'no mist_float destination' };
    // Clear shoes/gown so the gate is locked.
    const eq = g.profile.equipment || {};
    const savedShoes = eq.shoes || null;
    const savedGown = eq.gown || null;
    delete eq.shoes;
    delete eq.gown;
    g.player.recalc();
    const locked = !g.activities._wearsAbilityFor(mist);
    const label = (() => {
      // Mimic nearestInteract destination branch
      if (mist.needsFloat && !g.activities._wearsAbilityFor(mist)) {
        const ab = g.activities._abilityFor(mist);
        return ab ? `Ability Outfit · ${ab.name}` : 'Equip float outfit ✧';
      }
      return 'Collect Resonance Dew ✧';
    })();
    // Grant a shoes piece into equipment (Ability Outfit beat).
    eq.shoes = savedShoes || {
      uid: 99001, slot: 'shoes', name: 'Mist Slippers', rarity: 2, ilvl: 8,
      base: 'Slippers', family: 'melee', icon: 'shoes_slippers', affixes: [],
    };
    g.player.recalc();
    g.activities.onAbilityOutfitEquipped('shoes');
    const ready = g.activities._wearsAbilityFor(mist);
    // Unlock ceremony (first open path)
    const first = g.activities._unlockAbilityOutfit(g.activities._abilityFor(mist), mist.name);
    if (savedGown) eq.gown = savedGown;
    g.save();
    return {
      locked, ready, label, first,
      unlocked: [...(g.profile.abilityOutfits || [])],
      mistName: mist.name,
    };
  });
  assert.ok(!outfitBeat.error, outfitBeat.error);
  assert.equal(outfitBeat.locked, true, 'gate should lock without shoes');
  assert.match(outfitBeat.label, /Ability Outfit · Mist Float/);
  assert.equal(outfitBeat.ready, true, 'shoes should satisfy Mist Float');
  assert.ok(outfitBeat.unlocked.includes('mist_float'), 'mist_float recorded');
  pass('3-ability-outfit-beat', `${outfitBeat.mistName} · unlock=${outfitBeat.first}`);

  // 4. Wardrobe catalogue exposes all three Ability Outfits
  await page.evaluate(() => window.__melodia.ui.open('wardrobe'));
  await page.waitForTimeout(200);
  const wardrobe = await page.evaluate(() => {
    const body = document.querySelector('#panel .panel-body, #panel-body, .panel .card');
    const text = document.getElementById('panel')?.innerText || document.body.innerText;
    return {
      hasTitle: /Ability Outfits/i.test(text),
      hasMist: /Mist Float/i.test(text),
      hasPrism: /Prism Veil/i.test(text),
      hasNight: /Nightbell Glide/i.test(text),
    };
  });
  assert.ok(wardrobe.hasTitle && wardrobe.hasMist && wardrobe.hasPrism && wardrobe.hasNight, JSON.stringify(wardrobe));
  pass('4-wardrobe-catalogue');

  // 5. Ethereal veils named for Ability Outfits
  const veils = await page.evaluate(() => window.__melodia.activities.pois
    .filter((p) => p.type === 'ariagate' && p.abilityOutfit)
    .map((p) => p.name));
  assert.ok(veils.some((n) => /Mist Float Veil/.test(n)));
  assert.ok(veils.some((n) => /Prism Veil Veil|Prism Veil/.test(n)));
  assert.ok(veils.some((n) => /Nightbell Glide Veil/.test(n)));
  pass('5-ethereal-veils', veils.join(', '));

  // 6. Console clean
  assert.deepEqual(failures, [], failures.join('; '));
  pass('6-no-console-errors');

  console.log('Nikki live itinerary (desktop stand-in): PASS');
  console.log(JSON.stringify({ steps, note: 'Safari/offline owner QA still required for browser-approved' }, null, 2));
  await context.close();
} catch (err) {
  console.error('Nikki live itinerary FAIL', err);
  process.exitCode = 1;
} finally {
  await browser.close();
}
