export const DEFAULT_SILHOUETTE = 'aviator';
export const DEFAULT_VARIANT = 'Tortoise';
export const DEFAULT_HERO = DEFAULT_SILHOUETTE;

export const VARIANTS = ['Tortoise', 'Champagne'];

export const SILHOUETTES = {
  aviator: {
    label: 'Aviator',
    url: '../models/eyewear/aviator.glb',
  },
  cateye: {
    label: 'Cat-Eye',
    url: '../models/eyewear/cateye.glb',
  },
  panto: {
    label: 'Panto',
    url: '../models/eyewear/panto.glb',
  },
  rect: {
    label: 'Rectangular',
    url: '../models/eyewear/rect.glb',
  },
};

export const HEROES = SILHOUETTES;

export function heroOptions() {
  return Object.entries(SILHOUETTES).map(([id, hero]) => ({ id, ...hero }));
}
