/**
 * Premium Parallax System — mouse depth on cosmic hero layers.
 */

class PremiumParallax {
  constructor(container) {
    this.container = container;
    this.layers = [];
    this.mouseX = 0;
    this.mouseY = 0;
    this.currentX = 0;
    this.currentY = 0;
    this.depthFactors = [0.05, 0.12, 0.2, 0.28, 0.38, 0.48, 0.58, 0.68];
    this.smoothing = 0.08;
    this.initialized = false;
    this.init();
  }

  init() {
    const layers = this.container.querySelectorAll('[class*="parallax-layer-"]');
    if (layers.length === 0) return;

    layers.forEach((layer, index) => {
      this.layers.push({
        element: layer,
        depth: this.depthFactors[index] || 0.5,
      });
    });

    this.container.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.container.addEventListener('mouseleave', () => this.onMouseLeave());
    this.container.addEventListener('touchmove', (e) => this.onTouchMove(e), { passive: true });
    this.container.addEventListener('touchend', () => this.onMouseLeave());

    this.initialized = true;
    this.animate();
  }

  onMouseMove(e) {
    const rect = this.container.getBoundingClientRect();
    this.mouseX = (e.clientX - rect.left) / rect.width - 0.5;
    this.mouseY = (e.clientY - rect.top) / rect.height - 0.5;
  }

  onTouchMove(e) {
    const rect = this.container.getBoundingClientRect();
    const touch = e.touches[0];
    if (!touch) return;
    this.mouseX = (touch.clientX - rect.left) / rect.width - 0.5;
    this.mouseY = (touch.clientY - rect.top) / rect.height - 0.5;
  }

  onMouseLeave() {
    this.mouseX = 0;
    this.mouseY = 0;
  }

  animate() {
    if (!this.initialized) return;

    this.currentX += (this.mouseX - this.currentX) * this.smoothing;
    this.currentY += (this.mouseY - this.currentY) * this.smoothing;

    this.layers.forEach((layer) => {
      const moveX = this.currentX * layer.depth * 18;
      const moveY = this.currentY * layer.depth * 14;
      layer.element.style.transform = `translate3d(${moveX}px, ${moveY}px, 0)`;
    });

    requestAnimationFrame(() => this.animate());
  }

  destroy() {
    this.initialized = false;
  }
}

class PremiumMaterials {
  constructor() {
    this.materials = [];
    this.init();
  }

  init() {
    document.querySelectorAll('.material-gold-iridescent, .material-crystal, .material-premium').forEach((element) => {
      this.materials.push({
        element,
        type: element.classList.contains('material-gold-iridescent')
          ? 'gold'
          : element.classList.contains('material-crystal')
            ? 'crystal'
            : 'premium',
      });
    });
    this.animateMaterials();
  }

  animateMaterials() {
    const time = Date.now() / 1000;
    this.materials.forEach((material) => {
      const phase = (time + Math.random() * 2) % 6;
      if (material.type === 'gold') {
        material.element.style.backgroundPosition = `${(phase / 6) * 100}% 50%`;
      } else if (material.type === 'crystal') {
        material.element.style.opacity = String(0.5 + Math.sin(phase * Math.PI) * 0.3);
      } else {
        const shimmerOffset = Math.sin(phase * Math.PI * 2) * 10;
        material.element.style.backgroundPosition = `calc(50% + ${shimmerOffset}px) 50%`;
      }
    });
    requestAnimationFrame(() => this.animateMaterials());
  }
}

function populateConstellationLines(hero) {
  const layer4 = hero.querySelector('.parallax-layer-4');
  if (!layer4 || layer4.dataset.constellationPopulated === 'true') return;
  layer4.dataset.constellationPopulated = 'true';
  for (let i = 0; i < 5; i++) {
    const line = document.createElement('div');
    line.className = 'constellation-line';
    line.style.left = `${Math.random() * 80 + 10}%`;
    line.style.top = `${Math.random() * 80 + 10}%`;
    line.style.width = `${Math.random() * 30 + 20}%`;
    line.style.transform = `rotate(${Math.random() * 360}deg)`;
    line.style.animationDelay = `${i * 1.5}s`;
    layer4.appendChild(line);
  }
}

let premiumHeroInstance = null;

function initPremiumHero() {
  const hero = document.querySelector('.hero');
  if (!hero || !hero.querySelector('[class*="parallax-layer-"]')) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduceMotion.matches) return;

  if (premiumHeroInstance) premiumHeroInstance.destroy();
  populateConstellationLines(hero);
  premiumHeroInstance = {
    parallax: new PremiumParallax(hero),
    materials: new PremiumMaterials(),
    destroy() {
      if (this.parallax) this.parallax.destroy();
    },
  };
}

if (typeof window !== 'undefined') {
  window.initPremiumHero = initPremiumHero;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { PremiumParallax, PremiumMaterials, initPremiumHero };
}
