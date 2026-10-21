#!/usr/bin/env python3
"""
Assemble the Final Milestone Contact Sheet (2x3 Grid):
  1. Melusina V2 Body + Non-Inverted Idle (A_Shin_Idle_stand_MocapConv) + FaceSDF Toon
  2. Sir Melodious Canonical ARP v7 Mesh + ABP_SirMelodious_v7 + Toon Materials
  3. Melusina V2 Hat (re-weighted from orphan 'head' -> canonical 'head_x')
  4. WaveHarp 3rd Form: Carillon Chime-Scythe (1x Scale, 96.5 cm Span, 35 Morphs)
  5. Live PIE Run 1 (L_MelusinaMorning — 60 FPS Runtime Verification)
  6. Live PIE Run 2 (L_MelusinaMorning — PossessedBP_MelusinaJRPGCharacter + ACFU Stack + Chime-Scythe)
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT_PATH = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaPhase1_20261017/ContactSheet_Melusina_Final_Lookdev_And_ACFU_2026-10-17.png"

PANELS = [
    (
        "1. MELUSINA V2 BODY + MOCAP-CONV IDLE\n(A_Shin_Idle_stand_MocapConv, 120 FACS Morphs, T_Melusina_FaceSDF)",
        "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaPhase1_20261017/previews/Preview_02_Melusina_V2_IdleMocapConv.png",
    ),
    (
        "2. SIR MELODIOUS CANONICAL ARP v7\n(SKM_SirMelodious_ARP_v7 + ABP_SirMelodious_v7 — Fixed PlayerUnit & Intro)",
        "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaPhase1_20261017/previews/Preview_01_SirMelodious_ARPv7.png",
    ),
    (
        "3. MELUSINA V2 HAT (HEAD_X RE-WEIGHTED)\n(SK_Melusina_V2_Hat_Fixed — Orphan 'head' -> 'head_x' + Wardrobe Default)",
        "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaPhase1_20261017/previews/Preview_03_Melusina_V2_Hat.png",
    ),
    (
        "4. WAVEHARP 3RD FORM: CARILLON CHIME-SCYTHE\n(SK_ME_WaveHarp_Scythe — 1x Scale, 96.5 cm Span, 35 Morphs, 4 Sockets)",
        "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaPhase1_20261017/previews/Preview_04_WaveHarp_Scythe.png",
    ),
    (
        "5. LIVE PIE RUN — REAR 3/4 DUO + FIRST RESONANCE LOCK\n(Melusina + Sir Melodious v7 Pure + Flared Shirt + Chladni Slime)",
        "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaPhase1_20261017/pie_wave4_showcase/frame_002.png",
    ),
    (
        "6. LIVE PIE RUN — FRONT 3/4 HERO PORTRAIT + CHIME-SCYTHE\n(head_x Face/Hat + FaceSDF + WaterHair Cosmos + 1x Chime-Scythe + ACFU)",
        "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaPhase1_20261017/pie_wave4_showcase/frame_004.png",
    ),
]


def main():
    tile_w, tile_h = 640, 480
    header_h = 70
    label_h = 56
    pad = 18
    cols, rows = 3, 2

    canvas_w = cols * tile_w + (cols + 1) * pad
    canvas_h = header_h + rows * (tile_h + label_h) + (rows + 1) * pad

    canvas = Image.new("RGB", (canvas_w, canvas_h), (14, 12, 24))
    draw = ImageDraw.Draw(canvas)

    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
        font_label = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 14)
    except Exception:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    draw.text(
        (pad, 20),
        "MELUSINA RUNTIME ANIMATION, FACIAL LOOKDEV, SIR MELODIOUS v7 & ACFU 4.3.5 CONVERGENCE — MILESTONE SHEET (2026-10-17)",
        fill=(245, 236, 215),
        font=font_title,
    )

    for idx, (caption, img_path) in enumerate(PANELS):
        c = idx % cols
        r = idx // cols
        x0 = pad + c * (tile_w + pad)
        y0 = header_h + pad + r * (tile_h + label_h + pad)

        # Label box
        draw.rectangle([x0, y0, x0 + tile_w, y0 + label_h], fill=(28, 24, 46), outline=(92, 78, 138), width=1)
        draw.text((x0 + 10, y0 + 8), caption, fill=(230, 220, 250), font=font_label)

        # Image box
        img_y0 = y0 + label_h
        if os.path.isfile(img_path):
            im = Image.open(img_path).convert("RGB")
            im.thumbnail((tile_w, tile_h), Image.Resampling.LANCZOS)
            bg = Image.new("RGB", (tile_w, tile_h), (20, 18, 34))
            ox = (tile_w - im.width) // 2
            oy = (tile_h - im.height) // 2
            bg.paste(im, (ox, oy))
            canvas.paste(bg, (x0, img_y0))
        draw.rectangle([x0, img_y0, x0 + tile_w, img_y0 + tile_h], outline=(92, 78, 138), width=2)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    canvas.save(OUT_PATH, "PNG")
    print("WROTE_CONTACT_SHEET=" + OUT_PATH)


if __name__ == "__main__":
    main()
