/**
 * Melodia Planetarium — interactive armillary constellation navigator.
 * Drag to orbit · click stars to explore portfolio worlds.
 */
(function (global) {
  'use strict';

  const ARMS = [
    { tilt: 0, roll: 0, rx: 270, ry: 270, z: 0, speed: 0.052, hue: '#ff6eb4' },
    { tilt: 62, roll: 18, rx: 236, ry: 162, z: 28, speed: -0.041, hue: '#ffe666' },
    { tilt: -38, roll: -24, rx: 214, ry: 148, z: -22, speed: 0.036, hue: '#ff8ec8' },
    { tilt: 90, roll: 0, rx: 196, ry: 196, z: 12, speed: -0.028, hue: '#7dd3c0' },
    { tilt: 22, roll: 54, rx: 292, ry: 208, z: 36, speed: 0.024, hue: '#e8a0b0' },
    { tilt: -64, roll: 14, rx: 176, ry: 126, z: -18, speed: 0.061, hue: '#c8b6db' },
    { tilt: 78, roll: -6, rx: 248, ry: 88, z: 8, speed: -0.033, hue: '#66d9ff' },
    { tilt: -12, roll: 88, rx: 88, ry: 248, z: -8, speed: 0.029, hue: '#ffe666' },
  ];

  /* Mini mode — 4 arms, pink-forward, auto-spin only */
  const MINI_ARM_INDICES = [0, 1, 2, 4];
  const MINI_ARMS = MINI_ARM_INDICES.map((i) => {
    const src = ARMS[i];
    return {
      ...src,
      rx: Math.round(src.rx * 0.62),
      ry: Math.round(src.ry * 0.62),
      speed: src.speed * 1.15,
    };
  });

  const NODES = [
    { id: 'sakura', label: 'Sakura Dream', short: 'Sakura', kana: '桜', href: 'sakura-case-study.html', arm: 1, angle: 32, color: '#ff6eb4', r: 5.5 },
    { id: 'cathedral', label: 'Space Cathedral', short: 'Cathedral', kana: '星', href: 'world-bible.html', arm: 0, angle: 114, color: '#9b8fc4', r: 5.5 },
    { id: 'grotto', label: 'Baroque Grotto', short: 'Grotto', kana: '洞', href: 'world-bible.html', arm: 2, angle: 204, color: '#5eb8b0', r: 5 },
    { id: 'orrery', label: 'Cosmic Orrery', short: 'Orrery', kana: '宙', href: 'application-hub.html#worlds', arm: 4, angle: 292, color: '#ff8ec8', r: 5.5 },
    { id: 'shaders', label: 'Shader Breakdowns', short: 'Shaders', kana: '光', href: 'shader-breakdowns.html', arm: 0, angle: 252, color: '#ffe666', r: 4.5 },
    { id: 'renders', label: 'Hero Renders', short: 'Renders', kana: '景', href: 'hero-renders.html', arm: 5, angle: 160, color: '#e8c9b8', r: 4.5 },
    { id: 'hub', label: 'Application Hub', short: 'Hub', kana: '門', href: 'application-hub.html', arm: 3, angle: 320, color: '#c9a86a', r: 5 },
    { id: 'geometry', label: 'Geometry Nodes', short: 'GN', kana: '形', href: 'geometry-nodes.html', arm: 5, angle: 74, color: '#c8b6db', r: 4.5 },
  ];

  const MINI_NODES = [
    { ...NODES[0], arm: 1 },
    { ...NODES[1], arm: 0 },
    { ...NODES[2], arm: 2 },
    { ...NODES[3], arm: 3 },
    { ...NODES[4], arm: 0 },
    { ...NODES[6], arm: 3 },
  ];

  const MINI_LINES = [
    ['sakura', 'hub'],
    ['cathedral', 'shaders'],
    ['grotto', 'orrery'],
    ['orrery', 'hub'],
  ];

  const LINES = [
    ['sakura', 'renders'],
    ['cathedral', 'shaders'],
    ['grotto', 'geometry'],
    ['orrery', 'hub'],
    ['sakura', 'hub'],
    ['cathedral', 'orrery'],
  ];

  const SVGNS = 'http://www.w3.org/2000/svg';
  const CX = 300;
  const CY = 300;

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function polarOnArm(arm, angleDeg, armAngle) {
    const total = ((angleDeg + armAngle) * Math.PI) / 180;
    const x = Math.cos(total) * arm.rx;
    const y = Math.sin(total) * arm.ry;
    return { x, y };
  }

  class PlanetariumInstance {
    constructor(mount, options) {
      this.mount = mount;
      this.mode = options.mode || mount.getAttribute('data-planetarium') || 'explorer';
      this.isHero = this.mode === 'hero';
      this.isMini = this.mode === 'mini';
      this.reduceMotion = prefersReducedMotion();

      this.arms = this.isMini ? MINI_ARMS.map((a) => ({ ...a })) : ARMS.map((a) => ({ ...a }));
      this.nodes = this.isMini ? MINI_NODES.map((n) => ({ ...n })) : NODES.map((n) => ({ ...n }));
      this.lines = this.isMini ? MINI_LINES.slice() : LINES.slice();

      this.yaw = 0;
      this.pitch = this.isHero ? 16 : this.isMini ? 18 : 22;
      this.targetYaw = 0;
      this.targetPitch = this.pitch;
      this.drag = { on: false, x: 0, y: 0, yaw0: 0, pitch0: 0 };
      this.armAngles = this.arms.map(() => 0);
      this.activeId = null;
      this.focusEl = null;
      this.hintEl = null;
      this.legendEl = null;
      this.nodeEls = {};
      this.lineEls = [];
      this.raf = 0;

      this.build();
      this.bind();
      if (!this.reduceMotion) this.loop();
    }

    build() {
      this.root = document.createElement('div');
      this.root.className = `planetarium planetarium-${this.mode}`;
      this.root.setAttribute('role', this.isMini ? 'navigation' : 'application');
      this.root.setAttribute(
        'aria-label',
        this.isMini ? 'Mini constellation navigator' : 'Interactive portfolio planetarium'
      );

      this.canvas = document.createElement('canvas');
      this.canvas.className = 'planetarium-canvas';
      this.canvas.setAttribute('aria-hidden', 'true');

      this.svg = document.createElementNS(SVGNS, 'svg');
      this.svg.setAttribute('class', 'planetarium-svg');
      this.svg.setAttribute('viewBox', '0 0 600 600');

      const coreStops = this.isMini
        ? `<stop offset="0%" stop-color="#fff" stop-opacity="0.95"/>
            <stop offset="30%" stop-color="#ff6eb4" stop-opacity="0.85"/>
            <stop offset="65%" stop-color="#ffe666" stop-opacity="0.55"/>
            <stop offset="100%" stop-color="#66d9ff" stop-opacity="0.15"/>`
        : `<stop offset="0%" stop-color="#fff" stop-opacity="0.95"/>
            <stop offset="35%" stop-color="#ffe666" stop-opacity="0.85"/>
            <stop offset="70%" stop-color="#66d9ff" stop-opacity="0.5"/>
            <stop offset="100%" stop-color="#cc99ff" stop-opacity="0.15"/>`;

      this.svg.innerHTML = `
        <defs>
          <radialGradient id="planetarium-core-grad-${this.mode}" cx="40%" cy="35%">
            ${coreStops}
          </radialGradient>
          <filter id="planetarium-glow-${this.mode}" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2.5" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <filter id="planetarium-node-glow-${this.mode}" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="3" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        <circle class="planetarium-dome" cx="${CX}" cy="${CY}" r="${this.isMini ? 220 : 275}"/>
        <circle class="planetarium-dome" cx="${CX}" cy="${CY}" r="${this.isMini ? 185 : 235}" opacity="0.6"/>
        <g class="planetarium-world" transform="translate(${CX},${CY})"/>
      `;

      this.world = this.svg.querySelector('.planetarium-world');
      this.perspectiveWrap = document.createElement('div');
      this.perspectiveWrap.className = 'planetarium-3d';
      this.perspectiveWrap.appendChild(this.svg);
      this.linesG = document.createElementNS(SVGNS, 'g');
      this.linesG.setAttribute('class', 'planetarium-lines');
      this.armsG = document.createElementNS(SVGNS, 'g');
      this.armsG.setAttribute('class', 'planetarium-arms');
      this.nodesG = document.createElementNS(SVGNS, 'g');
      this.nodesG.setAttribute('class', 'planetarium-nodes');

      this.world.appendChild(this.linesG);
      this.world.appendChild(this.armsG);
      this.world.appendChild(this.nodesG);

      this.arms.forEach((arm, i) => {
        const g = document.createElementNS(SVGNS, 'g');
        g.setAttribute('class', `planetarium-arm-group arm-group-${i}`);
        g.setAttribute('data-arm', String(i));

        const ellipse = document.createElementNS(SVGNS, 'ellipse');
        ellipse.setAttribute('class', `planetarium-arm arm-${i}`);
        ellipse.setAttribute('cx', '0');
        ellipse.setAttribute('cy', '0');
        ellipse.setAttribute('rx', String(arm.rx));
        ellipse.setAttribute('ry', String(arm.ry));
        if (arm.hue) ellipse.style.stroke = arm.hue;
        g.appendChild(ellipse);

        const axis = document.createElementNS(SVGNS, 'line');
        axis.setAttribute('class', 'planetarium-axis');
        axis.setAttribute('x1', String(-arm.rx));
        axis.setAttribute('y1', '0');
        axis.setAttribute('x2', String(arm.rx));
        axis.setAttribute('y2', '0');
        g.appendChild(axis);

        this.armsG.appendChild(g);
        arm.group = g;
      });

      const coreG = document.createElementNS(SVGNS, 'g');
      coreG.innerHTML = `
        <circle class="planetarium-core-ring" cx="0" cy="0" r="${this.isMini ? 22 : 28}"/>
        <circle class="planetarium-core" cx="0" cy="0" r="${this.isMini ? 14 : 18}" fill="url(#planetarium-core-grad-${this.mode})"/>
      `;
      this.world.appendChild(coreG);

      this.nodes.forEach((node) => this.createNode(node));
      this.lines.forEach(([a, b]) => this.createLine(a, b));

      const hud = document.createElement('div');
      hud.className = 'planetarium-hud';
      if (!this.isHero && !this.isMini) {
        this.hintEl = document.createElement('p');
        this.hintEl.className = 'planetarium-hint';
        this.hintEl.textContent = 'Drag to orbit the armillary · Click a star to explore';
        hud.appendChild(this.hintEl);
      }
      if (this.isMini) {
        this.hintEl = document.createElement('p');
        this.hintEl.className = 'planetarium-hint planetarium-hint-mini';
        this.hintEl.textContent = 'Click a star to explore';
        hud.appendChild(this.hintEl);
      }
      this.focusEl = document.createElement('p');
      this.focusEl.className = 'planetarium-focus';
      this.focusEl.setAttribute('aria-live', 'polite');
      hud.appendChild(this.focusEl);

      this.root.appendChild(this.canvas);
      this.root.appendChild(this.perspectiveWrap);
      this.root.appendChild(hud);
      this.mount.appendChild(this.root);

      this.initStars();
      this.resizeCanvas();
      this.updateTransforms();
    }

    createNode(node) {
      const g = document.createElementNS(SVGNS, 'a');
      g.setAttribute('class', 'planetarium-node');
      g.setAttribute('href', node.href);
      g.setAttribute('data-id', node.id);
      g.setAttribute('aria-label', `${node.label} — open portfolio section`);

      const pulse = document.createElementNS(SVGNS, 'circle');
      pulse.setAttribute('class', 'node-pulse');
      pulse.setAttribute('cx', '0');
      pulse.setAttribute('cy', '0');
      pulse.setAttribute('r', '6');

      const body = document.createElementNS(SVGNS, 'circle');
      body.setAttribute('class', 'node-body');
      body.setAttribute('cx', '0');
      body.setAttribute('cy', '0');
      body.setAttribute('r', String(node.r));
      body.style.setProperty('--node-color', node.color);

      const label = document.createElementNS(SVGNS, 'text');
      label.setAttribute('class', 'planetarium-node-label');
      label.setAttribute('x', '0');
      label.setAttribute('y', '-12');
      label.setAttribute('text-anchor', 'middle');
      label.textContent = this.isHero || this.isMini ? node.kana : `${node.short} · ${node.kana}`;

      g.appendChild(pulse);
      g.appendChild(body);
      g.appendChild(label);

      g.addEventListener('mouseenter', () => this.setFocus(node));
      g.addEventListener('focus', () => this.setFocus(node));
      g.addEventListener('click', () => {
        this.setFocus(node);
      });

      const arm = this.arms[node.arm];
      arm.group.appendChild(g);
      this.nodeEls[node.id] = { el: g, data: node };
      node.el = g;
    }

    createLine(idA, idB) {
      const line = document.createElementNS(SVGNS, 'line');
      line.setAttribute('class', 'planetarium-constellation-line');
      line.dataset.a = idA;
      line.dataset.b = idB;
      this.linesG.appendChild(line);
      this.lineEls.push(line);
    }

    initStars() {
      this.stars = [];
      const count = this.isHero ? 120 : this.isMini ? 90 : 220;
      for (let i = 0; i < count; i++) {
        this.stars.push({
          x: Math.random(),
          y: Math.random(),
          z: Math.random(),
          size: Math.random() * 1.4 + 0.3,
          twinkle: Math.random() * Math.PI * 2,
        });
      }
    }

    resizeCanvas() {
      const rect = this.root.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      this.canvas.height = Math.max(1, Math.floor(rect.height * dpr));
      this.ctx = this.canvas.getContext('2d');
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      this.w = rect.width;
      this.h = rect.height;
    }

    drawStars(t) {
      if (!this.ctx) return;
      this.ctx.clearRect(0, 0, this.w, this.h);
      const cx = this.w / 2;
      const cy = this.h / 2;
      const parallaxX = this.yaw * 0.008;
      const parallaxY = this.pitch * 0.012;

      this.stars.forEach((s) => {
        const depth = 0.3 + s.z * 0.7;
        const x = (s.x + parallaxX * depth) * this.w;
        const y = (s.y + parallaxY * depth) * this.h;
        const tw = 0.45 + Math.sin(t * 0.002 + s.twinkle) * 0.35;
        const alpha = tw * depth * (this.isHero ? 0.35 : 0.55);
        this.ctx.fillStyle = s.z > 0.6 ? `rgba(255,230,102,${alpha})` : `rgba(236,234,244,${alpha})`;
        this.ctx.beginPath();
        this.ctx.arc(x, y, s.size * depth, 0, Math.PI * 2);
        this.ctx.fill();
      });

      const grad = this.ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.min(cx, cy));
      grad.addColorStop(0, 'rgba(102,217,255,0.04)');
      grad.addColorStop(0.55, 'transparent');
      grad.addColorStop(1, 'rgba(8,11,19,0.25)');
      this.ctx.fillStyle = grad;
      this.ctx.fillRect(0, 0, this.w, this.h);
    }

    setFocus(node) {
      this.activeId = node.id;
      Object.keys(this.nodeEls).forEach((id) => {
        this.nodeEls[id].el.classList.toggle('is-active', id === node.id);
      });
      this.lineEls.forEach((line) => {
        const lit = line.dataset.a === node.id || line.dataset.b === node.id;
        line.classList.toggle('is-lit', lit);
      });
      if (this.focusEl) {
        this.focusEl.textContent = `${node.label}  ${node.kana}`;
      }
      if (this.legendEl) {
        this.legendEl.querySelectorAll('button').forEach((btn) => {
          btn.classList.toggle('is-active', btn.dataset.id === node.id);
        });
      }
    }

    nodeWorldPos(node) {
      const arm = this.arms[node.arm];
      const spin = (this.armAngles[node.arm] + node.angle) * (Math.PI / 180);
      const tilt = arm.tilt * (Math.PI / 180);
      const roll = arm.roll * (Math.PI / 180);
      const z0 = arm.z || 0;

      let x = Math.cos(spin) * arm.rx;
      let y = Math.sin(spin) * arm.ry;
      let z = z0;

      const xr = x * Math.cos(roll) - y * Math.sin(roll);
      const yr = x * Math.sin(roll) + y * Math.cos(roll);
      const zr = z;

      const yt = yr * Math.cos(tilt) - zr * Math.sin(tilt);
      const zt = yr * Math.sin(tilt) + zr * Math.cos(tilt);
      const xt = xr;

      const yawR = this.yaw * (Math.PI / 180);
      const pitchR = this.pitch * (Math.PI / 180);

      const x1 = xt * Math.cos(yawR) + zt * Math.sin(yawR);
      const z1 = -xt * Math.sin(yawR) + zt * Math.cos(yawR);
      const y1 = yt * Math.cos(pitchR) - z1 * Math.sin(pitchR);
      const z2 = yt * Math.sin(pitchR) + z1 * Math.cos(pitchR);

      const depth = 1 / (1 + z2 * 0.0018);
      return { x: x1 * depth, y: y1 * depth, z: z2, scale: 0.55 + depth * 0.5, opacity: 0.45 + depth * 0.55 };
    }

    updateTransforms() {
      this.perspectiveWrap.style.transform = `rotateX(${this.pitch}deg) rotateY(${this.yaw}deg)`;

      this.arms.forEach((arm, i) => {
        const zScale = 1 - Math.abs(arm.z || 0) * 0.0008;
        arm.group.setAttribute(
          'transform',
          `rotate(${arm.tilt}) rotate(${arm.roll}) rotate(${this.armAngles[i]}) scale(${zScale})`
        );
        arm.group.style.opacity = String(0.5 + zScale * 0.5);
      });

      this.nodes.forEach((node) => {
        const arm = this.arms[node.arm];
        const pos = this.nodeWorldPos(node);
        node.el.setAttribute(
          'transform',
          `rotate(${node.angle}) translate(${arm.rx}, 0) scale(${pos.scale})`
        );
        node.el.style.opacity = String(pos.opacity);
      });

      this.lineEls.forEach((line) => {
        const na = this.nodeEls[line.dataset.a];
        const nb = this.nodeEls[line.dataset.b];
        if (!na || !nb) return;
        const pa = this.nodeWorldPos(na.data);
        const pb = this.nodeWorldPos(nb.data);
        line.setAttribute('x1', String(pa.x));
        line.setAttribute('y1', String(pa.y));
        line.setAttribute('x2', String(pb.x));
        line.setAttribute('y2', String(pb.y));
      });
    }

    bind() {
      if (!this.isMini) {
        const onDown = (e) => {
          const p = e.touches ? e.touches[0] : e;
          this.drag.on = true;
          this.drag.x = p.clientX;
          this.drag.y = p.clientY;
          this.drag.yaw0 = this.yaw;
          this.drag.pitch0 = this.pitch;
          this.root.classList.add('is-dragging');
        };

        const onMove = (e) => {
          if (!this.drag.on) return;
          const p = e.touches ? e.touches[0] : e;
          const dx = p.clientX - this.drag.x;
          const dy = p.clientY - this.drag.y;
          this.yaw = this.drag.yaw0 + dx * 0.35;
          this.pitch = Math.max(-28, Math.min(42, this.drag.pitch0 - dy * 0.22));
          this.targetYaw = this.yaw;
          this.targetPitch = this.pitch;
          this.updateTransforms();
          if (e.cancelable) e.preventDefault();
        };

        const onUp = () => {
          this.drag.on = false;
          this.root.classList.remove('is-dragging');
        };

        this.root.addEventListener('mousedown', onDown);
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);
        this.root.addEventListener('touchstart', onDown, { passive: true });
        window.addEventListener('touchmove', onMove, { passive: false });
        window.addEventListener('touchend', onUp);
      }

      const onHoverMove = (e) => {
        if (this.drag.on || this.reduceMotion) return;
        const rect = this.root.getBoundingClientRect();
        const nx = (e.clientX - rect.left) / rect.width - 0.5;
        const ny = (e.clientY - rect.top) / rect.height - 0.5;
        const strength = this.isHero ? 22 : this.isMini ? 14 : 28;
        this.targetYaw = nx * strength;
        this.targetPitch = (this.isHero ? 10 : this.isMini ? 14 : 16) + ny * -strength * 0.55;
      };

      this.root.addEventListener('pointermove', onHoverMove, { passive: true });
      window.addEventListener('resize', () => this.resizeCanvas());

      if (!this.isHero) {
        this.setFocus(this.nodes[0]);
      }
    }

    loop() {
      const tick = (t) => {
        if (!this.reduceMotion && !this.drag.on) {
          this.arms.forEach((arm, i) => {
            this.armAngles[i] += arm.speed;
          });
          if (this.isHero || this.isMini) {
            this.yaw += this.isMini ? 0.028 : 0.018;
          }
          const s = this.isHero ? 0.06 : this.isMini ? 0.07 : 0.08;
          this.yaw += (this.targetYaw - this.yaw) * s;
          this.pitch += (this.targetPitch - this.pitch) * s;
          this.updateTransforms();
        }
        this.drawStars(t);
        this.raf = requestAnimationFrame(tick);
      };
      this.raf = requestAnimationFrame(tick);
    }

    destroy() {
      cancelAnimationFrame(this.raf);
      if (this.root.parentNode) this.root.parentNode.removeChild(this.root);
    }
  }

  function buildLegend(mount, instance) {
    const legend = document.createElement('div');
    legend.className = 'planetarium-legend';
    legend.setAttribute('role', 'toolbar');
    legend.setAttribute('aria-label', 'Constellation destinations');

    NODES.forEach((node) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.dataset.id = node.id;
      btn.innerHTML = `<span class="dot" style="--dot:${node.color}"></span>${node.short}`;
      btn.addEventListener('click', () => {
        instance.setFocus(node);
        const target = instance.nodeEls[node.id].el;
        if (target) target.focus();
      });
      btn.addEventListener('dblclick', () => {
        window.location.href = node.href;
      });
      legend.appendChild(btn);
    });

    mount.appendChild(legend);
    instance.legendEl = legend;
  }

  function mountElement(el) {
    if (!el || el.dataset.planetariumMounted === 'true') return null;
    const mode = el.getAttribute('data-planetarium') || 'explorer';
    const instance = new PlanetariumInstance(el, { mode });
    el.dataset.planetariumMounted = 'true';

    if (mode === 'explorer' && el.hasAttribute('data-planetarium-legend')) {
      buildLegend(el, instance);
    }
    return instance;
  }

  function mountAll(root) {
    const scope = root || document;
    const instances = [];
    scope.querySelectorAll('[data-planetarium]').forEach((el) => {
      const inst = mountElement(el);
      if (inst) instances.push(inst);
    });
    return instances;
  }

  function mountHeroReplacement() {
    const hero = document.querySelector('.hero[data-planetarium-hero]');
    if (!hero || hero.querySelector('.planetarium-hero-slot')) return;

    const slot = document.createElement('div');
    slot.className = 'planetarium-hero-slot';
    slot.setAttribute('data-planetarium', 'hero');
    hero.appendChild(slot);
    mountElement(slot);
  }

  function boot() {
    mountAll();
    mountHeroReplacement();
  }

  global.MelodiaPlanetarium = {
    mountAll,
    mountElement,
    mountHeroReplacement,
    boot,
    NODES,
    ARMS,
  };
})(window);
