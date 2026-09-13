"""Procedural Music Visualizer — audio-reactive circular spectrum in Blender.

Takes any audio file and generates a circular bar visualizer that pulses to the beat.
Renders a turntable animation + contact sheet. Pure Blender Python.

Usage:
    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python Tools/music_visualizer.py -- --audio song.wav --bars 64 --duration 10
    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python Tools/music_visualizer.py -- --test-tone --bars 32 --duration 5
"""
import argparse
import math
import os
import struct
import sys
from pathlib import Path

import bpy

MM = 0.001


def generate_test_tone(path, duration=10.0, freq=440.0):
    """Generate a test WAV file with a sine wave + harmonics."""
    import wave
    sample_rate = 44100
    n_samples = int(duration * sample_rate)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            val = (0.5 * math.sin(2 * math.pi * freq * t) +
                   0.25 * math.sin(2 * math.pi * freq * 2 * t) +
                   0.125 * math.sin(2 * math.pi * freq * 3 * t) +
                   0.3 * math.sin(2 * math.pi * 0.5 * t))
            fade = min(1.0, t / 0.5, (duration - t) / 0.5)
            val *= fade
            wf.writeframes(struct.pack('<h', int(val * 32767 * 0.8)))
    return path


def _hsv_to_rgb(h, s, v):
    if s == 0:
        return (v, v, v)
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i %= 6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    return (v, p, q)


def build_visualizer(audio_path, n_bars=64, radius=2.0):
    scene = bpy.context.scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create bars in a circle
    bars = []
    for i in range(n_bars):
        angle = (i / n_bars) * 2 * math.pi
        bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(angle) * radius, math.sin(angle) * radius, 0))
        bar = bpy.context.active_object
        bar.name = f'Bar_{i:03d}'
        bar.scale = (0.08, 0.08, 0.5)
        bar.rotation_euler = (0, 0, angle - math.pi / 2)

        mat = bpy.data.materials.new(name=f'Mat_{i:03d}')
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        hue = i / n_bars
        color = _hsv_to_rgb(hue, 0.8, 1.0)
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Emission Color'].default_value = (*color, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 2.0
        bar.data.materials.append(mat)
        bars.append(bar)

    # Center sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 0))
    center = bpy.context.active_object
    center_mat = bpy.data.materials.new(name='Center_Mat')
    center_mat.use_nodes = True
    center_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)
    center_mat.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 1.0
    center.data.materials.append(center_mat)

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.5))
    ground = bpy.context.active_object
    ground_mat = bpy.data.materials.new(name='Ground_Mat')
    ground_mat.use_nodes = True
    ground_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.02, 0.03, 1.0)
    ground.data.materials.append(ground_mat)

    # Lights
    bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
    key = bpy.context.active_object
    key.name = 'Key'
    key.data.energy = 500
    key.data.size = 3

    bpy.ops.object.light_add(type='AREA', location=(-3, 2, 2))
    rim = bpy.context.active_object
    rim.name = 'Rim'
    rim.data.energy = 200
    rim.data.size = 2
    rim.data.color = (0.6, 0.7, 1.0)

    # Camera
    bpy.ops.object.camera_add(location=(0, -6, 3))
    cam = bpy.context.active_object
    cam.name = 'Cam_Visualizer'
    cam.data.lens = 35
    cam.data.clip_start = 0.01
    scene.camera = cam

    # World
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.01, 0.01, 0.02, 1.0)
    bg.inputs['Strength'].default_value = 0.5

    # Render settings
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.fps = 30

    return bars


def animate_bars(bars, fps=30, duration_seconds=10):
    scene = bpy.context.scene
    n_frames = int(duration_seconds * fps)
    scene.frame_start = 1
    scene.frame_end = n_frames

    for i, bar in enumerate(bars):
        freq = 0.5 + (i / len(bars)) * 3.0
        phase = i * 0.3

        for frame in range(1, n_frames + 1):
            t = frame / fps
            base = 0.3 + 0.2 * math.sin(2 * math.pi * freq * t + phase)
            beat = 0.4 * max(0, math.sin(2 * math.pi * 2.0 * t))
            wave = 0.3 * math.sin(2 * math.pi * freq * 0.5 * t)
            height = max(0.1, min(3.0, base + beat + wave))
            bar.scale.z = height
            bar.keyframe_insert(data_path='scale', index=2, frame=frame)

    for bar in bars:
        if bar.animation_data and bar.animation_data.action:
            action = bar.animation_data.action
            if hasattr(action, 'fcurves'):
                for fc in action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'BEZIER'


def animate_camera(duration_seconds=10, fps=30):
    scene = bpy.context.scene
    cam = bpy.data.objects.get('Cam_Visualizer')
    if not cam:
        return
    n_frames = int(duration_seconds * fps)

    for frame in range(1, n_frames + 1):
        t = frame / fps
        angle = (t / duration_seconds) * 2 * math.pi
        cam.location = (math.sin(angle) * 6, -math.cos(angle) * 6, 2.5 + 0.5 * math.sin(2 * math.pi * t * 0.5))
        direction = mathutils.Vector((0, 0, 0)) - cam.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam.rotation_euler = rot_quat.to_euler()
        cam.keyframe_insert(data_path='location', frame=frame)
        cam.keyframe_insert(data_path='rotation_euler', frame=frame)


def render_contact_sheet(frame_dir, output_path, n_frames=12):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print('PIL not available — skipping contact sheet')
        return

    frames = sorted(Path(frame_dir).glob('*.png'))
    if not frames:
        return

    step = max(1, len(frames) // n_frames)
    selected = frames[::step][:n_frames]

    cols = 4
    rows = (len(selected) + cols - 1) // cols
    thumb_w, thumb_h = 320, 180
    padding = 10
    label_h = 25

    sheet_w = cols * thumb_w + (cols + 1) * padding
    sheet_h = rows * (thumb_h + label_h) + (rows + 1) * padding

    sheet = Image.new('RGB', (sheet_w, sheet_h), (20, 20, 25))
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.truetype('arial.ttf', 14)
    except Exception:
        font = ImageFont.load_default()

    for i, frame_path in enumerate(selected):
        row = i // cols
        col = i % cols
        x = padding + col * (thumb_w + padding)
        y = padding + row * (thumb_h + label_h + padding)

        img = Image.open(frame_path)
        img = img.resize((thumb_w, thumb_h), Image.LANCZOS)
        sheet.paste(img, (x, y + label_h))

        frame_num = int(frame_path.stem)
        draw.text((x, y), f'Frame {frame_num}', fill=(255, 255, 255), font=font)

    sheet.save(output_path)
    print(f'Contact sheet: {output_path}')


def main():
    parser = argparse.ArgumentParser(description='Procedural Music Visualizer')
    parser.add_argument('--audio', type=str, help='Path to audio file (WAV/MP3)')
    parser.add_argument('--test-tone', action='store_true', help='Generate test tone')
    parser.add_argument('--output', type=str, default=r'P:/MelodiaMelusinaV2-Laptop/Saved/Accessories')
    parser.add_argument('--duration', type=float, default=10.0)
    parser.add_argument('--bars', type=int, default=64)
    # Blender passes --background --python script.py -- args; skip those
    args, _ = parser.parse_known_args()

    if args.audio:
        audio_path = args.audio
    else:
        audio_path = os.path.join(args.output, '_test_tone.wav')
        print(f'Generating test tone: {audio_path}')
        generate_test_tone(audio_path, duration=args.duration)

    if not os.path.exists(audio_path):
        print(f'Audio file not found: {audio_path}')
        return 1

    print(f'\nBuilding visualizer with {args.bars} bars...')
    bars = build_visualizer(audio_path, n_bars=args.bars)

    print('Animating bars...')
    animate_bars(bars, duration_seconds=args.duration)

    print('Animating camera...')
    animate_camera(duration_seconds=args.duration)

    blend_path = os.path.join(args.output, 'visualizer.blend')
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f'Saved blend: {blend_path}')

    frame_dir = os.path.join(args.output, 'frames')
    os.makedirs(frame_dir, exist_ok=True)

    scene = bpy.context.scene
    scene.render.filepath = os.path.join(frame_dir, '')

    print(f'\nRendering {scene.frame_end} frames...')
    bpy.ops.render.render(animation=True)

    contact_path = os.path.join(args.output, 'contact_sheet.png')
    render_contact_sheet(frame_dir, contact_path)

    print('\nDONE')
    return 0


if __name__ == '__main__':
    sys.exit(main())
