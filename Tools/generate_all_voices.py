"""ZunZun Family Voice Generator ΓÇö batch VOICEVOX for all 7 characters.

Reads dialogue JSON files from each character folder,
calls VOICEVOX API with the correct speaker ID per character,
and produces WAV files organized by character.

Usage:
  python generate_all_voices.py
  python generate_all_voices.py --character Zundamon --character Zunko
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Project root
ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
CHARACTERS_DIR = ROOT / "Content" / "Melodia" / "Characters"

# All 7 ZunZun family characters with VOICEVOX speaker IDs
CHARACTERS = {
    "Zundamon": {
        "speaker_id": 3,
        "voice_style": "πâÄπâ╝πâ₧πâ½",
        "folder": "Zundamon",
        "dialogue_file": "zundamon_dialogue.json",
    },
    "Zunko": {
        "speaker_id": 14,
        "voice_style": "πâÄπâ╝πâ₧πâ½",
        "folder": "Zunko",
        "dialogue_file": "zunko_dialogue.json",
    },
    "Kiritan": {
        "speaker_id": 5,
        "voice_style": "πâÄπâ╝πâ₧πâ½",
        "folder": "Kiritan",
        "dialogue_file": "kiritan_dialogue.json",
    },
    "Itako": {
        "speaker_id": 6,
        "voice_style": "πâÄπâ╝πâ₧πâ½",
        "folder": "Itako",
        "dialogue_file": "itako_dialogue.json",
    },
    "Metan": {
        "speaker_id": 2,
        "voice_style": "πâÄπâ╝πâ₧πâ½",
        "folder": "Metan",
        "dialogue_file": "metan_dialogue.json",
    },
    "Sora": {
        "speaker_id": 16,
        "voice_style": "πâÄπâ╝πâ₧πâ½",
        "folder": "Sora",
        "dialogue_file": "sora_dialogue.json",
    },
    "Tsurugi": {
        "speaker_id": 17,
        "voice_style": "πâÄπâ╝πâ₧πâ½",
        "folder": "Tsurugi",
        "dialogue_file": "tsurugi_dialogue.json",
    },
}

VOICEVOX_URL = "http://127.0.0.1:50021"


def check_voicevox():
    try:
        with urllib.request.urlopen(f"{VOICEVOX_URL}/version", timeout=3) as r:
            data = r.read().decode("utf-8").strip().strip('"')
            print(f"VOICEVOX v{data} online")
            return True
    except Exception as e:
        print(f"VOICEVOX not running on {VOICEVOX_URL}")
        print(f"  Error: {e}")
        print(f"  Download: https://voicevox.hiroshiba.jp/")
        return False


def generate_audio_query(text: str, speaker: int) -> dict:
    params = urllib.parse.urlencode({"text": text, "speaker": speaker})
    url = f"{VOICEVOX_URL}/audio_query?{params}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def synthesize(query: dict, speaker: int) -> bytes:
    url = f"{VOICEVOX_URL}/synthesis?speaker={speaker}"
    data = json.dumps(query).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def load_dialogue(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_for_character(char_name: str, char_config: dict,
                           speed: float = 1.1, pitch: float = 0.0) -> dict:
    """Generate all voice lines for one character."""
    char_folder = CHARACTERS_DIR / char_config["folder"]
    dialogue_path = char_folder / char_config["dialogue_file"]
    output_dir = char_folder / "Audio"

    dialogue = load_dialogue(str(dialogue_path))
    if dialogue is None:
        print(f"  [{char_name}] No dialogue file at {dialogue_path} ΓÇö skipping")
        return {"character": char_name, "status": "no_dialogue_file"}

    output_dir.mkdir(parents=True, exist_ok=True)
    lines = dialogue.get("lines", [])
    speaker = char_config["speaker_id"]
    total = len(lines)

    print(f"\n{'='*60}")
    print(f"  {char_name} (speaker {speaker}) ΓÇö {total} lines")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    results = []
    generated, cached, errors = 0, 0, 0

    for i, line in enumerate(lines):
        line_id = line["id"]
        text = line["text"]
        context = line.get("context", "")
        wav_path = output_dir / f"{line_id}.wav"

        preview = text[:45] + ("..." if len(text) > 45 else "")
        print(f"  [{i+1}/{total}] {line_id}: \"{preview}\"", end=" ", flush=True)

        if wav_path.exists():
            print("(cached)")
            results.append({"id": line_id, "status": "cached", "path": str(wav_path)})
            cached += 1
            continue

        try:
            query = generate_audio_query(text, speaker)
            query["speedScale"] = speed
            query["pitchScale"] = pitch
            wav = synthesize(query, speaker)
            wav_path.write_bytes(wav)
            kb = len(wav) / 1024
            print(f"({kb:.0f} KB)")
            results.append({"id": line_id, "status": "generated", "path": str(wav_path), "size_kb": kb})
            generated += 1
        except Exception as e:
            print(f"FAILED: {e}")
            results.append({"id": line_id, "status": "error", "error": str(e)})
            errors += 1

        time.sleep(0.3)

    # Write per-character manifest
    manifest = {
        "character": char_name,
        "speaker_id": speaker,
        "voice_style": char_config["voice_style"],
        "total": total,
        "generated": generated,
        "cached": cached,
        "errors": errors,
        "lines": results,
    }
    manifest_path = output_dir / "voice_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  ΓåÆ {generated} new, {cached} cached, {errors} errors")
    return {
        "character": char_name,
        "total": total,
        "generated": generated,
        "cached": cached,
        "errors": errors,
        "manifest": str(manifest_path),
    }


def generate_all(characters: list[str] | None = None,
                 speed: float = 1.1, pitch: float = 0.0):
    """Generate voices for specified characters (or all if None)."""
    if not check_voicevox():
        sys.exit(1)

    targets = characters if characters else list(CHARACTERS.keys())
    summary = []

    for name in targets:
        config = CHARACTERS.get(name)
        if config is None:
            print(f"Unknown character: {name}")
            continue
        result = generate_for_character(name, config, speed, pitch)
        summary.append(result)

    # Grand summary
    total_lines = sum(r.get("total", 0) for r in summary)
    total_gen = sum(r.get("generated", 0) for r in summary)
    total_cached = sum(r.get("cached", 0) for r in summary)
    total_errors = sum(r.get("errors", 0) for r in summary)

    print(f"\n{'='*60}")
    print(f"ALL CHARACTERS COMPLETE")
    print(f"  Lines:     {total_lines}")
    print(f"  Generated: {total_gen}")
    print(f"  Cached:    {total_cached}")
    print(f"  Errors:    {total_errors}")
    print(f"{'='*60}")

    # Write master manifest
    master = {
        "project": "Melodia ΓÇö ZunZun Family Voice Pack",
        "characters_processed": len(summary),
        "total_lines": total_lines,
        "total_generated": total_gen,
        "total_cached": total_cached,
        "total_errors": total_errors,
        "characters": summary,
    }
    master_path = CHARACTERS_DIR / "zunzun_voice_master_manifest.json"
    master_path.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Master manifest: {master_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate all ZunZun family voice lines")
    parser.add_argument("--character", action="append", dest="characters",
                        choices=list(CHARACTERS.keys()),
                        help="Generate for specific characters (repeatable). Omit for all.")
    parser.add_argument("--speed", type=float, default=1.1, help="Speech speed scale")
    parser.add_argument("--pitch", type=float, default=0.0, help="Pitch shift")
    args = parser.parse_args()

    generate_all(args.characters, args.speed, args.pitch)
