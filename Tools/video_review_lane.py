#!/usr/bin/env python3
"""Video Review Lane — fresh-eyes regression review of PIE captures.

Reviews frames (PNG/JPG) or a video (ffmpeg-extracted frames) with a vision
model and writes a JSON report with per-frame observations + verdict.

Usage:
  python video_review_lane.py --frames Saved/Playtest/*.png [--out report.json]
  python video_review_lane.py --video captured.mp4 [--fps 0.5]
  python video_review_lane.py --image shot.png
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_router import load_keys, ENDPOINTS, log_usage  # noqa: E402

REVIEW_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REVIEW_ENDPOINT = "openrouter"
MAX_IMAGE_BYTES = 19 * 1024 * 1024
REVIEW_PROMPT = (
    "You are a gameplay QA reviewer for an Unreal Engine JRPG. Examine this game frame. "
    "Report: (1) what UI is visible (dialogue box, battle menu, rhythm highway, HUD), "
    "(2) any visible errors (missing meshes, broken UI, debug text, black screen, "
    "T-pose, z-fighting), (3) overall visual state. Be terse, one line per item."
)


def vision_chat(model, endpoint, prompt, keys, images):
    url = ENDPOINTS[endpoint] + "/chat/completions"
    content = [{"type": "text", "text": prompt}]
    for img in images:
        with open(img, "rb") as fh:
            raw = fh.read()
        if len(raw) > MAX_IMAGE_BYTES:
            raw = raw[:MAX_IMAGE_BYTES]
        content.append({
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(raw).decode()},
        })
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 700,
        "temperature": 0.0,
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + keys[endpoint], "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def extract_frames(video, fps, workdir):
    out_dir = os.path.join(workdir, "frames")
    os.makedirs(out_dir, exist_ok=True)
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", video, "-vf", "fps=%s" % fps, os.path.join(out_dir, "f_%04d.png")],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg failed: %s" % proc.stderr[-500:])
    frames = sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith(".png"))
    return frames


def review(images, out_path, model=REVIEW_MODEL):
    keys = load_keys()
    if not keys.get(REVIEW_ENDPOINT):
        sys.exit("no key for %s" % REVIEW_ENDPOINT)
    observations = []
    errors = []
    for i, img in enumerate(images):
        try:
            result = vision_chat(model, REVIEW_ENDPOINT, REVIEW_PROMPT, keys, [img])
            usage = result.get("usage")
            log_usage("vision", model, REVIEW_ENDPOINT, usage)
            observations.append({
                "frame": os.path.basename(img),
                "index": i,
                "review": result["choices"][0]["message"]["content"],
            })
        except Exception as exc:
            errors.append({"frame": os.path.basename(img), "error": str(exc)[:300]})
            log_usage("vision", REVIEW_MODEL, REVIEW_ENDPOINT, None, ok=False)
    report = {
        "model": model,
        "frames_reviewed": len(observations),
        "frames_failed": len(errors),
        "observations": observations,
        "errors": errors,
    }
    flagged = 0
    for obs in observations:
        low = obs["review"].lower()
        if any(w in low for w in ["error", "broken", "missing", "black screen", "t-pose", "z-fighting", "crash"]):
            flagged += 1
    report["flagged_frames"] = flagged
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print("report: %s" % out_path)
    print(json.dumps(report, indent=2))
    return 0 if errors == [] else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", nargs="+", default=[])
    ap.add_argument("--video")
    ap.add_argument("--image")
    ap.add_argument("--fps", type=float, default=0.5)
    ap.add_argument("--out")
    ap.add_argument("--sample", type=int, default=0, help="max frames to send (0 = all)")
    ap.add_argument("--model", default=REVIEW_MODEL, help="vision model id")
    args = ap.parse_args()
    review_model = args.model

    images = list(args.frames)
    workdir = None
    if args.video:
        workdir = tempfile.mkdtemp(prefix="vidrev_")
        images = extract_frames(args.video, args.fps, workdir)
    if args.image:
        images.append(args.image)
    if not images:
        sys.exit("nothing to review: pass --frames, --video, or --image")
    if args.sample and len(images) > args.sample:
        step = len(images) / args.sample
        images = [images[int(i * step)] for i in range(args.sample)]
    sys.exit(review(images, args.out, model=review_model))


if __name__ == "__main__":
    main()
