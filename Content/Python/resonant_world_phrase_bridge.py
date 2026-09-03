"""Turn an existing MIDI asset into stable Resonant phrase voxels.

This bridge reuses the project's dependency-free MIDI parser at
``Tools/midi_to_voxel/midi_voxel.py`` and gives its note events the same
musical metadata as the world generator.  It is an authoring artifact for
PCG/Blender/Unreal, not a second runtime audio system.

Usage::

    python Content/Python/resonant_world_phrase_bridge.py \
        --midi Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid \
        --seed 3900 \
        --output Saved/Audit/resonant_world_phrase_128bpm.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from resonant_world_generator import NOTE_NAMES, WorldConfig, movement_for_chunk


PHRASE_GENERATOR_VERSION = "resonant_phrase_v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIDI_TOOL_PATH = PROJECT_ROOT / "Tools" / "midi_to_voxel" / "midi_voxel.py"


def _load_midi_parser():
    if not MIDI_TOOL_PATH.exists():
        raise FileNotFoundError(f"existing MIDI parser not found: {MIDI_TOOL_PATH}")
    spec = importlib.util.spec_from_file_location("melodia_midi_voxel", MIDI_TOOL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load MIDI parser from {MIDI_TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _phrase_id(midi_path: Path, seed: int) -> str:
    digest = hashlib.sha256()
    digest.update(midi_path.read_bytes())
    digest.update(str(int(seed)).encode("utf-8"))
    return digest.hexdigest()[:16]


def _mode_degree(config: WorldConfig, pitch_class: int) -> int | None:
    target = int(pitch_class) % 12
    for degree, interval in enumerate(config.mode.intervals):
        if (config.root_pitch_class + interval) % 12 == target:
            return degree
    return None


@dataclass(frozen=True)
class PhraseVoxel:
    cell_id: str
    source_index: int
    onset_tick: int
    time_step: int
    pitch: int
    pitch_name: str
    pitch_class: int
    register: int
    velocity: int
    energy: int
    scale_degree: int | None
    material_id: str
    voice: str
    timbre: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def notes_to_phrase_voxels(
    notes: Iterable[tuple[int, int, int]],
    ticks_per_beat: int,
    config: WorldConfig,
    phrase_id: str,
    *,
    beat_division: int = 4,
) -> list[PhraseVoxel]:
    notes = sorted((int(onset), int(pitch), int(velocity)) for onset, pitch, velocity in notes)
    if not notes:
        return []
    ticks_per_subdivision = max(1, int(ticks_per_beat) // max(1, int(beat_division)))
    min_tick = min(note[0] for note in notes)
    registers = [pitch // 12 for _, pitch, _ in notes]
    median_register = sorted(registers)[len(registers) // 2]
    movement = movement_for_chunk(config, 0, 0)
    voxels: list[PhraseVoxel] = []
    for index, (onset_tick, pitch, velocity) in enumerate(notes):
        pitch_class = pitch % 12
        register = pitch // 12
        degree = _mode_degree(config, pitch_class)
        time_step = (onset_tick - min_tick) // ticks_per_subdivision
        is_diatonic = degree is not None
        if register < median_register - 1:
            voice = "bass"
        elif register > median_register + 1:
            voice = "melody"
        else:
            voice = "harmony"
        material = "resonant_note" if is_diatonic else "dissonant_note"
        timbre_index = degree if degree is not None else pitch_class % len(config.mode.timbres)
        voxels.append(
            PhraseVoxel(
                cell_id=f"{PHRASE_GENERATOR_VERSION}:{phrase_id}:{time_step}:{pitch}:{index}",
                source_index=index,
                onset_tick=onset_tick,
                time_step=int(time_step),
                pitch=pitch,
                pitch_name=f"{NOTE_NAMES[pitch_class]}{register - 1}",
                pitch_class=pitch_class,
                register=register,
                velocity=max(0, min(127, velocity)),
                energy=max(0, min(100, int(round(velocity / 127.0 * 100.0)))),
                scale_degree=degree,
                material_id=material,
                voice=voice,
                timbre=config.mode.timbres[timbre_index],
            )
        )
    return voxels


def build_phrase_manifest(
    midi_path: str | Path,
    world_seed: int = 3900,
    *,
    beat_division: int = 4,
) -> dict[str, Any]:
    path = Path(midi_path).resolve()
    parser = _load_midi_parser()
    notes, ticks_per_beat = parser.parse_midi_notes(str(path))
    config = WorldConfig.from_seed(world_seed)
    phrase_id = _phrase_id(path, world_seed)
    voxels = notes_to_phrase_voxels(notes, ticks_per_beat, config, phrase_id, beat_division=beat_division)
    movement = movement_for_chunk(config, 0, 0)
    return {
        "format": "melodia_resonant_phrase_manifest",
        "schema_version": 1,
        "phrase_generator_version": PHRASE_GENERATOR_VERSION,
        "source": {
            "midi_path": path.as_posix(),
            "midi_file_name": path.name,
            "phrase_id": phrase_id,
            "ticks_per_beat": int(ticks_per_beat),
            "beat_division": int(beat_division),
        },
        "world": config.to_dict(),
        "movement": {
            "movement_id": movement.movement_id,
            "world_verb": movement.world_verb,
            "resonant_form_id": movement.resonant_form_id,
            "timbres": list(movement.musical_asset_fragments),
        },
        "rules": {
            "midi_is_authoring_input": True,
            "runtime_audio_authority": "existing Harmonix/Melodia music clock",
            "dissonant_notes_are_valid_material": True,
            "stable_phrase_voxel_ids": True,
        },
        "note_count": len(notes),
        "voxel_count": len(voxels),
        "voxels": [voxel.to_dict() for voxel in voxels],
    }


def validate_phrase_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("format") != "melodia_resonant_phrase_manifest":
        errors.append("unexpected phrase manifest format")
    if int(manifest.get("note_count", 0)) != int(manifest.get("voxel_count", 0)):
        errors.append("one phrase voxel is expected per parsed MIDI note")
    voxels = manifest.get("voxels", [])
    cell_ids = [str(voxel.get("cell_id")) for voxel in voxels]
    if len(cell_ids) != len(set(cell_ids)):
        errors.append("phrase voxel cell ids are not unique")
    for voxel in voxels:
        if voxel.get("material_id") not in {"resonant_note", "dissonant_note"}:
            errors.append(f"unsupported phrase material: {voxel.get('material_id')}")
        if not 0 <= int(voxel.get("energy", -1)) <= 100:
            errors.append("phrase voxel energy is out of bounds")
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--midi", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--beat-division", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = build_phrase_manifest(args.midi, args.seed, beat_division=args.beat_division)
    manifest["validation_errors"] = validate_phrase_manifest(manifest)
    manifest["ok"] = not manifest["validation_errors"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": manifest["ok"],
        "midi": str(args.midi),
        "notes": manifest["note_count"],
        "voxels": manifest["voxel_count"],
        "movement": manifest["movement"]["movement_id"],
        "output": str(args.output),
    }, indent=2))
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
