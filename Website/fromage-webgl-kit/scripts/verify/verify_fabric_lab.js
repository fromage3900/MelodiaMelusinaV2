// Real-browser verification of the Fabric Material Lab.
// Produces the captures and measurements the Evidence section asks for.
const puppeteer = require('puppeteer-core');
const fs = require('fs');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const URL = 'http://localhost:8126/tools/fromage-webgl-kit/prototypes/fabric-material-lab/';
const OUT = 'C:\\EnvironmentPortfolio\\browser-test\\fabric_lab';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars'],
  });
  const report = { url: URL, errors: [], requests404: [], presets: [], controls: {}, captures: [] };

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  page.on('console', (m) => { if (m.type() === 'error') report.errors.push(m.text().slice(0, 160)); });
  page.on('pageerror', (e) => report.errors.push('PAGEERROR ' + e.message.slice(0, 160)));
  page.on('response', (r) => { if (r.status() >= 400) report.requests404.push(r.status() + ' ' + r.url().split('/').pop()); });

  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise((r) => setTimeout(r, 6000));

  // 1. did it initialise and is anything drawn?
  report.init = await page.evaluate(() => ({
    preset: document.getElementById('p-preset').textContent.trim(),
    diag: document.getElementById('diag').textContent.trim(),
    fallbackVisible: getComputedStyle(document.getElementById('fallback')).display !== 'none',
    presetButtons: document.querySelectorAll('.preset').length,
    canvasPixels: (() => { const c = document.querySelector('canvas'); return c ? c.width + 'x' + c.height : 'none'; })(),
  }));

  // capture helper
  const shot = async (name) => {
    const f = `${OUT}\\${name}.png`;
    await page.screenshot({ path: f });
    report.captures.push({ name, bytes: fs.statSync(f).size });
    return f;
  };

  await shot('01_desktop_default');

  // 2. cycle every preset, capture one comparison pair, record the state each time
  const ids = await page.evaluate(() => Array.from(document.querySelectorAll('.preset'))
    .map((b) => b.querySelector('span').textContent.trim()));
  for (let i = 0; i < ids.length; i++) {
    await page.evaluate((n) => document.querySelectorAll('.preset')[n].click(), i);
    await new Promise((r) => setTimeout(r, 2600));
    const st = await page.evaluate(() => ({
      preset: document.getElementById('p-preset').textContent.trim(),
      state: document.getElementById('state').textContent.trim().slice(0, 90),
    }));
    report.presets.push({ label: ids[i], active: st.preset });
    if (i === 1) await shot('02_satin_like');
  }
  console.log('presets:', report.presets.map((p) => p.label + '=' + p.active).join('  '));

  // 3. grazing-angle inspection
  await page.evaluate(() => document.getElementById('b-light').click());
  await new Promise((r) => setTimeout(r, 2600));
  await shot('03_grazing_angle');
  report.controls.grazingLabel = await page.evaluate(() => document.getElementById('p-light').textContent.trim());

  // 4. controls actually move the material
  await page.evaluate(() => {
    const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); };
    set('rough', '1.8'); set('normal', '2.1'); set('sheen', '0.4');
  });
  await new Promise((r) => setTimeout(r, 1800));
  report.controls.afterSliders = await page.evaluate(() => document.getElementById('state').textContent.trim());
  await shot('04_controls_changed');

  // 5. wireframe
  await page.evaluate(() => document.getElementById('b-wire').click());
  await new Promise((r) => setTimeout(r, 1800));
  await shot('05_wireframe');
  await page.evaluate(() => document.getElementById('b-wire').click());

  // 6. phone width
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
  await new Promise((r) => setTimeout(r, 2600));
  report.mobile = await page.evaluate(() => ({
    canvasW: document.querySelector('canvas').getBoundingClientRect().width,
    docScrollW: document.documentElement.scrollWidth,
    innerW: window.innerWidth,
    overflows: document.documentElement.scrollWidth > window.innerWidth + 1,
  }));
  await shot('06_phone_390');

  // 7. exported state is valid JSON
  report.exportedState = await page.evaluate(() => document.getElementById('state').textContent.trim());
  try { JSON.parse(report.exportedState); report.stateParses = true; }
  catch (e) { report.stateParses = false; }

  report.finalDiag = await page.evaluate(() => document.getElementById('diag').textContent.trim());

  fs.writeFileSync(`${OUT}\\report.json`, JSON.stringify(report, null, 2));
  console.log('\n--- RESULT ---');
  console.log(JSON.stringify({
    init: report.init, errors: report.errors.length, requests404: report.requests404,
    controls: report.controls, mobile: report.mobile,
    stateParses: report.stateParses, finalDiag: report.finalDiag,
    captures: report.captures,
  }, null, 2));
  await browser.close();
})();
