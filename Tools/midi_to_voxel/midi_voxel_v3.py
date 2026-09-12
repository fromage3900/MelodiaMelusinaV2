#!/usr/bin/env python3
"""
Resonant World - v3: Two-track world generator.
Track 0 (melody) = surface terrain, Track 1 (beatgrid/kick) = underground caves.
Exports full OBJ with vertex colors + per-chunk files.
"""

import os
import struct

BLOCK_AIR = 0
BLOCK_STONE = 1
BLOCK_WOOD = 2
BLOCK_CRYSTAL = 3
BLOCK_GOLD = 4
BLOCK_VOID = 5

BLOCK_COLORS = {
    BLOCK_STONE: (0.45, 0.42, 0.40),
    BLOCK_WOOD: (0.55, 0.35, 0.20),
    BLOCK_CRYSTAL: (0.30, 0.65, 0.95),
    BLOCK_GOLD: (0.95, 0.78, 0.20),
    BLOCK_VOID: (0.12, 0.08, 0.18),
}
BLOCK_NAMES = {
    BLOCK_STONE: 'stone', BLOCK_WOOD: 'wood', BLOCK_CRYSTAL: 'crystal',
    BLOCK_GOLD: 'gold', BLOCK_VOID: 'void'
}


def vel2block(vel):
    if vel <= 40: return BLOCK_STONE
    if vel <= 60: return BLOCK_WOOD
    if vel <= 80: return BLOCK_CRYSTAL
    return BLOCK_GOLD


def parse_midi(path):
    with open(path, 'rb') as f:
        data = f.read()
    pos = 0

    def chunk():
        nonlocal pos
        cid = data[pos:pos+4].decode('ascii', errors='replace')
        ln = struct.unpack('>I', data[pos+4:pos+8])[0]
        cd = data[pos+8:pos+8+ln]
        pos += 8 + ln
        return cid, ln, cd

    hdr_id, _, hdr = chunk()
    if hdr_id != 'MThd': raise ValueError("not MIDI")
    fmt, ntrk, div = struct.unpack('>HHH', hdr[:6])
    tpb = div
    all_notes = []

    for _ in range(ntrk):
        tid, _, tdata = chunk()
        if tid != 'MTrk': continue
        p, tick, rs = 0, 0, 0
        onset, completed = {}, []
        while p < len(tdata):
            d = 0
            while True:
                b = tdata[p]; p += 1
                d = (d << 7) | (b & 0x7F)
                if not (b & 0x80): break
            tick += d
            s = tdata[p]
            if s & 0x80: rs = s; p += 1
            else: s = rs
            h = s >> 4

            if s == 0xFF:
                mt = tdata[p]; p += 1
                ml = tdata[p]; p += 1
                p += ml
                if mt == 0x2F: break
            elif h == 0x8:
                pit = tdata[p]; v = tdata[p+1]; p += 2
                if pit in onset:
                    completed.append((onset[pit][0], pit, onset[pit][1]))
                    del onset[pit]
            elif h == 0x9:
                pit = tdata[p]; v = tdata[p+1]; p += 2
                if v > 0:
                    onset[pit] = (tick, v)
                elif pit in onset:
                    completed.append((onset[pit][0], pit, onset[pit][1]))
                    del onset[pit]
            elif h in (0xA, 0xB, 0xE): p += 2
            elif h in (0xC, 0xD): p += 1
            else: p += 1

        if completed:
            all_notes.append(sorted(completed))

    return all_notes, tpb


def generate(tracks, tpb, chunk_beats=4, surface_div=32, cave_div=40):
    """Surface track 0, underground track 1+.

    Divisors control vel->height: h = max(1, vel // divisor). Smaller divisor
    = taller relief. Defaults 32/40 match legacy behavior; D7 fix threads per-preset
    surface_height_divisor / cave_height_divisor so abyss_caves != resonant_default.
    """
    # guard divisors (0 or None -> legacy default)
    try:
        surface_div = int(surface_div) if surface_div else 32
    except: surface_div = 32
    try:
        cave_div = int(cave_div) if cave_div else 40
    except: cave_div = 40
    if surface_div <= 0: surface_div = 32
    if cave_div <= 0: cave_div = 40
    tpc = chunk_beats * tpb
    chunks = {}

    for ti, notes in enumerate(tracks):
        surface = (ti == 0)
        for onset, pitch, vel in notes:
            cx = onset // tpc
            lt = onset % tpc
            sx = lt // (tpc // 4)  # 0-3 sub-cell
            pc = pitch % 12
            octv = pitch // 12

            block = vel2block(vel) if surface else BLOCK_VOID

            if surface:
                zb = octv - 2
                h = max(1, vel // surface_div)
                for dz in range(h):
                    key = (cx, sx, pc, zb + dz)
                    chunks[key] = block
            else:
                # Underground: caves go DOWN from z=0
                zb = -(octv - 2) - 1
                h = max(1, vel // cave_div)
                for dz in range(h):
                    key = (cx, sx, pc, zb - dz)
                    chunks[key] = block

    return chunks


def export_obj(chunks, path, name="ResonantWorld"):
    """Greedy-meshed OBJ with vertex colors. Handles both 3-tuple and 4-tuple (chunked) keys."""
    if not chunks: return 0, 0

    # Normalize keys to (x, y, z)
    normalized = {}
    for key, block in chunks.items():
        if len(key) == 4:
            cx, sx, pc, z = key
            x = cx * 4 + sx  # Combine chunk + sub-cell
            normalized[(x, pc, z)] = block
        elif len(key) == 3:
            normalized[key] = block
        else:
            continue

    chunks = normalized
    xs = [k[0] for k in chunks]
    ys = [k[1] for k in chunks]
    zs = [k[2] for k in chunks]
    min_z = min(zs)

    verts, faces, colors = [], [], []

    for (vx, vy, vz), block in sorted(chunks.items()):
        x, y, z = vx, vy, vz - min_z
        c = BLOCK_COLORS.get(block, (0.5, 0.5, 0.5))

        def has_nbr(dx, dy, dz):
            return (vx+dx, vy+dy, vz+dz) in chunks

        base = len(verts)
        for cz in (0, 1):
            for cy in (0, 1):
                for ctx in (0, 1):
                    verts.append((x+ctx, y+cy, z+cz))
                    colors.append(c)

        fi = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
        nbrs = [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]

        for f, n in zip(fi, nbrs):
            if not has_nbr(*n):
                faces.append(tuple(base+i for i in f))

    with open(path, 'w') as f:
        f.write(f"# {name}\n# Voxels: {len(chunks)}, Verts: {len(verts)}, Faces: {len(faces)}\n\n")
        for v, c in zip(verts, colors):
            f.write(f"v {v[0]} {v[1]} {v[2]} {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")

    return len(verts), len(faces)


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    midi_dir = os.path.normpath(os.path.join(base, '..', '..', 'Content', 'MelodiaIntegration', 'MIDI'))

    melody_path = os.path.join(midi_dir, '128BPMarpeggiomelody.mid')
    beatgrid_path = os.path.join(midi_dir, '128BPMarpeggiomelody_beatgrid.mid')

    if not os.path.exists(melody_path):
        print(f"Missing: {melody_path}")
        return

    print("=== Resonant World v3 ===")
    print(f"Parsing melody: {melody_path}")
    m_tracks, m_tpb = parse_midi(melody_path)
    print(f"  {len(m_tracks[0])} melody notes")

    all_tracks = m_tracks
    tpb = m_tpb

    if os.path.exists(beatgrid_path):
        print(f"Parsing beatgrid: {beatgrid_path}")
        b_tracks, b_tpb = parse_midi(beatgrid_path)
        # Rescale beatgrid to same tpb
        scale = tpb / b_tpb
        rescaled = []
        for note in b_tracks[0]:
            rescaled.append((int(note[0] * scale), note[1], note[2]))
        all_tracks.append(sorted(rescaled))
        print(f"  {len(rescaled)} beat notes (cave layer)")

    chunks = generate(all_tracks, tpb, chunk_beats=4)
    print(f"\nTotal voxels: {len(chunks)}")

    # Block stats
    stats = {}
    for b in chunks.values():
        stats[b] = stats.get(b, 0) + 1
    print("Blocks:")
    for b, c in sorted(stats.items()):
        name = BLOCK_NAMES.get(b, f'unknown_{b}')
        bar = '#' * (c // 3)
        print(f"  {name:10}: {c:4} {bar}")

    # Export
    out_dir = os.path.join(base, 'output_v3')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'resonant_world.obj')
    v, f = export_obj(chunks, out_path)
    print(f"\nExported: {out_path}")
    print(f"Vertices: {v}, Faces: {f}")

    # Also export per-chunk
    chunk_dir = os.path.join(out_dir, 'chunks')
    os.makedirs(chunk_dir, exist_ok=True)

    # Group
    cmap = {}
    for (cx, sx, pc, z), b in chunks.items():
        cmap.setdefault(cx, {})[(sx, pc, z)] = b

    for cx in sorted(cmap):
        cpath = os.path.join(chunk_dir, f"chunk_{cx:03d}.obj")
        export_obj(cmap[cx], cpath, f"Chunk_{cx}")

    print(f"Chunks: {len(cmap)}")


if __name__ == '__main__':
    main()
