// Verify the ORM channel-isolation fix for roughness / metallic / ao.
// Proves the three modes now render DIFFERENT things, and that they differ from PBR.
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const URL = 'http://localhost:8123/wix/realtime-3d-viewer.html';
const OUT = 'C:\\EnvironmentPortfolio\\browser-test\\viewer_modes';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.mkdirSync(OUT, { recursive: true });

const sha = (b) => crypto.createHash('sha256').update(b).digest('hex').slice(0, 12);

(async () => {
  const report = { url: URL, modes: {}, errors: [], shader_errors: [] };
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars'],
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 1 });
    page.on('console', (m) => {
      const t = m.text();
      if (m.type() === 'error') report.errors.push(t);
      if (/shader|glsl|program/i.test(t) && /error|fail/i.test(t)) report.shader_errors.push(t);
    });
    page.on('pageerror', (e) => report.errors.push('PAGEERROR: ' + e.message));

    await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
    await sleep(3500);

    // Find the mode controls the page actually exposes.
    const modeIds = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll('[data-mode]'));
      return els.map((e) => e.getAttribute('data-mode')).filter(Boolean);
    });
    report.available_modes = modeIds;

    for (const mode of ['pbr', 'roughness', 'metallic', 'ao', 'normal', 'clay']) {
      const clicked = await page.evaluate((m) => {
        const el = document.querySelector(`[data-mode="${m}"]`);
        if (!el) return false;
        el.click();
        return true;
      }, mode);
      if (!clicked) { report.modes[mode] = { clicked: false }; continue; }
      await sleep(1600);
      const file = path.join(OUT, `mode_${mode}.png`);
      await page.screenshot({ path: file });
      const buf = fs.readFileSync(file);
      report.modes[mode] = { clicked: true, bytes: buf.length, sha256_12: sha(buf) };
      console.log(`  ${mode.padEnd(10)} -> ${sha(buf)}  ${buf.length} bytes`);
    }

    // Distinctness check across the three fixed modes + their reference.
    const h = (m) => (report.modes[m] && report.modes[m].sha256_12) || null;
    report.distinct = {
      roughness_vs_metallic: h('roughness') !== h('metallic'),
      roughness_vs_ao: h('roughness') !== h('ao'),
      metallic_vs_ao: h('metallic') !== h('ao'),
      roughness_vs_pbr: h('roughness') !== h('pbr'),
      metallic_vs_pbr: h('metallic') !== h('pbr'),
      ao_vs_pbr: h('ao') !== h('pbr'),
    };
  } catch (e) {
    report.fatal = e && e.message ? e.message : String(e);
  } finally {
    fs.writeFileSync(path.join(OUT, 'modes_report.json'), JSON.stringify(report, null, 2));
    await browser.close();
  }
  console.log('---REPORT---');
  console.log(JSON.stringify(report, null, 2));
})();
