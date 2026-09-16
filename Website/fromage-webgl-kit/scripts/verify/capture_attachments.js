// Capture the 5 submission attachments for the $10k industrial-loop listing.
// Deterministic: drives window.__industrialLoop.setTime/setMode rather than wall-clock.
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE = 'https://fromage3900.github.io/my-site/tools/fromage-webgl-kit/prototypes/procedural-industrial-loop/';
const OUT = 'C:\\EnvironmentPortfolio\\browser-test\\attachments';
const FRAMES = path.join(OUT, '_frames');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

for (const d of [OUT, FRAMES]) fs.mkdirSync(d, { recursive: true });

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars', '--force-device-scale-factor=1'],
  });
  const log = [];
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

    // --- stills: one per visualisation mode, capture mode (chrome-free) ---
    const STILLS = [
      ['industrial_base_hero.png', 'base', 4],
      ['industrial_structural.png', 'structural', 5.2],
      ['industrial_flow.png', 'flow', 5.2],
      ['industrial_thermal.png', 'thermal', 5.2],
    ];
    for (const [file, mode, t] of STILLS) {
      await page.goto(`${BASE}?capture=1&seed=1&mode=${mode}&t=${t}`, { waitUntil: 'networkidle2', timeout: 60000 });
      await page.waitForFunction('window.__industrialLoop && typeof window.__industrialLoop.setTime === "function"', { timeout: 30000 });
      await page.evaluate((m, tt) => { window.__industrialLoop.setMode(m); window.__industrialLoop.setTime(tt); }, mode, t);
      await sleep(1200); // let the renderer settle a couple of frames
      const p = path.join(OUT, file);
      await page.screenshot({ path: p });
      const st = await page.evaluate(() => window.__industrialLoop.getState());
      log.push({ file, mode, t, state: st, bytes: fs.statSync(p).size });
      console.log('still:', file, JSON.stringify(st));
    }

    // --- video: real-time CDP screencast of the 16s BASE loop ---
    await page.goto(`${BASE}?capture=1&seed=1&mode=base`, { waitUntil: 'networkidle2', timeout: 60000 });
    await page.waitForFunction('window.__industrialLoop && typeof window.__industrialLoop.setTime === "function"', { timeout: 30000 });
    await page.evaluate(() => { window.__industrialLoop.setSeed(1); window.__industrialLoop.setMode('base'); window.__industrialLoop.setTime(0); });
    await sleep(1000);

    const client = await page.createCDPSession();
    let n = 0;
    client.on('Page.screencastFrame', async (f) => {
      fs.writeFileSync(path.join(FRAMES, `f${String(n).padStart(5, '0')}.jpg`), Buffer.from(f.data, 'base64'));
      n += 1;
      try { await client.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch (e) {}
    });
    await client.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
    const t0 = Date.now();
    await page.evaluate(() => window.__industrialLoop.play());
    while (Date.now() - t0 < 17000) {
      await sleep(250);
      const s = await page.evaluate(() => window.__industrialLoop.getState().time);
      if (s >= 16) break;
    }
    await client.send('Page.stopScreencast');
    const elapsed = (Date.now() - t0) / 1000;
    log.push({ video_frames: n, elapsed_s: elapsed, fps: +(n / elapsed).toFixed(2) });
    console.log('screencast frames:', n, 'in', elapsed.toFixed(1), 's =', (n / elapsed).toFixed(1), 'fps');
  } catch (e) {
    console.log('ERROR:', e && e.message ? e.message : e);
    log.push({ error: String(e) });
  } finally {
    fs.writeFileSync(path.join(OUT, 'capture_log.json'), JSON.stringify(log, null, 2));
    await browser.close();
  }
})();
