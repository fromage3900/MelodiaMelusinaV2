// Lane 3 runtime verification: does the Auriga GLB actually load and drive the timeline?
// Reports what it OBSERVES. A failure is reported as a failure, never smoothed over.
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const URL = 'https://fromage3900.github.io/my-site/tools/fromage-webgl-kit/prototypes/product-motion-lab/';
const OUT = 'C:\\EnvironmentPortfolio\\browser-test\\lane3';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const report = { url: URL, errors: [], warnings: [], steps: [] };
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars'],
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 1 });
    page.on('console', (m) => {
      if (m.type() === 'error') report.errors.push(m.text());
      else if (m.type() === 'warning') report.warnings.push(m.text());
    });
    page.on('pageerror', (e) => report.errors.push('PAGEERROR: ' + e.message));
    page.on('requestfailed', (r) => report.errors.push('REQFAIL: ' + r.url() + ' ' + (r.failure() && r.failure().errorText)));

    await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });

    // The loader writes its outcome into #assetStatus. Wait for a terminal state.
    const status = await page.waitForFunction(
      () => {
        const el = document.getElementById('assetStatus');
        if (!el) return false;
        const t = el.textContent || '';
        return t.includes('GLB loaded') || t.includes('GLB unavailable') ? t : false;
      },
      { timeout: 45000 },
    ).then((h) => h.jsonValue()).catch(() => 'TIMEOUT: #assetStatus never reached a terminal state');
    report.asset_status = status;
    report.glb_loaded = typeof status === 'string' && status.includes('GLB loaded');

    // Drive the timeline through the slider the page actually exposes.
    async function driveTo(t, label) {
      await page.evaluate((val) => {
        const s = document.getElementById('timeline');
        s.value = String(val);
        s.dispatchEvent(new Event('input', { bubbles: true }));
        s.dispatchEvent(new Event('change', { bubbles: true }));
      }, t);
      await sleep(900);
      const p = path.join(OUT, `lane3_t${String(t).replace('.', '_')}.png`);
      await page.screenshot({ path: p });
      const state = await page.evaluate(() => ({
        timeline: document.getElementById('timelineValue') ? document.getElementById('timelineValue').textContent : null,
        diagnostics: document.getElementById('diagnostics') ? document.getElementById('diagnostics').textContent.slice(0, 300) : null,
      }));
      report.steps.push({ label, t, file: path.basename(p), state });
      console.log(`  t=${t} (${label}) ->`, JSON.stringify(state.timeline));
    }

    await driveTo(0, 'start');
    await driveTo(0.5, 'mid');
    await driveTo(1, 'end');
    await driveTo(0, 'return-to-start');

    // Did the canvas actually produce pixels, or is it a blank frame?
    report.canvas = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      if (!c) return { present: false };
      return { present: true, width: c.width, height: c.height };
    });
  } catch (e) {
    report.fatal = e && e.message ? e.message : String(e);
  } finally {
    fs.writeFileSync(path.join(OUT, 'lane3_report.json'), JSON.stringify(report, null, 2));
    await browser.close();
  }
  console.log('---REPORT---');
  console.log(JSON.stringify(report, null, 2));
})();
