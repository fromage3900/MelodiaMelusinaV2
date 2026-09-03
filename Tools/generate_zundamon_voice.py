"""Zundamon VOICEVOX Dialogue Generator.

Reads a dialogue JSON file and generates WAV voice lines via VOICEVOX API.
VOICEVOX must be running locally (port 50021). Download from voicevox.hiroshiba.jp

Usage:
  python generate_zundamon_voice.py zundamon_dialogue.json
  python generate_zundamon_voice.py zundamon_dialogue.json --speaker 3 --output-dir ./voice_output
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

VOICEVOX_URL = "http://127.0.0.1:50021"
ZUNDAMON_SPEAKER_ID = 3  # Zundamon (ノーマル)
DEFAULT_SPEED = 1.1       # Slightly faster than default
DEFAULT_PITCH = 0.0


def check_voicevox():
    """Verify VOICEVOX engine is running."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{VOICEVOX_URL}/version", timeout=3) as r:
            data = json.loads(r.read())
            print(f"VOICEVOX v{data.get('version', '?')} ready")
            return True
    except Exception as e:
        print(f"VOICEVOX not running on {VOICEVOX_URL} - {e}")
        print("Download from: https://voicevox.hiroshiba.jp/")
        return False


def generate_audio_query(text: str, speaker: int = ZUNDAMON_SPEAKER_ID) -> dict:
    """Get audio query parameters from VOICEVOX."""
    import urllib.request
    import urllib.parse
    params = urllib.parse.urlencode({"text": text, "speaker": speaker})
    url = f"{VOICEVOX_URL}/audio_query?{params}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def synthesize(query: dict, speaker: int = ZUNDAMON_SPEAKER_ID) -> bytes:
    """Generate WAV audio from an audio query."""
    import urllib.request
    url = f"{VOICEVOX_URL}/synthesis?speaker={speaker}"
    data = json.dumps(query).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def load_dialogue(path: str) -> dict:
    """Load dialogue JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_all(dialogue_path: str, output_dir: str, speaker: int,
                 speed: float = DEFAULT_SPEED, pitch: float = DEFAULT_PITCH):
    """Generate WAV files for all dialogue lines."""
    if not check_voicevox():
        sys.exit(1)

    dialogue = load_dialogue(dialogue_path)
    lines = dialogue.get("lines", [])
    total = len(lines)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Generating {total} lines for '{dialogue.get('character', 'Zundamon')}'")
    print(f"Output: {out_path.absolute()}\n")

    results = []
    for i, line in enumerate(lines):
        line_id = line["id"]
        text = line["text"]
        context = line.get("context", "")

        wav_name = f"{line_id}.wav"
        wav_path = out_path / wav_name

        # Skip if already exists
        if wav_path.exists():
            print(f"  [{i+1}/{total}] {line_id} - already exists, skipping")
            results.append({"id": line_id, "path": str(wav_path), "status": "cached"})
            continue

        print(f"  [{i+1}/{total}] {line_id}: \"{text[:50]}{'...' if len(text)>50 else ''}\"", end=" ", flush=True)

        try:
            query = generate_audio_query(text, speaker)

            # Adjust parameters
            query["speedScale"] = speed
            query["pitchScale"] = pitch
            query["intonationScale"] = 1.0

            wav = synthesize(query, speaker)
            wav_path.write_bytes(wav)
            print(f"-> {wav_name} ({len(wav)/1024:.0f} KB)")
            results.append({"id": line_id, "path": str(wav_path), "status": "generated", "size_bytes": len(wav)})

        except Exception as e:
            print(f"-> FAILED: {e}")
            results.append({"id": line_id, "path": str(wav_path), "status": "error", "error": str(e)})

        # Rate limit
        time.sleep(0.3)

    # Write manifest
    manifest_path = out_path / "voice_manifest.json"
    manifest_path.write_text(json.dumps({
        "character": dialogue.get("character", "Zundamon"),
        "speaker_id": speaker,
        "total_lines": total,
        "generated": sum(1 for r in results if r["status"] in ("generated", "cached")),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "lines": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nDone: {sum(1 for r in results if r['status']!='error')}/{total} generated")
    print(f"Manifest: {manifest_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Zundamon voice lines via VOICEVOX")
    parser.add_argument("dialogue", help="Path to dialogue JSON file")
    parser.add_argument("--speaker", type=int, default=ZUNDAMON_SPEAKER_ID, help="VOICEVOX speaker ID (default: 3 = Zundamon)")
    parser.add_argument("--output-dir", default="./zundamon_voice", help="Output directory for WAV files")
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED, help="Speech speed scale")
    parser.add_argument("--pitch", type=float, default=DEFAULT_PITCH, help="Pitch shift")
    args = parser.parse_args()

    generate_all(args.dialogue, args.output_dir, args.speaker, args.speed, args.pitch)
