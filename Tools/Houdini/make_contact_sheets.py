import os, glob
from PIL import Image, ImageDraw, ImageFont

base_dirs = [
    ("Painterly Pearl Satin (3)", "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Painterly_4K", "T_PearlWoven_*_Painterly_BaseColor.png", 512),
    ("Pearl Lace — 9 Ornaments (Moon/Blush/Dusk x Floral/Geometric/Star)", "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Lace", "T_PearlWoven_Lace_*_BaseColor.png", 512),
]

out_contact = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/_ContactSheets"
os.makedirs(out_contact, exist_ok=True)

# also check Silk / Serene / Cosmic / Gilded / Flipbook if they exist yet
extra = [
    ("Silk Iridescent (6)", "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Silk", "T_*_BaseColor.png", 512),
    ("Serene — Canvas/Linen/Velvet (9)", "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Serene", "T_*_BaseColor.png", 512),
    ("Cosmic + Gilded (6)", "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Cosmic", "T_*_BaseColor.png", 512),
    ("Cosmic + Gilded (6)", "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Gilded", "T_*_BaseColor.png", 512),
    ("Flipbook (8 frames)", "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Flipbook", "T_*Frame*.png", 512),
]
base_dirs.extend(extra)

for title, folder, pattern, thumb in base_dirs:
    files = sorted(glob.glob(os.path.join(folder, pattern)))
    if not files:
        print(f"skip {title} — no files yet in {folder}")
        continue
    # filter only png
    files = [f for f in files if f.lower().endswith(".png")]
    if not files:
        continue
    n = len(files)
    cols = 3 if n <= 9 else 4
    if n == 8: cols = 4
    if n == 3: cols = 3
    rows = (n + cols - 1)//cols
    W = cols * thumb + (cols+1)*16
    header_h = 80
    label_h = 28
    H = header_h + rows * (thumb + label_h) + 24
    img = Image.new("RGB", (W, H), (18,16,22))
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
        font_label = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
    draw.rectangle([0,0,W,header_h], fill=(28,24,32))
    draw.text((16,18), title, fill=(245,238,230), font=font_title)
    draw.text((16,46), f"{n} variants  ·  4K tilable  ·  {os.path.basename(folder)}  ·  BaseColor preview (thumb {thumb}px)", fill=(180,170,165), font=font_label)
    for i, f in enumerate(files):
        col = i % cols
        row = i // cols
        x0 = 16 + col*(thumb+16)
        y0 = header_h + 16 + row*(thumb+label_h+8)
        try:
            im = Image.open(f)
            im.thumbnail((thumb, thumb), Image.LANCZOS)
            # center in thumb box
            bx = x0 + (thumb - im.width)//2
            by = y0 + (thumb - im.height)//2
            img.paste(im, (bx, by))
        except Exception as e:
            print(f"  thumb fail {f}: {e}")
            draw.rectangle([x0,y0,x0+thumb,y0+thumb], fill=(40,38,44))
        label = os.path.basename(f).replace("T_PearlWoven_","").replace("_BaseColor.png","").replace("T_","").replace(".png","")
        # draw label centered
        bbox = draw.textbbox((0,0), label, font=font_label)
        tw = bbox[2]-bbox[0]
        draw.text((x0 + (thumb-tw)//2, y0+thumb+4), label, fill=(210,200,195), font=font_label)
        # border
        draw.rectangle([x0-1,y0-1,x0+thumb+1,y0+thumb+1], outline=(60,58,65), width=1)
    safe_title = title.split(" —")[0].split(" (")[0].replace(" ","_").replace("/","_").replace("+","_")
    out = os.path.join(out_contact, f"ContactSheet_{safe_title}.png")
    img.save(out)
    print(f"saved {out}  {W}x{H}  {n} tiles")

# Also make a master lace detail sheet: each lace variant shows Base + Normal + Opacity + ORM crop 512
lace_folder = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Lace"
variants = sorted(set([os.path.basename(f).replace("T_PearlWoven_Lace_","").replace("_BaseColor.png","") for f in glob.glob(os.path.join(lace_folder,"T_PearlWoven_Lace_*_BaseColor.png"))]))
if variants:
    thumb = 384
    cols = 3
    rows = len(variants)
    W = cols*thumb + (cols+1)*12 + 16
    H = 80 + rows*(thumb+28) + 24
    img = Image.new("RGB", (W, H), (18,16,22))
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
        font_label = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 12)
        font_small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 11)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_small = ImageFont.load_default()
    draw.rectangle([0,0,W,80], fill=(28,24,32))
    draw.text((16,16), "Pearl Lace — Detail (Base + Normal + Opacity)  ·  9 ornaments", fill=(245,238,230), font=font_title)
    draw.text((16,44), "Left: BaseColor  Center: Normal  Right: Opacity (lace cutout)  ·  4K tilable", fill=(180,170,165), font=font_label)
    y = 80+16
    for v in variants:
        # row label
        draw.text((16, y-2), v, fill=(210,200,195), font=font_label)
        y_row = y+18
        for c, suffix in enumerate(["_BaseColor.png","_Normal.png","_Opacity.png"]):
            p = os.path.join(lace_folder, f"T_PearlWoven_Lace_{v}{suffix}")
            x0 = 16 + c*(thumb+12)
            try:
                im = Image.open(p)
                # crop center 1024 then thumb
                w,h = im.size
                crop = im.crop((w//2-512, h//2-512, w//2+512, h//2+512))
                crop.thumbnail((thumb,thumb), Image.LANCZOS)
                img.paste(crop, (x0, y_row))
            except Exception as e:
                print(f" detail fail {p}: {e}")
            draw.rectangle([x0-1,y_row-1,x0+thumb+1,y_row+thumb+1], outline=(60,58,65), width=1)
            lab = suffix.replace("_","").replace(".png","")
            draw.text((x0+6, y_row+thumb-18), lab, fill=(240,235,228), font=font_small)
        y += thumb + 28 + 10
    out = os.path.join(out_contact, "ContactSheet_Pearl_Lace_Detail.png")
    img.save(out)
    print(f"saved detail {out}")

print("done sheets in", out_contact)
