/**
 * Melodia Escher Interact — drag-to-rotate tessellation + Figma MotionDemo sheen.
 * Mounts on .escher-tessellation[data-escher-interact]
 */
(function (global) {
  'use strict';

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function mount(el) {
    if (!el || el.dataset.escherMounted === 'true') return;
    el.dataset.escherMounted = 'true';
    el.removeAttribute('aria-hidden');
    el.setAttribute('role', 'img');
    el.setAttribute('aria-label', 'Interactive Escher tessellation — drag to rotate');
    el.classList.add('escher-interactive');
    el.tabIndex = 0;

    const inner = el.querySelector('.escher-grid-inner') || el.querySelector('.escher-grid');
    if (!inner) return;

    // Figma Game/MotionDemo sheen layer
    if (!el.querySelector('.escher-sheen')) {
      const sheen = document.createElement('div');
      sheen.className = 'escher-sheen';
      sheen.setAttribute('aria-hidden', 'true');
      el.appendChild(sheen);
    }

    if (!el.querySelector('.escher-hint')) {
      const hint = document.createElement('p');
      hint.className = 'escher-hint';
      hint.textContent = 'Drag to rotate · tessellation logic';
      el.appendChild(hint);
    }

    let angle = 0;
    let auto = !prefersReducedMotion();
    let dragging = false;
    let lastX = 0;
    let vel = 0;
    let raf = 0;

    const apply = () => {
      inner.style.transform = `rotate(${angle}deg)`;
      inner.style.animation = 'none';
    };

    const tick = () => {
      if (!dragging && auto) {
        angle = (angle + 0.12 + vel) % 360;
        vel *= 0.96;
        apply();
      }
      raf = requestAnimationFrame(tick);
    };

    const onDown = (e) => {
      const p = e.touches ? e.touches[0] : e;
      dragging = true;
      auto = false;
      lastX = p.clientX;
      vel = 0;
      el.classList.add('is-dragging');
    };

    const onMove = (e) => {
      if (!dragging) return;
      const p = e.touches ? e.touches[0] : e;
      const dx = p.clientX - lastX;
      lastX = p.clientX;
      angle = (angle + dx * 0.45) % 360;
      vel = dx * 0.08;
      apply();
      if (e.cancelable) e.preventDefault();
    };

    const onUp = () => {
      if (!dragging) return;
      dragging = false;
      el.classList.remove('is-dragging');
      if (!prefersReducedMotion()) {
        // coast then resume slow auto-spin
        setTimeout(() => {
          if (!dragging) auto = true;
        }, 1600);
      }
    };

    el.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    el.addEventListener('touchstart', onDown, { passive: true });
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onUp);

    el.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') {
        angle -= 8;
        apply();
        e.preventDefault();
      } else if (e.key === 'ArrowRight') {
        angle += 8;
        apply();
        e.preventDefault();
      }
    });

    apply();
    if (!prefersReducedMotion()) raf = requestAnimationFrame(tick);

    el._escherDestroy = () => cancelAnimationFrame(raf);
  }

  function mountAll(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-escher-interact], .escher-tessellation').forEach(mount);
  }

  function mountCardTilt(card) {
    if (!card || card.dataset.tiltMounted === 'true') return;
    card.dataset.tiltMounted = 'true';
    card.style.transformStyle = 'preserve-3d';
    card.style.transition = 'transform 0.15s ease-out, box-shadow 0.3s ease';

    var sheen = card.querySelector('.escher-card-sheen');
    if (!sheen) {
      sheen = document.createElement('div');
      sheen.className = 'escher-card-sheen';
      sheen.setAttribute('aria-hidden', 'true');
      sheen.style.position = 'absolute';
      sheen.style.inset = '0';
      sheen.style.borderRadius = 'inherit';
      sheen.style.pointerEvents = 'none';
      sheen.style.opacity = '0';
      sheen.style.transition = 'opacity 0.25s ease';
      sheen.style.zIndex = '2';
      card.appendChild(sheen);
    }

    function onPointerMove(e) {
      if (prefersReducedMotion()) return;
      var rect = card.getBoundingClientRect();
      var cx = rect.left + rect.width / 2;
      var cy = rect.top + rect.height / 2;
      var relX = (e.clientX - cx) / (rect.width / 2);
      var relY = (e.clientY - cy) / (rect.height / 2);

      var rotX = (-relY * 10).toFixed(2);
      var rotY = (relX * 10).toFixed(2);

      card.style.transform = 'perspective(1000px) rotateX(' + rotX + 'deg) rotateY(' + rotY + 'deg) scale3d(1.02, 1.02, 1.02)';
      sheen.style.opacity = '1';
      sheen.style.background = 'radial-gradient(circle at ' + ((relX * 0.5 + 0.5) * 100).toFixed(1) + '% ' + ((relY * 0.5 + 0.5) * 100).toFixed(1) + '%, rgba(255, 230, 180, 0.25) 0%, rgba(204, 153, 255, 0.15) 45%, transparent 70%)';
    }

    function onPointerLeave() {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
      sheen.style.opacity = '0';
    }

    card.addEventListener('pointermove', onPointerMove);
    card.addEventListener('pointerleave', onPointerLeave);
  }

  function mountAllCards(root) {
    var scope = root || document;
    var selectors = '.portal-card, .guide-card, .stage-plate-card, .gate-card, .mg-ribbon-card, .escher-tilt-card, [data-escher-tilt], .env-card, .feature-card';
    scope.querySelectorAll(selectors).forEach(mountCardTilt);
  }

  function boot() {
    mountAll();
    mountAllCards();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  global.MelodiaEscher = { mount: mount, mountAll: mountAll, mountCardTilt: mountCardTilt, mountAllCards: mountAllCards, boot: boot };
})(window);

