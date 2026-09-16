export function createRuntime({
  THREE,
  container,
  camera = {},
  renderer = {},
  pixelRatioCap = 2,
  autoStart = true,
} = {}) {
  if (!THREE) throw new Error('createRuntime requires THREE.');
  if (!container) throw new Error('createRuntime requires a container element.');

  const scene = new THREE.Scene();
  const view = new THREE.PerspectiveCamera(
    camera.fov ?? 45,
    1,
    camera.near ?? 0.1,
    camera.far ?? 1000,
  );
  view.position.set(
    camera.x ?? 0,
    camera.y ?? 0,
    camera.z ?? 5,
  );

  const webgl = new THREE.WebGLRenderer({
    antialias: renderer.antialias ?? true,
    alpha: renderer.alpha ?? true,
    powerPreference: renderer.powerPreference ?? 'high-performance',
  });

  if ('outputColorSpace' in webgl && THREE.SRGBColorSpace) {
    webgl.outputColorSpace = THREE.SRGBColorSpace;
  }

  webgl.setPixelRatio(Math.min(window.devicePixelRatio || 1, pixelRatioCap));
  container.appendChild(webgl.domElement);

  const frameCallbacks = new Set();
  let frameId = 0;
  let running = false;
  let lastTime = performance.now();

  function resize() {
    const width = Math.max(1, container.clientWidth || 1);
    const height = Math.max(1, container.clientHeight || 1);
    view.aspect = width / height;
    view.updateProjectionMatrix();
    webgl.setSize(width, height, false);
  }

  function frame(now) {
    if (!running) return;
    const delta = Math.min((now - lastTime) / 1000, 0.1);
    lastTime = now;

    for (const callback of frameCallbacks) {
      callback({ delta, now, scene, camera: view, renderer: webgl });
    }

    webgl.render(scene, view);
    frameId = requestAnimationFrame(frame);
  }

  function start() {
    if (running) return;
    running = true;
    lastTime = performance.now();
    frameId = requestAnimationFrame(frame);
  }

  function stop() {
    running = false;
    if (frameId) cancelAnimationFrame(frameId);
    frameId = 0;
  }

  function onFrame(callback) {
    if (typeof callback !== 'function') throw new Error('onFrame requires a function.');
    frameCallbacks.add(callback);
    return () => frameCallbacks.delete(callback);
  }

  function disposeObject(root) {
    root?.traverse?.((object) => {
      object.geometry?.dispose?.();
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of materials) {
        if (!material) continue;
        for (const value of Object.values(material)) value?.isTexture && value.dispose?.();
        material.dispose?.();
      }
    });
  }

  function dispose() {
    stop();
    resizeObserver?.disconnect();
    window.removeEventListener('resize', resize);
    frameCallbacks.clear();
    disposeObject(scene);
    webgl.dispose();
    webgl.domElement.remove();
  }

  const resizeObserver = typeof ResizeObserver !== 'undefined'
    ? new ResizeObserver(resize)
    : null;

  if (resizeObserver) resizeObserver.observe(container);
  else window.addEventListener('resize', resize, { passive: true });

  resize();
  if (autoStart) start();

  return {
    scene,
    camera: view,
    renderer: webgl,
    resize,
    start,
    stop,
    onFrame,
    dispose,
    disposeObject,
  };
}
