// Resonant Wilds PWA cache. Keep shader, character, icon and GLB updates fresh.
// The browser game remains playable online even if optional preview assets fail.
const CACHE = 'resonant-wilds-v13-20261029-nikki-ability';
const ASSETS = [
  './', './index.html', './style.css', './manifest.json',
  './icon-192.png', './icon-512.png',
  './js/main.js', './js/game.js', './js/audio.js', './js/rhythm.js',
  './js/world.js', './js/entities.js', './js/cel.js', './js/painterly.js', './js/npr-tuner.js', './js/chibi.js', './js/mixamo.js', './js/heritage-timeline.js',
  './js/asset-loader.js', './js/bellflower.js', './js/flowerbeds.js', './js/openworld.js', './js/postfx.js', './js/grove.js',
  './js/playground.js',
  './js/flags.js',
  './js/combat.js', './js/loot.js', './js/echo.js', './js/encore.js',
  './js/activities.js', './js/progress.js', './js/ui.js',
  './js/player.js', './js/design.js', './js/fx.js', './js/util.js',
  './js/generated/ue_data.js',
  './vendor/three.module.min.js',
  './vendor/examples/jsm/loaders/GLTFLoader.js',
  './vendor/examples/jsm/utils/BufferGeometryUtils.js',
  './vendor/postprocessing/EffectComposer.js', './vendor/postprocessing/MaskPass.js',
  './vendor/postprocessing/OutlinePass.js', './vendor/postprocessing/OutputPass.js',
  './vendor/postprocessing/Pass.js', './vendor/postprocessing/RenderPass.js',
  './vendor/postprocessing/ShaderPass.js', './vendor/postprocessing/UnrealBloomPass.js',
  './vendor/shaders/CopyShader.js', './vendor/shaders/FXAAShader.js',
  './vendor/shaders/LuminosityHighPassShader.js', './vendor/shaders/OutputShader.js',
  './assets/models/resonance-shrine.glb',
  './assets/heritage/chromatic-orbit.svg', './assets/heritage/note-medallion.svg',
  './assets/heritage/filigree-frame.svg', './assets/heritage/resonance-core.svg',
  './assets/models/harmonic-grove-37.glb',
  './assets/models/mixamo-hero.glb',
  './assets/icons/charm_brooch.svg', './assets/icons/charm_clef_pendant.svg',
  './assets/icons/charm_music_box.svg', './assets/icons/charm_shell_charm.svg',
  './assets/icons/echo_phrase.svg',
  './assets/icons/gloves_gauntlets.svg', './assets/icons/gloves_gloves.svg', './assets/icons/gloves_mitts.svg',
  './assets/icons/gown_coat.svg', './assets/icons/gown_dress.svg', './assets/icons/gown_gown.svg',
  './assets/icons/gown_kimono.svg', './assets/icons/gown_robe.svg',
  './assets/icons/head_circlet.svg', './assets/icons/head_ribbon.svg', './assets/icons/head_sun_hat.svg',
  './assets/icons/head_tiara.svg', './assets/icons/head_veil.svg',
  './assets/icons/instrument_baton.svg', './assets/icons/instrument_chime_staff.svg',
  './assets/icons/instrument_flute.svg', './assets/icons/instrument_harp.svg',
  './assets/icons/instrument_lyre.svg', './assets/icons/instrument_violin_bow.svg',
  './assets/icons/motif_arcane.svg', './assets/icons/motif_forte.svg', './assets/icons/motif_gale.svg',
  './assets/icons/motif_radiant.svg', './assets/icons/motif_stone.svg', './assets/icons/motif_tide.svg',
  './assets/icons/motif_umbral.svg',
  './assets/icons/rarity_common.svg', './assets/icons/rarity_opus.svg', './assets/icons/rarity_resonant.svg',
  './assets/icons/rarity_tuned.svg', './assets/icons/rarity_virtuoso.svg',
  './assets/icons/shoes_boots.svg', './assets/icons/shoes_heels.svg', './assets/icons/shoes_slippers.svg',
  './assets/icons/slot_charm.svg', './assets/icons/slot_gloves.svg', './assets/icons/slot_gown.svg',
  './assets/icons/slot_head.svg', './assets/icons/slot_instrument.svg', './assets/icons/slot_shoes.svg',
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
