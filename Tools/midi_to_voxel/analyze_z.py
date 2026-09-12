#!/usr/bin/env python3
"""Analyze the Z-structure of the generated world."""
import os, struct

def parse_midi(path):
    with open(path, 'rb') as f: data = f.read()
    pos = 0
    def chunk():
        nonlocal pos
        cid = data[pos:pos+4].decode('ascii', errors='replace')
        ln = struct.unpack('>I', data[pos+4:pos+8])[0]
        cd = data[pos+8:pos+8+ln]; pos += 8 + ln
        return cid, ln, cd
    hdr_id, _, hdr = chunk()
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
                mt = tdata[p]; p += 1; ml = tdata[p]; p += 1; p += ml
                if mt == 0x2F: break
            elif h == 0x8:
                pit = tdata[p]; v = tdata[p+1]; p += 2
                if pit in onset:
                    completed.append((onset[pit][0], pit, onset[pit][1])); del onset[pit]
            elif h == 0x9:
                pit = tdata[p]; v = tdata[p+1]; p += 2
                if v > 0: onset[pit] = (tick, v)
                elif pit in onset:
                    completed.append((onset[pit][0], pit, onset[pit][1])); del onset[pit]
            elif h in (0xA, 0xB, 0xE): p += 2
            elif h in (0xC, 0xD): p += 1
            else: p += 1
        if completed: all_notes.append(sorted(completed))
    return all_notes, tpb

midi_dir = 'C:/EnvironmentPortfolio/BS_GodFile/Content/MelodiaIntegration/MIDI'
m_tracks, tpb = parse_midi(os.path.join(midi_dir, '128BPMarpeggiomelody.mid'))

print("=== Z-axis distribution (surface vs caves) ===")
print("Track 0 = melody (surface), Track 1 = beatgrid (caves)")
print()

surface_z = []
for onset, pitch, vel in m_tracks[0]:
    octv = pitch // 12
    zb = octv - 2
    h = max(1, vel // 32)
    for dz in range(h):
        surface_z.append(zb + dz)

b_tracks, b_tpb = parse_midi(os.path.join(midi_dir, '128BPMarpeggiomelody_beatgrid.mid'))
scale = tpb / b_tpb
cave_z = []
for onset, pitch, vel in b_tracks[0]:
    resc = int(onset * scale)
    octv = pitch // 12
    zb = -(octv - 2) - 1
    h = max(1, vel // 40)
    for dz in range(h):
        cave_z.append(zb - dz)

print("Surface Z levels:", sorted(set(surface_z)))
print("Cave Z levels:", sorted(set(cave_z)))
print()
print(f"Surface voxels: {len(surface_z)}")
print(f"Cave voxels: {len(cave_z)}")
print()

grid = {}
for z in surface_z:
    grid[z] = grid.get(z, 0) + 1
for z in cave_z:
    grid[z] = grid.get(z, 0) + 1

print("Layer distribution:")
for z in sorted(grid.keys()):
    bar = '#' * (grid[z] // 2)
    side = "SURFACE" if z >= 0 else "CAVE"
    print(f"  z={z:2} [{side:8}] {grid[z]:3} {bar}")
