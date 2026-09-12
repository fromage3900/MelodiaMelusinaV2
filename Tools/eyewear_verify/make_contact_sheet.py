"""Render contact sheet — one thumbnail per silhouette, labeled.

Uses a single Blender session to render each silhouette by hiding all others.
Faster than spawning Blender 6 times.
"""
import subprocess
import sys
import os

BLEND = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/Silhouette_Grid_v1.blend"
OUT_DIR = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories"
CONTACT_SHEET = os.path.join(OUT_DIR, "contact_sheet_silhouettes.png")

SILHOUETTES = ["Rect", "Panto", "CatEye", "Aviator", "Browline", "Round"]

# Regenerate the grid first (mesh hosts, not empties)
print("=== Regenerating grid with mesh hosts ===")
regen_result = subprocess.run(
    [
        r"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe",
        "--background",
        "--python", r"P:/MelodiaMelusinaV2-Laptop/Tools/eyewear_verify/stage_silhouette_grid.py"
    ],
    capture_output=True, text=True, timeout=120
)
print(f"  Regen: {'DONE' if 'DONE' in regen_result.stdout else 'FAILED'}")

# Now render all 6 in one Blender session
print("\n=== Rendering all 6 silhouettes ===")
render_script = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/_render_all.py"

with open(render_script, 'w') as f:
    f.write(f"""
import bpy
import os

OUT_DIR = r'{OUT_DIR}'
SILHOUETTES = {SILHOUETTES}

scene = bpy.context.scene
scene.render.resolution_x = 320
scene.render.resolution_y = 200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

for label in SILHOUETTES:
    target = f'Eyewear_{{label}}'
    
    # Hide all eyewear except target
    for obj in bpy.data.objects:
        if 'Eyewear_' in obj.name:
            hide = (obj.name != target)
            obj.hide_render = hide
            obj.hide_viewport = hide
    
    # Frame camera
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects.get(target)
    if obj:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.view3d.camera_to_view_selected()
    
    # Render
    scene.render.filepath = os.path.join(OUT_DIR, f'silhouette_{{label.lower()}}.png')
    bpy.ops.render.render(write_still=True)
    print(f'RENDERED:{{label}}')

print('ALL_RENDERED')
""")

result = subprocess.run(
    [
        r"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe",
        "--background", BLEND,
        "--python", render_script
    ],
    capture_output=True, text=True, timeout=300
)

print(f"  Result: {result.stdout[-300:]}")

# Build contact sheet
print("\n=== Building contact sheet ===")
try:
    from PIL import Image, ImageDraw, ImageFont
    
    THUMB_W, THUMB_H = 320, 200
    COLS, ROWS = 3, 2
    LABEL_H = 30
    PADDING = 10
    
    sheet_w = COLS * THUMB_W + (COLS + 1) * PADDING
    sheet_h = ROWS * (THUMB_H + LABEL_H) + (ROWS + 1) * PADDING
    
    sheet = Image.new('RGB', (sheet_w, sheet_h), (30, 30, 30))
    draw = ImageDraw.Draw(sheet)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    for i, label in enumerate(SILHOUETTES):
        row = i // COLS
        col = i % COLS
        x = PADDING + col * (THUMB_W + PADDING)
        y = PADDING + row * (THUMB_H + LABEL_H + PADDING)
        
        thumb_path = os.path.join(OUT_DIR, f"silhouette_{label.lower()}.png")
        if os.path.exists(thumb_path):
            thumb = Image.open(thumb_path)
            thumb = thumb.resize((THUMB_W, THUMB_H), Image.LANCZOS)
            sheet.paste(thumb, (x, y + LABEL_H))
        
        draw.text((x, y), label, fill=(255, 255, 255), font=font)
    
    sheet.save(CONTACT_SHEET)
    print(f"  Contact sheet saved: {CONTACT_SHEET} ({sheet_w}x{sheet_h})")
except ImportError:
    print("  PIL not available — install with: pip install Pillow")
    print("  Individual renders saved to Saved/Accessories/")

# Cleanup
if os.path.exists(render_script):
    os.remove(render_script)

print("\nDONE")
