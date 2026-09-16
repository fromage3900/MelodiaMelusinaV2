export const DEFAULT_HERO = 'aviator-tortoise';

export const HEROES = {
  'rect-tortoise': {
    label: 'Rectangular · Tortoise',
    url: '../../../wix/models/eyewear-heroes/rect-tortoise.glb',
  },
  'panto-tortoise': {
    label: 'Panto · Tortoise',
    url: '../../../wix/models/eyewear-heroes/panto-tortoise.glb',
  },
  'cateye-tortoise': {
    label: 'Cat-Eye · Tortoise',
    url: '../../../wix/models/eyewear-heroes/cateye-tortoise.glb',
  },
  'aviator-tortoise': {
    label: 'Aviator · Tortoise',
    url: '../../../wix/models/eyewear-heroes/aviator-tortoise.glb',
  },
  'rect-metal': {
    label: 'Rectangular · Champagne',
    url: '../../../wix/models/eyewear-heroes/rect-metal.glb',
  },
  'panto-metal': {
    label: 'Panto · Champagne',
    url: '../../../wix/models/eyewear-heroes/panto-metal.glb',
  },
  'cateye-metal': {
    label: 'Cat-Eye · Champagne',
    url: '../../../wix/models/eyewear-heroes/cateye-metal.glb',
  },
  'aviator-metal': {
    label: 'Aviator · Champagne',
    url: '../../../wix/models/eyewear-heroes/aviator-metal.glb',
  },
};

export function heroOptions() {
  return Object.entries(HEROES).map(([id, hero]) => ({ id, ...hero }));
}
