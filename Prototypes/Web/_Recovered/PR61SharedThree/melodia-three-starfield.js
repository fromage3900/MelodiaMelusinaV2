/**
 * MelodiaThreeStarfield — WebGL Points sky (Three.js).
 * When data-effects includes "three", editorial boots this instead of / alongside 2D canvas.
 * Falls back silently if WebGL / reduced-motion blocks.
 */
(function (global) {
  'use strict';

  var instance = null;

  function Core() {
    return global.MelodiaThreeCore;
  }

  function starCount(intensity) {
    var mobile = Core().isMobile();
    if (intensity === 'cosmic') return mobile ? 900 : 2200;
    if (intensity === 'subtle') return mobile ? 500 : 1100;
    return mobile ? 700 : 1600;
  }

  function buildGeometry(count) {
    var positions = new Float32Array(count * 3);
    var colors = new Float32Array(count * 3);
    var sizes = new Float32Array(count);
    var phases = new Float32Array(count);
    var c = Core().brandColors();
    var palette = [
      new THREE.Color(c.ivory),
      new THREE.Color(c.gold),
      new THREE.Color(c.lavender),
      new THREE.Color(c.astral),
      new THREE.Color(c.cyan),
      new THREE.Color(c.sakura),
    ];

    for (var i = 0; i < count; i++) {
      var radius = 18 + Math.random() * 42;
      var theta = Math.random() * Math.PI * 2;
      var phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta) * 0.62;
      positions[i * 3 + 2] = radius * Math.cos(phi);

      var col = palette[Math.floor(Math.random() * palette.length)].clone();
      var tint = 0.65 + Math.random() * 0.35;
      colors[i * 3] = col.r * tint;
      colors[i * 3 + 1] = col.g * tint;
      colors[i * 3 + 2] = col.b * tint;
      sizes[i] = 0.8 + Math.random() * 2.4;
      phases[i] = Math.random() * Math.PI * 2;
    }

    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
    geo.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1));
    return geo;
  }

  function buildMaterial() {
    return new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexColors: true,
      uniforms: {
        uTime: { value: 0 },
        uPixelRatio: { value: Math.min(window.devicePixelRatio || 1, 2) },
        uIntensity: { value: 1 },
      },
      vertexShader: [
        'attribute float aSize;',
        'attribute float aPhase;',
        'uniform float uTime;',
        'uniform float uPixelRatio;',
        'uniform float uIntensity;',
        'varying vec3 vColor;',
        'varying float vAlpha;',
        'void main() {',
        '  vColor = color;',
        '  float twinkle = 0.55 + 0.45 * sin(uTime * 1.4 + aPhase);',
        '  vAlpha = twinkle * uIntensity;',
        '  vec4 mv = modelViewMatrix * vec4(position, 1.0);',
        '  gl_PointSize = aSize * uPixelRatio * (180.0 / -mv.z);',
        '  gl_Position = projectionMatrix * mv;',
        '}',
      ].join('\n'),
      fragmentShader: [
        'varying vec3 vColor;',
        'varying float vAlpha;',
        'void main() {',
        '  vec2 uv = gl_PointCoord - 0.5;',
        '  float d = length(uv);',
        '  float core = smoothstep(0.5, 0.0, d);',
        '  float bloom = smoothstep(0.5, 0.12, d) * 0.55;',
        '  float a = (core + bloom) * vAlpha;',
        '  if (a < 0.01) discard;',
        '  gl_FragColor = vec4(vColor, a);',
        '}',
      ].join('\n'),
    });
  }

  function MelodiaThreeStarfield(options) {
    this.options = options || {};
    this.shell = null;
    this.container = null;
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.points = null;
    this.nebula = null;
    this.stopLoop = null;
    this.unresize = null;
    this.mouseX = 0;
    this.mouseY = 0;
    this.targetX = 0;
    this.targetY = 0;
    this.onPointer = null;
    this.onScroll = null;
  }

  MelodiaThreeStarfield.prototype.mount = function () {
    var self = this;
    var core = Core();
    if (!core || !core.canBoot({ skipMobile: false })) return Promise.resolve(false);

    return core.ensureThree().then(function () {
      self.shell = document.querySelector('.melodia-shell') || document.body;
      var existing = self.shell.querySelector('#ambient-three-starfield');
      if (existing) existing.remove();

      self.container = document.createElement('div');
      self.container.id = 'ambient-three-starfield';
      self.container.className = 'melodia-three-starfield';
      self.container.setAttribute('aria-hidden', 'true');
      self.shell.insertBefore(self.container, self.shell.firstChild);

      var intensity = self.options.intensity || 'standard';
      self.scene = new THREE.Scene();
      self.camera = new THREE.PerspectiveCamera(55, 1, 0.1, 200);
      self.camera.position.z = 28;

      self.renderer = core.createRenderer(self.container, {
        alpha: true,
        clearAlpha: 0,
        className: 'melodia-three-canvas melodia-three-starfield-canvas',
        maxDpr: core.isMobile() ? 1.5 : 2,
      });

      var geo = buildGeometry(starCount(intensity));
      var mat = buildMaterial();
      mat.uniforms.uIntensity.value = intensity === 'cosmic' ? 1.05 : intensity === 'subtle' ? 0.72 : 0.9;
      self.points = new THREE.Points(geo, mat);
      self.scene.add(self.points);

      // Soft nebula billboards — brand gold / lavender wash
      var nebulaGeo = new THREE.PlaneGeometry(60, 36);
      var nebulaMat = new THREE.MeshBasicMaterial({
        color: core.brandColors().lavender,
        transparent: true,
        opacity: 0.045,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });
      self.nebula = new THREE.Mesh(nebulaGeo, nebulaMat);
      self.nebula.position.set(0, 0, -20);
      self.scene.add(self.nebula);

      self.unresize = core.bindResize(self.renderer, self.camera, self.container);

      self.onPointer = function (e) {
        var x = e.clientX / window.innerWidth;
        var y = e.clientY / window.innerHeight;
        self.targetX = (x - 0.5) * 2;
        self.targetY = (y - 0.5) * 2;
      };
      self.onScroll = function () {
        self.targetY = Math.min(1, window.scrollY / (window.innerHeight * 2)) * 0.6;
      };
      window.addEventListener('pointermove', self.onPointer, { passive: true });
      window.addEventListener('scroll', self.onScroll, { passive: true });

      // Hide legacy 2D starfield canvas when WebGL owns the sky
      var legacy = document.getElementById('ambient-starfield');
      if (legacy) {
        legacy.classList.add('melodia-starfield-superseded');
        legacy.style.opacity = '0';
        legacy.style.pointerEvents = 'none';
      }
      document.documentElement.setAttribute('data-three-starfield', 'live');

      var t0 = performance.now();
      self.stopLoop = core.startLoop(function (now) {
        var t = (now - t0) * 0.001;
        self.mouseX += (self.targetX - self.mouseX) * 0.04;
        self.mouseY += (self.targetY - self.mouseY) * 0.04;
        self.points.rotation.y = t * 0.018 + self.mouseX * 0.12;
        self.points.rotation.x = self.mouseY * 0.08;
        mat.uniforms.uTime.value = t;
        if (self.nebula) {
          self.nebula.rotation.z = t * 0.02;
          self.nebula.material.opacity = 0.035 + Math.sin(t * 0.4) * 0.012;
        }
        self.renderer.render(self.scene, self.camera);
      });

      return true;
    }).catch(function (err) {
      console.warn('[MelodiaThreeStarfield]', err);
      return false;
    });
  };

  MelodiaThreeStarfield.prototype.destroy = function () {
    var core = Core();
    if (this.stopLoop) this.stopLoop();
    if (this.unresize) this.unresize();
    if (this.onPointer) window.removeEventListener('pointermove', this.onPointer);
    if (this.onScroll) window.removeEventListener('scroll', this.onScroll);
    if (this.points) core.disposeObject3D(this.points);
    if (this.nebula) core.disposeObject3D(this.nebula);
    if (this.renderer) {
      this.renderer.dispose();
      if (this.renderer.domElement && this.renderer.domElement.parentNode) {
        this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
      }
    }
    if (this.container && this.container.parentNode) this.container.parentNode.removeChild(this.container);
    document.documentElement.removeAttribute('data-three-starfield');
  };

  function init(options) {
    if (instance) {
      instance.destroy();
      instance = null;
    }
    instance = new MelodiaThreeStarfield(options || {});
    return instance.mount();
  }

  global.MelodiaThreeStarfield = {
    init: init,
    getInstance: function () { return instance; },
  };
})(typeof window !== 'undefined' ? window : this);
