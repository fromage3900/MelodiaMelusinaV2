// Resonant Wilds daily leaderboard: a small dependency-free Node server.
//   node server/server.mjs            (PORT=8787 by default, DATA_DIR=./server/data)
//   POST /api/daily  { date, name, cleared, time, tier, kills }   keep each player's best per day
//   GET  /api/daily?date=YYYY-MM-DD                              top 20 for that day
// Input is validated and size-limited. Serve the game from the same origin, or set ALLOW_ORIGIN.
import http from 'node:http';
import { promises as fs } from 'node:fs';
import path from 'node:path';

const PORT = Number(process.env.PORT || 8787);
const DATA_DIR = process.env.DATA_DIR || path.join(path.dirname(new URL(import.meta.url).pathname), 'data');
const ALLOW_ORIGIN = process.env.ALLOW_ORIGIN || '*';
const FILE = path.join(DATA_DIR, 'daily.json');
const MAX_BODY = 2048;
const MAX_PER_DAY = 500;

async function load() {
  try { return JSON.parse(await fs.readFile(FILE, 'utf8')); } catch { return {}; }
}
async function save(db) {
  await fs.mkdir(DATA_DIR, { recursive: true });
  const tmp = FILE + '.tmp';
  await fs.writeFile(tmp, JSON.stringify(db));
  await fs.rename(tmp, FILE);
}

// Ordering: cleared runs first, then fastest time, then most slimes.
const rank = (a, b) => (b.cleared - a.cleared) || (a.time - b.time) || (b.kills - a.kills);

function validate(e) {
  const isDate = typeof e.date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(e.date);
  const name = typeof e.name === 'string' ? e.name.replace(/[^\p{L}\p{N} _-]/gu, '').trim().slice(0, 16) : '';
  const ok = isDate && name.length >= 1 && typeof e.cleared === 'boolean'
    && Number.isInteger(e.time) && e.time >= 0 && e.time <= 900
    && Number.isInteger(e.tier) && e.tier >= 1 && e.tier <= 30
    && Number.isInteger(e.kills) && e.kills >= 0 && e.kills <= 999;
  return ok ? { date: e.date, name, cleared: e.cleared, time: e.time, tier: e.tier, kills: e.kills } : null;
}

function send(res, code, body) {
  res.writeHead(code, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': ALLOW_ORIGIN,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Cache-Control': 'no-store',
  });
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on('data', (c) => { size += c.length; if (size > MAX_BODY) { reject(new Error('too large')); req.destroy(); } else chunks.push(c); });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

// One write at a time, so concurrent submits can't drop each other's entries.
let queue = Promise.resolve();
const serial = (fn) => (queue = queue.then(fn, fn));

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  if (req.method === 'OPTIONS') return send(res, 204, {});
  if (url.pathname !== '/api/daily') return send(res, 404, { error: 'not found' });

  if (req.method === 'GET') {
    const date = url.searchParams.get('date') || '';
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return send(res, 400, { error: 'bad date' });
    const db = await load();
    const top = (db[date] || []).slice().sort(rank).slice(0, 20);
    return send(res, 200, { date, top });
  }

  if (req.method === 'POST') {
    let entry;
    try { entry = validate(JSON.parse(await readBody(req))); } catch { return send(res, 400, { error: 'bad body' }); }
    if (!entry) return send(res, 400, { error: 'invalid entry' });
    await serial(async () => {
      const db = await load();
      const list = db[entry.date] || [];
      const i = list.findIndex((x) => x.name === entry.name);
      if (i < 0) list.push(entry);
      else if (rank(entry, list[i]) < 0) list[i] = entry;
      db[entry.date] = list.sort(rank).slice(0, MAX_PER_DAY);
      await save(db);
    });
    return send(res, 200, { ok: true });
  }
  return send(res, 405, { error: 'method not allowed' });
});

server.listen(PORT, () => console.log(`Resonant Wilds leaderboard on :${PORT} (data: ${DATA_DIR})`));
