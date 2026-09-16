#!/usr/bin/env python3
"""DCC pass: tortoise + champagne vertex-color finishes → KHR_materials_variants GLBs."""

from __future__ import annotations

import io
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent.parent / "wix" / "models" / "eyewear-heroes"
OUT = ROOT / "models" / "eyewear"
SIZE = 1024
CHAMPAGNE = (0.95, 0.80, 0.60, 1.0)
SILHOUETTES = ("aviator", "cateye", "panto", "rect")


def read_glb(path: Path):
    data = path.read_bytes()
    offset = 12
    length = struct.unpack_from("<I", data, 8)[0]
    js = None
    blob = b""
    while offset < length:
        clen, ctype = struct.unpack_from("<I4s", data, offset)
        offset += 8
        chunk = data[offset : offset + clen]
        offset += clen
        if ctype == b"JSON":
            js = json.loads(chunk)
        elif ctype.rstrip(b"\x00") == b"BIN":
            blob = chunk
    return js, bytearray(blob)


def write_glb(path: Path, js: dict, blob: bytes) -> None:
    blob = bytes(blob)
    if len(blob) % 4:
        blob += b"\x00" * (4 - len(blob) % 4)
    js["buffers"] = [{"byteLength": len(blob)}]
    raw = json.dumps(js, separators=(",", ":")).encode("utf-8")
    if len(raw) % 4:
        raw += b" " * (4 - len(raw) % 4)
    total = 12 + 8 + len(raw) + 8 + len(blob)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(struct.pack("<4sII", b"glTF", 2, total))
        handle.write(struct.pack("<I4s", len(raw), b"JSON"))
        handle.write(raw)
        handle.write(struct.pack("<I4s", len(blob), b"BIN\x00"))
        handle.write(blob)


def unpack(js, blob, acc_idx):
    acc = js["accessors"][acc_idx]
    view = js["bufferViews"][acc["bufferView"]]
    offset = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    n = acc["count"]
    comps = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    fmt = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}[acc["componentType"]]
    size = struct.calcsize(fmt)
    stride = view.get("byteStride", size * comps)
    out = []
    for i in range(n):
        out.append(struct.unpack_from("<" + fmt * comps, blob, offset + i * stride))
    return out, acc["componentType"]


def color_stats(colors):
    spread = max(max(c[i] for c in colors) - min(c[i] for c in colors) for i in range(3))
    mean = tuple(sum(c[i] for c in colors) / len(colors) for i in range(3))
    return spread, mean


def append_blob(blob: bytearray, payload: bytes, stride: int | None = None) -> int:
    while len(blob) % 4:
        blob.append(0)
    offset = len(blob)
    blob.extend(payload)
    view = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
    if stride:
        view["byteStride"] = stride
    return view


def bake_texture(js, blob, prim) -> bytes:
    uvs, _ = unpack(js, blob, prim["attributes"]["TEXCOORD_0"])
    colors, _ = unpack(js, blob, prim["attributes"]["COLOR_0"])
    indices, itype = unpack(js, blob, prim["indices"])
    idx = [i[0] for i in indices]
    img = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    pix = img.load()
    filled = Image.new("L", (SIZE, SIZE), 0)
    fpix = filled.load()

    def to_px(uv):
        u = min(max(uv[0], 0.0), 1.0)
        v = min(max(uv[1], 0.0), 1.0)
        return int(u * (SIZE - 1)), int((1.0 - v) * (SIZE - 1))

    def to_rgb(color):
        return tuple(max(0, min(255, int(c * 255))) for c in color[:3])

    for t in range(0, len(idx), 3):
        a, b, c = idx[t], idx[t + 1], idx[t + 2]
        pts = [to_px(uvs[a]), to_px(uvs[b]), to_px(uvs[c])]
        cols = [to_rgb(colors[a]), to_rgb(colors[b]), to_rgb(colors[c])]
        minx = max(0, min(p[0] for p in pts))
        maxx = min(SIZE - 1, max(p[0] for p in pts))
        miny = max(0, min(p[1] for p in pts))
        maxy = min(SIZE - 1, max(p[1] for p in pts))
        x0, y0 = pts[0]
        x1, y1 = pts[1]
        x2, y2 = pts[2]
        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if denom == 0:
            continue
        for y in range(miny, maxy + 1):
            for x in range(minx, maxx + 1):
                w0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / denom
                w1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / denom
                w2 = 1.0 - w0 - w1
                if w0 < -0.01 or w1 < -0.01 or w2 < -0.01:
                    continue
                rgb = tuple(int(w0 * cols[0][i] + w1 * cols[1][i] + w2 * cols[2][i]) for i in range(3))
                pix[x, y] = rgb
                fpix[x, y] = 255

    mask = filled.filter(ImageFilter.MaxFilter(5))
    out = Image.new("RGB", (SIZE, SIZE), (128, 128, 128))
    src = img.load()
    dst = out.load()
    mpix = mask.load()
    for y in range(SIZE):
        for x in range(SIZE):
            if fpix[x, y]:
                dst[x, y] = src[x, y]
            elif mpix[x, y]:
                # pull a nearby filled pixel
                found = src[x, y]
                for r in range(1, 4):
                    hit = False
                    for yy in range(max(0, y - r), min(SIZE, y + r + 1)):
                        for xx in range(max(0, x - r), min(SIZE, x + r + 1)):
                            if fpix[xx, yy]:
                                found = src[xx, yy]
                                hit = True
                                break
                        if hit:
                            break
                    if hit:
                        break
                dst[x, y] = found
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def add_png(js, blob: bytearray, png: bytes, name: str) -> int:
    view = append_blob(blob, png)
    js.setdefault("bufferViews", []).append(view)
    view_idx = len(js["bufferViews"]) - 1
    js.setdefault("images", []).append({"mimeType": "image/png", "bufferView": view_idx, "name": name})
    image_idx = len(js["images"]) - 1
    js.setdefault("samplers", []).append({"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497})
    sampler_idx = len(js["samplers"]) - 1
    js.setdefault("textures", []).append({"sampler": sampler_idx, "source": image_idx})
    return len(js["textures"]) - 1


def copy_mat(mat: dict, name: str, **pbr) -> dict:
    cloned = json.loads(json.dumps(mat))
    cloned["name"] = name
    cloned.setdefault("pbrMetallicRoughness", {}).update(pbr)
    return cloned


def author(silhouette: str) -> dict:
    src = SRC / f"{silhouette}-tortoise.glb"
    js, blob = read_glb(src)
    materials = js.setdefault("materials", [])
    tortoise_idx = {}
    champagne_idx = {}

    # Fold / bake per primitive, then assign variant mappings.
    mappings_by_prim = []
    for mesh in js["meshes"]:
        for prim in mesh["primitives"]:
            colors, _ = unpack(js, blob, prim["attributes"]["COLOR_0"])
            spread, mean = color_stats(colors)
            src_mat = materials[prim["material"]]
            role = src_mat["name"]
            if spread > 0.05:
                tex = add_png(js, blob, bake_texture(js, blob, prim), f"{silhouette}_{role}_color")
                t_mat = copy_mat(
                    src_mat,
                    f"{role}_tortoise",
                    baseColorTexture={"index": tex},
                    baseColorFactor=[1, 1, 1, src_mat.get("pbrMetallicRoughness", {}).get("baseColorFactor", [1, 1, 1, 1])[3] if src_mat.get("pbrMetallicRoughness", {}).get("baseColorFactor") else 1],
                )
                if "lens" in role:
                    c_mat = json.loads(json.dumps(t_mat))
                    c_mat["name"] = f"{role}_champagne"
                else:
                    c_mat = copy_mat(
                        materials[0],
                        f"{role}_champagne",
                        baseColorFactor=list(CHAMPAGNE),
                        metallicFactor=1,
                        roughnessFactor=0.28,
                    )
                    c_mat["pbrMetallicRoughness"].pop("baseColorTexture", None)
            else:
                t_mat = copy_mat(
                    src_mat,
                    f"{role}_tortoise",
                    baseColorFactor=[mean[0], mean[1], mean[2], 1],
                )
                if "lens" in role:
                    c_mat = json.loads(json.dumps(t_mat))
                    c_mat["name"] = f"{role}_champagne"
                else:
                    c_mat = copy_mat(
                        materials[0],
                        f"{role}_champagne",
                        baseColorFactor=[mean[0], mean[1], mean[2], 1],
                        metallicFactor=1,
                        roughnessFactor=0.28,
                    )
            prim["attributes"].pop("COLOR_0", None)
            mappings_by_prim.append((prim, t_mat, c_mat))

    materials.clear()
    for prim, t_mat, c_mat in mappings_by_prim:
        t_key = json.dumps(t_mat, sort_keys=True)
        c_key = json.dumps(c_mat, sort_keys=True)
        if t_key not in tortoise_idx:
            tortoise_idx[t_key] = len(materials)
            materials.append(t_mat)
        if c_key not in champagne_idx:
            champagne_idx[c_key] = len(materials)
            materials.append(c_mat)
        t_i = tortoise_idx[t_key]
        c_i = champagne_idx[c_key]
        prim["material"] = t_i
        prim.setdefault("extensions", {})["KHR_materials_variants"] = {
            "mappings": [
                {"material": t_i, "variants": [0]},
                {"material": c_i, "variants": [1]},
            ]
        }

    js["extensionsUsed"] = ["KHR_materials_variants"]
    js["extensions"] = {"KHR_materials_variants": {"variants": [{"name": "Tortoise"}, {"name": "Champagne"}]}}
    out = OUT / f"{silhouette}.glb"
    write_glb(out, js, blob)
    return {"silhouette": silhouette, "path": str(out.relative_to(ROOT)), "bytes": out.stat().st_size, "materials": [m["name"] for m in materials]}


def main() -> int:
    if not SRC.exists():
        print(f"missing source GLBs: {SRC}", file=sys.stderr)
        return 1
    report = [author(name) for name in SILHOUETTES]
    (OUT / "variants.json").write_text(json.dumps(report, indent=2) + "\n")
    for row in report:
        print(f"{row['silhouette']:8} {row['bytes']:8}  {row['path']}  {row['materials']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
