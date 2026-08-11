/**
 * Cosmic Instruments — clock + compass (NASA-textured, dreamy).
 * Click clock to toggle \"cosmic time\" speed.
 * Click compass to jump between major sections (closest band/hero).
 */
(function (global) {
  'use strict';

  // Editorial-only: no remote imagery dependencies.

  function mount(root) {
    const shell = root || document.querySelector('.melodia-shell');
    if (!shell) return null;
    if (shell.querySelector('.cosmic-instruments')) return null;

    const wrap = document.createElement('div');
    wrap.className = 'cosmic-instruments';

    const clock = document.createElement('div');
    clock.className = 'instrument cosmic-clock';
    clock.innerHTML = `
      <div class="nasa" aria-hidden="true"></div>
      <svg viewBox="0 0 120 120" aria-hidden="true">
        <circle class="ring" cx="60" cy="60" r="48"/>
        ${Array.from({ length: 12 })
          .map((_, i) => {
            const a = (i / 12) * Math.PI * 2;
            const x1 = 60 + Math.cos(a) * 44;
            const y1 = 60 + Math.sin(a) * 44;
            const x2 = 60 + Math.cos(a) * 48;
            const y2 = 60 + Math.sin(a) * 48;
            return `<line class="tick" x1="${x1.toFixed(2)}" y1="${y1.toFixed(2)}" x2="${x2.toFixed(2)}" y2="${y2.toFixed(2)}"/>`;
          })
          .join('')}
        <line class="hand hour" x1="60" y1="60" x2="60" y2="34"/>
        <line class="hand min" x1="60" y1="60" x2="60" y2="24"/>
        <line class="hand sec" x1="60" y1="60" x2="60" y2="18"/>
        <circle class="core" cx="60" cy="60" r="2.8"/>
      </svg>
      <button class="click" type="button" aria-label="Toggle cosmic clock speed"></button>
      <div class="label">Cosmic Clock</div>
    `;

    const compass = document.createElement('div');
    compass.className = 'instrument cosmic-compass';
    compass.innerHTML = `
      <div class="nasa" aria-hidden="true"></div>
      <svg viewBox="0 0 120 120" aria-hidden="true">
        <circle class="rose" cx="60" cy="60" r="48"/>
        <path class="rose" d="M60 16v88M16 60h88" opacity="0.7"/>
        <path class="rose" d="M28 28l64 64M92 28L28 92" opacity="0.25"/>
        <text class="cardinal" x="60" y="14" text-anchor="middle">N</text>
        <text class="cardinal" x="108" y="63" text-anchor="middle">E</text>
        <text class="cardinal" x="60" y="114" text-anchor="middle">S</text>
        <text class="cardinal" x="12" y="63" text-anchor="middle">W</text>
        <path class="bearing" d="M60 60 L60 22"/>
        <circle class="core" cx="60" cy="60" r="2.6" fill="rgba(255,230,102,0.8)"/>
      </svg>
      <button class="click" type="button" aria-label="Jump via cosmic compass"></button>
      <div class="label">Cosmic Compass</div>
    `;

    wrap.appendChild(clock);
    wrap.appendChild(compass);
    shell.appendChild(wrap);

    const hour = clock.querySelector('.hand.hour');
    const min = clock.querySelector('.hand.min');
    const sec = clock.querySelector('.hand.sec');
    const bearing = compass.querySelector('.bearing');

    // Keep it subtle: clock speed toggle removed; keep 1× time.
    let speed = 1;
    clock.querySelector('.click').addEventListener('click', () => {
      // Minimal editorial behavior: click toggles instruments visibility
      const wrap = clock.closest('.cosmic-instruments');
      if (wrap) wrap.classList.toggle('is-collapsed');
    });

    // Compass: jump between major sections
    const targets = [
      '#main',
      '#constellation',
      '#renders',
      '#portals',
      '#worlds',
      '#planetarium',
      '#logic',
      '#passports',
      '#review',
    ]
      .map((id) => document.querySelector(id))
      .filter(Boolean);

    compass.querySelector('.click').addEventListener('click', () => {
      if (!targets.length) return;
      const y = window.scrollY;
      let next = targets[0];
      for (let i = 0; i < targets.length; i++) {
        const ty = targets[i].getBoundingClientRect().top + window.scrollY;
        if (ty > y + 40) {
          next = targets[i];
          break;
        }
      }
      next.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    function update() {
      const now = Date.now();
      const d = new Date(now);
      const s = d.getSeconds() + d.getMilliseconds() / 1000;
      const m = d.getMinutes() + s / 60;
      const h = (d.getHours() % 12) + m / 60;

      const secA = (s * 6 * speed) % 360;
      const minA = (m * 6) % 360;
      const hourA = (h * 30) % 360;

      sec.setAttribute('transform', `rotate(${secA} 60 60)`);
      min.setAttribute('transform', `rotate(${minA} 60 60)`);
      hour.setAttribute('transform', `rotate(${hourA} 60 60)`);

      // Compass bearing: map scroll position to 0..360
      const doc = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      const t = window.scrollY / doc;
      const a = t * 360;
      bearing.setAttribute('d', `M60 60 L60 22`);
      bearing.setAttribute('transform', `rotate(${a.toFixed(2)} 60 60)`);

      requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
    return wrap;
  }

  global.MelodiaCosmicInstruments = { mount };
})(window);

