#!/usr/bin/env python3
"""
Resonant World - MIDI-to-Voxel Chunk Generator (v2)
Cuts melody into bar-sized chunks, assigns block types by velocity layer,
adds underground cave track, exports per-chunk OBJ files with material hints.
No external deps.
"""

import os
import struct

# --- MIDI parser (same as v1) ---

def parse_midi_notes(path):
    """Extract (time, pitch, velocity) note events."""
    with open(path, 'rb') as f:
        data = f.read()
    pos = 0

    def read_chunk():
        nonlocal pos
        if pos + 8 > len(data):
            return None, None, None
        chunk_id = data[pos:pos + 4].decode('ascii', errors='replace')
        length = struct.unpack('>I', data[pos + 4:pos + 8])[0]
        chunk_data = data[pos + 8:pos + 8 + length]
        pos += 8 + length
        return chunk_id, length, chunk_data

    header_id, header_len, header = read_chunk()
    if header_id != 'MThd':
        raise ValueError("Not a MIDI file")
    fmt, num_tracks, division = struct.unpack('>HHH', header[:6])
    ticks_per_beat = division

    tracks_notes = []
    for track_idx in range(num_tracks):
        track_id, track_len, track_data = read_chunk()
        if track_id != 'MTrk':
            continue
        tpos = 0
        track_tick = 0
        running_status = 0
        note_onset = {}
        notes = []

        while tpos < len(track_data):
            delta = 0
            while True:
                b = track_data[tpos]
                tpos += 1
                delta = (delta << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            track_tick += delta

            status = track_data[tpos]
            if status & 0x80:
                running_status = status
                tpos += 1
            else:
                status = running_status

            high = status >> 4
            low = status & 0x0F

            if status == 0xFF:
                meta_type = track_data[tpos]
                tpos += 1
                meta_len = track_data[tpos]
                tpos += 1
                tpos += meta_len
                if meta_type == 0x2F:
                    break
            elif high == 0x8:
                pitch = track_data[tpos]
                vel = track_data[tpos + 1]
                tpos += 2
                if pitch in note_onset:
                    onset, on_vel = note_onset.pop(pitch)
                    notes.append((onset, pitch, on_vel))
            elif high == 0x9:
                pitch = track_data[tpos]
                vel = track_data[tpos + 1]
                tpos += 2
                if vel > 0:
                    note_onset[pitch] = (track_tick, vel)
                elif pitch in note_onset:
                    onset, on_vel = note_onset.pop(pitch)
                    notes.append((onset, pitch, on_vel))
            elif high in (0xA, 0xB, 0xE):
                tpos += 2
            elif high in (0xC, 0xD):
                tpos += 1
            else:
                tpos += 1

        if notes:
            tracks_notes.append(notes)

    return tracks_notes, ticks_per_beat


# --- Block type system ---

# Velocity ranges -> block material families
BLOCK_AIR = 0
BLOCK_STONE = 1      # soft (0-40)
BLOCK_WOOD = 2       # medium (41-60)
BLOCK_CRYSTAL = 3    # loud (61-80)
BLOCK_GOLD = 4       # accent (81-100)
BLOCK_VOID = 5       # below ground / caves

BLOCK_COLORS = {
    BLOCK_AIR: (0, 0, 0),
    BLOCK_STONE: (0.45, 0.42, 0.40),     # grey
    BLOCK_WOOD: (0.55, 0.35, 0.20),      # brown
    BLOCK_CRYSTAL: (0.30, 0.65, 0.95),    # cyan-blue
    BLOCK_GOLD: (0.95, 0.78, 0.20),       # gold
    BLOCK_VOID: (0.15, 0.10, 0.20),       # deep purple-black
}

BLOCK_NAMES = {
    BLOCK_AIR: 'air',
    BLOCK_STONE: 'stone',
    BLOCK_WOOD: 'wood',
    BLOCK_CRYSTAL: 'crystal',
    BLOCK_GOLD: 'gold',
    BLOCK_VOID: 'void',
}


def velocity_to_block(vel):
    if vel <= 40:
        return BLOCK_STONE
    elif vel <= 60:
        return BLOCK_WOOD
    elif vel <= 80:
        return BLOCK_CRYSTAL
    else:
        return BLOCK_GOLD


# --- World generation ---

def generate_world(tracks_notes, ticks_per_beat, chunk_beats=4):
    """
    Generate chunked world from MIDI tracks.
    Track 0 = surface melody, Track 1+ = underground cave layers.
    Returns list of chunks, each a dict of (x,y,z) -> block_id.
    """
    beats_per_chunk = chunk_beats
    ticks_per_chunk = ticks_per_chunk = beats_per_chunk * ticks_per_beat

    all_chunks = {}

    for track_idx, notes in enumerate(tracks_notes):
        is_surface = (track_idx == 0)

        for onset, pitch, velocity in notes:
            # Time -> chunk X
            chunk_x = onset // ticks_per_chunk
            local_tick = onset % ticks_per_chunk

            # Subdivide chunk into 4-wide cells
            sub_x = local_tick // (ticks_per_chunk // 4)

            # Pitch -> Y
            pitch_class = pitch % 12
            octave = pitch // 12

            # Block type from velocity
            block = velocity_to_block(velocity)

            # Surface track: stack by octave; underground: mirrored below
            if is_surface:
                z_base = octave - 2  # center around z=2
                height = max(1, velocity // 32)
                for dz in range(height):
                    key = (chunk_x, sub_x, pitch_class, z_base + dz)
                    all_chunks[key] = block
            else:
                # Cave layer: below the surface, mirrored
                z_base = -(octave - 2) - 1
                height = max(1, velocity // 40)
                for dz in range(height):
                    key = (chunk_x, sub_x, pitch_class, z_base - dz)
                    all_chunks[key] = block

    return all_chunks


def chunks_to_obj(all_chunks, output_dir):
    """Export per-chunk OBJ files with vertex colors."""
    os.makedirs(output_dir, exist_ok=True)

    # Group by chunk_x
    chunk_map = {}
    for (cx, sx, pc, z), block in all_chunks.items():
        if cx not in chunk_map:
            chunk_map[cx] = {}
        # Local coords within chunk: sx (0-3), pc (0-11), z
        local_key = (sx, pc, z)
        chunk_map[cx][local_key] = block

    exported = []

    for chunk_x in sorted(chunk_map.keys()):
        grid = chunk_map[chunk_x]
        if not grid:
            continue

        # Bounds
        xs = [k[0] for k in grid]
        ys = [k[1] for k in grid]
        zs = [k[2] for k in grid]

        # Normalize z to start at 0
        min_z = min(zs)
        max_x = max(xs)

        verts = []
        faces = []
        vert_colors = []  # per-vertex RGB

        for (vx, vy, vz), block in sorted(grid.items()):
            if block == BLOCK_AIR:
                continue

            x = vx
            y = vy
            z = vz - min_z

            color = BLOCK_COLORS.get(block, (0.5, 0.5, 0.5))

            # Greedy face culling
            def has_neighbor(dx, dy, dz):
                return (vx + dx, vy + dy, vz + dz) in grid and grid[(vx + dx, vy + dy, vz + dz)] != BLOCK_AIR

            base = len(verts)

            # 8 corners with color
            for cz in (0, 1):
                for cy in (0, 1):
                    for cx in (0, 1):
                        verts.append((x + cx, y + cy, z + cz))
                        vert_colors.append(color)

            # 6 faces
            face_indices = [
                (0, 1, 3, 2),  # -X
                (4, 6, 7, 5),  # +X
                (0, 4, 5, 1),  # -Y
                (2, 3, 7, 6),  # +Y
                (0, 2, 6, 4),  # -Z
                (1, 5, 7, 3),  # +Z
            ]
            neighbors = [
                (-1, 0, 0), (1, 0, 0),
                (0, -1, 0), (0, 1, 0),
                (0, 0, -1), (0, 0, 1),
            ]

            for face_idx, nbr in zip(face_indices, neighbors):
                if not has_neighbor(*nbr):
                    faces.append(tuple(base + i for i in face_idx))

        if not verts:
            continue

        # Write OBJ
        filepath = os.path.join(output_dir, f"chunk_{chunk_x:03d}.obj")
        with open(filepath, 'w') as f:
            f.write(f"# Resonant World - Chunk {chunk_x}\n")
            f.write(f"# Grid: {max_x + 1} x {max(ys) + 1} x {max(zs) - min_z + 1}\n")
            f.write(f"# Voxels: {len(grid)}, Vertices: {len(verts)}, Faces: {len(faces)}\n")
            f.write(f"# Block types: {', '.join(BLOCK_NAMES[b] for b in set(grid.values()) if b != BLOCK_AIR)}\n\n")

            for v, c in zip(verts, vert_colors):
                f.write(f"v {v[0]} {v[1]} {v[2]} {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}\n")

            for face in faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")

        exported.append((chunk_x, len(grid), len(verts), len(faces)))

    return exported


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    midi_path = os.path.normpath(os.path.join(
        base, '..', '..', 'Content', 'MelodiaIntegration', 'MIDI', '128BPMarpeggiomelody.mid'
    ))

    if not os.path.exists(midi_path):
        print(f"MIDI file not found: {midi_path}")
        return

    print(f"Parsing: {midi_path}")
    tracks_notes, ticks_per_beat = parse_midi_notes(midi_path)
    print(f"Tracks: {len(tracks_notes)}")
    for i, notes in enumerate(tracks_notes):
        print(f"  Track {i}: {len(notes)} notes")

    all_chunks = generate_world(tracks_notes, ticks_per_beat, chunk_beats=4)
    print(f"Total voxel cells: {len(all_chunks)}")

    # Block distribution
    blocks = {}
    for b in all_chunks.values():
        blocks[b] = blocks.get(b, 0) + 1
    print("Block distribution:")
    for b, count in sorted(blocks.items()):
        name = BLOCK_NAMES[b]
        color = BLOCK_COLORS[b]
        bar = '#' * (count // 4)
        print(f"  {name:10}: {count:4} {bar}")

    output_dir = os.path.join(base, 'chunks')
    exported = chunks_to_obj(all_chunks, output_dir)
    print(f"\nExported {len(exported)} chunks to: {output_dir}")
    for cx, voxels, verts, faces in exported:
        print(f"  chunk_{cx:03d}.obj: {voxels} voxels, {verts} verts, {faces} faces")


if __name__ == '__main__':
    main()
