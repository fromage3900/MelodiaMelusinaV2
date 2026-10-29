// Resonant Wilds URL presentation flags.
// Live publish is Nikki-by-default: worldexp + dense dressing + nikkilook + daycycle + soft postfx.
// Escape hatch for low-end / A-B: ?lite=1 (or any flag=0 / dressing=sparse).

const q = typeof location !== 'undefined'
  ? new URLSearchParams(location.search)
  : new URLSearchParams();

/** Low-end / sparse escape — turns Nikki presentation off unless a flag is explicitly =1. */
export const liteMode = q.get('lite') === '1';

function onByDefault(key) {
  const v = q.get(key);
  if (liteMode) return v === '1';
  if (v === '0') return false;
  if (v === '1') return true;
  return true;
}

/** Named destinations, Dew, overlooks, fashion frames, dense exploration density. */
export const flagWorldexp = onByDefault('worldexp');

/** Landmark silhouette scale (OW_RULES.landmarkScale). */
export const flagNikkiLook = onByDefault('nikkilook');

/** Soft day/night light swing. */
export const flagDaycycle = onByDefault('daycycle');

/** OutlinePass + selective bloom (phones still pay for it when not lite — use ?postfx=0 or ?lite=1). */
export const flagPostfx = onByDefault('postfx');

/**
 * Dense biome prop budgets. Explicit dressing=dense keeps the old URL;
 * dressing=sparse|0|lite forces sparse; otherwise Nikki default = dense.
 */
export const flagDressingDense = (() => {
  const v = q.get('dressing');
  if (liteMode) return v === 'dense';
  if (v === '0' || v === 'sparse' || v === 'lite') return false;
  if (v === 'dense') return true;
  return true;
})();

export function flagSnapshot() {
  return {
    lite: liteMode,
    worldexp: flagWorldexp,
    dressingDense: flagDressingDense,
    nikkilook: flagNikkiLook,
    daycycle: flagDaycycle,
    postfx: flagPostfx,
  };
}
