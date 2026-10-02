from PIL import Image, ImageDraw
import os, glob

SRC = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic\proxy\panels_v5"
OUT = r"C:\Users\brenn\AppData\Local\Temp\animcheck\contact_sheet.png"

files = sorted(glob.glob(os.path.join(SRC, "panel_*.png")))
print("contact sheet: %d panels" % len(files))
COLS, ROWS = 5, 4
TW, TH = 384, 216
sheet = Image.new("RGB", (COLS*TW, ROWS*TH), (12, 14, 22))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB").resize((TW, TH))
    x = (i % COLS) * TW
    y = (i // COLS) * TH
    sheet.paste(im, (x, y))
    n = os.path.basename(f).replace("panel_", "").replace(".png", "")
    d.rectangle([x, y, x+34, y+22], fill=(0, 0, 0))
    d.text((x+8, y+5), n, fill=(255, 220, 160))
    d.rectangle([x, y, x+TW-1, y+TH-1], outline=(70, 70, 90))
sheet.save(OUT)
print("wrote", OUT, sheet.size)