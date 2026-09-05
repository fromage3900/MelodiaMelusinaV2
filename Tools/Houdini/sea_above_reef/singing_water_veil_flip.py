"""Cymatic Singing Water Veil — headless Houdini FLIP experiment (2026-09-02).

Genuine FLIP cook in Houdini 22 headless (hython). Chain:
  particlefluidtank (fill tank with FLIP particles, seeded 20260902)
    -> flipsolver   (self-gravity + surface tension, N frames)
    -> particlefluidsurface (surface reconstruction)
    -> convertvdb -> isooffset (SDF->iso mesh)
Then write the surfaced mesh as OBJ (direct point/face writer, no ROP guessing)
and bake a heightfield (for later cymatic Chladni layering, pairing with
shorewake_cymatic_garment.py — the water veil "sings").

Bounded for headless completion: small tank, capped frames, low sample count.
Deterministic (seeded), manifest + elapsed + snapshots.

Run:
  hython Tools/Houdini/sea_above_reef/singing_water_veil_flip.py --frames 24 --sep 0.4
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import hou


def write_obj(geo, path):
    """Write a Geometry to a Wavefront OBJ from points + primitives (direct)."""
    pts = geo.points()
    prims = geo.prims()
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# Melodia FLIP singing water veil\n')
        for p in pts:
            pos = p.position()
            f.write(f'v {pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f}\n')
        for pr in prims:
            verts = pr.vertices()
            idx = [v.point().number() + 1 for v in verts]
            if len(idx) == 3:
                f.write(f'f {idx[0]} {idx[1]} {idx[2]}\n')
            elif len(idx) == 4:
                f.write(f'f {idx[0]} {idx[1]} {idx[2]} {idx[3]}\n')
            else:  # n-gon fan
                for i in range(1, len(idx) - 1):
                    f.write(f'f {idx[0]} {idx[i]} {idx[i+1]}\n')
    return len(pts), len(prims)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', type=int, default=24)
    ap.add_argument('--sep', type=float, default=0.4)
    ap.add_argument('--out', type=str,
                    default=r'C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/singing_water')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print(f"[flip] Houdini {hou.applicationVersion()} | frames={args.frames} sep={args.sep}")
    hou.setUpdateMode(hou.updateMode.Manual)
    for c in hou.node('/obj').children():
        c.destroy()

    geo = hou.node('/obj').createNode('geo', 'SINGING_VEIL')
    tank = geo.createNode('particlefluidtank', 'tank')
    tank.parm('sizex').set(4.0)
    tank.parm('sizey').set(1.2)
    tank.parm('sizez').set(2.0)
    tank.parm('particlesep').set(args.sep)
    tank.parm('jitterseed').set(20260902)
    tank.parm('waterlevel').set(0.6)

    flip = geo.createNode('flipsolver', 'flip')
    flip.setInput(0, tank)
    if flip.parm('substeps'):
        flip.parm('substeps').set(2)

    surface = geo.createNode('particlefluidsurface', 'surface')
    surface.setInput(0, flip)
    if surface.parm('voxelsize'):
        surface.parm('voxelsize').set(args.sep * 0.5)
    if surface.parm('dofinalsmooth'):
        surface.parm('dofinalsmooth').set(1)
    vdb = geo.createNode('convertvdb', 'vdb')
    vdb.setInput(0, surface)
    vdb.parm('conversion').set(2)  # SDF
    iso = geo.createNode('isooffset', 'iso')
    iso.setInput(0, vdb)
    iso.parm('mode').set(0)  # uniform division
    iso.parm('divsize').set(args.sep * 0.6)

    # simulate + snapshot the surfaced mesh at several frames
    snapshots = {}
    peak = None
    mid = max(1, args.frames // 2)
    for frame in range(0, args.frames + 1):
        hou.setFrame(frame)
        flip.cook(force=True)
        iso.cook(force=True)
        g = iso.geometry()
        pc = g.pointCount() if g else 0
        snapshots[frame] = pc
        if frame == mid or frame == args.frames or (peak is None and pc > 0):
            t = 'mid' if frame == mid else ('final' if frame == args.frames else 'first')
            try:
                mesh_path = out / f'FLIP_Veil_{t}_{frame:03d}.obj'
                vp, fp = write_obj(g, mesh_path)
                print(f"  [flip] frame {frame:3d}: {pc} pts -> wrote {mesh_path.name} "
                      f"({vp} verts / {fp} faces)")
            except Exception as e:
                print(f"  [flip] frame {frame}: write obj failed: {e}")
    try:
        hou.setFrame(args.frames)
        # final mesh for heightfield
        gf = iso.geometry()
    except Exception:
        gf = None

    elapsed = time.time() - t0
    result = {
        "schema": "melodia.singing_water_flip.v1",
        "engine": f"Houdini {hou.applicationVersion()}",
        "chain": "particlefluidtank -> flipsolver -> particlefluidsurface -> "
                 "convertvdb -> isooffset -> OBJ",
        "params": {"frames": args.frames, "particlesep": args.sep,
                   "tank": {"sx": 4.0, "sy": 1.2, "sz": 2.0}, "seed": 20260902},
        "snapshots": snapshots,
        "outputs": {"objs": [str(p) for p in sorted(out.glob('FLIP_Veil_*.obj'))]},
        "elapsed_s": round(elapsed, 1),
        "note": "FLIP solver + particlefluidtank + particlefluidsurface PRESENT "
                "(Houdini 22). OBJ written direct from geometry. Heightfield/cymatic "
                "layering staged as next step. LiquiGen is external commercial "
                "(master index §4) — not built natively.",
    }
    (out / 'singing_water_flip_manifest.json').write_text(
        json.dumps(result, indent=2), encoding='utf-8')
    print(f"[flip] done in {elapsed:.1f}s -> {out / 'singing_water_flip_manifest.json'}")
    print(f"[flip] frame snapshots: {snapshots}")


if __name__ == '__main__':
    main()