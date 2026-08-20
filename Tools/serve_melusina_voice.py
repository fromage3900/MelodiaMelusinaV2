"""Melusina Voice Server ΓÇö serve the Melusina Unified Feminine TTS model as an HTTP API.

Uses the pre-trained Style-Bert-VITS2 ONNX model from Downloads.
Drop-in compatible with VOICEVOX API format so the existing dialogue
generator can call either VOICEVOX (ZunZun family) or Melusina.

Usage:
  pip install style-bert-vits2 soundfile
  python serve_melusina_voice.py --port 50022
  
Then call:  POST http://127.0.0.1:50022/audio_query + /synthesis
(same API shape as VOICEVOX for drop-in compatibility)
"""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Paths
MODEL_DIR = Path(r"C:\Users\froma\Downloads\Melusina_Unified_Feminine_Step1000_Candidate")
OUTPUT_DIR = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Characters\Melusina\Audio")

# Style-Bert-VITS2 model files
MODEL_FILES = {
    "acoustic": MODEL_DIR / "acoustic.onnx",
    "dur": MODEL_DIR / "dur.onnx",
    "linguistic": MODEL_DIR / "linguistic.onnx",
    "pitch": MODEL_DIR / "pitch.onnx",
    "variance": MODEL_DIR / "variance.onnx",
    "vocoder": MODEL_DIR / "vocoder.onnx",
    "config": MODEL_DIR / "dsconfig.yaml",
    "phonemes": MODEL_DIR / "phonemes.json",
    "languages": MODEL_DIR / "languages.json",
}

MELUSINA_SPEAKER_ID = 100  # Custom ID for Melusina (above standard VOICEVOX range)
DEFAULT_PORT = 50022


class MelusinaVoiceHandler(BaseHTTPRequestHandler):
    """Minimal VOICEVOX-compatible HTTP handler for Melusina's voice."""

    model = None  # Lazy-loaded TTS model

    def log_message(self, fmt, *args):
        pass  # Silent

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_wav(self, audio_bytes: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(audio_bytes)))
        self.end_headers()
        self.wfile.write(audio_bytes)

    def do_GET(self):
        if self.path == "/version":
            self._send_json({"version": "melusina-1.0"})
        elif self.path == "/speakers":
            self._send_json([{
                "name": "Melusina",
                "speaker_uuid": "melusina-unified-feminine",
                "styles": [{"name": "Feminine", "id": MELUSINA_SPEAKER_ID}],
            }])
        elif self.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/audio_query":
            self._handle_audio_query()
        elif self.path == "/synthesis":
            self._handle_synthesis()
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_audio_query(self):
        """VOICEVOX-compatible audio query endpoint."""
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        text = params.get("text", [""])[0]
        speaker = int(params.get("speaker", [MELUSINA_SPEAKER_ID])[0])

        if not text:
            self._send_json({"error": "No text provided"}, 400)
            return

        # Return a query object with phoneme timing
        query = {
            "accent_phrases": [],
            "speedScale": 1.0,
            "pitchScale": 0.0,
            "intonationScale": 1.0,
            "volumeScale": 1.0,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1,
            "outputSamplingRate": 24000,
            "outputStereo": False,
            "kana": text,  # Text in kana/kanji preserved
        }
        self._send_json(query)

    def _handle_synthesis(self):
        """Synthesize audio from a query."""
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        speaker = int(params.get("speaker", [MELUSINA_SPEAKER_ID])[0])

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        query = json.loads(body.decode("utf-8"))

        text = query.get("kana", "")
        if not text:
            self._send_json({"error": "No text (kana) in query"}, 400)
            return

        try:
            audio = self._synthesize_text(text, query)
            self._send_wav(audio)
        except Exception as e:
            self._send_json({"error": f"Synthesis failed: {e}"}, 500)

    def _synthesize_text(self, text: str, query: dict) -> bytes:
        """Run the Style-Bert-VITS2 model to synthesize audio.

        Falls back to a simple sine-wave placeholder if the model isn't loaded.
        """
        if MelusinaVoiceHandler.model is None:
            # Try to load, or fall back to placeholder
            try:
                MelusinaVoiceHandler.model = _load_melusina_model()
            except Exception as e:
                print(f"[MelusinaVoice] Model not loaded: {e}")
                print("[MelusinaVoice] Generating placeholder audio (install SBV2 for real voice)")
                return _generate_placeholder_audio(text, query)

        # Real synthesis via Style-Bert-VITS2
        try:
            return MelusinaVoiceHandler.model.synthesize(text, query)
        except Exception as e:
            print(f"[MelusinaVoice] Synthesis error: {e}")
            return _generate_placeholder_audio(text, query)


def _load_melusina_model():
    """Load the Melusina Unified Feminine ONNX model via Style-Bert-VITS2."""
    try:
        import style_bert_vits2 as sbv2

        print("[MelusinaVoice] Loading model...")
        model = sbv2.TTSModel(
            model_dir=str(MODEL_DIR),
            config_path=str(MODEL_FILES["config"]),
            device="cpu",  # or "cuda"
        )
        print("[MelusinaVoice] Model loaded successfully")
        return model
    except ImportError:
        raise RuntimeError(
            "Style-Bert-VITS2 not installed.\n"
            "  pip install style-bert-vits2 soundfile\n"
            "Or use placeholder mode (generates sine beeps for testing)."
        )
    except Exception as e:
        raise RuntimeError(f"Model load failed: {e}")


def _generate_placeholder_audio(text: str, query: dict) -> bytes:
    """Generate a simple sine-tone placeholder WAV for testing pipeline."""
    import math
    import struct
    import wave
    import io

    sr = query.get("outputSamplingRate", 24000)
    # Duration: ~0.15s per character
    duration = max(0.3, len(text) * 0.15)
    freq = 440  # A4 note as placeholder

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1 if not query.get("outputStereo") else 2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = int(sr * duration)
        for i in range(frames):
            sample = int(16000 * math.sin(2.0 * math.pi * freq * i / sr))
            wf.writeframes(struct.pack("<h", sample))

    return buf.getvalue()


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Server launcher
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def start_server(port: int = DEFAULT_PORT):
    """Start the Melusina voice HTTP server."""
    server = HTTPServer(("127.0.0.1", port), MelusinaVoiceHandler)
    print(f"[MelusinaVoice] Server running on http://127.0.0.1:{port}")
    print(f"  Endpoints:  /version  /speakers  /health  /audio_query  /synthesis")
    print(f"  Speaker ID: {MELUSINA_SPEAKER_ID} (Melusina)")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[MelusinaVoice] Server stopped")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Melusina Voice Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--check-model", action="store_true", help="Verify model files exist")
    args = parser.parse_args()

    if args.check_model:
        print("Checking Melusina model files:")
        all_ok = True
        for name, path in MODEL_FILES.items():
            exists = path.exists()
            status = "Γ£ô" if exists else "Γ£ù MISSING"
            size_mb = round(path.stat().st_size / 1e6, 1) if exists else 0
            print(f"  {status} {name}: {path.name} ({size_mb} MB)")
            if not exists:
                all_ok = False
        if all_ok:
            print("\nAll model files present. Ready to start server.")
        sys.exit(0 if all_ok else 1)

    start_server(args.port)
