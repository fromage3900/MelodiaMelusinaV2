"""Read-only UE animation track probe for root-motion and unit evidence."""
from __future__ import annotations

import argparse
import json
import sys

from mcp_client import monolith


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("asset", nargs="+")
    parser.add_argument("--bones", default="root,root_x,c_traj,c_root_master_x,c_spine_02_x")
    args = parser.parse_args()
    paths = args.asset
    bones = [item.strip() for item in args.bones.split(",") if item.strip()]
    command = (
        "import unreal, json\n"
        f"paths = {paths!r}\n"
        f"bones = {bones!r}\n"
        "out = []\n"
        "for path in paths:\n"
        "    sequence = unreal.EditorAssetLibrary.load_asset(path)\n"
        "    row = {'asset': path, 'loaded': bool(sequence), 'samples': []}\n"
        "    if sequence:\n"
        "        frame_count = unreal.AnimationLibrary.get_num_frames(sequence)\n"
        "        frames = [0, max(0, frame_count // 2), max(0, frame_count - 1)]\n"
        "        for bone in bones:\n"
        "            values = []\n"
        "            for frame in frames:\n"
        "                try:\n"
        "                    t = unreal.AnimationLibrary.get_bone_pose_for_frame(sequence, bone, frame, False).translation\n"
        "                    values.append({'frame': frame, 'x': float(t.x), 'y': float(t.y), 'z': float(t.z)})\n"
        "                except Exception as exc:\n"
        "                    values.append({'frame': frame, 'error': str(exc)})\n"
        "            row['samples'].append({'bone': bone, 'values': values})\n"
        "    out.append(row)\n"
        "print(json.dumps(out))\n"
    )
    raw = monolith("editor_query", {"action": "run_python", "command": command}, timeout=90)
    if raw.startswith("ERROR:"):
        print(raw)
        return 1
    print(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
