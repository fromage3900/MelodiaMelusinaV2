// Boot: build the world behind the title screen, start audio on the first tap
// (browsers require a gesture), then hand over to the game loop.

import { Game } from './game.js';
const tuningMode = new URLSearchParams(location.search).get('tune') === '1';

const state = document.getElementById('loadstate');
const play = document.getElementById('play');

function fail(err) {
  console.error(err);
  state.textContent = 'Could not start: ' + (err && err.message ? err.message : err) + ' — try a WebGL-capable browser.';
}

try {
  const game = new Game();
  window.__melodia = game;
  if (tuningMode) import('./npr-tuner.js').then(({ attachShaderTuner }) => {
    window.__melodiaShaderTuner = attachShaderTuner(game);
  }).catch((err) => console.warn('NPR tuning UI unavailable', err));
  game.warm((msg) => { state.textContent = msg; }).then(() => {
    play.disabled = false;
    state.textContent = 'Ready. Headphones recommended.';
    const go = (e) => {
      e.preventDefault();
      document.getElementById('title').classList.add('hidden');
      game.start();
    };
    play.addEventListener('pointerdown', go, { once: true });
  }).catch(fail);
} catch (err) {
  fail(err);
}
