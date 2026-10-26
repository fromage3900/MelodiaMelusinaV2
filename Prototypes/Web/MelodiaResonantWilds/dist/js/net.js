// Daily leaderboard client. Talks to server/server.mjs when the page declares an API
// base with <meta name="melodia-api" content="https://host">, or same-origin /api otherwise.
// With no server reachable, every call quietly does nothing and the game stays fully playable.

const meta = document.querySelector('meta[name="melodia-api"]');
const BASE = meta ? meta.content.replace(/\/$/, '') : '';

export async function postDaily(entry) {
  try {
    const res = await fetch(`${BASE}/api/daily`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(entry),
    });
    return res.ok;
  } catch { return false; }
}

export async function fetchDaily(date) {
  try {
    const res = await fetch(`${BASE}/api/daily?date=${encodeURIComponent(date)}`);
    return res.ok ? (await res.json()).top : null;
  } catch { return null; }
}
