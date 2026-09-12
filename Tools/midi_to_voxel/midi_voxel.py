#!/usr/bin/env python3
"""
MIDI-to-Voxel prototype - Resonant World proof of concept.
Reads a MIDI file, generates voxel terrain where:
  X = time (beats)
  Y = pitch (MIDI note)
  Z = velocity / density (stacked blocks)
Outputs an OBJ file for import into Blender/UE5.
No external deps - uses struct to parse MIDI.
"""

import struct
import os

CHUNK_SIZE = 16


def parse_midi_notes(path):
    """Extract (time, pitch, velocity) note events from a Type 0/1 MIDI file."""
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

    # Header
    header_id, header_len, header = read_chunk()
    if header_id != 'MThd':
        raise ValueError("Not a MIDI file")

    fmt, num_tracks, division = struct.unpack('>HHH', header[:6])
    ticks_per_beat = division

    notes = []  # (onset_tick, pitch, velocity)

    for track_idx in range(num_tracks):
        track_id, track_len, track_data = read_chunk()
        if track_id != 'MTrk':
            continue

        tpos = 0
        track_tick = 0
        running_status = 0
        note_onset = {}  # pitch -> (tick, velocity) for active notes

        while tpos < len(track_data):
            # Delta time (VLQ)
            delta = 0
            while True:
                b = track_data[tpos]
                tpos += 1
                delta = (delta << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            track_tick += delta

            # Event
            status = track_data[tpos]
            if status & 0x80:
                running_status = status
                tpos += 1
            else:
                status = running_status

            high = status >> 4
            low = status & 0x0F

            if status == 0xFF:  # Meta
                meta_type = track_data[tpos]
                tpos += 1
                meta_len = track_data[tpos]
                tpos += 1
                tpos += meta_len
                if meta_type == 0x2F:  # End of Track
                    break

            elif high == 0x8:  # Note Off
                pitch = track_data[tpos]
                vel = track_data[tpos + 1]
                tpos += 2
                if pitch in note_onset:
                    onset, on_vel = note_onset.pop(pitch)
                    notes.append((onset, pitch, on_vel))

            elif high == 0x9:  # Note On
                pitch = track_data[tpos]
                vel = track_data[tpos + 1]
                tpos += 2
                if vel > 0:
                    note_onset[pitch] = (track_tick, vel)
                elif pitch in note_onset:
                    onset, on_vel = note_onset.pop(pitch)
                    notes.append((onset, pitch, on_vel))

            elif high in (0xA, 0xB, 0xE):  # 2-byte events
                tpos += 2

            elif high in (0xC, 0xD):  # 1-byte events
                tpos += 1

            else:
                tpos += 1

    # Sort by onset
    notes.sort(key=lambda n: (n[0], n[1]))
    return notes, ticks_per_beat


def notes_to_voxel_grid(notes, ticks_per_beat, beat_division=4):
    """
    Convert notes to voxel grid.
    X: time (subdivided beats)
    Y: pitch class (mod 12) for chromatic terrain
    Z: octave layer + velocity density
    """
    if not notes:
        return {}

    min_tick = min(n[0] for n in notes)
    max_tick = max(n[0] for n in notes)

    # Scale: X = subdivisions of a beat
    ticks_per_sub = ticks_per_beat // beat_division
    max_x = int((max_tick - min_tick) / ticks_per_sub) + 1

    # Y = pitch (0-127), Z = octave layer
    min_pitch = min(n[1] for n in notes)
    max_pitch = max(n[1] for n in notes)

    # Build grid: (x, y, z) -> velocity value
    grid = {}

    for onset, pitch, velocity in notes:
        x = int((onset - min_tick) / ticks_per_sub)
        y = pitch % 12       # chromatic pitch class
        z = pitch // 12      # octave
        v = velocity

        # Stack velocity as height
        height = max(1, v // 32)
        for dz in range(height):
            key = (x, y, z * 4 + dz)
            grid[key] = v

    return grid


def grid_to_obj(grid, output_path):
    """Export voxel grid to Wavefront OBJ with per-vertex color hints."""
    if not grid:
        return

    # Bounds
    xs = [k[0] for k in grid]
    ys = [k[1] for k in grid]
    zs = [k[2] for k in grid]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    # Center vertically
    z_offset = min_z

    verts = []
    faces = []

    voxel_list = sorted(grid.keys())

    for vx, vy, vz in voxel_list:
        if vz < z_offset:
            continue

        x = vx - min_x
        y = vy - min_y
        z = vz - z_offset

        # Skip faces between adjacent voxels (greedy-ish: only add faces if neighbor empty)
        def has_neighbor(dx, dy, dz):
            return (vx + dx, vy + dy, vz + dz) in grid

        base = len(verts)

        # 8 cube corners
        for cz in (0, 1):
            for cy in (0, 1):
                for cx in (0, 1):
                    verts.append((x + cx, y + cy, z + cz))

        # 6 faces (only if no neighbor)
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

    # Write OBJ
    with open(output_path, 'w') as f:
        f.write("# Resonant World - MIDI-to-Voxel prototype\n")
        f.write(f"# Voxels: {len(voxel_list)}\n")
        f.write(f"# Grid: {max_x - min_x + 1} x {max_y - min_y + 1} x {max_z - z_offset + 1}\n")
        f.write(f"# Vertices: {len(verts)}, Faces: {len(faces)}\n\n")

        for v in verts:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")

        for face in faces:
            # OBJ is 1-indexed
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")

    return len(verts), len(faces)


def main():
    import sys

    base = os.path.dirname(os.path.abspath(__file__))
    midi_path = os.path.join(base, '..', '..', 'Content', 'MelodiaIntegration', 'MIDI', '128BPMarpeggiomelody.mid')
    midi_path = os.path.normpath(midi_path)

    if not os.path.exists(midi_path):
        print(f"MIDI file not found: {midi_path}")
        sys.exit(1)

    print(f"Parsing: {midi_path}")
    notes, ticks_per_beat = parse_midi_notes(midi_path)
    print(f"Notes extracted: {len(notes)}")
    print(f"Ticks per beat: {ticks_per_beat}")

    if notes:
        pitches = [n[1] for n in notes]
        vels = [n[2] for n in notes]
        print(f"Pitch range: {min(pitches)}-{max(pitches)} ({min(pitches)}={pitch_name(min(pitches))}, {max(pitches)}={pitch_name(max(pitches))})")
        print(f"Velocity range: {min(vels)}-{max(vels)}")
        print(f"Note density: {len(notes)} notes")

    grid = notes_to_voxel_grid(notes, ticks_per_beat)
    print(f"Voxel grid: {len(grid)} filled cells")

    output_path = os.path.join(base, 'resonant_world.obj')
    verts, faces = grid_to_obj(grid, output_path)
    print(f"\nOBJ exported: {output_path}")
    print(f"Vertices: {verts}, Faces: {faces}")


def pitch_name(n):
    names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return f"{names[n % 12]}{(n // 12) - 1}"


if __name__ == '__main__':
    main()
