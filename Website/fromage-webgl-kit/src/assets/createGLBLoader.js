export function createGLBLoader({ GLTFLoader, manager } = {}) {
  if (!GLTFLoader) throw new Error('createGLBLoader requires GLTFLoader.');

  const loader = new GLTFLoader(manager);

  function load(url, { onProgress } = {}) {
    if (!url) return Promise.reject(new Error('GLB URL is required.'));

    return new Promise((resolve, reject) => {
      loader.load(
        url,
        (gltf) => resolve(gltf),
        (event) => {
          if (typeof onProgress !== 'function') return;
          const total = Number(event.total) || 0;
          const loaded = Number(event.loaded) || 0;
          onProgress({
            loaded,
            total,
            ratio: total > 0 ? Math.min(1, loaded / total) : null,
          });
        },
        (error) => reject(error instanceof Error ? error : new Error('Failed to load GLB.')),
      );
    });
  }

  function prepareScene(root, { castShadow = true, receiveShadow = true } = {}) {
    root?.traverse?.((object) => {
      if (!object?.isMesh) return;
      object.castShadow = castShadow;
      object.receiveShadow = receiveShadow;
    });
    return root;
  }

  return { loader, load, prepareScene };
}
