#!/usr/bin/env python3
"""Analyze both MIDI files for layering potential."""

import os
import struct

def parse_midi_notes(path):
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
        tpos, track_tick, running_status = 0, 0, 0
        note_onset, notes = {}, []

        while tpos < len(track_data):
            delta = 0
            while True:
                b = track_data[tpos]; tpos += 1
                delta = (delta << 7) | (b & 0x7F)
                if not (b & 0x80): break
            track_tick += delta
            status = track_data[tpos]
            if status & 0x80: running_status = status; tpos += 1
            else: status = running_status
            high = status >> 4

            if status == 0xFF:
                meta_type = track_data[tpos]; tpos += 1
                meta_len = track_data[tpos]; tpos += 1
                tpos += meta_len
                if meta_type == 0x2F: break
            elif high == 0x8:
                pitch = track_data[tpos]; vel = track_data[tpos + 1]; tpos += 2
                if pitch in note_onset:
                    onset, on_vel = note_onset.pop(pitch)
                    notes.append((onset, pitch, on_vel))
            elif high == 0x9:
                pitch = track_data[tpos]; vel = track_data[tpos + 1]; tpos += 2
                if vel > 0: note_onset[pitch] = (track_tick, vel)
                elif pitch in note_onset:
                    onset, on_vel = note_onset.pop(pitch)
                    notes.append((onset, pitch, on_vel))
            elif high in (0xA, 0xB, 0xE): tpos += 2
            elif high in (0xC, 0xD): tpos += 1
            else: tpos += 1

        if notes: tracks_notes.append(notes)
    return tracks_notes, ticks_per_beat


def analyze(name, path):
    tracks, tpb = parse_midi_notes(path)
    print(f"\n=== {name} ===")
    print(f"Tracks: {len(tracks)}, TPBeat: {tpb}")
    for i, notes in enumerate(tracks):
        ticks = [n[0] for n in notes]
        pitches = [n[1] for n in notes]
        vels = [n[2] for n in notes]
        print(f"  Track {i}: {len(notes)} notes, duration {max(ticks)} ticks ({max(ticks)/tpb:.1f} beats)")
        print(f"    Pitch: {min(pitches)}-{max(pitches)}, Vel: {min(vels)}-{max(vels)}")
    return tracks, tpb


base = os.path.dirname(os.path.abspath(__file__))
midi_dir = os.path.normpath(os.path.join(base, '..', '..', 'Content', 'MelodiaIntegration', 'MIDI'))

a_tracks, a_tpb = analyze("128BPMarpeggiomelody.mid", os.path.join(midi_dir, '128BPMarpeggiomelody.mid'))
b_tracks, b_tpb = analyze("128BPMarpeggiomelody_beatgrid.mid", os.path.join(midi_dir, '128BPMarpeggiomelody_beatgrid.mid'))

print("\n=== Layering assessment ===")
print(f"Main melody: {len(a_tracks[0])} notes across {len(a_tracks)} track(s)")
print(f"Beatgrid:    {len(b_tracks[0]) if b_tracks else 0} notes across {len(b_tracks)} track(s)")
