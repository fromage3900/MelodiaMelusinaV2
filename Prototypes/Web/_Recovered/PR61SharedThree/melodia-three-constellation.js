/**
 * MelodiaThreeConstellation — interactive 3D world map of Melodia's four levels + Orrery pillar.
 * Mount: #three-constellation-mount or [data-three-constellation]
 */
(function (global) {
  'use strict';

  var instance = null;

  var WORLDS = [
    {
      id: 'morning',
      label: 'L_MelusinaMorning',
      tag: 'Opening Atelier',
      href: 'melodia-stage-character.html',
      color: 0xd6a9b0,
      pos: [-2.4, 0.6, 0.2],
    },
    {
      id: 'sakura',
      label: 'L_SakuraDream',
      tag: 'Nikki Proof',
      href: 'sakura-case-study.html',
      color: 0xc9a86a,
      pos: [-0.8, -0.4, 0.8],
    },
    {
      id: 'nave',
      label: 'L_KaleidoNave',
      tag: 'Space Cathedral',
      href: 'space-cathedral.html',
      color: 0x9f94c6,
      pos: [1.0, 0.5, -0.2],
    },
    {
      id: 'fallen',
      label: 'L_FallenMoon',
      tag: 'PCG Crater',
      href: 'pcg-system-impact.html',
      color: 0x3c5c9e,
      pos: [2.4, -0.35, 0.4],
    },
    {
      id: 'orrery',
      label: 'Cosmic Orrery',
      tag: 'Pillar',
      href: 'cosmic-orrery.html',
      color: 0x66d9ff,
      pos: [0.15, 1.35, -0.9],
    },
  ];

  var EDGES = [
    [0, 1],
    [1, 2],
    [2, 3],
    [1, 4],
    [2, 4],
    [0, 4],
  ];

  function Core() {
    return global.MelodiaThreeCore;
  }

  function makeLabelSprite(text, sub) {
    var canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 160;
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'rgba(20, 26, 48, 0.72)';
    ctx.strokeStyle = 'rgba(201, 168, 106, 0.55)';
    ctx.lineWidth = 2;
    roundRect(ctx, 16, 24, 480, 112, 12);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#F7F4EF';
    ctx.font = '600 36px "Syne", "Fraunces", Georgia, serif';
    ctx.fillText(text, 36, 78);
    ctx.fillStyle = '#C9A86A';
    ctx.font = '500 22px "IBM Plex Mono", monospace';
    ctx.fillText(sub.toUpperCase(), 36, 112);
    var tex = new THREE.CanvasTexture(canvas);
    tex.needsUpdate = true;
    var mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false });
    var sprite = new THREE.Sprite(mat);
    sprite.scale.set(1.6, 0.5, 1);
    return sprite;
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function Constellation(mount, options) {
    this.mount = mount;
    this.options = options || {};
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.root = null;
    this.nodes = [];
    this.raycaster = null;
    this.pointer = new THREE.Vector2();
    this.hud = null;
    this.stopLoop = null;
    this.unresize = null;
    this.hover = null;
  }

  Constellation.prototype.build = function () {
    var self = this;
    var core = Core();
    var colors = core.brandColors();

    this.mount.classList.add('melodia-three-constellation');
    this.mount.innerHTML = '';

    var stage = document.createElement('div');
    stage.className = 'melodia-three-constellation-stage';
    this.mount.appendChild(stage);

    this.hud = document.createElement('div');
    this.hud.className = 'melodia-three-constellation-hud';
    this.hud.innerHTML =
      '<span class="pill">✦ WebGL constellation</span>' +
      '<span class="hint">Drag to orbit · Click a world</span>' +
      '<a class="cta" href="realtime-3d-viewer.html">Open Realtime 3D Studio →</a>';
    this.mount.appendChild(this.hud);

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    this.camera.position.set(0, 1.2, 7.5);

    this.renderer = core.createRenderer(stage, {
      alpha: true,
      clearAlpha: 0,
      className: 'melodia-three-canvas melodia-three-constellation-canvas',
    });
    this.renderer.domElement.style.cursor = 'grab';

    this.scene.add(new THREE.AmbientLight(0xfff8ee, 0.5));
    var key = new THREE.DirectionalLight(0xffeedd, 1.0);
    key.position.set(4, 5, 3);
    this.scene.add(key);
    var rim = new THREE.PointLight(colors.gold, 0.8, 20);
    rim.position.set(-2, 2, 3);
    this.scene.add(rim);

    this.root = new THREE.Group();
    this.scene.add(this.root);

    // Soft void disc
    var disc = new THREE.Mesh(
      new THREE.CircleGeometry(4.2, 64),
      new THREE.MeshBasicMaterial({
        color: colors.astralNight,
        transparent: true,
        opacity: 0.35,
        side: THREE.DoubleSide,
      })
    );
    disc.rotation.x = -Math.PI / 2.4;
    disc.position.y = -1.4;
    this.root.add(disc);

    // Stars dust
    var dustCount = 180;
    var dustPos = new Float32Array(dustCount * 3);
    for (var i = 0; i < dustCount; i++) {
      dustPos[i * 3] = (Math.random() - 0.5) * 10;
      dustPos[i * 3 + 1] = (Math.random() - 0.5) * 5;
      dustPos[i * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    var dustGeo = new THREE.BufferGeometry();
    dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
    var dust = new THREE.Points(
      dustGeo,
      new THREE.PointsMaterial({
        color: colors.ivory,
        size: 0.035,
        transparent: true,
        opacity: 0.7,
        depthWrite: false,
      })
    );
    this.root.add(dust);

    // Edges
    var edgeMat = new THREE.LineBasicMaterial({
      color: colors.gold,
      transparent: true,
      opacity: 0.35,
    });
    EDGES.forEach(function (pair) {
      var a = WORLDS[pair[0]].pos;
      var b = WORLDS[pair[1]].pos;
      var geo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(a[0], a[1], a[2]),
        new THREE.Vector3(b[0], b[1], b[2]),
      ]);
      self.root.add(new THREE.Line(geo, edgeMat));
    });

    // Nodes
    this.nodes = WORLDS.map(function (world) {
      var group = new THREE.Group();
      group.position.set(world.pos[0], world.pos[1], world.pos[2]);
      group.userData = world;

      var glow = new THREE.Mesh(
        new THREE.SphereGeometry(0.28, 24, 24),
        new THREE.MeshBasicMaterial({
          color: world.color,
          transparent: true,
          opacity: 0.18,
          depthWrite: false,
        })
      );
      glow.scale.setScalar(1.8);
      group.add(glow);

      var coreSphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.22, 28, 28),
        new THREE.MeshStandardMaterial({
          color: world.color,
          emissive: world.color,
          emissiveIntensity: 0.45,
          metalness: 0.35,
          roughness: 0.4,
        })
      );
      group.add(coreSphere);

      var ring = new THREE.Mesh(
        new THREE.TorusGeometry(0.38, 0.018, 10, 48),
        new THREE.MeshStandardMaterial({
          color: colors.gold,
          metalness: 0.9,
          roughness: 0.25,
          emissive: colors.gold,
          emissiveIntensity: 0.2,
        })
      );
      ring.rotation.x = Math.PI / 2.5;
      group.add(ring);

      var label = makeLabelSprite(world.label, world.tag);
      label.position.set(0, 0.72, 0);
      group.add(label);

      self.root.add(group);
      return { group: group, core: coreSphere, glow: glow, ring: ring, world: world };
    });

    this.raycaster = new THREE.Raycaster();

    return core.ensureOrbitControls().then(function () {
      if (THREE.OrbitControls) {
        self.controls = new THREE.OrbitControls(self.camera, self.renderer.domElement);
        self.controls.enableDamping = true;
        self.controls.dampingFactor = 0.06;
        self.controls.enablePan = false;
        self.controls.minDistance = 4;
        self.controls.maxDistance = 12;
        self.controls.target.set(0, 0.2, 0);
        self.controls.autoRotate = !core.prefersReducedMotion();
        self.controls.autoRotateSpeed = 0.55;
      }

      self.unresize = core.bindResize(self.renderer, self.camera, stage);

      self.renderer.domElement.addEventListener('pointermove', function (e) {
        var rect = self.renderer.domElement.getBoundingClientRect();
        self.pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        self.pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      });

      self.renderer.domElement.addEventListener('click', function () {
        if (!self.hover) return;
        window.location.href = self.hover.world.href;
      });

      var t0 = performance.now();
      self.stopLoop = core.startLoop(function (now) {
        var t = (now - t0) * 0.001;
        if (self.controls) self.controls.update();

        self.nodes.forEach(function (n, idx) {
          n.ring.rotation.z = t * (0.4 + idx * 0.07);
          n.glow.scale.setScalar(1.7 + Math.sin(t * 2 + idx) * 0.12);
        });

        self.raycaster.setFromCamera(self.pointer, self.camera);
        var hits = self.raycaster.intersectObjects(
          self.nodes.map(function (n) { return n.core; }),
          false
        );
        var next = hits.length ? self.nodes.find(function (n) { return n.core === hits[0].object; }) : null;
        if (self.hover !== next) {
          if (self.hover) self.hover.core.scale.setScalar(1);
          self.hover = next;
          if (self.hover) self.hover.core.scale.setScalar(1.25);
          self.renderer.domElement.style.cursor = self.hover ? 'pointer' : 'grab';
          if (self.hud) {
            var hint = self.hud.querySelector('.hint');
            if (hint) {
              hint.textContent = self.hover
                ? 'Open ' + self.hover.world.label
                : 'Drag to orbit · Click a world';
            }
          }
        }

        self.renderer.render(self.scene, self.camera);
      });

      self.mount.setAttribute('data-three-constellation-live', '1');
      return true;
    });
  };

  Constellation.prototype.destroy = function () {
    var core = Core();
    if (this.stopLoop) this.stopLoop();
    if (this.unresize) this.unresize();
    if (this.controls && this.controls.dispose) this.controls.dispose();
    if (this.root) core.disposeObject3D(this.root);
    if (this.renderer) {
      this.renderer.dispose();
      if (this.renderer.domElement && this.renderer.domElement.parentNode) {
        this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
      }
    }
  };

  function mountAll(options) {
    var core = Core();
    if (!core || !core.canBoot({})) return Promise.resolve(false);

    var mount =
      document.getElementById('three-constellation-mount') ||
      document.querySelector('[data-three-constellation]');
    if (!mount) return Promise.resolve(false);

    return core.ensureThree().then(function () {
      if (instance) {
        instance.destroy();
        instance = null;
      }
      instance = new Constellation(mount, options || {});
      return instance.build();
    }).catch(function (err) {
      console.warn('[MelodiaThreeConstellation]', err);
      mount.innerHTML =
        '<p class="melodia-three-fallback">WebGL constellation unavailable — ' +
        '<a href="application-hub.html">browse worlds in the hub</a>.</p>';
      return false;
    });
  }

  global.MelodiaThreeConstellation = {
    mountAll: mountAll,
    WORLDS: WORLDS,
  };
})(typeof window !== 'undefined' ? window : this);
