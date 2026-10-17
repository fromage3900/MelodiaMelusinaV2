#!/usr/bin/env python3
"""
Dual-mode script:
  1. When run inside Blender (--factory-startup), dumps evaluated poses + triangles + material IDs to waveharp_sheet_data.npz.
  2. When run inside system Python (C:/Python314/python.exe), renders the 4-panel high-res contact sheet PNG.
"""
import os
import sys
import numpy as np

STAGE_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Staging/WaveHarpScythe_20261017"
FBX_PATH = os.path.join(STAGE_DIR, "SK_ME_WaveHarp_Scythe.fbx")
NPZ_PATH = os.path.join(STAGE_DIR, "waveharp_sheet_data.npz")
OUT_SHEET = os.path.join(STAGE_DIR, "ContactSheet_WaveHarp_3Forms_2026-10-17.png")


def dump_from_blender():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)
    ob = next(o for o in bpy.data.objects if o.type == "MESH")
    mesh = ob.data
    kb = mesh.shape_keys.key_blocks

    n_verts = len(mesh.vertices)
    basis = np.zeros((n_verts, 3), dtype=np.float32)
    kb["Basis"].data.foreach_get("co", basis.ravel())

    bow = np.zeros_like(basis)
    kb["Bow_Deployment"].data.foreach_get("co", bow.ravel())
    draw = np.zeros_like(basis)
    kb["Draw"].data.foreach_get("co", draw.ravel())
    flex = np.zeros_like(basis)
    kb["Flex_Draw"].data.foreach_get("co", flex.ravel())
    pose_bow = bow + 0.55 * (draw - basis) + 0.55 * (flex - basis)

    scy = np.zeros_like(basis)
    kb["Scythe_Deployment"].data.foreach_get("co", scy.ravel())
    res4 = np.zeros_like(basis)
    kb["Scythe_Residual_04"].data.foreach_get("co", res4.ravel())
    alpha = 4.0 / 9.0
    pose_mid = basis * (1.0 - alpha) + scy * alpha + (res4 - basis)

    chord = np.zeros_like(basis)
    kb["Scythe_Chord_Tension"].data.foreach_get("co", chord.ravel())
    bell = np.zeros_like(basis)
    kb["Scythe_Bell_Swing"].data.foreach_get("co", bell.ravel())
    pose_scythe = scy + 0.35 * (chord - basis) + 0.45 * (bell - basis)

    mesh.calc_loop_triangles()
    tris = np.array([[lt.vertices[0], lt.vertices[1], lt.vertices[2]] for lt in mesh.loop_triangles], dtype=np.int32)
    mat_idx = np.array([lt.material_index for lt in mesh.loop_triangles], dtype=np.int32)

    np.savez_compressed(
        NPZ_PATH,
        astrolabe=basis,
        bow=pose_bow,
        scythe_mid=pose_mid,
        scythe=pose_scythe,
        tris=tris,
        mat_idx=mat_idx,
    )
    print("DUMPED_NPZ=" + NPZ_PATH)


def render_with_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    data = np.load(NPZ_PATH)
    tris = data["tris"]
    mat_idx = data["mat_idx"]

    palette = {
        0: (0.65, 0.92, 1.0, 0.85),   # Strings: glowing cyan-silver
        1: (0.95, 0.78, 0.54, 0.95),  # PaleBrass / RoseGold
        2: (0.96, 0.95, 0.98, 0.95),  # IvoryPearl
        3: (0.92, 0.66, 0.52, 0.95),  # RoseGold
        4: (0.35, 0.80, 1.0, 0.95),   # CrystalBlue
        5: (0.80, 0.45, 0.98, 0.95),  # CrystalViolet
        6: (0.60, 0.40, 0.90, 0.95),  # Chladni Ultraviolet
        7: (0.84, 0.68, 0.96, 0.95),  # EnamelLilac
    }

    fig = plt.figure(figsize=(20, 7.5), dpi=160, facecolor="#0e0c18")
    fig.suptitle(
        "MELUSINA WAVEHARP — 3-FORM HARMONIC TRANSFORMATION CONTACT SHEET (SK_ME_WaveHarp)",
        color="#f5ecd7", fontsize=15, fontweight="bold", y=0.96
    )

    panels = [
        ("FORM 0: FLOATING ASTROLABE\n(Caster / Exploration — Basis)", "astrolabe"),
        ("FORM 1: WAVEHARP BOW\n(RMB Charged Sparrow Draw — Bow_Deployment + Draw)", "bow"),
        ("TRANSITION: HARMONIC UNFOLD\n(ScytheAlpha = 0.44 + Scythe_Residual_04)", "scythe_mid"),
        ("FORM 2: CARILLON CHIME-SCYTHE\n(ACFU Melee Combo — Scythe_Deployment + Sockets)", "scythe"),
    ]

    step = 1 if len(tris) <= 25000 else 2
    tris_sub = tris[::step]
    mat_sub = mat_idx[::step]
    face_colors = [palette.get(int(m), (0.85, 0.85, 0.9, 0.9)) for m in mat_sub]

    for idx, (title, key) in enumerate(panels, start=1):
        ax = fig.add_subplot(1, 4, idx, projection="3d", facecolor="#141124")
        pts = data[key]
        poly_verts = pts[tris_sub]
        coll = Poly3DCollection(poly_verts, facecolors=face_colors, linewidths=0.06, edgecolors=(0.18, 0.14, 0.28, 0.2))
        ax.add_collection3d(coll)

        if key == "scythe":
            sockets = {
                "Scythe_BladeStart\n(Chime Throat)": (6.8, 0.0, 32.0),
                "Scythe_BladeMid\n(Crescent Belly)": (26.5, 0.0, 36.0),
                "Scythe_BladeTip\n(Harmonic Point)": (43.5, 0.0, 17.5),
                "Scythe_Pommel\n(Tuning Fork)": (1.5, 0.0, -40.5),
            }
            for s_name, (sx, sy, sz) in sockets.items():
                ax.scatter([sx], [sy], [sz], color="#00ffcc", s=60, zorder=10, edgecolors="white", linewidths=1.2)
                ax.text(sx + 2.0, sy, sz + 2.5, s_name, color="#80ffe5", fontsize=7.5, fontweight="bold")
            ax.plot([6.8, 26.5, 43.5], [0, 0, 0], [32.0, 36.0, 17.5], color="#ff44aa", linewidth=2.4, linestyle="--")

        ax.set_xlim(-25, 65)
        ax.set_ylim(-40, 40)
        ax.set_zlim(-55, 105)
        ax.view_init(elev=12, azim=-78)
        ax.set_title(title, color="#e8dff5", fontsize=10, pad=10, fontweight="bold")
        ax.set_xlabel("X Reach (cm)", color="#9a8fb8", fontsize=8)
        ax.set_zlabel("Z Height (cm)", color="#9a8fb8", fontsize=8)
        ax.tick_params(colors="#7c7199", labelsize=7)
        ax.set_yticks([])
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.grid(True, color="#2a2442", linestyle=":", linewidth=0.5)

    plt.tight_layout(rect=[0.01, 0.02, 0.99, 0.91])
    plt.savefig(OUT_SHEET, dpi=160, facecolor=fig.get_facecolor())
    print("WROTE_SHEET=" + OUT_SHEET)


if __name__ == "__main__":
    try:
        import bpy as _bpy  # noqa: F401
        in_blender = True
    except ImportError:
        in_blender = False

    if in_blender:
        dump_from_blender()
    else:
        render_with_matplotlib()
