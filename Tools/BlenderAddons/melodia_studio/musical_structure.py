"""Musical structure analyzer - detects song sections and maps them to biomes.

Analyzes MIDI structure:
- Section detection (intro/verse/chorus/bridge/outro)
- Tempo (BPM) from note spacing
- Dynamics (velocity variance) per section
- Section -> biome mapping

Pure Python, no bpy. Deterministic.
"""

import os
import sys

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
ADDON = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)

import midi_bridge


SECTION_BIOMES = {
    "intro": "plains",
    "verse": "forest",
    "chorus": "mountains",
    "bridge": "canyon",
    "outro": "beach",
}


def analyze_song(midi_path):
    """Analyze musical structure of a MIDI file.

    Returns dict with:
    - sections: list of {name, start, end, notes, biome}
    - tempo_bpm: estimated BPM
    - dynamics: {section_name: velocity_variance}
    - overall_mood: string
    """
    mv = midi_bridge.load_voxel_module()
    tracks, tpb = mv.parse_midi(midi_path)
    if not tracks:
        return {
            "sections": [],
            "tempo_bpm": 120,
            "dynamics": {},
            "overall_mood": "neutral",
        }

    notes = tracks[0]

    # Detect sections
    sections = _detect_sections(notes, tpb)

    # Compute tempo
    tempo_bpm = _estimate_tempo(notes, tpb)

    # Compute dynamics per section
    dynamics = {}
    for section in sections:
        section_notes = section["notes"]
        if section_notes:
            velocities = [n[2] for n in section_notes]
            mean_v = sum(velocities) / len(velocities)
            variance = sum((v - mean_v) ** 2 for v in velocities) / len(velocities)
            dynamics[section["name"]] = variance

    # Overall mood
    overall_mood = _compute_mood(notes, tempo_bpm)

    return {
        "sections": sections,
        "tempo_bpm": tempo_bpm,
        "dynamics": dynamics,
        "overall_mood": overall_mood,
    }


def _detect_sections(notes, tpb):
    """Detect song sections from note patterns."""
    if not notes:
        return []

    # Simple heuristic: split into chunks by note density
    total_notes = len(notes)
    if total_notes == 0:
        return []

    # Use ~16-note chunks as section boundaries
    chunk_size = max(1, total_notes // 5)

    section_names = ["intro", "verse", "chorus", "bridge", "outro"]
    sections = []

    for i, start_idx in enumerate(range(0, total_notes, chunk_size)):
        end_idx = min(start_idx + chunk_size, total_notes)
        section_notes = notes[start_idx:end_idx]

        name = section_names[min(i, len(section_names) - 1)]
        biome = SECTION_BIOMES.get(name, "plains")

        sections.append({
            "name": name,
            "start": start_idx,
            "end": end_idx,
            "notes": section_notes,
            "biome": biome,
        })

    return sections


def _estimate_tempo(notes, tpb):
    """Estimate BPM from note spacing."""
    if len(notes) < 2:
        return 120

    # Average time between notes
    intervals = []
    for i in range(1, len(notes)):
        dt = notes[i][0] - notes[i-1][0]
        if dt > 0:
            intervals.append(dt)

    if not intervals:
        return 120

    avg_interval = sum(intervals) / len(intervals)

    # Convert to BPM: avg_interval is in ticks, tpb is ticks per beat
    # BPM = 60 / (seconds_per_beat) = 60 / (avg_interval / tpb / tempo_base)
    # Simplified: if avg_interval is ticks between notes, and quarter note = tpb ticks
    # Then beats per note = avg_interval / tpb, and BPM = 60 / (avg_interval / tpb)
    # But we need to account for the fact that notes may not be quarter notes
    # Simple heuristic: BPM = (tpb * 60) / (avg_interval * 4) assumes 16th notes
    # Better: just use the standard formula
    if avg_interval > 0:
        bpm = (tpb * 60.0) / avg_interval
        bpm = max(60, min(200, bpm))
        return round(bpm)

    return 120


def _compute_mood(notes, tempo_bpm):
    """Compute overall mood from notes and tempo."""
    if not notes:
        return "neutral"

    # Average velocity
    velocities = [n[2] for n in notes]
    avg_velocity = sum(velocities) / len(velocities)

    # Pitch range
    pitches = [n[1] for n in notes]
    pitch_range = max(pitches) - min(pitches)

    # Heuristic mood
    if tempo_bpm > 140 and avg_velocity > 80:
        return "energetic"
    elif tempo_bpm < 100 and avg_velocity < 60:
        return "calm"
    elif pitch_range > 40:
        return "dramatic"
    else:
        return "balanced"
