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
    const scope = root || document;
    scope.querySelectorAll('[data-escher-interact], .escher-tessellation').forEach(mount);
  }

  function boot() {
    mountAll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  global.MelodiaEscher = { mount, mountAll, boot };
})(window);
