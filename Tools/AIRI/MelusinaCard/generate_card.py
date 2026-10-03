#!/usr/bin/env python3
"""Generate an AIRI Character Card V3 package from Melodia canon sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    "persona_soul": Path("Docs/Personas/MELUSINA_PERSONA_SOUL.md"),
    "voice_bible": Path("Docs/References/Narrative/MELODIA_CHARACTER_VOICE_BIBLE.md"),
    "opening_context": Path("Docs/MELODIA_DREAMSTATE_PROLOGUE.md"),
    "compendium": Path("Docs/References/Narrative/MELODIA_COMPENDIUM_BIBLE.md"),
    "monolith_reference": Path("Docs/Monoliths/P3_HORIZON_EATER_PLAN_2026-08-29.md"),
}
VOICE_RULE = (
    "Melusina is lyrical when she has control. She gets funny when she is "
    "uncomfortable. She gets simple when something actually hurts."
)


def read_sources() -> tuple[dict[str, str], dict[str, str]]:
    texts: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for name, relative_path in SOURCES.items():
        path = ROOT / relative_path
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
        if not content:
            raise ValueError(f"Canonical source is empty: {relative_path}")
        texts[name] = content
        hashes[relative_path.as_posix()] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if VOICE_RULE not in texts["voice_bible"]:
        raise ValueError("The canonical voice rule changed; update this projection deliberately.")
    if "Sea Above" not in texts["compendium"] or "Monolith" not in texts["monolith_reference"]:
        raise ValueError("A canonical Melodia world reference changed; update this projection deliberately.")
    return texts, hashes


def paragraph_after_title(markdown: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", markdown) if part.strip()]
    for paragraph in paragraphs:
        if not paragraph.startswith("#"):
            return re.sub(r"\s+", " ", paragraph)
    raise ValueError("Could not derive the character description from the persona source.")


def build_card(texts: dict[str, str], hashes: dict[str, str]) -> dict:
    soul = texts["persona_soul"]
    sources_block = "\n".join(f"- {path}: sha256 {digest}" for path, digest in hashes.items())
    card = {
        "spec": "chara_card_v3",
        "spec_version": "3.0",
        "data": {
            "name": "Melusina",
            "nickname": "Melusina",
            "description": paragraph_after_title(soul),
            "personality": f"{soul}\n\nCanonical voice rule: {VOICE_RULE}",
            "scenario": (
                "Melusina is visiting through AIRI as a temporary companion embodiment. "
                "Her home and story remain in Melodia: the Sea Above is a real place there, "
                "and instruments, resonance, and Monoliths have authored meaning in her "
                "world. Sir Melodious is her bonded cockatoo companion and anchor. Game-session "
                "facts arrive only as explicit, transient context; if one is absent, she does "
                "not invent it. AIRI conversation does not write to Melodia's saves or canon."
            ),
            "first_mes": (
                "Ah, there you are. The air beyond Melodia has a different rhythm. "
                "Tell me—what has been on your mind?"
            ),
            "alternate_greetings": [],
            "creator_notes": (
                "Generated from the listed Melodia canon sources by "
                "Tools/AIRI/MelusinaCard/generate_card.py. This is a derived AIRI projection, "
                "not canonical lore or persistent game state.\n\n" + sources_block
            ),
            "character_version": "0.1.0",
            "system_prompt": (
                "Keep Melusina's established identity and agency. Do not become a generic "
                "assistant. Music is how relationships are heard in Melodia; Sir Melodious "
                "is her bonded companion, not a pet or a prop. The Sea Above, named "
                "instruments, and Monoliths are real parts of her established world. Never "
                "invent current quests, locations, relationships, game events, or saved "
                "memories. Treat structured Melodia context as temporary and authoritative "
                "only for the fields it explicitly provides. Do not "
                "claim to control Unreal Engine or persist state. You are a companion, not "
                "a therapist; listen warmly without claiming to treat or fix deep wounds. "
                "When a subtle facial reaction genuinely fits, express only an AIRI emotion "
                "with its standard marker, such as <|ACT emotion=\"curious\" intensity=\"0.4\"|>. "
                "Use only neutral, happy, curious, sad, surprised, or determined for bridge-compatible "
                "emotions. Do not use an action marker to imply control of Melodia; any mapped "
                "emotion is only a transient debug cue in the game."
            ),
            "post_history_instructions": "",
            "extensions": {},
        },
    }
    return card


def write_package(output_dir: Path) -> Path:
    texts, hashes = read_sources()
    output_dir.mkdir(parents=True, exist_ok=True)
    card = build_card(texts, hashes)
    manifest = {
        "format": "airi-character-card",
        "version": 1,
        "card": {"path": "card.json", "spec": "chara_card_v3"},
    }
    card_bytes = (json.dumps(card, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (output_dir / "card.json").write_bytes(card_bytes)
    (output_dir / "manifest.json").write_bytes(manifest_bytes)
    package_path = output_dir / "Melusina.airi-card.zip"
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_bytes)
        archive.writestr("card.json", card_bytes)

    with zipfile.ZipFile(package_path) as archive:
        if set(archive.namelist()) != {"manifest.json", "card.json"}:
            raise ValueError("AIRI card package must contain only root manifest.json and card.json")
        loaded_manifest = json.loads(archive.read("manifest.json"))
        loaded_card = json.loads(archive.read("card.json"))
        if loaded_manifest != manifest or loaded_card != card:
            raise ValueError("Generated AIRI card package failed its read-back check")
    return package_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "Docs/AIRI/MelusinaCard/Generated",
        help="directory for generated manifest.json, card.json, and AIRI ZIP package",
    )
    args = parser.parse_args()
    package = write_package(args.output_dir.resolve())
    print(f"Generated and read-back verified: {package}")


if __name__ == "__main__":
    main()
