// Resonant Wilds — cel-only shader controls. Loaded only with ?tune=1.
// No postprocessing or offscreen render targets; URL links reproduce the look.
import { nprV2, setNPRInkOpacity, setNPRShadowTint, setNPRBands } from './cel.js';

const PRESETS = Object.freeze({
  soft: { shadow: 0.60, ink: 0.66, hardness: 0.82, threshold: 0.48, depth: 0.55 },
  storybook: { shadow: 0.82, ink: 0.85, hardness: 0.98, threshold: 0.49, depth: 0.39 },
  dream: { shadow: 0.98, ink: 0.96, hardness: 1.00, threshold: 0.54, depth: 0.26 },
});
const FIELDS = [
  { key: 'shadow', query: 'shadow', label: 'Shadow colour', min: 0, max: 1, step: 0.01 },
  { key: 'hardness', query: 'hard', label: 'Band hardness', min: 0, max: 1, step: 0.01 },
  { key: 'threshold', query: 'cut', label: 'Shadow cutoff', min: 0.28, max: 0.70, step: 0.01 },
  { key: 'depth', query: 'dark', label: 'Shadow darkness', min: 0.15, max: 1, step: 0.01 },
  { key: 'ink', query: 'ink', label: 'Ink opacity', min: 0, max: 1, step: 0.01 },
];
const bound = (f, value) => {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(f.max, Math.max(f.min, n)) : undefined;
};
export function attachShaderTuner(game) {
  const params = new URLSearchParams(location.search);
  if (!nprV2) {
    const link = document.createElement('a');
    const url = new URL(location.href);
    url.searchParams.set('npr', 'v2');
    url.searchParams.set('tune', '1');
    link.href = url.href;
    link.textContent = 'Enable cel-shading tuner';
    link.style.cssText = 'position:fixed;z-index:9999;right:12px;top:12px;padding:12px 16px;border-radius:12px;background:#302344;color:#fff;font:600 14px system-ui';
    document.body.append(link);
    return { enabled: false, panel: link };
  }
  const presetName = params.get('look');
  const chosen = Object.hasOwn(PRESETS, presetName) ? presetName : 'storybook';
  let state = { ...PRESETS[chosen] };
  for (const f of FIELDS) {
    if (params.has(f.query)) {
      const v = bound(f, params.get(f.query));
      if (v !== undefined) state[f.key] = v;
    }
  }
  let look = chosen;
  const host = document.createElement('aside');
  host.id = 'npr-tuner';
  host.style.cssText = 'position:fixed;right:12px;top:12px;z-index:9999;width:min(304px,calc(100vw - 24px));font-family:system-ui,-apple-system,sans-serif;';
  const root = host.attachShadow({ mode: 'open' });
  const css = document.createElement('style');
  css.textContent = [
    ':host{color-scheme:dark} *{box-sizing:border-box} details{overflow:hidden;border-radius:14px;background:rgba(38,27,64,.96);border:1px solid #b3a0d7;box-shadow:0 8px 32px #120b2899;color:#f8f1ff;font-size:12px}',
    'summary{cursor:pointer;padding:13px 14px;font-size:13px;font-weight:800;list-style:none;display:flex;justify-content:space-between} summary::-webkit-details-marker{display:none}',
    '.body{padding:0 13px 13px;max-height:min(72vh,650px);overflow:auto}.lead{color:#d2c6ed;line-height:1.5;margin:0 0 12px}.presets{display:flex;gap:5px;margin-bottom:13px}',
    'button{cursor:pointer;font:inherit;color:#fff;border-radius:8px;background:#544179;border:1px solid #8973b0;padding:7px 8px} button.active{background:#8171b5;border-color:#d8c3ff}',
    '.field{display:block;margin:0 0 11px}.field-head{display:flex;justify-content:space-between;margin-bottom:4px;color:#f1e8ff}.value{color:#a9edf4;font-variant-numeric:tabular-nums}',
    'input[type=range]{width:100%;margin:0;accent-color:#b8a4f0;min-height:22px}.foot{display:flex;gap:7px;margin-top:8px}.foot button{flex:1}.tip{color:#bfb1d5;margin-top:7px;font-size:11px;line-height:1.45}',
  ].join('\n');
  const details = document.createElement('details');
  details.open = !matchMedia('(pointer:coarse)').matches;
  const summary = document.createElement('summary');
  summary.textContent = '✧ NPR V2 · Cel lighting';
  const arrow = document.createElement('span');
  arrow.textContent = '☰';
  summary.append(arrow); details.append(summary);
  const body = document.createElement('div');
  body.className = 'body';
  const lead = document.createElement('p'); lead.className = 'lead';
  lead.textContent = 'Tune hard cel bands, shadow colours and outlines directly. No blur filter or extra GPU pass.';
  body.append(lead);
  const presetRow = document.createElement('div');
  presetRow.className = 'presets';
  const buttons = {};
  for (const [key, label] of [['soft','Soft cel'],['storybook','Storybook'],['dream','Hard ink']]) {
    const btn = document.createElement('button'); btn.type = 'button'; btn.textContent = label;
    btn.addEventListener('click', () => apply(PRESETS[key], key));
    presetRow.append(btn); buttons[key] = btn;
  }
  body.append(presetRow);
  const inputs = {}, values = {};
  for (const f of FIELDS) {
    const label = document.createElement('label'); label.className = 'field';
    const top = document.createElement('span'); top.className = 'field-head';
    const name = document.createElement('span'); name.textContent = f.label;
    const value = document.createElement('span'); value.className = 'value';
    top.append(name, value);
    const input = document.createElement('input');
    input.type = 'range'; input.min = String(f.min); input.max = String(f.max); input.step = String(f.step);
    input.setAttribute('aria-label', f.label);
    input.addEventListener('input', () => apply({ [f.key]: input.value }, 'custom'));
    label.append(top, input); body.append(label);
    inputs[f.key] = input; values[f.key] = value;
  }
  const footer = document.createElement('div'); footer.className = 'foot';
  const copy = document.createElement('button'); copy.textContent = 'Copy this look';
  copy.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(location.href); copy.textContent = 'Copied ✓'; }
    catch { copy.textContent = 'Copy from address bar'; }
  });
  const hide = document.createElement('button'); hide.textContent = 'Collapse';
  hide.addEventListener('click', () => { details.open = false; });
  footer.append(copy, hide); body.append(footer);
  const tip = document.createElement('p'); tip.className = 'tip';
  tip.textContent = 'Shareable URL saves all five cel values. Legacy painterly URL parameters are ignored.';
  body.append(tip); details.append(body);
  root.append(css, details); document.body.append(host);
  for (const event of ['pointerdown','pointermove','pointerup','touchstart','touchmove','touchend','wheel']) {
    host.addEventListener(event, e => e.stopPropagation(), { passive: true });
  }
  function apply(changes, selected = 'custom', updateURL = true) {
    for (const f of FIELDS) {
      if (!(f.key in changes)) continue;
      const value = bound(f, changes[f.key]);
      if (value !== undefined) state[f.key] = value;
    }
    state.shadow = setNPRShadowTint(state.shadow);
    state.ink = setNPRInkOpacity(state.ink);
    Object.assign(state, setNPRBands({
      hardness: state.hardness, threshold: state.threshold, depth: state.depth,
    }));
    look = selected;
    for (const f of FIELDS) {
      inputs[f.key].value = String(state[f.key]);
      values[f.key].textContent = state[f.key].toFixed(2);
    }
    for (const [key, button] of Object.entries(buttons)) button.classList.toggle('active', key === look);
    if (updateURL) {
      const url = new URL(location.href);
      url.searchParams.set('look', look);
      // Remove retired shader parameters from copied links.
      for (const dead of ['kuwahara','paint','rad','anis','edge','scale']) url.searchParams.delete(dead);
      for (const f of FIELDS) url.searchParams.set(f.query, String(Number(state[f.key].toFixed(3))));
      history.replaceState(history.state, '', url.href);
    }
    return { ...state };
  }
  apply(state, chosen, false);
  return { enabled: true, panel: host, apply, state: () => ({ ...state }), get look() { return look; }, presets: PRESETS };
}
