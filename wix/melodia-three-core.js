/**
 * MelodiaThreeCore — shared Three.js bootstrap for Melodia site FX + viewers.
 * Loads r128 (UMD) once, exposes capability gates, RAF helpers, and dispose utils.
 */
(function (global) {
  'use strict';

  var CDN = {
    three: 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
    orbit: 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js',
    obj: 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js',
    gltf: 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js',
    fbx: 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/FBXLoader.js',
    fflate: 'https://cdn.jsdelivr.net/npm/fflate@0.8.0/umd/index.js',
  };

  var loadPromise = null;
  var loadersPromise = null;

  function prefersReducedMotion() {
    try {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (_e) {
      return false;
    }
  }

  function isMobile() {
    try {
      return window.matchMedia('(max-width: 680px)').matches;
    } catch (_e) {
      return false;
    }
  }

  function webglAvailable() {
    try {
      var canvas = document.createElement('canvas');
      return !!(
        window.WebGLRenderingContext &&
        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
      );
    } catch (_e) {
      return false;
    }
  }

  function canBoot(options) {
    options = options || {};
    if (options.requireWebGL !== false && !webglAvailable()) return false;
    if (options.respectReducedMotion !== false && prefersReducedMotion()) return false;
    if (options.skipMobile && isMobile()) return false;
    return true;
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var existing = document.querySelector('script[data-melodia-three="' + src + '"]');
      if (existing) {
        if (existing.getAttribute('data-loaded') === '1') return resolve();
        existing.addEventListener('load', function () { resolve(); });
        existing.addEventListener('error', function () { reject(new Error(src)); });
        return;
      }
      var s = document.createElement('script');
      s.src = src;
      s.async = false;
      s.setAttribute('data-melodia-three', src);
      s.onload = function () {
        s.setAttribute('data-loaded', '1');
        resolve();
      };
      s.onerror = function () {
        reject(new Error('Failed to load ' + src));
      };
      document.head.appendChild(s);
    });
  }

  function ensureThree() {
    if (typeof THREE !== 'undefined') return Promise.resolve(THREE);
    if (loadPromise) return loadPromise;
    loadPromise = loadScript(CDN.three).then(function () {
      if (typeof THREE === 'undefined') throw new Error('THREE global missing after load');
      return THREE;
    });
    return loadPromise;
  }

  function ensureOrbitControls() {
    return ensureThree().then(function () {
      if (THREE.OrbitControls) return THREE;
      return loadScript(CDN.orbit).then(function () { return THREE; });
    });
  }

  function ensureLoaders(kinds) {
    kinds = kinds || ['obj', 'gltf', 'fbx'];
    return ensureThree().then(function () {
      if (loadersPromise) return loadersPromise;
      var chain = Promise.resolve();
      var needFflate = kinds.indexOf('fbx') !== -1 && typeof fflate === 'undefined';
      if (needFflate) {
        chain = chain.then(function () { return loadScript(CDN.fflate); });
      }
      kinds.forEach(function (kind) {
        var src = CDN[kind];
        if (!src) return;
        var already =
          (kind === 'obj' && THREE.OBJLoader) ||
          (kind === 'gltf' && THREE.GLTFLoader) ||
          (kind === 'fbx' && THREE.FBXLoader);
        if (already) return;
        chain = chain.then(function () { return loadScript(src); });
      });
      loadersPromise = chain.then(function () { return THREE; });
      return loadersPromise;
    });
  }

  function createRenderer(container, opts) {
    opts = opts || {};
    var width = container.clientWidth || opts.width || 800;
    var height = container.clientHeight || opts.height || 450;
    var renderer = new THREE.WebGLRenderer({
      antialias: opts.antialias !== false,
      alpha: opts.alpha !== false,
      powerPreference: opts.powerPreference || 'high-performance',
    });
    renderer.setSize(width, height, false);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, opts.maxDpr || 2));
    if (opts.clearAlpha != null) renderer.setClearColor(opts.clearColor || 0x000000, opts.clearAlpha);
    else if (opts.clearColor != null) renderer.setClearColor(opts.clearColor, 1);
    renderer.domElement.className = (opts.className || 'melodia-three-canvas') + '';
    renderer.domElement.setAttribute('aria-hidden', 'true');
    container.appendChild(renderer.domElement);
    return renderer;
  }

  function bindResize(renderer, camera, container, onResize) {
    function handle() {
      var w = container.clientWidth || 1;
      var h = container.clientHeight || 1;
      if (camera && camera.isPerspectiveCamera) {
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      }
      renderer.setSize(w, h, false);
      if (typeof onResize === 'function') onResize(w, h);
    }
    window.addEventListener('resize', handle);
    return function dispose() {
      window.removeEventListener('resize', handle);
    };
  }

  function startLoop(tick) {
    var raf = 0;
    var running = true;
    function frame(t) {
      if (!running) return;
      raf = requestAnimationFrame(frame);
      tick(t);
    }
    raf = requestAnimationFrame(frame);
    return function stop() {
      running = false;
      if (raf) cancelAnimationFrame(raf);
    };
  }

  function disposeObject3D(root) {
    if (!root) return;
    root.traverse(function (obj) {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        var mats = Array.isArray(obj.material) ? obj.material : [obj.material];
        mats.forEach(function (m) {
          if (!m) return;
          Object.keys(m).forEach(function (key) {
            var v = m[key];
            if (v && v.isTexture) v.dispose();
          });
          m.dispose();
        });
      }
    });
  }

  function brandColors() {
    return {
      ivory: 0xf7f4ef,
      gold: 0xc9a86a,
      goldDeep: 0xb08d4f,
      astral: 0x3c5c9e,
      astralNight: 0x141a30,
      lavender: 0x9f94c6,
      plum: 0x241b2e,
      sakura: 0xd6a9b0,
      cyan: 0x66d9ff,
      magenta: 0xff6eb4,
    };
  }

  global.MelodiaThreeCore = {
    CDN: CDN,
    prefersReducedMotion: prefersReducedMotion,
    isMobile: isMobile,
    webglAvailable: webglAvailable,
    canBoot: canBoot,
    ensureThree: ensureThree,
    ensureOrbitControls: ensureOrbitControls,
    ensureLoaders: ensureLoaders,
    createRenderer: createRenderer,
    bindResize: bindResize,
    startLoop: startLoop,
    disposeObject3D: disposeObject3D,
    brandColors: brandColors,
  };
})(typeof window !== 'undefined' ? window : this);
