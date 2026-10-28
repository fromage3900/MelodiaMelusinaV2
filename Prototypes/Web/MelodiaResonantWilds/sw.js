// Resonant Wilds PWA cache v2. Keep shader, character and GLB updates fresh.
// The browser game remains playable online even if optional preview assets fail.
const CACHE = 'resonant-wilds-v5-20261027-npr-tune';
const ASSETS = [
  './', './index.html', './style.css', './manifest.json',
  './icon-192.png', './icon-512.png',
  './js/main.js', './js/game.js', './js/audio.js', './js/rhythm.js',
  './js/world.js', './js/entities.js', './js/cel.js', './js/painterly.js', './js/npr-tuner.js', './js/chibi.js',
  './js/asset-loader.js', './js/combat.js', './js/loot.js',
  './js/activities.js', './js/progress.js', './js/ui.js',
  './js/player.js', './js/design.js', './js/fx.js', './js/util.js',
  './js/generated/ue_data.js',
  './vendor/three.module.min.js',
  './vendor/examples/jsm/loaders/GLTFLoader.js',
  './vendor/examples/jsm/utils/BufferGeometryUtils.js',
  './assets/models/resonance-shrine.glb',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const scope = new URL('./', self.registration.scope);
  if (url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
  const freshFirst = req.mode === 'navigate' || /\.(?:js|css|json|html)$/i.test(url.pathname);
  event.respondWith(caches.open(CACHE).then(async (cache) => {
    if (freshFirst) {
      try {
        const res = await fetch(req);
        if (res.ok) await cache.put(req, res.clone());
        return res;
      } catch (err) {
        // The cached index is still a valid fallback when navigating offline with flags.
        return (await cache.match(req)) ||
          (req.mode === 'navigate' ? await cache.match('./index.html') : null) ||
          Response.error();
      }
    }
    const hit = await cache.match(req);
    if (hit) return hit;
    const res = await fetch(req);
    if (res.ok) await cache.put(req, res.clone());
    return res;
  }));
});
