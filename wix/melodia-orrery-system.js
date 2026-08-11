/**
 * Melodia Orrery System — real 3D CSS armillary (local arm spin + plane tilts).
 */
(function (global) {
  'use strict';

  const RING_CONFIG = [
    { size: [88, 72], duration: 16, color: 'rgba(255, 110, 180, 0.55)', tiltX: 72, tiltY: -12, z: 10 },
    { size: [128, 108], duration: 24, color: 'rgba(255, 230, 102, 0.42)', tiltX: 22, tiltY: 28, z: 18, reverse: true },
    { size: [178, 148], duration: 36, color: 'rgba(255, 142, 200, 0.44)', tiltX: 58, tiltY: -22, z: 28 },
    { size: [228, 198], duration: 48, color: 'rgba(204, 153, 255, 0.36)', tiltX: 14, tiltY: 40, z: 38, reverse: true },
    { size: [298, 268], duration: 72, color: 'rgba(255, 110, 180, 0.24)', tiltX: 68, tiltY: 12, z: 48 },
    { size: [368, 328], duration: 96, color: 'rgba(102, 217, 255, 0.22)', tiltX: 32, tiltY: -48, z: 58, reverse: true },
    { size: [248, 248], duration: 56, color: 'rgba(255, 230, 102, 0.24)', tiltX: 86, tiltY: 6, z: 22, reverse: true },
    { size: [312, 312], duration: 84, color: 'rgba(255, 110, 180, 0.18)', tiltX: 84, tiltY: 52, z: 42 },
  ];

  const VARIANTS = {
    cosmic: `
      <g class="ring slow"><circle class="orbit" cx="260" cy="260" r="226"/><path class="axis" d="M98 422 422 98"/><circle class="node" cx="420" cy="100" r="4"/></g>
      <g class="ring"><circle class="orbit" cx="260" cy="260" r="166"/><path class="axis" d="M132 260h256"/><circle class="node" cx="389" cy="260" r="3.5"/></g>
      <g class="ring fast"><circle class="orbit" cx="260" cy="260" r="92"/><path class="axis" d="M260 168v184"/><circle class="node" cx="260" cy="168" r="3"/></g>
      <ellipse class="orbit meridian" cx="260" cy="260" rx="198" ry="72" transform="rotate(24 260 260)"/>
      <ellipse class="orbit meridian thin" cx="260" cy="260" rx="248" ry="88" transform="rotate(-18 260 260)"/>
      <circle class="orbit" cx="260" cy="260" r="22"/>
    `,
    atelier: `
      <ellipse class="orbit ellipse" cx="200" cy="200" rx="178" ry="132" transform="rotate(-18 200 200)"/>
      <ellipse class="orbit ellipse thin" cx="200" cy="200" rx="128" ry="94" transform="rotate(24 200 200)"/>
      <ellipse class="orbit ellipse" cx="200" cy="200" rx="72" ry="52" transform="rotate(-8 200 200)"/>
      <ellipse class="orbit meridian" cx="200" cy="200" rx="156" ry="58" transform="rotate(68 200 200)"/>
      <path class="axis" d="M40 200h320"/>
      <path class="axis" d="M200 48v304"/>
      <circle class="node quatrefoil" cx="200" cy="200" r="5"/>
      <circle class="node" cx="368" cy="168" r="2.8"/>
      <circle class="node" cx="56" cy="232" r="2.2"/>
      <path class="axis fashion-cross" d="M200 20v24M200 356v24M20 200h24M356 200h24"/>
    `,
    constellation: `
      <g class="ring"><circle class="orbit" cx="120" cy="120" r="98"/><circle class="node" cx="210" cy="120" r="2.5"/></g>
      <g class="ring slow"><circle class="orbit" cx="120" cy="120" r="62"/><path class="axis" d="M58 120h124"/></g>
      <ellipse class="orbit meridian" cx="120" cy="120" rx="88" ry="34" transform="rotate(32 120 120)"/>
      <circle class="orbit" cx="120" cy="120" r="14"/>
      <circle class="node" cx="120" cy="38" r="2"/>
      <circle class="node" cx="178" cy="168" r="1.8"/>
    `,
  };

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function ensureRig(system) {
    let rig = system.querySelector(':scope > .orrery-rig');
    if (rig) return rig;
    rig = document.createElement('div');
    rig.className = 'orrery-rig';
    const yaw = document.createElement('div');
    yaw.className = 'orrery-yaw';
    while (system.firstChild) {
      yaw.appendChild(system.firstChild);
    }
    rig.appendChild(yaw);
    system.appendChild(rig);
    return rig;
  }

  function addRingNodes(spin, index) {
    const angles = index < 4 ? [0, 120, 240] : [45, 225];
    angles.forEach((deg) => {
      const node = document.createElement('div');
      node.className = 'orbital-node-marker';
      node.style.setProperty('--node-angle', deg + 'deg');
      node.setAttribute('aria-hidden', 'true');
      const dot = document.createElement('span');
      dot.className = 'orbital-node-dot';
      node.appendChild(dot);
      spin.appendChild(node);
    });
  }

  function addArms(spin, index) {
    const count = index < 3 ? 4 : index < 6 ? 3 : 2;
    for (let i = 0; i < count; i += 1) {
      const arm = document.createElement('div');
      arm.className = 'orbital-arm';
      arm.style.setProperty('--arm-angle', (i * (360 / count) + (index % 2) * 15) + 'deg');
      arm.setAttribute('aria-hidden', 'true');
      spin.appendChild(arm);
    }
  }

  function buildCssRings(system) {
    if (system.querySelector('.orbital-shell')) {
      ensureRig(system);
      return;
    }

    const rig = ensureRig(system);
    const yaw = rig.querySelector('.orrery-yaw') || rig;

    if (!yaw.querySelector('.orrery-axis-gimbal')) {
      const gimbal = document.createElement('div');
      gimbal.className = 'orrery-axis-gimbal';
      gimbal.setAttribute('aria-hidden', 'true');
      yaw.appendChild(gimbal);
    }

    RING_CONFIG.forEach((cfg, index) => {
      const shell = document.createElement('div');
      shell.className = 'orbital-shell';
      shell.style.width = cfg.size[0] + 'px';
      shell.style.height = cfg.size[1] + 'px';
      shell.style.setProperty('--ring-depth', String(cfg.z));

      const tilt = document.createElement('div');
      tilt.className = 'orbital-tilt';
      tilt.style.setProperty('--tilt-x', cfg.tiltX + 'deg');
      tilt.style.setProperty('--tilt-y', cfg.tiltY + 'deg');
      tilt.style.setProperty('--z', cfg.z + 'px');

      const spin = document.createElement('div');
      spin.className = 'orbital-spin';
      spin.style.setProperty('--duration', cfg.duration + 's');
      if (cfg.reverse) spin.style.animationDirection = 'reverse';

      const ring = document.createElement('div');
      ring.className = 'orbital-path orbital-ring-' + ((index % 6) + 1);
      ring.style.borderColor = cfg.color;
      ring.style.opacity = String(0.4 + (cfg.z / 58) * 0.4);

      spin.appendChild(ring);
      addArms(spin, index);
      addRingNodes(spin, index);
      tilt.appendChild(spin);
      shell.appendChild(tilt);
      yaw.appendChild(shell);
    });

    if (!yaw.querySelector('.orrery-core')) {
      const core = document.createElement('div');
      core.className = 'orrery-core';
      yaw.appendChild(core);
    }
  }

  function upgradePremiumOrreries() {
    document.querySelectorAll('.orrery-system').forEach((system) => {
      buildCssRings(system);
    });

    document.querySelectorAll('.parallax-layer-5').forEach((layer) => {
      layer.classList.add('orrery-perspective-layer');
      if (!layer.querySelector('.orrery-system')) {
        const system = document.createElement('div');
        system.className = 'orrery-system';
        layer.appendChild(system);
        buildCssRings(system);
      }
    });
  }

  function bindOrreryTilt() {
    if (prefersReducedMotion()) return;

    const rigs = () => document.querySelectorAll('.orrery-system .orrery-rig');
    if (!rigs().length) return;

    const isMobile = window.matchMedia('(max-width: 680px)').matches;
    const range = isMobile ? 8 : 16;

    const onMove = (e) => {
      const mx = (e.clientX / window.innerWidth - 0.5) * range;
      const my = (e.clientY / window.innerHeight - 0.5) * range * 0.55;
      rigs().forEach((rig) => {
        /* Outer 3D tilt; inner .orrery-yaw keeps continuous local yaw */
        rig.style.transform = `rotateX(${(-my).toFixed(2)}deg) rotateY(${mx.toFixed(2)}deg)`;
      });
    };
    window.addEventListener('pointermove', onMove, { passive: true });
  }

  function createOrrery(variant, viewBox) {
    const wrap = document.createElement('div');
    const v = VARIANTS[variant] ? variant : 'atelier';
    const vb = viewBox || (v === 'constellation' ? '0 0 240 240' : '0 0 400 400');
    wrap.className = `orrery-mount orrery-${v} orrery-3d-mount`;
    wrap.innerHTML = `<div class="orrery-3d-tilt"><svg viewBox="${vb}" role="img" aria-hidden="true">${VARIANTS[v]}</svg></div>`;
    return wrap;
  }

  function mountElement(el) {
    if (!el || el.dataset.orreryMounted === 'true') return;
    const variant = el.getAttribute('data-orrery') || 'atelier';
    const viewBox = el.getAttribute('data-orrery-viewbox') || '';
    const mount = createOrrery(variant, viewBox || undefined);
    el.appendChild(mount);
    el.dataset.orreryMounted = 'true';
  }

  function mountAll(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-orrery]').forEach(mountElement);
  }

  function upgradeHeroOrreries() {
    document.querySelectorAll('.melodia-orrery').forEach((el) => {
      if (el.querySelector('.orrery-3d-mount, .orrery-mount')) return;
      el.setAttribute('data-orrery', 'cosmic');
      el.setAttribute('data-orrery-viewbox', '0 0 520 520');
      el.innerHTML = '';
      mountElement(el);
      const svg = el.querySelector('svg');
      if (svg) svg.setAttribute('viewBox', '0 0 520 520');
    });
  }

  function boot() {
    upgradePremiumOrreries();
    upgradeHeroOrreries();
    mountAll();
    bindOrreryTilt();
  }

  global.MelodiaOrrery = {
    mountAll,
    mountElement,
    createOrrery,
    upgradeHeroOrreries,
    upgradePremiumOrreries,
    bindOrreryTilt,
    boot,
  };
})(window);
