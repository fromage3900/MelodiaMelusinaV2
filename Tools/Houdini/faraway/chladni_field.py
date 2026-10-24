r"""chladni_field.py -- the one Faraway Mother Chladni field, in Houdini metres.

F(u,v) = cos(n*pi*u)*cos(m*pi*v) - cos(m*pi*u)*cos(n*pi*v),  (n,m) = (3,5),
u = (X + 4000) / 8000,  v = (Y + 4000) / 8000   (X,Y in metres; 1 uu = 1 cm, so +-4000 m == +-400000 uu).

Same formula and frame as Tools/PCG/build_faraway_mother_pcg_ecosystem.py:evaluate_chladni, the authority.
Everything else (SilkPeak VEX, g1_stitch_proof, faraway_static_field, cook_field_atlas) should import from here.
Pure numpy, no hou. Embeddable in a Python SOP (names only, no relative imports).

    python Tools/Houdini/faraway/chladni_field.py --selftest
"""
import math

import numpy as np

N_MODE = 3
M_MODE = 5
HALF_M = 4000.0
PLATE_M = 2.0 * HALF_M
SEAM_THRESHOLD = 0.12           # |F| < this is the ResonantSeamWay band (area mask, not a curve)
TILE_M = 250.0
TILE_DIVISIONS = 128
LATTICE_M = TILE_M / TILE_DIVISIONS   # 1.953125 m: every tile origin must sit on this global lattice
GRAD_UV_MAX = 8.0 * math.pi           # sup |grad_uv F| for (3,5); the PCG "/8" divisor saturates 73% of the plate
GRAD_M_MAX = GRAD_UV_MAX / PLATE_M    # pi/1000 per metre


def uv(x_m, y_m):
    return (np.asarray(x_m, dtype=np.float64) + HALF_M) / PLATE_M, (np.asarray(y_m, dtype=np.float64) + HALF_M) / PLATE_M


def F_uv(u, v, n=N_MODE, m=M_MODE):
    pi = math.pi
    return np.cos(n * pi * u) * np.cos(m * pi * v) - np.cos(m * pi * u) * np.cos(n * pi * v)


def F(x_m, y_m, n=N_MODE, m=M_MODE):
    """Signed field at world metres. Range [-2, 2]; F(v,u) = -F(u,v)."""
    u, v = uv(x_m, y_m)
    return F_uv(u, v, n, m)


def grad(x_m, y_m, n=N_MODE, m=M_MODE):
    """Analytic (dF/dX, dF/dY) per metre."""
    pi = math.pi
    u, v = uv(x_m, y_m)
    fu = -n * pi * np.sin(n * pi * u) * np.cos(m * pi * v) + m * pi * np.sin(m * pi * u) * np.cos(n * pi * v)
    fv = -m * pi * np.cos(n * pi * u) * np.sin(m * pi * v) + n * pi * np.cos(m * pi * u) * np.sin(n * pi * v)
    return fu / PLATE_M, fv / PLATE_M


def tension01(x_m, y_m, n=N_MODE, m=M_MODE):
    """|grad F| in uv units over its true maximum -> 0..1 without the PCG saturation. NOT the PCG tension (that is /8)."""
    gx, gy = grad(x_m, y_m, n, m)
    return np.clip(np.hypot(gx, gy) * PLATE_M / GRAD_UV_MAX, 0.0, 1.0)


def seam_distance_m(x_m, y_m, n=N_MODE, m=M_MODE, eps=1e-9):
    """First-order distance to the F=0 curve, |F|/|grad F| in metres. Meaningless near grad F = 0 (origin, saddles)."""
    gx, gy = grad(x_m, y_m, n, m)
    return np.abs(F(x_m, y_m, n, m)) / np.maximum(np.hypot(gx, gy), eps)


def tile_of(x_m, y_m):
    """Global tile index (i, j) of a world point; tile (0,0) has its min corner at the world origin."""
    return int(math.floor(x_m / TILE_M)), int(math.floor(y_m / TILE_M))


def tile_min_corner(i, j):
    return i * TILE_M, j * TILE_M


def on_lattice(v_m, tol=1e-9):
    k = v_m / LATTICE_M
    return abs(k - round(k)) < tol


def pleat(x_m, y_m, wl, th_deg=35.0, warp=80.0, p=1.0):
    """Python twin of VEX chl_pleat: signed pleat profile in [-1, 1] on the global phase."""
    th = math.radians(th_deg)
    q = (np.asarray(x_m) * math.cos(th) + np.asarray(y_m) * math.sin(th) + warp * F(x_m, y_m)) / max(wl, 1.0)
    sv = np.sin(2.0 * math.pi * (q - np.floor(q)))
    return np.sign(sv) * np.abs(sv) ** max(p, 1.0)


def vex_function():
    """VEX source for a global F and analytic gradient (per metre); paste into a wrangle so it matches this module."""
    return (
        "float chl_F(float X; float Y; int n; int m) {\n"
        "    float u = (X + 4000.0) / 8000.0; float v = (Y + 4000.0) / 8000.0;\n"
        "    return cos(n*M_PI*u)*cos(m*M_PI*v) - cos(m*M_PI*u)*cos(n*M_PI*v);\n"
        "}\n"
        "vector2 chl_grad(float X; float Y; int n; int m) {\n"
        "    float u = (X + 4000.0) / 8000.0; float v = (Y + 4000.0) / 8000.0;\n"
        "    float fu = -n*M_PI*sin(n*M_PI*u)*cos(m*M_PI*v) + m*M_PI*sin(m*M_PI*u)*cos(n*M_PI*v);\n"
        "    float fv = -m*M_PI*cos(n*M_PI*u)*sin(m*M_PI*v) + n*M_PI*cos(m*M_PI*u)*sin(n*M_PI*v);\n"
        "    return set(fu, fv) / 8000.0;\n"
        "}\n"
        "// one global pleat phase for every Faraway terrain HDA: phi = X*cos(th) + Y*sin(th) + warp*F;\n"
        "// |grad phi| in [1-d, 1+d], d = warp*pi/1000. frac() before sin() keeps fp32 exact at |phi| ~ 4e3 m.\n"
        "float chl_pleat(float X; float Y; float wl; float th_deg; float warp; float p) {\n"
        "    float th = radians(th_deg);\n"
        "    float q = (X*cos(th) + Y*sin(th) + warp*chl_F(X, Y, 3, 5)) / max(wl, 1.0);\n"
        "    float sv = sin(2.0*M_PI*(q - floor(q)));\n"
        "    return sign(sv) * pow(abs(sv), max(p, 1.0));\n"
        "}\n"
    )


def _load_by_path(name, path):
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod         # dataclasses resolve cls.__module__ through sys.modules
    spec.loader.exec_module(mod)
    return mod


def selftest():
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    rng = np.random.default_rng(3900)
    X = rng.uniform(-HALF_M, HALF_M, 400)
    Y = rng.uniform(-HALF_M, HALF_M, 400)
    bad = []

    def check(name, ok, detail=""):
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
        if not ok:
            bad.append(name)

    # authority parity, to the bit
    pcg = _load_by_path("_pcg_auth", root / "Tools" / "PCG" / "build_faraway_mother_pcg_ecosystem.py")
    worst = max(abs(float(F(x, y)) - pcg.evaluate_chladni((x + HALF_M) / PLATE_M, (y + HALF_M) / PLATE_M, 3, 5)) for x, y in zip(X, Y))
    check("matches PCG evaluate_chladni", worst < 1e-12, f"worst {worst:.2e}")

    try:
        sf = _load_by_path("_static_field", root / "Tools" / "Houdini" / "vdm_fabric_mountains" / "faraway_static_field.py")
        u, v = uv(X, Y)
        worst = float(np.max(np.abs(F(X, Y) - sf._chladni(u, v, 3, 5))))
        check("matches faraway_static_field._chladni", worst < 1e-12, f"worst {worst:.2e}")
    except Exception as e:  # Pillow etc. may be missing; the PCG parity above is the one that matters
        print(f"[SKIP] faraway_static_field parity: {type(e).__name__}: {e}")

    # symmetries and nodal set of the (3,5) plate
    check("antisymmetric F(v,u)=-F(u,v)", float(np.max(np.abs(F(X, Y) + F(Y, X)))) < 1e-12)
    line = np.linspace(-HALF_M, HALF_M, 257)
    for nm, a, b in (("X=0", np.zeros_like(line), line), ("Y=0", line, np.zeros_like(line)), ("X=Y", line, line), ("X=-Y", line, -line)):
        check(f"nodal on {nm}", float(np.max(np.abs(F(a, b)))) < 1e-12)
    gx0, gy0 = grad(0.0, 0.0)
    check("grad F = 0 at the origin (the 8-way crossing)", abs(float(gx0)) < 1e-12 and abs(float(gy0)) < 1e-12)

    # analytic gradient vs central difference
    h = 0.05
    gx, gy = grad(X, Y)
    nx = (F(X + h, Y) - F(X - h, Y)) / (2 * h)
    ny = (F(X, Y + h) - F(X, Y - h)) / (2 * h)
    err = float(max(np.max(np.abs(gx - nx)), np.max(np.abs(gy - ny))))
    check("analytic grad == central difference", err < 1e-8, f"worst {err:.2e} /m (limit 1e-8)")

    # gradient bound
    gg = np.linspace(-HALF_M, HALF_M, 1601)
    GX, GY = np.meshgrid(gg, gg)
    gmx, gmy = grad(GX, GY)
    top = float(np.max(np.hypot(gmx, gmy)))
    check("sup|grad F| = pi/1000 per metre", abs(top - GRAD_M_MAX) / GRAD_M_MAX < 1e-3, f"{top:.6e} vs {GRAD_M_MAX:.6e}")

    # the PCG tension (/8) saturation claim, so the number in the docs is re-derivable
    sat = float(np.mean(np.hypot(gmx, gmy) * PLATE_M / 8.0 >= 1.0))
    check("PCG tension (/8) saturates on a majority of the plate", sat > 0.5, f"{sat:.0%}")
    t01 = tension01(GX, GY)
    check("tension01 is not saturated", float(np.mean(t01 >= 1.0)) < 0.02, f"{float(np.mean(t01 >= 1.0)):.1%} at 1.0, mean {float(np.mean(t01)):.2f}")

    # first-order seam distance, against a brute-force nearest sign change on a fine line through a seam crossing
    # probe a clean stretch of the Y=0 seam, away from the origin's 8-way crossing where grad F -> 0 and
    # |F|/|grad F| underestimates (F ~ r^4 there: at (350,120) it reads ~91 m for a true 120 m)
    px, py = 2000.0, 100.0
    d_est = float(seam_distance_m(px, py))
    xs = np.linspace(px - 200, px + 200, 40001)
    ys = np.linspace(py - 200, py + 200, 40001)
    # nearest point on the F=0 level set within the window, found from grid sign changes
    GXs, GYs = np.meshgrid(xs[::100], ys[::100])
    Fw = F(GXs, GYs)
    sgn = np.sign(Fw)
    edge = (sgn[:, 1:] != sgn[:, :-1])[:-1, :] | (sgn[1:, :] != sgn[:-1, :])[:, :-1]
    ex, ey = GXs[:-1, :-1][edge], GYs[:-1, :-1][edge]
    d_true = float(np.min(np.hypot(ex - px, ey - py)))
    check("seam_distance_m within 15% of brute force", abs(d_est - d_true) / d_true < 0.15, f"est {d_est:.2f} m, brute {d_true:.2f} m")

    # pleat phase: gradient bound and continuity across a tile border
    for warp in (80.0, 127.0):
        th = math.radians(35.0)
        pgx, pgy = math.cos(th) + warp * gmx, math.sin(th) + warp * gmy
        mag = np.hypot(pgx, pgy)
        d = warp * GRAD_M_MAX
        check(f"|grad phi| within [1-d, 1+d] at warp {warp:g}", float(mag.min()) >= 1 - d - 1e-9 and float(mag.max()) <= 1 + d + 1e-9,
              f"[{float(mag.min()):.3f}, {float(mag.max()):.3f}] vs d={d:.3f}")
    ys = np.linspace(-300, 300, 601)
    jump = float(np.max(np.abs(pleat(249.9999, ys, 36.0) - pleat(250.0001, ys, 36.0))))
    check("pleat continuous across x=250 border", jump < 1e-2, f"max jump {jump:.2e}")
    q0 = (10.0 * math.cos(math.radians(35)) + 20.0 * math.sin(math.radians(35)) + 80.0 * float(F(10.0, 20.0))) / 36.0
    check("pleat exponent 1 is a pure sine", abs(float(pleat(10.0, 20.0, 36.0)) - math.sin(2 * math.pi * (q0 % 1.0))) < 1e-12)

    # lattice
    check("LATTICE_M = 250/128 = 1.953125", LATTICE_M == 1.953125)
    check("tile origins 250 m are lattice aligned", all(on_lattice(k * TILE_M) for k in range(-16, 17)))
    check("tile_of / tile_min_corner round trip", tile_of(*tile_min_corner(-3, 7)) == (-3, 7) and tile_of(249.999, -0.001) == (0, -1))
    check("VEX snippet carries the same constants", "cos(n*M_PI*u)*cos(m*M_PI*v) - cos(m*M_PI*u)*cos(n*M_PI*v)" in vex_function() and "8000.0" in vex_function() and "chl_pleat" in vex_function())

    print("[PASS] all" if not bad else f"[FAIL] {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest() if "--selftest" in sys.argv else (print(__doc__) or 0))
