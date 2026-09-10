// Melodia Design System Builder — Figma plugin
// Builds: 7-page structure, variable collections (Primitives, Semantic[Light/Dark],
// Spacing, Radius), text styles, effect styles, and core components
// (Star, Brand/Mark, Divider/Section, Row/Spec, Tag/Technical, Tag/Software,
// Card/Info, Brand/AssetPassport).
//
// Defensive by design: optional features (variable binding to fills, component
// properties) are wrapped in try/catch so the core still builds on older API
// versions. Run via: Plugins > Development > Import plugin from manifest > Run.

const log = [];
function note(msg) { log.push(msg); console.log("[Melodia] " + msg); }

// ---------- color helpers ----------
function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return {
    r: parseInt(h.substring(0, 2), 16) / 255,
    g: parseInt(h.substring(2, 4), 16) / 255,
    b: parseInt(h.substring(4, 6), 16) / 255,
  };
}
function solid(hex, opacity) {
  return { type: "SOLID", color: hexToRgb(hex), opacity: opacity == null ? 1 : opacity };
}

// ---------- token data (mirrors tokens.json / DESIGN-SYSTEM.md) ----------
const PRIMITIVES = {
  "ivory/50": "#FCFBF8", "ivory/100": "#F7F4EF", "ivory/200": "#EFEAE1", "ivory/300": "#E3DACE",
  "plum/500": "#6E6080", "plum/600": "#463A54", "plum/700": "#2E2438", "plum/800": "#241B2E", "plum/900": "#1C1426",
  "gold/100": "#F0E6D2", "gold/300": "#DDC79B", "gold/500": "#C9A86A", "gold/700": "#A7884E",
  "lavender/100": "#E8E4F2", "lavender/300": "#C2BAE0", "lavender/500": "#9F94C6",
  "sakura/100": "#F5E8EA", "sakura/300": "#E7C9CE", "sakura/500": "#D6A9B0",
  "astral/100": "#E5EAF5", "astral/300": "#8AA9D6", "astral/500": "#3C5C9E", "astral/700": "#26365E", "astral/900": "#141A30",
  "iris/100": "#ECE6F4", "iris/300": "#A99AD0", "iris/500": "#6E5AA6",
  "slate/200": "#D5D8DE", "slate/300": "#AEB4BF", "slate/400": "#828A98", "slate/500": "#5A6170", "slate/700": "#3C414B",
  "status/success": "#5E8B7E", "status/warning": "#B8862F", "status/error": "#A85751", "status/info": "#6B7CA8",
};

// semantic -> { light: primitiveName, dark: primitiveName }
const SEMANTIC = {
  "color/surface/base": { light: "ivory/100", dark: "astral/900" },
  "color/surface/raised": { light: "ivory/50", dark: "astral/700" },
  "color/surface/sunken": { light: "ivory/200", dark: "plum/900" },
  "color/surface/inverse": { light: "plum/800", dark: "ivory/100" },
  "color/text/primary": { light: "plum/800", dark: "ivory/50" },
  "color/text/secondary": { light: "slate/500", dark: "slate/300" },
  "color/text/tertiary": { light: "slate/400", dark: "slate/400" },
  "color/text/inverse": { light: "ivory/50", dark: "astral/900" },
  "color/text/accent": { light: "gold/700", dark: "gold/300" },
  "color/border/subtle": { light: "ivory/300", dark: "astral/700" },
  "color/border/default": { light: "slate/200", dark: "astral/500" },
  "color/border/strong": { light: "slate/300", dark: "iris/500" },
  "color/accent/primary": { light: "gold/500", dark: "gold/500" },
  "color/accent/secondary": { light: "lavender/500", dark: "lavender/300" },
  "color/accent/tertiary": { light: "sakura/300", dark: "sakura/300" },
  "color/accent/astral": { light: "astral/500", dark: "astral/300" },
  "color/accent/iris": { light: "iris/500", dark: "iris/300" },
  "color/rule/gold": { light: "gold/500", dark: "gold/500" },
  "color/feedback/success": { light: "status/success", dark: "status/success" },
  "color/feedback/warning": { light: "status/warning", dark: "status/warning" },
  "color/feedback/error": { light: "status/error", dark: "status/error" },
  "color/feedback/info": { light: "status/info", dark: "status/info" },
};

const SPACING = { "space/4": 4, "space/8": 8, "space/16": 16, "space/24": 24, "space/32": 32, "space/48": 48, "space/64": 64, "space/96": 96, "space/128": 128 };
const RADIUS = { "radius/none": 0, "radius/sm": 2, "radius/md": 4, "radius/lg": 8, "radius/pill": 999 };

// Resolved light-mode hex for direct styling of components (fallback when binding unavailable)
function L(semanticName) { return PRIMITIVES[SEMANTIC[semanticName].light]; }

// Text styles: [name, family, style, size, lineHeightPx, letterSpacingPct, textCase]
const TYPE = [
  ["Display/XL", "Fraunces", "Light", 72, 76, -2, "ORIGINAL"],
  ["Display/Large", "Fraunces", "Light", 56, 60, -2, "ORIGINAL"],
  ["Title/Project", "Fraunces", "Regular", 40, 44, -1, "ORIGINAL"],
  ["Header/Section", "Fraunces", "Medium", 28, 34, 0, "ORIGINAL"],
  ["Header/Sub", "Inter", "Semi Bold", 20, 28, 0, "ORIGINAL"],
  ["Body/Large", "Inter", "Regular", 18, 30, 0, "ORIGINAL"],
  ["Body/Default", "Inter", "Regular", 16, 26, 0, "ORIGINAL"],
  ["Caption", "Inter", "Regular", 13, 18, 1, "ORIGINAL"],
  ["Label/Technical", "IBM Plex Mono", "Medium", 12, 16, 8, "UPPER"],
  ["Metadata", "IBM Plex Mono", "Regular", 11, 14, 6, "UPPER"],
];

// font fallbacks if the ideal family/style is unavailable
const FALLBACK = { family: "Inter", style: "Regular" };

// ---------- variable creation (version-tolerant) ----------
function createCollection(name) {
  return figma.variables.createVariableCollection(name);
}
function createVar(name, collection, type) {
  try { return figma.variables.createVariable(name, collection, type); }
  catch (e) { return figma.variables.createVariable(name, collection.id, type); }
}

let colorVarByName = {}; // semanticName -> Variable (for binding)
let semCollection = null, semLightModeId = null, semDarkModeId = null; // for explicit mode on dark templates

async function buildVariables() {
  // Primitives (single mode)
  const prim = createCollection("Primitives");
  const primMode = prim.modes[0].modeId;
  const primVars = {};
  for (const key in PRIMITIVES) {
    const v = createVar(key, prim, "COLOR");
    v.setValueForMode(primMode, hexToRgb(PRIMITIVES[key]));
    primVars[key] = v;
  }
  note("Created " + Object.keys(primVars).length + " primitive color variables.");

  // Semantic (Light + Dark modes), aliased to primitives
  const sem = createCollection("Semantic");
  const lightMode = sem.modes[0].modeId;
  sem.renameMode(lightMode, "Light");
  const darkMode = sem.addMode("Dark");
  semCollection = sem; semLightModeId = lightMode; semDarkModeId = darkMode;
  for (const key in SEMANTIC) {
    const v = createVar(key, sem, "COLOR");
    const map = SEMANTIC[key];
    try {
      v.setValueForMode(lightMode, figma.variables.createVariableAlias(primVars[map.light]));
      v.setValueForMode(darkMode, figma.variables.createVariableAlias(primVars[map.dark]));
    } catch (e) {
      v.setValueForMode(lightMode, hexToRgb(PRIMITIVES[map.light]));
      v.setValueForMode(darkMode, hexToRgb(PRIMITIVES[map.dark]));
    }
    colorVarByName[key] = v;
  }
  note("Created " + Object.keys(SEMANTIC).length + " semantic color variables (Light + Dark).");

  // Spacing
  const sp = createCollection("Spacing");
  const spMode = sp.modes[0].modeId;
  for (const key in SPACING) { const v = createVar(key, sp, "FLOAT"); v.setValueForMode(spMode, SPACING[key]); }

  // Radius
  const rad = createCollection("Radius");
  const radMode = rad.modes[0].modeId;
  for (const key in RADIUS) { const v = createVar(key, rad, "FLOAT"); v.setValueForMode(radMode, RADIUS[key]); }
  note("Created spacing + radius variables.");
}

// bind a node's fill to a semantic color variable; fallback to resolved light hex
function setFill(node, semanticName) {
  const v = colorVarByName[semanticName];
  let paint = solid(L(semanticName));
  if (v) {
    try { paint = figma.variables.setBoundVariableForPaint(paint, "color", v); }
    catch (e) { /* keep raw */ }
  }
  node.fills = [paint];
}
function setStroke(node, semanticName, weight) {
  const v = colorVarByName[semanticName];
  let paint = solid(L(semanticName));
  if (v) { try { paint = figma.variables.setBoundVariableForPaint(paint, "color", v); } catch (e) {} }
  node.strokes = [paint];
  node.strokeWeight = weight == null ? 1 : weight;
}

// ---------- fonts + text styles ----------
const loadedFonts = {};
async function safeLoad(family, style) {
  const key = family + "|" + style;
  if (loadedFonts[key]) return loadedFonts[key];
  try { await figma.loadFontAsync({ family, style }); loadedFonts[key] = { family, style }; return loadedFonts[key]; }
  catch (e) {
    try { await figma.loadFontAsync(FALLBACK); loadedFonts[key] = FALLBACK; note("Font '" + family + " " + style + "' unavailable — fell back to Inter Regular. Install the font, then re-run for exact styles."); return FALLBACK; }
    catch (e2) { const def = { family: "Roboto", style: "Regular" }; await figma.loadFontAsync(def); loadedFonts[key] = def; return def; }
  }
}

const textStyleByName = {};
async function buildTextStyles() {
  for (const t of TYPE) {
    const [name, family, style, size, lh, ls, tc] = t;
    const fn = await safeLoad(family, style);
    const ts = figma.createTextStyle();
    ts.name = name;
    ts.fontName = fn;
    ts.fontSize = size;
    ts.lineHeight = { value: lh, unit: "PIXELS" };
    ts.letterSpacing = { value: ls, unit: "PERCENT" };
    if (tc === "UPPER") ts.textCase = "UPPER";
    textStyleByName[name] = ts;
  }
  note("Created " + TYPE.length + " text styles.");
}

// helper: create a text node using a named style + semantic color
async function makeText(styleName, chars, semanticColor) {
  const ts = textStyleByName[styleName];
  // ensure font loaded for direct set
  const fn = ts ? ts.fontName : await safeLoad("Inter", "Regular");
  await figma.loadFontAsync(fn);
  const t = figma.createText();
  t.fontName = fn;
  t.characters = chars;
  if (ts) { try { await t.setTextStyleIdAsync(ts.id); } catch (e) { t.textStyleId = ts.id; } }
  setFill(t, semanticColor || "color/text/primary");
  return t;
}

// ---------- effect styles ----------
function buildEffectStyles() {
  const sm = figma.createEffectStyle();
  sm.name = "shadow/sm";
  sm.effects = [{ type: "DROP_SHADOW", color: { r: 0.141, g: 0.106, b: 0.18, a: 0.06 }, offset: { x: 0, y: 1 }, radius: 2, spread: 0, visible: true, blendMode: "NORMAL" }];
  const md = figma.createEffectStyle();
  md.name = "shadow/md";
  md.effects = [{ type: "DROP_SHADOW", color: { r: 0.141, g: 0.106, b: 0.18, a: 0.10 }, offset: { x: 0, y: 8 }, radius: 24, spread: 0, visible: true, blendMode: "NORMAL" }];
  // HoYoverse-style luminous glows (rationed: mark + one hero element only)
  const gg = figma.createEffectStyle();
  gg.name = "glow/gold";
  gg.effects = [{ type: "DROP_SHADOW", color: { r: 0.788, g: 0.659, b: 0.416, a: 0.45 }, offset: { x: 0, y: 0 }, radius: 16, spread: 0, visible: true, blendMode: "NORMAL" }];
  const ga = figma.createEffectStyle();
  ga.name = "glow/astral";
  ga.effects = [{ type: "DROP_SHADOW", color: { r: 0.235, g: 0.361, b: 0.620, a: 0.50 }, offset: { x: 0, y: 0 }, radius: 20, spread: 0, visible: true, blendMode: "NORMAL" }];
  note("Created effect styles shadow/sm, shadow/md, glow/gold, glow/astral.");
}

// soft gold glow effect applied directly to a node (HoYoverse mark accent)
function applyGoldGlow(node) {
  try { node.effects = [{ type: "DROP_SHADOW", color: { r: 0.788, g: 0.659, b: 0.416, a: 0.45 }, offset: { x: 0, y: 0 }, radius: 16, spread: 0, visible: true, blendMode: "NORMAL" }]; } catch (e) {}
}

// ---------- pages ----------
const PAGE_NAMES = ["00 Cover", "01 Foundations", "02 Tokens", "03 Components", "04 Patterns", "05 Layouts", "06 Templates", "07 Archive"];
let componentsPage, templatesPage, coverPage;
async function buildPages() {
  await figma.loadAllPagesAsync();
  const existing = {};
  figma.root.children.forEach(p => existing[p.name] = p);
  for (const name of PAGE_NAMES) {
    if (!existing[name]) { const p = figma.createPage(); p.name = name; existing[name] = p; }
  }
  componentsPage = existing["03 Components"];
  templatesPage = existing["06 Templates"];
  coverPage = existing["00 Cover"];
  // remove default empty "Page 1" if it is empty and not one of ours
  const def = figma.root.children.find(p => p.name === "Page 1" && p.children.length === 0);
  if (def && figma.root.children.length > 1) { try { def.remove(); } catch (e) {} }
  note("Ensured 8 pages exist (00 Cover + 01–07).");
}

// ---------- geometry helper: 4-point star ----------
function fourPointStar(size, hex) {
  const s = size, h = size / 2, t = size * 0.16;
  const star = figma.createVector();
  star.resize(s, s);
  // 4-point concave star path
  const path = `M ${h} 0 L ${h + t} ${h - t} L ${s} ${h} L ${h + t} ${h + t} L ${h} ${s} L ${h - t} ${h + t} L 0 ${h} L ${h - t} ${h - t} Z`;
  star.vectorPaths = [{ windingRule: "NONZERO", data: path }];
  star.fills = [solid(hex)];
  star.strokes = [];
  star.name = "✦";
  return star;
}

// generic N-point star path
function starPathData(size, points, innerRatio) {
  const c = size / 2, outer = size / 2, inner = outer * innerRatio;
  let d = "";
  const total = points * 2;
  for (let i = 0; i < total; i++) {
    const r = (i % 2 === 0) ? outer : inner;
    const a = -Math.PI / 2 + i * Math.PI / points;
    const x = c + r * Math.cos(a), y = c + r * Math.sin(a);
    d += (i === 0 ? "M " : "L ") + x.toFixed(2) + " " + y.toFixed(2) + " ";
  }
  return d + "Z";
}

// ---------- geometry helper: 8-point astral star (signature) ----------
function eightPointStar(size, hex) {
  const star = figma.createVector();
  star.resize(size, size);
  star.vectorPaths = [{ windingRule: "NONZERO", data: starPathData(size, 8, 0.40) }];
  star.fills = [solid(hex)];
  star.strokes = [];
  star.name = "✸";
  return star;
}
// returns an 8-pt star tinted to accent/primary, variable-bound when possible
function brandStar(size) {
  const star = eightPointStar(size, L("color/accent/primary"));
  if (colorVarByName["color/accent/primary"]) {
    try { star.fills = [figma.variables.setBoundVariableForPaint(solid(L("color/accent/primary")), "color", colorVarByName["color/accent/primary"])]; } catch (e) {}
  }
  return star;
}

// absolute-positioned rectangle (for frames / brackets)
function rectAt(x, y, w, h, hex, opacity) {
  const r = figma.createRectangle();
  r.x = x; r.y = y; r.resize(w, h);
  r.fills = [solid(hex, opacity)];
  r.strokes = [];
  return r;
}
// small filled ellipse (star dot / bloom)
function ellipseAt(x, y, w, h, hex, opacity) {
  const e = figma.createEllipse();
  e.x = x; e.y = y; e.resize(w, h);
  e.fills = [solid(hex, opacity)];
  e.strokes = [];
  return e;
}
function blur(node, radius) { try { node.effects = [{ type: "LAYER_BLUR", radius: radius, visible: true }]; } catch (e) {} }
function setConstraint(node, h, v) { try { node.constraints = { horizontal: h, vertical: v }; } catch (e) {} }

// seeded scatter of tiny star dots + a few gold sparkles onto a frame
function scatterStars(parent, w, h, count, goldEvery) {
  let seed = 7;
  function rnd() { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; }
  for (let i = 0; i < count; i++) {
    const x = rnd() * w, y = rnd() * h, s = 0.8 + rnd() * 1.6;
    if (goldEvery && i % goldEvery === 0) {
      const st = fourPointStar(7 + rnd() * 4, L("color/accent/primary"));
      st.x = x; st.y = y; st.opacity = 0.85; applyGoldGlow(st); setConstraint(st, "SCALE", "SCALE");
      parent.appendChild(st);
    } else {
      const d = ellipseAt(x, y, s, s, "#FFFFFF", 0.25 + rnd() * 0.4);
      setConstraint(d, "SCALE", "SCALE");
      parent.appendChild(d);
    }
  }
}

// ---------- Star/Constellation (star-chart backplate) ----------
function buildConstellation() {
  const c = figma.createComponent();
  c.name = "Star/Constellation";
  c.resize(220, 140);
  c.fills = [];
  c.clipsContent = false;
  const pts = [[12, 36], [70, 78], [128, 44], [188, 96], [150, 18], [96, 120]];
  const edges = "M 12 36 L 70 78 L 128 44 L 188 96 M 128 44 L 150 18 M 70 78 L 96 120";
  const v = figma.createVector();
  v.resize(220, 140);
  v.vectorPaths = [{ windingRule: "NONZERO", data: edges }];
  v.strokes = [solid(L("color/accent/primary"), 0.55)];
  v.strokeWeight = 0.75;
  v.fills = [];
  c.appendChild(v);
  for (const [x, y] of pts) {
    const dot = ellipseAt(x - 2, y - 2, 4, 4, L("color/accent/primary"), 0.95);
    c.appendChild(dot);
  }
  return c;
}

// ---------- Frame/Corner (ornate gold brackets, corner-pinned) ----------
function buildCornerFrame() {
  const c = figma.createComponent();
  c.name = "Frame/Corner";
  const W = 360, H = 240, len = 56, t = 1.5, gold = L("color/accent/primary");
  c.resize(W, H);
  c.fills = [];
  c.clipsContent = false;
  // thin full frame
  const top = rectAt(0, 0, W, t, gold, 0.45); setConstraint(top, "STRETCH", "MIN");
  const bot = rectAt(0, H - t, W, t, gold, 0.45); setConstraint(bot, "STRETCH", "MAX");
  const lft = rectAt(0, 0, t, H, gold, 0.45); setConstraint(lft, "MIN", "STRETCH");
  const rgt = rectAt(W - t, 0, t, H, gold, 0.45); setConstraint(rgt, "MAX", "STRETCH");
  c.appendChild(top); c.appendChild(bot); c.appendChild(lft); c.appendChild(rgt);
  // accent brackets (brighter) at each corner
  const corners = [
    ["MIN", "MIN", 0, 0, 0, 0],
    ["MAX", "MIN", W - len, 0, W - t, 0],
    ["MIN", "MAX", 0, H - t, 0, H - len],
    ["MAX", "MAX", W - len, H - t, W - t, H - len],
  ];
  for (const [h, v2, hx, hy, vx, vy] of corners) {
    const hb = rectAt(hx, hy, len, t, gold, 1); setConstraint(hb, h, v2);
    const vb = rectAt(vx, vy, t, len, gold, 1); setConstraint(vb, h, v2);
    c.appendChild(hb); c.appendChild(vb);
  }
  // corner stars
  const s1 = brandStar(12); s1.x = 14; s1.y = 14; applyGoldGlow(s1); setConstraint(s1, "MIN", "MIN"); c.appendChild(s1);
  return c;
}

// ---------- component builders ----------
function frame(name, w, h) {
  const f = figma.createFrame();
  f.name = name;
  if (w && h) f.resize(w, h);
  f.fills = [];
  f.clipsContent = false;
  return f;
}
function autoV(f, gap, pad) { f.layoutMode = "VERTICAL"; f.itemSpacing = gap; f.paddingTop = f.paddingBottom = f.paddingLeft = f.paddingRight = pad; f.primaryAxisSizingMode = "AUTO"; f.counterAxisSizingMode = "AUTO"; return f; }
function autoH(f, gap, pad) { f.layoutMode = "HORIZONTAL"; f.itemSpacing = gap; f.paddingTop = f.paddingBottom = f.paddingLeft = f.paddingRight = pad; f.primaryAxisSizingMode = "AUTO"; f.counterAxisSizingMode = "AUTO"; f.counterAxisAlignItems = "CENTER"; return f; }

let layoutX = 0;
function place(node) { node.x = layoutX; node.y = 0; componentsPage.appendChild(node); layoutX += (node.width || 200) + 80; }

// Star/8pt component (signature astral burst, with gold glow)
function buildStar8Component() {
  const c = figma.createComponent();
  c.name = "Star/8pt";
  c.resize(24, 24);
  c.fills = [];
  const star = brandStar(24);
  applyGoldGlow(star);
  c.appendChild(star);
  return c;
}
// Star/4pt component (secondary sparkle)
function buildStar4Component() {
  const c = figma.createComponent();
  c.name = "Star/4pt";
  c.resize(24, 24);
  c.fills = [];
  const star = fourPointStar(24, L("color/accent/primary"));
  if (colorVarByName["color/accent/primary"]) { try { star.fills = [figma.variables.setBoundVariableForPaint(solid(L("color/accent/primary")), "color", colorVarByName["color/accent/primary"])]; } catch (e) {} }
  c.appendChild(star);
  return c;
}

// Divider/Section (Star variant, Full)
async function buildDivider() {
  const c = figma.createComponent();
  c.name = "Divider/Section";
  autoH(c, 16, 0);
  c.counterAxisAlignItems = "CENTER";
  c.resize(640, 24);
  c.layoutAlign = "STRETCH";
  const ruleL = figma.createRectangle(); ruleL.resize(290, 1); setFill(ruleL, "color/rule/gold"); ruleL.layoutGrow = 1;
  const star = fourPointStar(14, L("color/accent/primary"));
  if (colorVarByName["color/accent/primary"]) { try { star.fills = [figma.variables.setBoundVariableForPaint(solid(L("color/accent/primary")), "color", colorVarByName["color/accent/primary"])]; } catch (e) {} }
  const ruleR = figma.createRectangle(); ruleR.resize(290, 1); setFill(ruleR, "color/rule/gold"); ruleR.layoutGrow = 1;
  c.appendChild(ruleL); c.appendChild(star); c.appendChild(ruleR);
  c.primaryAxisSizingMode = "FIXED";
  return c;
}

// Row/Spec  (key + value)
async function buildSpecRow() {
  const c = figma.createComponent();
  c.name = "Row/Spec";
  autoH(c, 16, 0);
  c.paddingTop = 8; c.paddingBottom = 8;
  c.resize(320, 32);
  c.primaryAxisAlignItems = "SPACE_BETWEEN";
  c.primaryAxisSizingMode = "FIXED";
  const key = await makeText("Label/Technical", "TRIANGLES", "color/text/secondary");
  const val = await makeText("Metadata", "482,318", "color/text/primary");
  c.appendChild(key); c.appendChild(val);
  // component properties
  try {
    const kp = c.addComponentProperty("key", "TEXT", "TRIANGLES");
    const vp = c.addComponentProperty("value", "TEXT", "482,318");
    key.componentPropertyReferences = { characters: kp };
    val.componentPropertyReferences = { characters: vp };
  } catch (e) { note("Row/Spec: component properties unavailable on this version (cosmetic only)."); }
  return c;
}

// Tag/Technical (default emphasis)
async function buildTechTag() {
  const c = figma.createComponent();
  c.name = "Tag/Technical";
  autoH(c, 8, 12);
  c.paddingTop = 8; c.paddingBottom = 8;
  c.cornerRadius = 2;
  setFill(c, "color/surface/raised");
  setStroke(c, "color/rule/gold", 1);
  const label = await makeText("Label/Technical", "TRIANGLES", "color/text/secondary");
  const val = await makeText("Metadata", "482,318", "color/text/primary");
  c.appendChild(label); c.appendChild(val);
  try {
    const vp = c.addComponentProperty("value", "TEXT", "482,318");
    val.componentPropertyReferences = { characters: vp };
  } catch (e) {}
  return c;
}

// Tag/Software (chip)
async function buildSoftwareTag() {
  const c = figma.createComponent();
  c.name = "Tag/Software";
  autoH(c, 8, 12);
  c.paddingTop = 6; c.paddingBottom = 6;
  c.cornerRadius = 2;
  setFill(c, "color/surface/sunken");
  const dot = fourPointStar(10, L("color/accent/secondary"));
  const label = await makeText("Label/Technical", "BLENDER", "color/text/secondary");
  c.appendChild(dot); c.appendChild(label);
  try { const tp = c.addComponentProperty("tool", "TEXT", "BLENDER"); label.componentPropertyReferences = { characters: tp }; } catch (e) {}
  return c;
}

// Card/Info
async function buildInfoCard() {
  const c = figma.createComponent();
  c.name = "Card/Info";
  autoV(c, 16, 24);
  c.resize(360, 240);
  c.cornerRadius = 2;
  setFill(c, "color/surface/raised");
  setStroke(c, "color/border/subtle", 1);
  c.primaryAxisSizingMode = "AUTO";
  c.counterAxisSizingMode = "FIXED";
  const title = await makeText("Header/Sub", "Asset Statistics", "color/text/primary");
  title.layoutAlign = "STRETCH";
  const rule = figma.createRectangle(); rule.resize(312, 1); setFill(rule, "color/rule/gold"); rule.layoutAlign = "STRETCH";
  c.appendChild(title); c.appendChild(rule);
  const rows = [["TRIANGLES", "482,318"], ["TEXTURES", "4K · 36"], ["MATERIALS", "12"], ["DRAW CALLS", "184"]];
  for (const [k, v] of rows) {
    const row = frame("row", 312, 32); autoH(row, 16, 0); row.paddingTop = 8; row.paddingBottom = 8;
    row.layoutAlign = "STRETCH"; row.primaryAxisAlignItems = "SPACE_BETWEEN"; row.primaryAxisSizingMode = "FIXED";
    const key = await makeText("Label/Technical", k, "color/text/secondary");
    const val = await makeText("Metadata", v, "color/text/primary");
    row.appendChild(key); row.appendChild(val);
    c.appendChild(row);
  }
  try { const tp = c.addComponentProperty("title", "TEXT", "Asset Statistics"); title.componentPropertyReferences = { characters: tp }; } catch (e) {}
  return c;
}

// wordmark text in Cinzel (engraved celestial caps) with graceful fallback
async function makeWordmark(chars, semanticColor) {
  const fn = await safeLoad("Cinzel", "Regular");
  const t = figma.createText();
  t.fontName = fn;
  t.characters = chars;
  t.fontSize = 18;
  t.letterSpacing = { value: 12, unit: "PERCENT" };
  setFill(t, semanticColor || "color/text/primary");
  return t;
}

// Brand/Mark lockup (✸ MELODIA) — 8-pt astral star + Cinzel wordmark + gold glow
async function buildBrandMark() {
  const c = figma.createComponent();
  c.name = "Brand/Mark";
  autoH(c, 10, 0);
  const star = brandStar(20);
  applyGoldGlow(star);
  const word = await makeWordmark("MELODIA", "color/text/primary");
  c.appendChild(star); c.appendChild(word);
  return c;
}

// wire canonical automation text props onto a passport variant
function wirePassportProps(c, map) {
  try {
    for (const name in map) {
      const node = map[name];
      if (!node) continue;
      const id = c.addComponentProperty(name, "TEXT", node.characters);
      node.componentPropertyReferences = { characters: id };
    }
  } catch (e) { note("Passport variant: component properties unavailable on this version (visual still built)."); }
}

// Brand/AssetPassport — Banner (landscape) variant
async function buildPassportBanner() {
  const c = figma.createComponent();
  c.name = "Format=Banner";
  autoV(c, 14, 24);
  c.resize(680, 200);
  c.cornerRadius = 2;
  setFill(c, "color/surface/raised");
  setStroke(c, "color/border/strong", 1);
  c.counterAxisSizingMode = "FIXED";
  c.primaryAxisSizingMode = "AUTO";

  const header = frame("header", 632, 18); autoH(header, 8, 0); header.layoutAlign = "STRETCH"; header.primaryAxisAlignItems = "SPACE_BETWEEN"; header.primaryAxisSizingMode = "FIXED"; header.counterAxisAlignItems = "CENTER";
  const left = frame("left", 360, 18); autoH(left, 8, 0);
  const star = brandStar(14); applyGoldGlow(star);
  const kicker = await makeText("Label/Technical", "ASSET PASSPORT", "color/text/accent");
  const title = await makeText("Header/Sub", "Ashen Cathedral", "color/text/primary");
  const category = await makeText("Label/Technical", "ENVIRONMENT", "color/text/secondary");
  left.appendChild(star); left.appendChild(kicker); left.appendChild(title); left.appendChild(category);
  const version = await makeText("Metadata", "v1.2 · 2026-03", "color/text/secondary");
  header.appendChild(left); header.appendChild(version);
  c.appendChild(header);

  const rule = figma.createRectangle(); rule.resize(632, 1); setFill(rule, "color/rule/gold"); rule.layoutAlign = "STRETCH";
  c.appendChild(rule);

  const cells = [["TRIANGLES", "482,318"], ["TEXTURES", "4K"], ["MATERIALS", "12"], ["DRAW CALLS", "184"], ["ENGINE", "UE 5.4"]];
  const row = frame("cells", 632, 44); autoH(row, 24, 0); row.layoutAlign = "STRETCH"; row.primaryAxisAlignItems = "SPACE_BETWEEN"; row.primaryAxisSizingMode = "FIXED";
  const fieldNodes = {};
  for (const [k, v] of cells) {
    const cell = frame("cell", 110, 40); autoV(cell, 3, 0);
    const key = await makeText("Metadata", k, "color/text/secondary");
    const val = await makeText("Label/Technical", v, "color/text/primary");
    cell.appendChild(key); cell.appendChild(val);
    row.appendChild(cell);
    fieldNodes[k] = val;
  }
  c.appendChild(row);

  const rule2 = figma.createRectangle(); rule2.resize(632, 1); setFill(rule2, "color/rule/gold"); rule2.layoutAlign = "STRETCH";
  c.appendChild(rule2);
  const footer = frame("footer", 632, 16); autoH(footer, 8, 0); footer.layoutAlign = "STRETCH"; footer.primaryAxisAlignItems = "SPACE_BETWEEN"; footer.primaryAxisSizingMode = "FIXED"; footer.counterAxisAlignItems = "CENTER";
  const tag = await makeText("Metadata", "NANITE · LOD 0–3 · PC / CONSOLE", "color/text/secondary");
  const mark = frame("mark", 90, 14); autoH(mark, 7, 0); const fstar = brandStar(10); const brand = await makeText("Metadata", "MELODIA", "color/text/secondary"); mark.appendChild(fstar); mark.appendChild(brand);
  footer.appendChild(tag); footer.appendChild(mark);
  c.appendChild(footer);

  wirePassportProps(c, { projectName: title, category: category, triangles: fieldNodes["TRIANGLES"], textureResolution: fieldNodes["TEXTURES"], materials: fieldNodes["MATERIALS"], engine: fieldNodes["ENGINE"], version: version });
  return c;
}

// Brand/AssetPassport — Compact variant
async function buildPassportCompact() {
  const c = figma.createComponent();
  c.name = "Format=Compact";
  autoV(c, 12, 22);
  c.resize(300, 240);
  c.cornerRadius = 2;
  setFill(c, "color/surface/raised");
  setStroke(c, "color/border/strong", 1);
  c.counterAxisSizingMode = "FIXED";
  c.primaryAxisSizingMode = "AUTO";

  const header = frame("header", 256, 16); autoH(header, 8, 0); header.layoutAlign = "STRETCH"; header.primaryAxisAlignItems = "SPACE_BETWEEN"; header.primaryAxisSizingMode = "FIXED"; header.counterAxisAlignItems = "CENTER";
  const left = frame("left", 120, 16); autoH(left, 6, 0);
  const star = brandStar(12); applyGoldGlow(star);
  const kicker = await makeText("Label/Technical", "PASSPORT", "color/text/accent");
  left.appendChild(star); left.appendChild(kicker);
  const version = await makeText("Metadata", "v1.2", "color/text/secondary");
  header.appendChild(left); header.appendChild(version);
  c.appendChild(header);

  const rule = figma.createRectangle(); rule.resize(256, 1); setFill(rule, "color/rule/gold"); rule.layoutAlign = "STRETCH";
  c.appendChild(rule);
  const title = await makeText("Header/Sub", "Ashen Cathedral", "color/text/primary"); title.layoutAlign = "STRETCH";
  const category = await makeText("Label/Technical", "ENVIRONMENT", "color/text/secondary"); category.layoutAlign = "STRETCH";
  c.appendChild(title); c.appendChild(category);

  const specs = [["TRIANGLES", "482,318"], ["TEXTURES", "4K"], ["ENGINE", "UE 5.4"]];
  const fieldNodes = {};
  for (const [k, v] of specs) {
    const r = frame("row", 256, 26); autoH(r, 16, 0); r.paddingTop = 6; r.paddingBottom = 6; r.layoutAlign = "STRETCH"; r.primaryAxisAlignItems = "SPACE_BETWEEN"; r.primaryAxisSizingMode = "FIXED";
    const key = await makeText("Label/Technical", k, "color/text/secondary");
    const val = await makeText("Metadata", v, "color/text/primary");
    r.appendChild(key); r.appendChild(val); c.appendChild(r);
    fieldNodes[k] = val;
  }
  const rule2 = figma.createRectangle(); rule2.resize(256, 1); setFill(rule2, "color/rule/gold"); rule2.layoutAlign = "STRETCH";
  c.appendChild(rule2);
  const footer = frame("footer", 256, 14); autoH(footer, 8, 0); footer.layoutAlign = "STRETCH"; footer.primaryAxisAlignItems = "SPACE_BETWEEN"; footer.primaryAxisSizingMode = "FIXED"; footer.counterAxisAlignItems = "CENTER";
  const fstar = brandStar(10); const brand = await makeText("Metadata", "MELODIA", "color/text/secondary");
  footer.appendChild(fstar); footer.appendChild(brand); c.appendChild(footer);

  wirePassportProps(c, { projectName: title, category: category, triangles: fieldNodes["TRIANGLES"], textureResolution: fieldNodes["TEXTURES"], engine: fieldNodes["ENGINE"], version: version });
  return c;
}

// combine the three Passport formats into one variant set (Format = Card / Banner / Compact)
async function buildPassportSet() {
  const card = await buildAssetPassport();   // Format=Card
  const banner = await buildPassportBanner();
  const compact = await buildPassportCompact();
  try {
    const set = figma.combineAsVariants([card, banner, compact], componentsPage);
    set.name = "Brand/AssetPassport";
    autoV(set, 24, 24); set.primaryAxisSizingMode = "AUTO"; set.counterAxisSizingMode = "AUTO";
    note("Combined Asset Passport into a Format variant set (Card / Banner / Compact).");
    return set;
  } catch (e) {
    note("combineAsVariants unavailable; placed Passport formats as separate components.");
    place(banner); place(compact);
    return card;
  }
}

// Brand/AssetPassport (signature, Card format, Light)
async function buildAssetPassport() {
  const c = figma.createComponent();
  c.name = "Format=Card";
  autoV(c, 16, 24);
  c.resize(360, 520);
  c.cornerRadius = 2;
  setFill(c, "color/surface/raised");
  setStroke(c, "color/border/strong", 1);
  c.counterAxisSizingMode = "FIXED";
  c.primaryAxisSizingMode = "AUTO";

  // header: ✦ ASSET PASSPORT ........ v1.2
  const header = frame("header", 312, 18); autoH(header, 8, 0); header.layoutAlign = "STRETCH"; header.primaryAxisAlignItems = "SPACE_BETWEEN"; header.primaryAxisSizingMode = "FIXED"; header.counterAxisAlignItems = "CENTER";
  const left = frame("left", 100, 18); autoH(left, 6, 0);
  const star = brandStar(14);
  applyGoldGlow(star);
  const kicker = await makeText("Label/Technical", "ASSET PASSPORT", "color/text/accent");
  left.appendChild(star); left.appendChild(kicker);
  const version = await makeText("Metadata", "v1.2", "color/text/secondary");
  header.appendChild(left); header.appendChild(version);
  c.appendChild(header);

  // gold rule
  const rule = figma.createRectangle(); rule.resize(312, 1); setFill(rule, "color/rule/gold"); rule.layoutAlign = "STRETCH";
  c.appendChild(rule);

  // title + category
  const title = await makeText("Title/Project", "Ashen Cathedral", "color/text/primary"); title.layoutAlign = "STRETCH";
  const category = await makeText("Label/Technical", "ENVIRONMENT", "color/text/secondary"); category.layoutAlign = "STRETCH";
  c.appendChild(title); c.appendChild(category);

  // subtle divider
  const div2 = figma.createRectangle(); div2.resize(312, 1); setFill(div2, "color/border/subtle"); div2.layoutAlign = "STRETCH";
  c.appendChild(div2);

  // spec rows
  const specs = [["TRIANGLES", "482,318"], ["TEXTURES", "4K"], ["MATERIALS", "12"], ["SOFTWARE", "Blender · ZBrush"], ["ENGINE", "Unreal Engine 5.4"], ["DATE", "2026-03"]];
  const fieldNodes = {};
  for (const [k, v] of specs) {
    const row = frame("row", 312, 30); autoH(row, 16, 0); row.paddingTop = 7; row.paddingBottom = 7;
    row.layoutAlign = "STRETCH"; row.primaryAxisAlignItems = "SPACE_BETWEEN"; row.primaryAxisSizingMode = "FIXED";
    const key = await makeText("Label/Technical", k, "color/text/secondary");
    const val = await makeText("Metadata", v, "color/text/primary");
    row.appendChild(key); row.appendChild(val);
    c.appendChild(row);
    fieldNodes[k] = val;
  }

  // footer rule + mark
  const rule2 = figma.createRectangle(); rule2.resize(312, 1); setFill(rule2, "color/rule/gold"); rule2.layoutAlign = "STRETCH";
  c.appendChild(rule2);
  const footer = frame("footer", 312, 16); autoH(footer, 8, 0); footer.layoutAlign = "STRETCH"; footer.primaryAxisAlignItems = "SPACE_BETWEEN"; footer.primaryAxisSizingMode = "FIXED"; footer.counterAxisAlignItems = "CENTER";
  const fstar = brandStar(10);
  const brand = await makeText("Metadata", "MELODIA", "color/text/secondary");
  footer.appendChild(fstar); footer.appendChild(brand);
  c.appendChild(footer);

  // automation-ready component properties (names match data schema in DESIGN-SYSTEM.md §9.1)
  try {
    const map = {
      projectName: title, category: category,
      triangles: fieldNodes["TRIANGLES"], textureResolution: fieldNodes["TEXTURES"],
      materials: fieldNodes["MATERIALS"], software: fieldNodes["SOFTWARE"],
      engine: fieldNodes["ENGINE"], date: fieldNodes["DATE"], version: version,
    };
    for (const name in map) {
      const node = map[name];
      const id = c.addComponentProperty(name, "TEXT", node.characters);
      node.componentPropertyReferences = { characters: id };
    }
    note("Asset Passport: wired 9 automation text properties.");
  } catch (e) { note("Asset Passport: component properties unavailable on this version (visual still built)."); }

  return c;
}

// set a frame to render with the Dark (Astral Night) semantic mode
function applyDarkMode(node) {
  try { node.setExplicitVariableModeForCollection(semCollection, semDarkModeId); return; } catch (e) {}
  try { node.setExplicitVariableModeForCollection(semCollection.id, semDarkModeId); } catch (e2) {}
}

// ---------- hero templates (06 Templates) — responsive Desktop / Tablet / Mobile ----------
function tplBaseAt(name, dark, w, h, x, y) {
  const f = figma.createFrame();
  f.name = name;
  f.resize(w, h);
  f.x = x; f.y = y;
  f.clipsContent = true;
  f.layoutMode = "NONE";
  if (dark) applyDarkMode(f);
  setFill(f, "color/surface/base");
  templatesPage.appendChild(f);
  return f;
}
function passportVariant(passport, fmt) {
  try { if (passport.children) { for (const ch of passport.children) { if (ch.name && ch.name.indexOf(fmt) >= 0) return ch; } } } catch (e) {}
  return passport.defaultVariant || passport;
}
async function addMark(f, comp, x, y, scale) {
  try { const m = comp.createInstance(); if (scale && scale !== 1) m.rescale(scale); m.x = x; m.y = y; f.appendChild(m); return m; } catch (e) { return null; }
}
async function addPassport(f, passport, fmt, x, y) {
  try { const v = passportVariant(passport, fmt); const inst = v.createInstance(); inst.x = x; inst.y = y; f.appendChild(inst); return inst; } catch (e) { return null; }
}
async function addText(f, style, chars, color, x, y, center, frameW) {
  const t = await makeText(style, chars, color);
  f.appendChild(t);
  t.x = center ? Math.round((frameW - t.width) / 2) : x;
  t.y = y;
  return t;
}

const BPS = [
  { id: "Desktop", w: 1440, h: 900, pad: 96, title: "Display/XL", sub: "Body/Large", pp: "Card", stars: 90, every: 18, markScale: 1 },
  { id: "Tablet", w: 834, h: 1112, pad: 56, title: "Display/Large", sub: "Body/Large", pp: "Card", stars: 55, every: 16, markScale: 1 },
  { id: "Mobile", w: 390, h: 844, pad: 24, title: "Title/Project", sub: "Body/Default", pp: "Compact", stars: 30, every: 12, markScale: 0.85 },
];

async function buildHero(t, bp, ox, oy) {
  const f = tplBaseAt("Hero/" + t.name + " — " + bp.id, t.dark, bp.w, bp.h, ox, oy);
  const W = bp.w, H = bp.h, p = bp.pad, mobile = bp.id === "Mobile";

  // atmosphere
  if (t.key === "constellation") {
    scatterStars(f, W, H, bp.stars, bp.every);
    try { const con = refs0.constel.createInstance(); const cw = Math.min(W * 0.42, 460); con.resize(cw, cw * 0.63); con.x = W - cw - (mobile ? p : p / 2); con.y = mobile ? p + 200 : p; con.opacity = 0.9; f.appendChild(con); } catch (e) {}
  } else if (t.key === "nebula") {
    const b1 = ellipseAt(W * 0.5, -H * 0.18, W * 0.6, H * 0.7, PRIMITIVES["iris/500"], 0.55); blur(b1, Math.round(W * 0.1)); f.appendChild(b1);
    const b2 = ellipseAt(-W * 0.12, H * 0.55, W * 0.55, H * 0.6, PRIMITIVES["astral/500"], 0.45); blur(b2, Math.round(W * 0.1)); f.appendChild(b2);
    scatterStars(f, W, H, bp.stars, bp.every);
  } else if (t.key === "ornate") {
    scatterStars(f, W, H, Math.round(bp.stars * 0.7), bp.every);
    try { const fr = refs0.corner.createInstance(); fr.resize(W - p, H - p); fr.x = p / 2; fr.y = p / 2; f.appendChild(fr); } catch (e) {}
  } else if (t.key === "ivory") {
    let seed = 11; const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
    const n = mobile ? 4 : 7;
    for (let i = 0; i < n; i++) { const st = fourPointStar(7 + rnd() * 5, L("color/accent/primary")); st.x = W * 0.5 + rnd() * (W * 0.45); st.y = p + rnd() * (H - 2 * p); st.opacity = 0.5; f.appendChild(st); }
  }

  // brand mark
  await addMark(f, refs0.mark, p, p, bp.markScale);

  const accentTitle = t.dark ? "color/text/primary" : "color/text/primary";
  if (t.key === "ornate") {
    // centered cover composition
    const cap = await addText(f, "Label/Technical", t.kicker, "color/text/accent", 0, H * 0.40, true, W);
    const ttl = await addText(f, bp.title, t.title, accentTitle, 0, H * 0.40 + (mobile ? 24 : 34), true, W);
    await addText(f, bp.sub, t.sub, "color/text/accent", 0, ttl.y + ttl.height + 12, true, W);
    const specs = await addText(f, "Metadata", "482,318 TRI · 4K · 12 MAT · UE 5.4", "color/text/secondary", 0, H - p - 8, true, W);
    void specs;
  } else if (mobile) {
    const ky = p + 130;
    await addText(f, "Label/Technical", t.kicker, "color/text/accent", p, ky, false, W);
    const ttl = await addText(f, bp.title, t.title, accentTitle, p, ky + 24, false, W);
    await addText(f, bp.sub, t.sub, "color/text/accent", p, ttl.y + ttl.height + 8, false, W);
    await addPassport(f, refs0.passport, "Compact", p, H - 240 - p);
  } else {
    // desktop / tablet: title lower-left, passport upper-right
    if (t.key === "ivory") { const ebrule = rectAt(p + 280, H * 0.34 + 6, W - (p + 280) - p, 1, L("color/rule/gold"), 0.9); f.appendChild(ebrule); }
    const ky = H * 0.50;
    await addText(f, "Label/Technical", t.kicker, t.key === "ivory" ? "color/text/secondary" : "color/text/accent", p, ky, false, W);
    const ttl = await addText(f, bp.title, t.title, accentTitle, p, ky + 26, false, W);
    await addText(f, bp.sub, t.sub, "color/text/accent", p, ttl.y + ttl.height + 12, false, W);
    await addPassport(f, refs0.passport, "Card", W - 360 - p, p + 8);
  }
  return f;
}

let refs0 = null;
const TREATMENTS = [
  { key: "constellation", name: "Constellation", dark: true, kicker: "3D ENVIRONMENT & TECHNICAL ART · ASTRAL NIGHT", title: "Ashen Cathedral", sub: "mapped to the stars" },
  { key: "nebula", name: "Nebula", dark: true, kicker: "ENVIRONMENT · HERO PIECE", title: "Veil of Amethyst", sub: "where violet meets the void" },
  { key: "ornate", name: "Ornate Frame", dark: true, kicker: "ENVIRONMENT · ASSET STUDY", title: "Ashen Cathedral", sub: "an artbook plate" },
  { key: "ivory", name: "Ivory Editorial", dark: false, kicker: "ENVIRONMENT BREAKDOWN", title: "Ashen Cathedral", sub: "light, stone, and stardust" },
];

async function buildTemplates(refs) {
  refs0 = refs;
  const colGap = 160, rowGap = 120;
  const colW = 1440 + colGap;
  const rowY = [0, 1000, 1000 + 1112 + rowGap]; // Desktop, Tablet, Mobile rows
  let count = 0;
  for (let ti = 0; ti < TREATMENTS.length; ti++) {
    for (let bi = 0; bi < BPS.length; bi++) {
      await buildHero(TREATMENTS[ti], BPS[bi], ti * colW, rowY[bi]);
      count++;
    }
  }
  note("Built " + count + " hero templates on '06 Templates' (4 treatments × Desktop/Tablet/Mobile).");
}

// ---------- main ----------
async function main() {
  note("Melodia build starting…");
  await buildPages();
  await buildVariables();
  await buildTextStyles();
  buildEffectStyles();

  // build components on the Components page
  await figma.setCurrentPageAsync(componentsPage);
  layoutX = 0;
  place(buildStar8Component());
  place(buildStar4Component());
  const constel = buildConstellation(); place(constel);
  const corner = buildCornerFrame(); place(corner);
  const mark = await buildBrandMark(); place(mark);
  place(await buildDivider());
  place(await buildSpecRow());
  place(await buildTechTag());
  place(await buildSoftwareTag());
  place(await buildInfoCard());
  const passport = await buildPassportSet(); place(passport);
  note("Built core components + Constellation, Corner Frame, and Asset Passport variant set on '03 Components'.");

  // build hero templates on the Templates page
  try {
    await figma.setCurrentPageAsync(templatesPage);
    await buildTemplates({ mark: mark, constel: constel, corner: corner, passport: passport });
  } catch (e) { note("Templates step skipped: " + (e && e.message ? e.message : String(e))); }

  figma.notify("Melodia design system built ✸  See 02 Tokens / 03 Components / 06 Templates.");
  console.log("\n[Melodia] BUILD SUMMARY\n" + log.map(l => " • " + l).join("\n"));
  figma.closePlugin("Melodia built — variables, styles, pages, components, and hero templates are ready.");
}

main().catch(err => {
  console.error("[Melodia] build error", err);
  figma.closePlugin("Melodia build error: " + (err && err.message ? err.message : String(err)));
});
