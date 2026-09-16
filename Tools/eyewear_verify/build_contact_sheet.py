"""Build contact sheet from existing silhouette renders."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories"
CONTACT_SHEET = os.path.join(OUT_DIR, "contact_sheet_silhouettes.png")

SILHOUETTES = ["Rect", "Panto", "CatEye", "Aviator", "Browline", "Round"]
THUMB_W, THUMB_H = 320, 200
COLS, ROWS = 3, 2
LABEL_H = 30
PADDING = 10

sheet_w = COLS * THUMB_W + (COLS + 1) * PADDING
sheet_h = ROWS * (THUMB_H + LABEL_H) + (ROWS + 1) * PADDING

print(f"Building contact sheet: {sheet_w}x{sheet_h}")
sheet = Image.new('RGB', (sheet_w, sheet_h), (25, 25, 30))
draw = ImageDraw.Draw(sheet)

try:
    font = ImageFont.truetype("arial.ttf", 16)
    small_font = ImageFont.truetype("arial.ttf", 12)
except Exception:
    font = ImageFont.load_default()
    small_font = font

for i, label in enumerate(SILHOUETTES):
    row = i // COLS
    col = i % COLS
    x = PADDING + col * (THUMB_W + PADDING)
    y = PADDING + row * (THUMB_H + LABEL_H + PADDING)
    
    thumb_path = os.path.join(OUT_DIR, f"silhouette_{label.lower()}.png")
    if os.path.exists(thumb_path):
        thumb = Image.open(thumb_path)
        thumb.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
        # Center in cell
        tx = x + (THUMB_W - thumb.width) // 2
        ty = y + LABEL_H + (THUMB_H - thumb.height) // 2
        sheet.paste(thumb, (tx, ty))
    
    # Label with index
    draw.text((x, y), f"{i}. {label}", fill=(255, 255, 255), font=font)
    # File name under
    draw.text((x, y + 16), f"silhouette_{label.lower()}.png", fill=(180, 180, 180), font=small_font)

sheet.save(CONTACT_SHEET)
print(f"Saved: {CONTACT_SHEET}")
print(f"File size: {os.path.getsize(CONTACT_SHEET) / 1024:.0f} KB")

# Also make a labeled composite showing measurements
print("\nIndividual files:")
for label in SILHOUETTES:
    p = os.path.join(OUT_DIR, f"silhouette_{label.lower()}.png")
    if os.path.exists(p):
        sz = os.path.getsize(p) / 1024
        print(f"  silhouette_{label.lower()}.png  ({sz:.0f} KB)")

print("DONE")
