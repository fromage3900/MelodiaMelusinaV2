// Assemble layered .psd files from rendered transparent PNG layers using ag-psd.
const fs = require("fs");
const path = require("path");
const { writePsd } = require("ag-psd");
const { PNG } = require("pngjs");

const ROOT = "/home/ubuntu/melodia-design-system";
const OUT = path.join(ROOT, "psd");
fs.mkdirSync(OUT, { recursive: true });

const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "psd_layers", "manifest.json"), "utf8"));

function load(fp) {
  const png = PNG.sync.read(fs.readFileSync(fp));
  return { width: png.width, height: png.height, data: new Uint8Array(png.data.buffer, png.data.byteOffset, png.data.length) };
}
const PRETTY = { bg: "Background", atmosphere: "Atmosphere", brandmark: "Brand Mark", headline: "Headline", passport: "Asset Passport" };
const TITLE = {
  "constellation": "Melodia-Hero-Constellation",
  "nebula": "Melodia-Hero-Nebula",
  "ornate": "Melodia-Cover-OrnateFrame",
  "ivory": "Melodia-Hero-IvoryEditorial",
  "passport-dark": "Melodia-AssetPassport-Dark",
  "passport-light": "Melodia-AssetPassport-Light",
};

for (const stage of Object.keys(manifest)) {
  const m = manifest[stage];
  const psd = { width: m.w, height: m.h, children: [] };
  if (m.composite) { const c = load(m.composite); psd.imageData = c; } // merged preview
  for (const ly of m.layers) {
    psd.children.push({ name: PRETTY[ly.name] || ly.name, top: 0, left: 0, opacity: 255, imageData: load(ly.file) });
  }
  const buf = writePsd(psd);
  const fp = path.join(OUT, (TITLE[stage] || stage) + ".psd");
  fs.writeFileSync(fp, Buffer.from(buf));
  console.log("wrote", path.basename(fp), "(" + m.children + m.layers.length + " layers)");
}
console.log("done");
