"""VOICEVOX Installer & Setup ΓÇö downloads and configures VOICEVOX for ZunZun integration.

Downloads VOICEVOX (free text-to-speech engine) and the Zundamon/Zunko voice libraries.

Usage:
  python setup_voicevox.py
  python setup_voicevox.py --check-only
  python setup_voicevox.py --start-server
"""

import json
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

VOICEVOX_VERSION = "0.25.2"
VOICEVOX_DOWNLOAD = f"https://github.com/VOICEVOX/voicevox/releases/download/{VOICEVOX_VERSION}/VOICEVOX.{VOICEVOX_VERSION}.win-x64.zip"
INSTALL_DIR = Path(r"G:\programs\VOICEVOX")
VOICEVOX_API = "http://127.0.0.1:50021"
VOICEVOX_EXE = INSTALL_DIR / "VOICEVOX.exe"


# ΓöÇΓöÇ Check ΓöÇΓöÇ

def check_installed() -> bool:
    """Check if VOICEVOX is already installed."""
    return VOICEVOX_EXE.exists()


def check_running() -> bool:
    """Check if VOICEVOX engine is running."""
    try:
        with urllib.request.urlopen(f"{VOICEVOX_API}/version", timeout=3) as r:
            data = json.loads(r.read())
            print(f"  VOICEVOX v{data.get('version', '?')} is running")
            return True
    except Exception:
        return False


def check_speakers() -> dict:
    """List installed voice speakers via API."""
    if not check_running():
        return {}
    try:
        with urllib.request.urlopen(f"{VOICEVOX_API}/speakers", timeout=5) as r:
            speakers = json.loads(r.read())
            result = {}
            for s in speakers:
                name = s.get("name", "?")
                styles = [st.get("name", "?") for st in s.get("styles", [])]
                speaker_uuid = s.get("speaker_uuid", "")
                result[name] = {
                    "styles": styles,
                    "speaker_uuid": speaker_uuid,
                }
            return result
    except Exception as e:
        print(f"  Could not fetch speaker list: {e}")
        return {}


# ΓöÇΓöÇ Download ΓöÇΓöÇ

def download_voicevox():
    """Download and extract VOICEVOX."""
    if check_installed():
        print(f"VOICEVOX already installed at {INSTALL_DIR}")
        return True

    print(f"Downloading VOICEVOX v{VOICEVOX_VERSION}...")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = INSTALL_DIR / f"VOICEVOX-{VOICEVOX_VERSION}.zip"

    try:
        urllib.request.urlretrieve(VOICEVOX_DOWNLOAD, zip_path)
        print(f"  Downloaded to {zip_path}")

        print("  Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(INSTALL_DIR)
        zip_path.unlink()

        print(f"  Installed to {INSTALL_DIR}")
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        print(f"  Please download manually from: https://voicevox.hiroshiba.jp/")
        return False


# ΓöÇΓöÇ Launch ΓöÇΓöÇ

def start_server():
    """Launch VOICEVOX engine in the background."""
    if check_running():
        print("VOICEVOX is already running.")
        return True

    if not check_installed():
        print("VOICEVOX not installed. Run download_voicevox() first.")
        return False

    print("Starting VOICEVOX engine...")
    try:
        subprocess.Popen(
            [str(VOICEVOX_EXE)],
            cwd=str(INSTALL_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("  VOICEVOX launched (it may take a few seconds to start)")
        return True
    except Exception as e:
        print(f"  Failed to start: {e}")
        print(f"  Please start VOICEVOX manually: {VOICEVOX_EXE}")
        return False


# ΓöÇΓöÇ Main ΓöÇΓöÇ

def setup():
    """Full setup: download, install, launch."""
    print("=" * 60)
    print("VOICEVOX SETUP FOR ZUNZUN PROJECT")
    print("=" * 60)

    # 1. Download
    if not check_installed():
        ok = download_voicevox()
        if not ok:
            return

    # 2. Launch
    if not check_running():
        start_server()
        import time
        time.sleep(3)
        if not check_running():
            print("VOICEVOX didn't start. Please launch it manually.")
            return

    # 3. Show available speakers
    print("\nAvailable voice speakers:")
    speakers = check_speakers()
    if speakers:
        for name, info in speakers.items():
            styles_str = ", ".join(info["styles"])
            print(f"  {name}: {styles_str}")
    else:
        print("  Could not fetch speakers ΓÇö engine may still be loading.")

    # 4. Verify ZunZun family speakers
    needed = ["πüÜπéôπüáπééπéô", "σ¢¢σ¢╜πéüπüƒπéô", "µ¥▒σîùπüìπéèπüƒπéô", "µ¥▒σîùπéñπé┐πé│", "µ¥▒σîùπüÜπéôσ¡É", "Σ╣¥σ╖₧πü¥πéë", "Σ╕¡Θâ¿πüñπéïπüÄ"]
    print("\nZunZun family speaker check:")
    for name in needed:
        found = name in speakers
        status = "Γ£ô" if found else "Γ£ù MISSING"
        print(f"  {status} {name}")
        if not found:
            print(f"    ΓåÆ Open VOICEVOX and check: Settings ΓåÆ Manage Voice Libraries")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="VOICEVOX setup for ZunZun project")
    parser.add_argument("--check-only", action="store_true", help="Only check status")
    parser.add_argument("--start-server", action="store_true", help="Start VOICEVOX engine")
    parser.add_argument("--list-speakers", action="store_true", help="List installed speakers")
    args = parser.parse_args()

    if args.check_only:
        print(f"Installed: {check_installed()}")
        print(f"Running:   {check_running()}")
        speakers = check_speakers()
        if speakers:
            print(f"Speakers:  {len(speakers)} voices available")
    elif args.start_server:
        start_server()
    elif args.list_speakers:
        check_speakers()
    else:
        setup()
