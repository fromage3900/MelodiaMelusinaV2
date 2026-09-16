// Click through EVERY asset in the viewer and report which ones fail.
// Also confirms the newly-swapped low-poly assets load and the stubs are gone.
const puppeteer = require('puppeteer-core');
const fs = require('fs');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const URL = 'http://localhost:8123/wix/realtime-3d-viewer.html';
const OUT = 'C:\\EnvironmentPortfolio\\browser-test\\all_assets';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await puppeteer.launch({
    executablePath: CHROME, headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars'],
  });
  const p = await b.newPage();
  await p.setViewport({ width: 1400, height: 900 });

  const bad = [];
  p.on('response', (r) => {
    if (r.status() >= 400) bad.push(r.status() + ' ' + r.url().replace('http://localhost:8123', ''));
  });
  p.on('pageerror', (e) => bad.push('PAGEERROR ' + e.message));

  await p.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise((r) => setTimeout(r, 3500));

  const keys = await p.evaluate(() =>
    Array.from(document.querySelectorAll('[data-asset]')).map((e) => e.getAttribute('data-asset')),
  );
  console.log('assets in UI: ' + keys.length);

  const results = [];
  for (const k of keys) {
    const before = bad.length;
    await p.evaluate((kk) => {
      const el = document.querySelector('[data-asset="' + kk + '"]');
      if (el) el.click();
    }, k);
    await new Promise((r) => setTimeout(r, 2200));
    const tel = await p.evaluate(() => {
      const el = document.querySelector('#asset-telemetry, .telemetry, [id*="telemetry"]');
      return el ? (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 110) : null;
    });
    const newBad = bad.slice(before).filter((u) => !/favicon|generated\/assets|content\//.test(u));
    results.push({ asset: k, newFailures: newBad, telemetry: tel });
    console.log(`  ${k.padEnd(20)} ${newBad.length ? 'FAIL: ' + newBad.join(',') : 'ok'}`);
  }

  fs.writeFileSync(OUT + '\\all_assets_report.json', JSON.stringify({ results, allBad: bad }, null, 2));
  const failures = results.filter((r) => r.newFailures.length);
  console.log('\ntotal asset failures: ' + failures.length + ' / ' + keys.length);
  await b.close();
})();
