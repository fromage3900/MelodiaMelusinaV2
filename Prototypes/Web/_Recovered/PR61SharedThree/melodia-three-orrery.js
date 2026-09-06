/**
 * MelodiaThreeOrrery — WebGL armillary / celestial rings for [data-three-orrery] mounts.
 * Complements CSS MelodiaOrrery; does not replace hero CSS rings unless mount is present.
 */
(function (global) {
  'use strict';

  var instances = [];

  function Core() {
    return global.MelodiaThreeCore;
  }

  function ringMesh(radius, tube, color, opacity) {
    var geo = new THREE.TorusGeometry(radius, tube, 12, 96);
    var mat = new THREE.MeshStandardMaterial({
      color: color,
      metalness: 0.85,
      roughness: 0.28,
      emissive: color,
      emissiveIntensity: 0.22,
      transparent: true,
      opacity: opacity,
    });
    return new THREE.Mesh(geo, mat);
  }

  function nodeSphere(r, color) {
    var geo = new THREE.SphereGeometry(r, 16, 16);
    var mat = new THREE.MeshStandardMaterial({
      color: color,
      emissive: color,
      emissiveIntensity: 0.55,
      metalness: 0.4,
      roughness: 0.35,
    });
    return new THREE.Mesh(geo, mat);
  }

  function OrreryInstance(el, options) {
    this.el = el;
    this.options = options || {};
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.rig = null;
    this.stopLoop = null;
    this.unresize = null;
    this.pointerBound = false;
    this.yaw = 0;
    this.pitch = 0.35;
    this.targetYaw = 0;
    this.targetPitch = 0.35;
  }

  OrreryInstance.prototype.build = function () {
    var self = this;
    var core = Core();
    var colors = core.brandColors();
    var sizeHint = parseFloat(this.el.getAttribute('data-orrery-size') || '1') || 1;

    this.el.classList.add('melodia-three-orrery');
    this.el.innerHTML = '';

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    this.camera.position.set(0, 0.4, 6.2);

    this.renderer = core.createRenderer(this.el, {
      alpha: true,
      clearAlpha: 0,
      className: 'melodia-three-canvas melodia-three-orrery-canvas',
      maxDpr: 2,
    });

    this.scene.add(new THREE.AmbientLight(0xfff5ea, 0.55));
    var key = new THREE.DirectionalLight(0xffeedd, 1.1);
    key.position.set(3, 4, 2);
    this.scene.add(key);
    var fill = new THREE.DirectionalLight(colors.astral, 0.55);
    fill.position.set(-2, 1, -3);
    this.scene.add(fill);
    var rim = new THREE.PointLight(colors.magenta, 0.9, 12);
    rim.position.set(0, -1, 2);
    this.scene.add(rim);

    this.rig = new THREE.Group();
    this.scene.add(this.rig);

    var coreBall = nodeSphere(0.28 * sizeHint, colors.gold);
    this.rig.add(coreBall);

    var specs = [
      { r: 0.85, t: 0.018, c: colors.gold, o: 0.9, rx: 1.2, ry: 0.2, speed: 0.35 },
      { r: 1.25, t: 0.014, c: colors.magenta, o: 0.7, rx: 0.4, ry: 0.9, speed: -0.22 },
      { r: 1.7, t: 0.012, c: colors.lavender, o: 0.55, rx: 1.0, ry: -0.5, speed: 0.16 },
      { r: 2.15, t: 0.01, c: colors.cyan, o: 0.42, rx: 0.2, ry: 1.1, speed: -0.11 },
      { r: 2.65, t: 0.008, c: colors.astral, o: 0.32, rx: 1.4, ry: 0.3, speed: 0.08 },
    ];

    this.rings = specs.map(function (s) {
      var g = new THREE.Group();
      g.rotation.x = s.rx;
      g.rotation.y = s.ry;
      var mesh = ringMesh(s.r * sizeHint, s.t * sizeHint, s.c, s.o);
      g.add(mesh);
      var node = nodeSphere(0.06 * sizeHint, s.c);
      node.position.set(s.r * sizeHint, 0, 0);
      g.add(node);
      self.rig.add(g);
      return { group: g, speed: s.speed };
    });

    // Meridian ellipse (thin)
    var mer = ringMesh(1.95 * sizeHint, 0.006 * sizeHint, colors.ivory, 0.28);
    mer.rotation.x = Math.PI / 2;
    mer.rotation.z = 0.4;
    this.rig.add(mer);

    this.unresize = core.bindResize(this.renderer, this.camera, this.el);

    this.el.addEventListener('pointerdown', function () { self.pointerBound = true; });
    window.addEventListener('pointerup', function () { self.pointerBound = false; });
    this.el.addEventListener('pointermove', function (e) {
      if (!self.pointerBound) return;
      self.targetYaw += e.movementX * 0.008;
      self.targetPitch = Math.max(-0.6, Math.min(1.1, self.targetPitch + e.movementY * 0.006));
    });

    var t0 = performance.now();
    this.stopLoop = core.startLoop(function (now) {
      var t = (now - t0) * 0.001;
      if (!self.pointerBound) self.targetYaw += 0.0035;
      self.yaw += (self.targetYaw - self.yaw) * 0.08;
      self.pitch += (self.targetPitch - self.pitch) * 0.08;
      self.rig.rotation.y = self.yaw;
      self.rig.rotation.x = self.pitch;
      self.rings.forEach(function (r) {
        r.group.rotation.z += r.speed * 0.016;
      });
      coreBall.scale.setScalar(1 + Math.sin(t * 2.2) * 0.04);
      self.renderer.render(self.scene, self.camera);
    });

    this.el.setAttribute('data-three-orrery-live', '1');
  };

  OrreryInstance.prototype.destroy = function () {
    var core = Core();
    if (this.stopLoop) this.stopLoop();
    if (this.unresize) this.unresize();
    if (this.rig) core.disposeObject3D(this.rig);
    if (this.renderer) {
      this.renderer.dispose();
      if (this.renderer.domElement && this.renderer.domElement.parentNode) {
        this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
      }
    }
  };

  function mountAll(options) {
    var core = Core();
    if (!core || !core.canBoot({})) return Promise.resolve([]);

    var nodes = document.querySelectorAll('[data-three-orrery]');
    if (!nodes.length) return Promise.resolve([]);

    return core.ensureThree().then(function () {
      // Tear previous
      instances.forEach(function (inst) { inst.destroy(); });
      instances = [];
      Array.prototype.forEach.call(nodes, function (el) {
        var inst = new OrreryInstance(el, options);
        inst.build();
        instances.push(inst);
      });
      document.documentElement.setAttribute('data-three-orrery', 'live');
      return instances;
    }).catch(function (err) {
      console.warn('[MelodiaThreeOrrery]', err);
      return [];
    });
  }

  global.MelodiaThreeOrrery = {
    mountAll: mountAll,
    instances: function () { return instances; },
  };
})(typeof window !== 'undefined' ? window : this);
