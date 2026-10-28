// Resonant Wilds NPR live look tuner. Loaded ONLY when ?tune=1.
// No new framework, no gameplay/save changes. Preset links are fully shareable.
import { nprV2, setNPRInkOpacity, setNPRShadowTint } from './cel.js';

const PRESETS = Object.freeze({
  soft:      { strength: 0.36, radius: 2, anisotropy: 1.50, edgeProtect: 3.30, shadow: 0.60, ink: 0.66, scale: 0.50 },
  storybook: { strength: 0.53, radius: 2, anisotropy: 1.85, edgeProtect: 2.80, shadow: 0.82, ink: 0.85, scale: 0.50 },
  dream:     { strength: 0.70, radius: 3, anisotropy: 2.65, edgeProtect: 3.70, shadow: 0.98, ink: 0.96, scale: 0.50 },
});
const FIELDS = [
  { key: 'strength', query: 'paint', label: 'Painterly strength', min: 0, max: 1, step: 0.01 },
  { key: 'radius', query: 'rad', label: 'Brush radius', min: 1, max: 3, step: 1 },
  { key: 'anisotropy', query: 'anis', label: 'Stroke direction', min: 1, max: 3.2, step: 0.05 },
  { key: 'edgeProtect', query: 'edge', label: 'Edge preservation', min: 1, max: 4.5, step: 0.1 },
  { key: 'shadow', query: 'shadow', label: 'Shadow colour', min: 0, max: 1, step: 0.01 },
  { key: 'ink', query: 'ink', label: 'Ink opacity', min: 0, max: 1, step: 0.01 },
  { key: 'scale', query: 'scale', label: 'Render resolution', min: 0.25, max: 0.75, step: 0.05 },
];
function bounded(key, value, coarse) {
  const f = FIELDS.find(item => item.key === key);
  if (!f) return undefined;
  const upper = key === 'scale' && coarse ? 0.5 : f.max;
  const n = Number(value);
  if (!Number.isFinite(n)) return undefined;
  return Math.max(f.min, Math.min(upper, key === 'radius' ? Math.round(n) : n));
}
function fmt(f, v) { return f.step === 1 ? String(Math.round(v)) : Number(v).toFixed(2); }

export function attachShaderTuner(game) {
  const params = new URLSearchParams(location.search);
  if (!game.painterly || !nprV2) {
    const a = document.createElement('a');
    const url = new URL(location.href);
    url.searchParams.set('npr', 'v2');
    url.searchParams.set('kuwahara', '1');
    url.searchParams.set('tune', '1');
    a.href = url.href;
    a.textContent = 'Enable NPR V2 + painterly tuning';
    a.style.cssText = 'position:fixed;z-index:9999;right:12px;top:12px;padding:12px 16px;border-radius:12px;background:#302344;color:#fff;font:600 14px system-ui';
    document.body.append(a);
    return { enabled: false, panel: a };
  }
  const presetName = params.get('look');
  const chosen = Object.hasOwn(PRESETS, presetName) ? presetName : 'storybook';
  const coarse = game.painterly.coarse;
  let state = { ...PRESETS[chosen], scale: coarse ? 0.35 : PRESETS[chosen].scale };
  for (const field of FIELDS) {
    if (!params.has(field.query)) continue;
    const value = bounded(field.key, params.get(field.query), coarse);
    if (value !== undefined) state[field.key] = value;
  }
  let look = chosen;

  const host = document.createElement('aside');
  host.id = 'npr-tuner';
  host.style.cssText = 'position:fixed;right:12px;top:12px;z-index:9999;width:min(304px,calc(100vw - 24px));font-family:system-ui,-apple-system,sans-serif;';
  const root = host.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = [
    ':host{color-scheme:dark} *{box-sizing:border-box} details{overflow:hidden;border-radius:14px;background:rgba(38,27,64,.96);border:1px solid #b3a0d7;box-shadow:0 8px 32px #120b2899;color:#f8f1ff;font-size:12px}',
    'summary{cursor:pointer;padding:13px 14px;font-size:13px;font-weight:800;list-style:none;display:flex;justify-content:space-between;align-items:center} summary::-webkit-details-marker{display:none}',
    '.body{padding:0 13px 13px;max-height:min(72vh,650px);overflow:auto} .lead{color:#d2c6ed;line-height:1.5;margin:0 0 12px} .presets{display:flex;gap:5px;margin-bottom:13px}',
    'button{cursor:pointer;font:inherit;color:#fff;border-radius:8px;background:#544179;border:1px solid #8973b0;padding:7px 8px} button.active{background:#8171b5;border-color:#d8c3ff} button:hover{background:#705690}',
    '.field{display:block;margin:0 0 11px}.field-head{display:flex;justify-content:space-between;margin-bottom:4px;color:#f1e8ff}.value{color:#a9edf4;font-variant-numeric:tabular-nums}',
    'input[type=range]{width:100%;margin:0;accent-color:#b8a4f0;min-height:22px} .foot{display:flex;align-items:center;gap:7px;margin-top:8px} .foot button{flex:1}.tip{color:#bfb1d5;margin-top:7px;font-size:11px;line-height:1.45}',
  ].join('\n');
  const details = document.createElement('details');
  details.open = !coarse;
  const summary = document.createElement('summary');
  summary.textContent = '✧ NPR V2 · Live look lab';
  const arrow = document.createElement('span');
  arrow.textContent = '☰';
  summary.append(arrow);
  details.append(summary);
  const body = document.createElement('div');
  body.className = 'body';
  const lead = document.createElement('p');
  lead.className = 'lead';
  lead.textContent = 'Tune the actual GPU shader while the game runs. No gameplay settings change.';
  body.append(lead);

  const presetRow = document.createElement('div');
  presetRow.className = 'presets';
  const presetButtons = {};
  for (const [key, label] of [['soft','Soft wash'],['storybook','Storybook'],['dream','Dream']]) {
    const btn = document.createElement('button');
    btn.type = 'button'; btn.textContent = label;
    btn.addEventListener('click', () => apply(PRESETS[key], key));
    presetRow.append(btn); presetButtons[key] = btn;
  }
  body.append(presetRow);
  const inputs = {}, values = {};
  for (const field of FIELDS) {
    const label = document.createElement('label'); label.className = 'field';
    const top = document.createElement('span'); top.className = 'field-head';
    const name = document.createElement('span'); name.textContent = field.label;
    const value = document.createElement('span'); value.className = 'value';
    top.append(name,value);
    const input = document.createElement('input');
    input.type = 'range'; input.min = String(field.min);
    input.max = String(field.key === 'scale' && coarse ? 0.5 : field.max);
    input.step = String(field.step);
    input.setAttribute('aria-label', field.label);
    input.addEventListener('input', () => apply({ [field.key]: input.value }, 'custom'));
    label.append(top,input); body.append(label);
    inputs[field.key] = input; values[field.key] = value;
  }
  const footer = document.createElement('div'); footer.className = 'foot';
  const share = document.createElement('button'); share.textContent = 'Copy this look';
  share.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(location.href);
      share.textContent = 'Copied ✓';
    } catch {
      share.textContent = 'Copy from address bar';
    }
  });
  const hide = document.createElement('button'); hide.textContent = 'Collapse';
  hide.addEventListener('click', () => { details.open = false; });
  footer.append(share, hide); body.append(footer);
  const tip = document.createElement('p'); tip.className = 'tip';
  tip.textContent = 'Paint is opt-in. Lower render resolution on mobile for FPS. URL stores all settings for side-by-side screenshots.';
  body.append(tip);
  details.append(body); root.append(style, details); document.body.append(host);
  // Prevent the in-game pointer controls from capturing slider interactions.
  for (const event of ['pointerdown','pointermove','pointerup','touchstart','touchmove','touchend','wheel']) {
    host.addEventListener(event, e => e.stopPropagation(), { passive: true });
  }

  function apply(changes, selected = 'custom', updateUrl = true) {
    for (const [key, raw] of Object.entries(changes)) {
      const n = bounded(key, raw, coarse);
      if (n !== undefined) state[key] = n;
    }
    const actual = game.painterly.applySettings(state);
    Object.assign(state, actual);
    state.shadow = setNPRShadowTint(state.shadow);
    state.ink = setNPRInkOpacity(state.ink);
    look = selected;
    for (const field of FIELDS) {
      inputs[field.key].value = String(state[field.key]);
      values[field.key].textContent = fmt(field, state[field.key]);
    }
    for (const [key, btn] of Object.entries(presetButtons)) btn.classList.toggle('active', key === look);
    if (updateUrl) {
      const url = new URL(location.href);
      url.searchParams.set('look', look);
      for (const field of FIELDS) url.searchParams.set(field.query, String(Number(state[field.key].toFixed(3))));
      history.replaceState(history.state, '', url.href);
    }
    return { ...state };
  }
  apply(state, chosen, false);
  return {
    enabled: true, panel: host, apply,
    state: () => ({ ...state }),
    get look() { return look; },
    presets: PRESETS,
  };
}
