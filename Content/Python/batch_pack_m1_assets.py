"""
Batch Packing Script for Milestone 1: PBR Texture Channel Standardization
========================================================================
Executes full PBR packing across:
    1. Melusina Wardrobe Sets (Shirt, FrontPanel, Shawl, Skirt, Sleeve, Bow, Gloves, Boot, Iris)
    2. Rhinestone Bling Sets (Bling 01-15)
    3. Trimsheet Cloth and Zen Variants (Linen, Gingham, Plush, Base4K, HeartTiles, Concrete, etc.)

Author: Teamwork PBR Pipeline Worker (Milestone 1)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Add Content/Python to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from melodia_pbr_packer import ChannelSlot, PBRChannelPacker
from validate_melodia_pipeline import PipelineValidator


def pack_all_milestone1_assets():
    project_root = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
    content_dir = project_root / "Content"
    imports_dir = project_root / "Imports"

    melusina_out = content_dir / "Melodia" / "Characters" / "Melusina" / "Textures"
    textures_out = content_dir / "Textures"
    bling_out = textures_out / "Bling"

    melusina_out.mkdir(parents=True, exist_ok=True)
    textures_out.mkdir(parents=True, exist_ok=True)
    bling_out.mkdir(parents=True, exist_ok=True)

    packer = PBRChannelPacker()
    all_results = []

    print("==================================================================")
    print("Executing Batch Packing for Milestone 1 PBR Standard")
    print("==================================================================")

    # -------------------------------------------------------------------------
    # 1. Melusina Wardrobe Sets
    # -------------------------------------------------------------------------
    print("\n--- 1. Melusina Wardrobe & Hero Garments ---")
    melusina_source_dir = imports_dir / "MelusinaTextures"

    melusina_mappings = [
        ("MelusinaUpdatedShirt", "Melusina_UpdatedShirt"),
        ("m_frontpanel", "Melusina_FrontPanel"),
        ("m_shawl", "Melusina_Shawl"),
        ("m_skirt", "Melusina_Skirt"),
        ("m_sleeve", "Melusina_Sleeve"),
        ("m_bow", "Melusina_Bow"),
        ("m_gloves", "Melusina_Gloves"),
        ("m_boot", "Melusina_Boot"),
        ("M_Iris_front", "Melusina_IrisFront"),
        ("M_Iris_Back", "Melusina_IrisBack"),
        ("M_Melusina", "Melusina_Body"),
        ("skirtpanel.004", "Melusina_SkirtPanel"),
    ]

    for src_prefix, clean_name in melusina_mappings:
        channels = {}
        # Check source files
        ch_types = [
            ("BaseColor", ChannelSlot.BASECOLOR),
            ("Roughness", ChannelSlot.ROUGHNESS),
            ("Metallic", ChannelSlot.METALLIC),
            ("Normal", ChannelSlot.NORMAL),
            ("Displacement", ChannelSlot.HEIGHT),
            ("Emission", ChannelSlot.EMISSION),
            ("Alpha", ChannelSlot.MASK),
        ]
        for suffix, slot in ch_types:
            file_p = melusina_source_dir / f"{src_prefix}_{suffix}.png"
            if file_p.exists():
                channels[slot] = file_p

        # Fallback to root Melusina'sUpdatedShirt_*.png if needed
        if src_prefix == "MelusinaUpdatedShirt" and not channels.get(ChannelSlot.BASECOLOR):
            for suffix, slot in ch_types:
                file_p = project_root / f"Melusina'sUpdatedShirt_{suffix}.png"
                if file_p.exists():
                    channels[slot] = file_p

        if channels:
            print(f"Packing Melusina Set: {clean_name} ({len(channels)} source maps)")
            # Export to Melodia Characters folder
            res_m = packer.process_material_set(
                material_name=clean_name,
                channel_files=channels,
                output_dir=melusina_out,
                prefix="T_",
                target_resolution=(4096, 4096),
            )
            all_results.append(res_m)

            # For UpdatedShirt and FrontPanel, also export standardized versions to Content/Textures/
            if clean_name in ("Melusina_UpdatedShirt", "Melusina_FrontPanel"):
                res_t = packer.process_material_set(
                    material_name=clean_name,
                    channel_files=channels,
                    output_dir=textures_out,
                    prefix="T_",
                    target_resolution=(4096, 4096),
                )
                all_results.append(res_t)

    # -------------------------------------------------------------------------
    # 2. Rhinestone Bling Sets (Bling 01-15)
    # -------------------------------------------------------------------------
    print("\n--- 2. Substance Source Bling Vol 3 Rhinestones (01-15) ---")
    bling_src_dir = imports_dir / "SubstanceSource" / "BlingVol3" / "rhinestoneTextures"

    for i in range(1, 16):
        num_str = f"{i:02d}"
        channels = {}
        ch_map = [
            (f"bling_surface_vol3_{num_str}_ambientocclusion.jpg", ChannelSlot.AO),
            (f"bling_surface_vol3_{num_str}_basecolor.jpg", ChannelSlot.BASECOLOR),
            (f"bling_surface_vol3_{num_str}_height.jpg", ChannelSlot.HEIGHT),
            (f"bling_surface_vol3_{num_str}_metallic.jpg", ChannelSlot.METALLIC),
            (f"bling_surface_vol3_{num_str}_normal.jpg", ChannelSlot.NORMAL),
            (f"bling_surface_vol3_{num_str}_roughness.jpg", ChannelSlot.ROUGHNESS),
        ]
        for fname, slot in ch_map:
            p = bling_src_dir / fname
            if p.exists():
                channels[slot] = p

        if channels:
            b_name = f"Bling_Rhinestone{num_str}"
            print(f"Packing Bling Set: {b_name} ({len(channels)} source maps)")
            # Export to Bling folder and Textures folder
            res_b = packer.process_material_set(
                material_name=b_name,
                channel_files=channels,
                output_dir=bling_out,
                prefix="T_",
                target_resolution=(2048, 2048),
            )
            all_results.append(res_b)

            res_b_root = packer.process_material_set(
                material_name=b_name,
                channel_files=channels,
                output_dir=textures_out,
                prefix="T_",
                target_resolution=(2048, 2048),
            )
            all_results.append(res_b_root)

    # -------------------------------------------------------------------------
    # 3. Trimsheets & Fabric Sets
    # -------------------------------------------------------------------------
    print("\n--- 3. Trimsheet Cloth & Zen Variants ---")

    # 3a. PBR Fabrics -> ClothTrims
    pbr_fabrics_dir = imports_dir / "Environment" / "PBRFabrics"
    cloth_fabric_mappings = [
        ("linen-slub", "51", "ClothTrim_Linen"),
        ("gingham", "198", "ClothTrim_Gingham"),
        ("plush-cut-pile", "73", "ClothTrim_Plush"),
    ]

    for fab_folder, fab_id, variant_name in cloth_fabric_mappings:
        channels = {}
        sub_dir = pbr_fabrics_dir / "fabric" / fab_folder / fab_id
        if sub_dir.exists():
            channels[ChannelSlot.AO] = sub_dir / f"fabric-{fab_folder}-ambientOcclusion-{fab_id}-1024.png"
            channels[ChannelSlot.BASECOLOR] = sub_dir / f"fabric-{fab_folder}-baseColor-{fab_id}-1024.png"
            channels[ChannelSlot.HEIGHT] = sub_dir / f"fabric-{fab_folder}-height-{fab_id}-1024.png"
            channels[ChannelSlot.NORMAL] = sub_dir / f"fabric-{fab_folder}-normal-{fab_id}-1024.png"
            channels[ChannelSlot.ROUGHNESS] = sub_dir / f"fabric-{fab_folder}-roughness-{fab_id}-1024.png"

        valid_channels = {k: v for k, v in channels.items() if v.exists()}
        if valid_channels:
            print(f"Packing ClothTrim Set: {variant_name} ({len(valid_channels)} source maps)")
            res_c = packer.process_material_set(
                material_name=variant_name,
                channel_files=valid_channels,
                output_dir=textures_out,
                prefix="T_",
                target_resolution=(2048, 2048),
            )
            all_results.append(res_c)

    # 3b. HeartTiles & Concrete Trims
    heart_channels = {}
    for suffix, slot in [
        ("BaseColor", ChannelSlot.BASECOLOR),
        ("Roughness", ChannelSlot.ROUGHNESS),
        ("Metallic", ChannelSlot.METALLIC),
        ("Normal", ChannelSlot.NORMAL),
        ("Displacement", ChannelSlot.HEIGHT),
        ("Emission", ChannelSlot.EMISSION),
        ("Alpha", ChannelSlot.MASK),
    ]:
        p = textures_out / f"HeartTilesBase_{suffix}.png"
        if p.exists():
            heart_channels[slot] = p

    if heart_channels:
        print(f"Packing HeartTiles Set: ClothTrim_Base4K / Trimsheet_HeartTiles")
        res_ht = packer.process_material_set(
            material_name="ClothTrim_Base4K",
            channel_files=heart_channels,
            output_dir=textures_out,
            prefix="T_",
            target_resolution=(4096, 4096),
        )
        all_results.append(res_ht)

        res_ht2 = packer.process_material_set(
            material_name="Trimsheet_HeartTiles",
            channel_files=heart_channels,
            output_dir=textures_out,
            prefix="T_",
            target_resolution=(4096, 4096),
        )
        all_results.append(res_ht2)

    # Concrete Trim
    concrete_src = imports_dir / "Environment" / "Trimsheets" / "Concrete"
    concrete_channels = {}
    for suffix, slot in [
        ("BaseColor", ChannelSlot.BASECOLOR),
        ("Roughness", ChannelSlot.ROUGHNESS),
        ("Metallic", ChannelSlot.METALLIC),
        ("Normal", ChannelSlot.NORMAL),
        ("Emission", ChannelSlot.EMISSION),
        ("Alpha", ChannelSlot.MASK),
    ]:
        p = concrete_src / f"DefaultMaterial_{suffix}.png"
        if p.exists():
            concrete_channels[slot] = p

    if concrete_channels:
        print(f"Packing Concrete Set: ZenTrim_Base4K / Trimsheet_Concrete")
        res_zt = packer.process_material_set(
            material_name="ZenTrim_Base4K",
            channel_files=concrete_channels,
            output_dir=textures_out,
            prefix="T_",
            target_resolution=(2048, 2048),
        )
        all_results.append(res_zt)

        res_zt2 = packer.process_material_set(
            material_name="Trimsheet_Concrete",
            channel_files=concrete_channels,
            output_dir=textures_out,
            prefix="T_",
            target_resolution=(2048, 2048),
        )
        all_results.append(res_zt2)

    # ZenTrim Variants (ColourShift, CrackedToHell, FlowersLittleBit, FlowersLots, FlowersMid, Wet)
    zen_variants = [
        ("ZenTrim_ColourShift", 200, 100),
        ("ZenTrim_CrackedToHell", 220, 150),
        ("ZenTrim_FlowersLIttleBit", 240, 120),
        ("ZenTrim_FlowersLOTS", 230, 140),
        ("ZenTrim_FlowersMid", 235, 130),
        ("ZenTrim_Wet", 150, 40), # Lower roughness for wet variation
    ]
    for z_name, ao_val, rough_val in zen_variants:
        print(f"Generating ZenTrim Variant ORM: {z_name}")
        orm_path = textures_out / f"T_{z_name}_ORM.png"
        packer.pack_orm(
            ao_path=None,
            roughness_path=None,
            metallic_path=None,
            output_path=orm_path,
            target_resolution=(2048, 2048),
        )
        # Apply custom roughness and AO variation
        from PIL import Image
        import numpy as np
        with Image.open(orm_path) as img:
            arr = np.array(img)
            arr[:, :, 0] = ao_val
            arr[:, :, 1] = rough_val
            arr[:, :, 2] = 0
            Image.fromarray(arr).save(orm_path)

    print("\n==================================================================")
    print(f"Batch Packing Completed: {len(all_results)} operations executed.")
    print("==================================================================")

    # -------------------------------------------------------------------------
    # 4. Run Complete Quality Validation
    # -------------------------------------------------------------------------
    print("\n--- 4. Running Pipeline Validation Harness ---")
    validator = PipelineValidator()

    # Collect all generated PNGs
    textures_to_validate = {}
    for scan_folder in [melusina_out, textures_out, bling_out]:
        for p in scan_folder.glob("*.png"):
            textures_to_validate[p.stem] = p

    report = validator.validate_texture_set(textures_to_validate)
    print(f"Total Textures Validated: {report.total_textures}")
    print(f"Passed:                  {report.passed_textures}")
    print(f"Failed:                  {report.failed_textures}")
    print(f"Warnings:                {report.warning_count}")
    print(f"Errors:                  {report.error_count}")
    print(f"Overall Valid:           {report.is_valid()}")

    report_path = project_root / "Saved" / "Audit" / "melodia_m1_pbr_validation.json"
    report.save(report_path)
    print(f"Validation Report saved: {report_path}")

    return report.is_valid()


if __name__ == "__main__":
    success = pack_all_milestone1_assets()
    sys.exit(0 if success else 1)
